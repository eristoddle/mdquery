"""
Performance optimization and monitoring system for mdquery.

This module implements comprehensive performance optimization strategies including
query optimization, result caching, lazy loading, and performance monitoring.
Addresses requirements 3.4, 5.5 from the MCP workflow optimization spec.
"""

import logging
import sqlite3
import time
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
import hashlib
import json
import re
import weakref

from .exceptions import PerformanceError, QueryExecutionError
from .query import QueryEngine, QueryResult

logger = logging.getLogger(__name__)


@dataclass
class QueryMetrics:
    """Metrics for a single query execution."""
    query_hash: str
    execution_time: float
    result_count: int
    timestamp: datetime
    optimization_applied: bool = False
    cache_hit: bool = False
    estimated_cost: str = "unknown"


@dataclass
class PerformanceStats:
    """Aggregated performance statistics."""
    total_queries: int = 0
    avg_execution_time: float = 0.0
    cache_hit_rate: float = 0.0
    slow_query_count: int = 0
    optimization_success_rate: float = 0.0
    memory_usage_mb: float = 0.0


@dataclass
class OptimizationRule:
    """Rule for query optimization."""
    name: str
    pattern: str
    replacement: str
    description: str
    performance_impact: str
    conditions: Optional[Callable[[str], bool]] = None


@dataclass
class CacheEntry:
    """Entry in the result cache."""
    result: QueryResult
    timestamp: datetime
    hit_count: int = 0
    last_access: datetime = field(default_factory=datetime.now)


