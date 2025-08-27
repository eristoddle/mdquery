"""
Concurrent request handling and database coordination for mdquery MCP server.

This module provides comprehensive concurrent access management for multiple
AI assistants accessing the MCP server simultaneously, ensuring data consistency,
proper database locking, and optimal performance under concurrent load.
"""

import asyncio
import logging
import sqlite3
import threading
import time
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable, Awaitable
from threading import RLock, Semaphore, Event
import weakref

from .exceptions import DatabaseError, ResourceError, PerformanceError

logger = logging.getLogger(__name__)


class RequestType(Enum):
    """Types of requests for priority management."""
    READ_ONLY = "read_only"
    WRITE = "write"
    ANALYSIS = "analysis"
    INDEXING = "indexing"
    ADMIN = "admin"


class RequestPriority(Enum):
    """Request priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class RequestContext:
    """Context information for a concurrent request."""
    request_id: str
    client_id: str
    request_type: RequestType
    priority: RequestPriority
    started_at: datetime
    tool_name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    timeout_seconds: float = 30.0
    estimated_duration: Optional[float] = None


@dataclass
class ConcurrentStats:
    """Statistics for concurrent request handling."""
    total_requests: int = 0
    active_requests: int = 0
    queued_requests: int = 0
    completed_requests: int = 0
    failed_requests: int = 0
    avg_wait_time: float = 0.0
    avg_execution_time: float = 0.0
    peak_concurrent_requests: int = 0
    database_lock_contentions: int = 0


class DatabaseLockManager:
    """
    Manages database access coordination for concurrent requests.

    Implements read-write locking with priority handling and deadlock prevention.
    """

    def __init__(self, max_concurrent_readers: int = 10):
        """Initialize database lock manager."""
        self.max_concurrent_readers = max_concurrent_readers

        # Read-write lock implementation
        self._readers_count = 0
        self._writers_waiting = 0
        self._writer_active = False

        # Synchronization primitives
        self._lock = RLock()
        self._readers_semaphore = Semaphore(max_concurrent_readers)
        self._writer_lock = threading.Lock()
        self._no_readers = threading.Condition(self._lock)
        self._no_writer = threading.Condition(self._lock)

        # Request tracking
        self._active_requests: Dict[str, RequestContext] = {}
        self._lock_contentions = 0

    @contextmanager
    def read_lock(self, request_context: RequestContext):
        """Acquire read lock for database access."""
        start_time = time.time()

        try:
            with self._lock:
                # Wait for writers to finish
                while self._writer_active or self._writers_waiting > 0:
                    if time.time() - start_time > request_context.timeout_seconds:
                        self._lock_contentions += 1
                        raise ResourceError(f"Read lock timeout after {request_context.timeout_seconds}s")

                    self._no_writer.wait(timeout=1.0)

                # Acquire reader semaphore
                if not self._readers_semaphore.acquire(blocking=False):
                    self._lock_contentions += 1
                    raise ResourceError("Too many concurrent readers")

                self._readers_count += 1
                self._active_requests[request_context.request_id] = request_context

                logger.debug(f"Read lock acquired: {request_context.request_id} ({self._readers_count} active readers)")

            yield

        finally:
            with self._lock:
                self._readers_count -= 1
                self._active_requests.pop(request_context.request_id, None)
                self._readers_semaphore.release()

                if self._readers_count == 0:
                    self._no_readers.notify_all()

                logger.debug(f"Read lock released: {request_context.request_id} ({self._readers_count} active readers)")

    @contextmanager
    def write_lock(self, request_context: RequestContext):
        """Acquire write lock for database access."""
        start_time = time.time()

        try:
            with self._lock:
                self._writers_waiting += 1

                # Wait for other writers and all readers to finish
                while self._writer_active or self._readers_count > 0:
                    if time.time() - start_time > request_context.timeout_seconds:
                        self._writers_waiting -= 1
                        self._lock_contentions += 1
                        raise ResourceError(f"Write lock timeout after {request_context.timeout_seconds}s")

                    if self._writer_active:
                        self._no_writer.wait(timeout=1.0)
                    else:
                        self._no_readers.wait(timeout=1.0)

                # Acquire writer lock
                self._writers_waiting -= 1
                self._writer_active = True
                self._active_requests[request_context.request_id] = request_context

                logger.debug(f"Write lock acquired: {request_context.request_id}")

            yield

        finally:
            with self._lock:
                self._writer_active = False
                self._active_requests.pop(request_context.request_id, None)

                # Notify waiting readers and writers
                self._no_writer.notify_all()

                logger.debug(f"Write lock released: {request_context.request_id}")

    def get_lock_stats(self) -> Dict[str, Any]:
        """Get database lock statistics."""
        with self._lock:
            return {
                'active_readers': self._readers_count,
                'writers_waiting': self._writers_waiting,
                'writer_active': self._writer_active,
                'active_requests': len(self._active_requests),
                'lock_contentions': self._lock_contentions,
                'max_concurrent_readers': self.max_concurrent_readers
            }


class RequestQueue:
    """
    Priority queue for managing concurrent requests.

    Implements fair scheduling with priority handling and timeout management.
    """

    def __init__(self, max_queue_size: int = 100):
        """Initialize request queue."""
        self.max_queue_size = max_queue_size
        self._queue: List[RequestContext] = []
        self._lock = threading.Lock()
        self._not_empty = threading.Condition(self._lock)
        self._queue_stats = {
            'enqueued': 0,
            'dequeued': 0,
            'timeouts': 0,
            'peak_size': 0
        }

    def enqueue(self, request_context: RequestContext) -> bool:
        """
        Add request to queue.

        Returns:
            bool: True if request was queued, False if queue is full
        """
        with self._lock:
            if len(self._queue) >= self.max_queue_size:
                logger.warning(f"Request queue full, rejecting request: {request_context.request_id}")
                return False

            # Insert based on priority (higher priority first)
            inserted = False
            for i, queued_request in enumerate(self._queue):
                if request_context.priority.value > queued_request.priority.value:
                    self._queue.insert(i, request_context)
                    inserted = True
                    break

            if not inserted:
                self._queue.append(request_context)

            self._queue_stats['enqueued'] += 1
            self._queue_stats['peak_size'] = max(self._queue_stats['peak_size'], len(self._queue))

            self._not_empty.notify()

            logger.debug(f"Request queued: {request_context.request_id} (queue size: {len(self._queue)})")
            return True

    def dequeue(self, timeout: Optional[float] = None) -> Optional[RequestContext]:
        """
        Remove and return next request from queue.

        Args:
            timeout: Maximum time to wait for a request

        Returns:
            RequestContext or None if timeout
        """
        with self._not_empty:
            while not self._queue:
                if not self._not_empty.wait(timeout):
                    return None

            # Remove expired requests
            current_time = datetime.now()
            while self._queue:
                request = self._queue[0]
                elapsed = (current_time - request.started_at).total_seconds()

                if elapsed > request.timeout_seconds:
                    self._queue.pop(0)
                    self._queue_stats['timeouts'] += 1
                    logger.warning(f"Request timed out in queue: {request.request_id}")
                    continue

                break

            if not self._queue:
                return None

            request = self._queue.pop(0)
            self._queue_stats['dequeued'] += 1

            logger.debug(f"Request dequeued: {request.request_id} (queue size: {len(self._queue)})")
            return request

    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        with self._lock:
            return {
                'current_size': len(self._queue),
                'max_size': self.max_queue_size,
                **self._queue_stats
            }


class ConcurrentRequestManager:
    """
    Comprehensive concurrent request manager for MCP server.

    Coordinates multiple AI assistants accessing the server simultaneously,
    ensuring data consistency and optimal performance.
    """

    def __init__(self,
                 max_concurrent_requests: int = 20,
                 max_queue_size: int = 100,
                 default_timeout: float = 30.0):
        """Initialize concurrent request manager."""
        self.max_concurrent_requests = max_concurrent_requests
        self.default_timeout = default_timeout

        # Core components
        self.db_lock_manager = DatabaseLockManager()
        self.request_queue = RequestQueue(max_queue_size)

        # Request tracking
        self._active_requests: Dict[str, RequestContext] = {}
        self._request_history: deque = deque(maxlen=1000)
        self._client_sessions: Dict[str, Set[str]] = defaultdict(set)

        # Synchronization
        self._lock = RLock()
        self._request_semaphore = Semaphore(max_concurrent_requests)

        # Statistics
        self._stats = ConcurrentStats()

        # Background cleanup task
        self._cleanup_event = Event()
        self._cleanup_thread = threading.Thread(target=self._cleanup_expired_requests, daemon=True)
        self._cleanup_thread.start()

    def create_request_context(self,
                             client_id: str,
                             tool_name: str,
                             request_type: RequestType = RequestType.READ_ONLY,
                             priority: RequestPriority = RequestPriority.NORMAL,
                             timeout_seconds: Optional[float] = None,
                             **parameters) -> RequestContext:
        """Create a new request context."""
        return RequestContext(
            request_id=str(uuid.uuid4()),
            client_id=client_id,
            request_type=request_type,
            priority=priority,
            started_at=datetime.now(),
            tool_name=tool_name,
            parameters=parameters,
            timeout_seconds=timeout_seconds or self.default_timeout
        )

    @asynccontextmanager
    async def handle_request(self, request_context: RequestContext):
        """
        Handle a concurrent request with proper coordination.

        This is the main entry point for all MCP tool requests.
        """
        start_time = time.time()

        try:
            # Check if we can handle the request immediately
            if not self._request_semaphore.acquire(blocking=False):
                # Queue the request
                if not self.request_queue.enqueue(request_context):
                    raise ResourceError("Server is overloaded, request queue is full")

                # Wait for our turn
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._wait_for_request_slot, request_context)

            # Register active request
            with self._lock:
                self._active_requests[request_context.request_id] = request_context
                self._client_sessions[request_context.client_id].add(request_context.request_id)
                self._stats.active_requests += 1
                self._stats.total_requests += 1
                self._stats.peak_concurrent_requests = max(
                    self._stats.peak_concurrent_requests,
                    self._stats.active_requests
                )

            # Acquire appropriate database lock
            if request_context.request_type in [RequestType.WRITE, RequestType.INDEXING]:
                lock_context = self.db_lock_manager.write_lock(request_context)
            else:
                lock_context = self.db_lock_manager.read_lock(request_context)

            with lock_context:
                wait_time = time.time() - start_time
                self._update_wait_time_stats(wait_time)

                logger.info(f"Request started: {request_context.request_id} "
                           f"(client: {request_context.client_id}, tool: {request_context.tool_name})")

                yield request_context

        except Exception as e:
            with self._lock:
                self._stats.failed_requests += 1

            logger.error(f"Request failed: {request_context.request_id} - {e}")
            raise

        finally:
            # Cleanup
            execution_time = time.time() - start_time
            self._update_execution_time_stats(execution_time)

            with self._lock:
                self._active_requests.pop(request_context.request_id, None)
                self._client_sessions[request_context.client_id].discard(request_context.request_id)
                self._stats.active_requests -= 1
                self._stats.completed_requests += 1

            # Add to history
            request_context.estimated_duration = execution_time
            self._request_history.append(request_context)

            # Release semaphore
            self._request_semaphore.release()

            logger.info(f"Request completed: {request_context.request_id} "
                       f"(duration: {execution_time:.3f}s)")

    def _wait_for_request_slot(self, request_context: RequestContext):
        """Wait for an available request slot."""
        timeout_time = time.time() + request_context.timeout_seconds

        while time.time() < timeout_time:
            # Try to get our request from the queue
            queued_request = self.request_queue.dequeue(timeout=1.0)

            if queued_request and queued_request.request_id == request_context.request_id:
                # Our turn - acquire semaphore
                if self._request_semaphore.acquire(timeout=request_context.timeout_seconds):
                    return
                else:
                    raise ResourceError("Failed to acquire request slot after queuing")
            elif queued_request:
                # Not our request - put it back (this shouldn't happen with proper queue implementation)
                logger.warning(f"Unexpected request dequeued: {queued_request.request_id}")

        raise ResourceError(f"Request timeout waiting for slot: {request_context.request_id}")

    def _update_wait_time_stats(self, wait_time: float):
        """Update wait time statistics."""
        with self._lock:
            if self._stats.total_requests > 1:
                self._stats.avg_wait_time = (
                    (self._stats.avg_wait_time * (self._stats.total_requests - 1) + wait_time) /
                    self._stats.total_requests
                )
            else:
                self._stats.avg_wait_time = wait_time

    def _update_execution_time_stats(self, execution_time: float):
        """Update execution time statistics."""
        with self._lock:
            completed = self._stats.completed_requests + self._stats.failed_requests
            if completed > 1:
                self._stats.avg_execution_time = (
                    (self._stats.avg_execution_time * (completed - 1) + execution_time) /
                    completed
                )
            else:
                self._stats.avg_execution_time = execution_time

    def _cleanup_expired_requests(self):
        """Background thread to cleanup expired requests."""
        while not self._cleanup_event.wait(timeout=60):  # Run every minute
            try:
                current_time = datetime.now()
                expired_requests = []

                with self._lock:
                    for request_id, request_context in self._active_requests.items():
                        elapsed = (current_time - request_context.started_at).total_seconds()
                        if elapsed > request_context.timeout_seconds * 2:  # Grace period
                            expired_requests.append(request_id)

                    for request_id in expired_requests:
                        request_context = self._active_requests.pop(request_id, None)
                        if request_context:
                            self._client_sessions[request_context.client_id].discard(request_id)
                            self._stats.active_requests -= 1
                            self._stats.failed_requests += 1
                            logger.warning(f"Cleaned up expired request: {request_id}")

            except Exception as e:
                logger.error(f"Error in cleanup thread: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        with self._lock:
            stats_dict = {
                'concurrent_stats': {
                    'total_requests': self._stats.total_requests,
                    'active_requests': self._stats.active_requests,
                    'completed_requests': self._stats.completed_requests,
                    'failed_requests': self._stats.failed_requests,
                    'avg_wait_time': self._stats.avg_wait_time,
                    'avg_execution_time': self._stats.avg_execution_time,
                    'peak_concurrent_requests': self._stats.peak_concurrent_requests
                },
                'database_locks': self.db_lock_manager.get_lock_stats(),
                'request_queue': self.request_queue.get_queue_stats(),
                'client_sessions': {
                    client_id: len(requests)
                    for client_id, requests in self._client_sessions.items()
                    if requests
                }
            }

        return stats_dict

    def get_client_requests(self, client_id: str) -> List[str]:
        """Get active request IDs for a specific client."""
        with self._lock:
            return list(self._client_sessions.get(client_id, set()))

    def shutdown(self):
        """Shutdown the concurrent request manager."""
        logger.info("Shutting down concurrent request manager")
        self._cleanup_event.set()
        self._cleanup_thread.join(timeout=5.0)


def create_concurrent_manager(**kwargs) -> ConcurrentRequestManager:
    """Create a concurrent request manager with default configuration."""
    return ConcurrentRequestManager(**kwargs)