class PerformanceOptimizer:
    """
    Comprehensive performance optimizer with query optimization, caching, and monitoring.

    This class implements all performance optimization requirements from the
    MCP workflow optimization specification.
    """

    def __init__(self, query_engine: QueryEngine,
                 cache_size: int = 1000,
                 cache_ttl_minutes: int = 30,
                 slow_query_threshold_seconds: float = 2.0):
        """
        Initialize performance optimizer.

        Args:
            query_engine: Query engine to optimize
            cache_size: Maximum number of cached results
            cache_ttl_minutes: Time-to-live for cached results in minutes
            slow_query_threshold_seconds: Threshold for slow query detection
        """
        self.query_engine = query_engine
        self.cache_size = cache_size
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self.slow_query_threshold = slow_query_threshold_seconds

        # Performance monitoring
        self._metrics: deque = deque(maxlen=10000)
        self._query_stats: Dict[str, List[float]] = defaultdict(list)
        self._lock = Lock()

        # Result caching
        self._cache: Dict[str, CacheEntry] = {}
        self._cache_access_order: deque = deque()

        # Query optimization rules
        self._optimization_rules = self._initialize_optimization_rules()

        # Lazy loading registry
        self._lazy_components: Dict[str, Callable] = {}
        self._loaded_components: Dict[str, Any] = {}

        # Thread pool for async operations
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="perf-opt")

    def optimize_query(self, query: str, auto_apply: bool = True) -> Tuple[str, List[str]]:
        """
        Optimize a query for better performance.

        Args:
            query: SQL query to optimize
            auto_apply: Whether to automatically apply optimizations

        Returns:
            Tuple of (optimized_query, list_of_applied_optimizations)
        """
        optimized_query = query
        applied_optimizations = []

        try:
            for rule in self._optimization_rules:
                if rule.conditions and not rule.conditions(query):
                    continue

                if re.search(rule.pattern, optimized_query, re.IGNORECASE):
                    if auto_apply:
                        optimized_query = re.sub(
                            rule.pattern, rule.replacement,
                            optimized_query, flags=re.IGNORECASE
                        )
                        applied_optimizations.append(rule.name)
                        logger.debug(f"Applied optimization: {rule.name}")
                    else:
                        applied_optimizations.append(f"Suggested: {rule.name}")

            return optimized_query, applied_optimizations

        except Exception as e:
            logger.error(f"Query optimization failed: {e}")
            return query, []

    def execute_with_optimization(self, query: str, use_cache: bool = True) -> QueryResult:
        """
        Execute query with optimization and caching.

        Args:
            query: SQL query to execute
            use_cache: Whether to use result caching

        Returns:
            Query execution result
        """
        start_time = time.time()
        query_hash = self._hash_query(query)

        try:
            # Check cache first
            if use_cache:
                cached_result = self._get_cached_result(query_hash)
                if cached_result is not None:
                    execution_time = time.time() - start_time
                    self._record_metrics(query_hash, execution_time,
                                       len(cached_result.rows), cache_hit=True)
                    return cached_result

            # Optimize query
            optimized_query, optimizations = self.optimize_query(query)

            # Execute query
            result = self.query_engine.execute_query(optimized_query)

            # Calculate execution time
            execution_time = time.time() - start_time

            # Cache result if appropriate
            if use_cache and self._should_cache_result(query, result, execution_time):
                self._cache_result(query_hash, result)

            # Record metrics
            self._record_metrics(
                query_hash, execution_time, len(result.rows),
                optimization_applied=(len(optimizations) > 0)
            )

            # Check for slow query
            if execution_time > self.slow_query_threshold:
                self._handle_slow_query(query, execution_time, optimizations)

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Optimized query execution failed: {e}")
            raise QueryExecutionError(f"Query execution failed: {e}") from e

    def get_performance_stats(self, hours: int = 24) -> PerformanceStats:
        """
        Get performance statistics for the specified time period.

        Args:
            hours: Number of hours to look back

        Returns:
            Performance statistics
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)

        with self._lock:
            recent_metrics = [
                m for m in self._metrics
                if m.timestamp >= cutoff_time
            ]

        if not recent_metrics:
            return PerformanceStats()

        total_queries = len(recent_metrics)
        avg_execution_time = sum(m.execution_time for m in recent_metrics) / total_queries
        cache_hits = sum(1 for m in recent_metrics if m.cache_hit)
        cache_hit_rate = cache_hits / total_queries if total_queries > 0 else 0.0
        slow_queries = sum(1 for m in recent_metrics if m.execution_time > self.slow_query_threshold)
        optimizations_applied = sum(1 for m in recent_metrics if m.optimization_applied)
        optimization_success_rate = optimizations_applied / total_queries if total_queries > 0 else 0.0

        return PerformanceStats(
            total_queries=total_queries,
            avg_execution_time=avg_execution_time,
            cache_hit_rate=cache_hit_rate,
            slow_query_count=slow_queries,
            optimization_success_rate=optimization_success_rate,
            memory_usage_mb=self._estimate_memory_usage()
        )

    def suggest_optimizations(self, query: str) -> List[Dict[str, Any]]:
        """
        Suggest optimizations for a query without applying them.

        Args:
            query: SQL query to analyze

        Returns:
            List of optimization suggestions
        """
        suggestions = []

        for rule in self._optimization_rules:
            if rule.conditions and not rule.conditions(query):
                continue

            if re.search(rule.pattern, query, re.IGNORECASE):
                suggestions.append({
                    'rule_name': rule.name,
                    'description': rule.description,
                    'performance_impact': rule.performance_impact,
                    'pattern': rule.pattern,
                    'replacement': rule.replacement
                })

        return suggestions

    def clear_cache(self) -> None:
        """Clear the result cache."""
        with self._lock:
            self._cache.clear()
            self._cache_access_order.clear()
        logger.info("Performance cache cleared")

    def register_lazy_component(self, name: str, loader: Callable) -> None:
        """
        Register a component for lazy loading.

        Args:
            name: Component name
            loader: Function to load the component
        """
        self._lazy_components[name] = loader
        logger.debug(f"Registered lazy component: {name}")

    def get_lazy_component(self, name: str) -> Any:
        """
        Get a lazy-loaded component.

        Args:
            name: Component name

        Returns:
            Loaded component
        """
        if name not in self._loaded_components:
            if name not in self._lazy_components:
                raise ValueError(f"Unknown lazy component: {name}")

            loader = self._lazy_components[name]
            self._loaded_components[name] = loader()
            logger.debug(f"Lazy loaded component: {name}")

        return self._loaded_components[name]

    def _initialize_optimization_rules(self) -> List[OptimizationRule]:
        """Initialize query optimization rules."""
        return [
            OptimizationRule(
                name="Use FTS for content search",
                pattern=r"WHERE\s+content\s+LIKE\s+'%([^%]+)%'",
                replacement=r"WHERE EXISTS (SELECT 1 FROM content_fts WHERE content_fts.file_id = files.id AND content_fts MATCH '\1')",
                description="Replace LIKE content search with full-text search",
                performance_impact="high"
            ),
            OptimizationRule(
                name="Add LIMIT to prevent large result sets",
                pattern=r"^(SELECT.*?)(\s+ORDER\s+BY\s+[^;]+)?;?\s*$",
                replacement=r"\1\2 LIMIT 1000",
                description="Add LIMIT clause to queries without explicit limits",
                performance_impact="medium",
                conditions=lambda q: "LIMIT" not in q.upper() and "COUNT" not in q.upper()
            ),
            OptimizationRule(
                name="Use IN clause for multiple OR conditions",
                pattern=r"(\w+)\s*=\s*'([^']+)'\s+OR\s+\1\s*=\s*'([^']+)'(?:\s+OR\s+\1\s*=\s*'([^']+)')*",
                replacement=r"\1 IN ('\2', '\3')",
                description="Replace multiple OR conditions with IN clause",
                performance_impact="low"
            ),
            OptimizationRule(
                name="Use EXISTS instead of IN with subquery",
                pattern=r"WHERE\s+(\w+)\s+IN\s*\(\s*SELECT\s+(\w+)\s+FROM\s+(\w+)",
                replacement=r"WHERE EXISTS (SELECT 1 FROM \3 WHERE \3.\2 = \1",
                description="Use EXISTS instead of IN with subquery for better performance",
                performance_impact="medium"
            ),
            OptimizationRule(
                name="Push WHERE conditions into JOINs",
                pattern=r"FROM\s+(\w+)\s+(\w+)\s+JOIN\s+(\w+)\s+(\w+)\s+ON\s+([^W]+)\s+WHERE\s+\4\.(\w+)\s*=\s*'([^']+)'",
                replacement=r"FROM \1 \2 JOIN \3 \4 ON \5 AND \4.\6 = '\7'",
                description="Push WHERE conditions into JOIN clauses for better optimization",
                performance_impact="medium"
            )
        ]

    def _hash_query(self, query: str) -> str:
        """Generate hash for query caching."""
        return hashlib.md5(query.encode()).hexdigest()

    def _get_cached_result(self, query_hash: str) -> Optional[QueryResult]:
        """Get cached result if available and not expired."""
        with self._lock:
            if query_hash not in self._cache:
                return None

            entry = self._cache[query_hash]

            # Check if expired
            if datetime.now() - entry.timestamp > self.cache_ttl:
                del self._cache[query_hash]
                try:
                    self._cache_access_order.remove(query_hash)
                except ValueError:
                    pass
                return None

            # Update access statistics
            entry.hit_count += 1
            entry.last_access = datetime.now()

            # Update access order
            try:
                self._cache_access_order.remove(query_hash)
            except ValueError:
                pass
            self._cache_access_order.append(query_hash)

            return entry.result

    def _cache_result(self, query_hash: str, result: QueryResult) -> None:
        """Cache query result."""
        with self._lock:
            # Enforce cache size limit
            while len(self._cache) >= self.cache_size:
                if self._cache_access_order:
                    oldest_hash = self._cache_access_order.popleft()
                    self._cache.pop(oldest_hash, None)
                else:
                    break

            # Add new entry
            entry = CacheEntry(
                result=result,
                timestamp=datetime.now()
            )
            self._cache[query_hash] = entry
            self._cache_access_order.append(query_hash)

    def _should_cache_result(self, query: str, result: QueryResult, execution_time: float) -> bool:
        """Determine if a result should be cached."""
        # Cache criteria
        return (
            execution_time > 0.1  # Only cache queries that took some time
            and len(result.rows) < 10000  # Don't cache huge result sets
            and "INSERT" not in query.upper()  # Don't cache modification queries
            and "UPDATE" not in query.upper()
            and "DELETE" not in query.upper()
        )

    def _record_metrics(self, query_hash: str, execution_time: float,
                       result_count: int, optimization_applied: bool = False,
                       cache_hit: bool = False) -> None:
        """Record query execution metrics."""
        metrics = QueryMetrics(
            query_hash=query_hash,
            execution_time=execution_time,
            result_count=result_count,
            timestamp=datetime.now(),
            optimization_applied=optimization_applied,
            cache_hit=cache_hit
        )

        with self._lock:
            self._metrics.append(metrics)
            self._query_stats[query_hash].append(execution_time)

    def _handle_slow_query(self, query: str, execution_time: float,
                          optimizations: List[str]) -> None:
        """Handle slow query detection and logging."""
        logger.warning(
            f"Slow query detected: {execution_time:.3f}s "
            f"(threshold: {self.slow_query_threshold}s)"
        )

        if not optimizations:
            suggestions = self.suggest_optimizations(query)
            if suggestions:
                logger.info(f"Optimization suggestions available: {len(suggestions)}")

    def _estimate_memory_usage(self) -> float:
        """Estimate memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0

    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)


class LazyComponentLoader:
    """Helper class for lazy loading of heavy components."""

    def __init__(self, performance_optimizer: PerformanceOptimizer):
        """Initialize with performance optimizer."""
        self.optimizer = performance_optimizer
        self._setup_lazy_components()

    def _setup_lazy_components(self) -> None:
        """Setup lazy loading for heavy components."""

        def load_tag_analysis_engine():
            from .tag_analysis import TagAnalysisEngine
            return TagAnalysisEngine(self.optimizer.query_engine)

        def load_workflow_analyzer():
            from .workflow_analysis import WorkflowAnalyzer
            return WorkflowAnalyzer(self.optimizer.query_engine)

        def load_query_guidance_engine():
            from .query_guidance import QueryGuidanceEngine
            return QueryGuidanceEngine()

        # Register lazy components
        self.optimizer.register_lazy_component("tag_analysis", load_tag_analysis_engine)
        self.optimizer.register_lazy_component("workflow_analysis", load_workflow_analyzer)
        self.optimizer.register_lazy_component("query_guidance", load_query_guidance_engine)


def create_performance_optimizer(query_engine: QueryEngine, **kwargs) -> PerformanceOptimizer:
    """
    Create a performance optimizer instance with lazy loading.

    Args:
        query_engine: Query engine to optimize
        **kwargs: Additional configuration options

    Returns:
        Configured PerformanceOptimizer instance
    """
    optimizer = PerformanceOptimizer(query_engine, **kwargs)
    LazyComponentLoader(optimizer)
    return optimizer