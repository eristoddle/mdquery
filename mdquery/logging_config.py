"""
Comprehensive logging configuration for mdquery.

This module provides centralized logging configuration with performance monitoring,
structured logging, and error tracking capabilities.
"""

import logging
import logging.handlers
import sys
import time
import json
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from contextlib import contextmanager
from functools import wraps

from .exceptions import MdqueryError, PerformanceError, create_error_summary


class PerformanceMonitor:
    """Monitor and track performance metrics."""

    def __init__(self):
        """Initialize performance monitor."""
        self._metrics: Dict[str, List[float]] = {}
        self._thresholds: Dict[str, float] = {
            'query_execution': 5.0,  # 5 seconds
            'file_indexing': 2.0,    # 2 seconds per file
            'directory_scan': 30.0,  # 30 seconds
            'database_operation': 1.0, # 1 second
            'parsing_operation': 0.5,  # 0.5 seconds per file
        }
        self._lock = threading.Lock()

    def record_metric(self, operation: str, duration: float) -> None:
        """
        Record a performance metric.

        Args:
            operation: Name of the operation
            duration: Duration in seconds
        """
        with self._lock:
            if operation not in self._metrics:
                self._metrics[operation] = []

            self._metrics[operation].append(duration)

            # Keep only last 1000 measurements
            if len(self._metrics[operation]) > 1000:
                self._metrics[operation] = self._metrics[operation][-1000:]

    def check_threshold(self, operation: str, duration: float) -> bool:
        """
        Check if operation duration exceeds threshold.

        Args:
            operation: Name of the operation
            duration: Duration in seconds

        Returns:
            True if threshold is exceeded
        """
        threshold = self._thresholds.get(operation)
        if threshold and duration > threshold:
            return True
        return False

    def get_statistics(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """
        Get performance statistics.

        Args:
            operation: Specific operation to get stats for, or None for all

        Returns:
            Dictionary containing performance statistics
        """
        with self._lock:
            if operation:
                if operation not in self._metrics:
                    return {}

                durations = self._metrics[operation]
                if not durations:
                    return {}

                return {
                    'operation': operation,
                    'count': len(durations),
                    'avg_duration': sum(durations) / len(durations),
                    'min_duration': min(durations),
                    'max_duration': max(durations),
                    'threshold': self._thresholds.get(operation),
                    'threshold_violations': sum(1 for d in durations if self.check_threshold(operation, d))
                }
            else:
                stats = {}
                for op in self._metrics:
                    stats[op] = self.get_statistics(op)
                return stats

    def set_threshold(self, operation: str, threshold: float) -> None:
        """
        Set performance threshold for an operation.

        Args:
            operation: Name of the operation
            threshold: Threshold in seconds
        """
        self._thresholds[operation] = threshold


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # Add exception information if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }

        # Add custom attributes
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created',
                          'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'getMessage', 'exc_info', 'exc_text', 'stack_info']:
                log_data[key] = value

        return json.dumps(log_data, default=str)


class ErrorTracker:
    """Track and analyze errors for monitoring and debugging."""

    def __init__(self, max_errors: int = 1000):
        """
        Initialize error tracker.

        Args:
            max_errors: Maximum number of errors to keep in memory
        """
        self._errors: List[Dict[str, Any]] = []
        self._max_errors = max_errors
        self._lock = threading.Lock()

    def record_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Record an error for tracking.

        Args:
            error: Exception that occurred
            context: Additional context information
        """
        with self._lock:
            error_data = create_error_summary(error)
            error_data['timestamp'] = datetime.now().isoformat()

            if context:
                error_data['additional_context'] = context

            self._errors.append(error_data)

            # Keep only recent errors
            if len(self._errors) > self._max_errors:
                self._errors = self._errors[-self._max_errors:]

    def get_error_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get error statistics for the specified time period.

        Args:
            hours: Number of hours to look back

        Returns:
            Dictionary containing error statistics
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)

        with self._lock:
            recent_errors = [
                error for error in self._errors
                if datetime.fromisoformat(error['timestamp']) > cutoff_time
            ]

            if not recent_errors:
                return {'total_errors': 0, 'error_types': {}, 'recent_errors': []}

            # Count by error type
            error_types = {}
            for error in recent_errors:
                error_type = error['error_type']
                error_types[error_type] = error_types.get(error_type, 0) + 1

            return {
                'total_errors': len(recent_errors),
                'error_types': error_types,
                'recent_errors': recent_errors[-10:],  # Last 10 errors
                'time_period_hours': hours
            }


# Global instances
_performance_monitor = PerformanceMonitor()
_error_tracker = ErrorTracker()


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance."""
    return _performance_monitor


def get_error_tracker() -> ErrorTracker:
    """Get global error tracker instance."""
    return _error_tracker


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    structured: bool = False,
    enable_performance_monitoring: bool = True
) -> None:
    """
    Set up comprehensive logging configuration.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file to write logs to
        structured: Whether to use structured JSON logging
        enable_performance_monitoring: Whether to enable performance monitoring
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create formatter
    if structured:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Set up mdquery logger
    mdquery_logger = logging.getLogger('mdquery')
    mdquery_logger.setLevel(numeric_level)

    # Add performance monitoring if enabled
    if enable_performance_monitoring:
        # Add performance logging handler
        perf_handler = PerformanceLoggingHandler()
        perf_handler.setLevel(logging.WARNING)  # Only log performance issues
        root_logger.addHandler(perf_handler)


class PerformanceLoggingHandler(logging.Handler):
    """Custom logging handler for performance monitoring."""

    def emit(self, record: logging.LogRecord) -> None:
        """Handle log record for performance monitoring."""
        # Check if this is a performance-related log
        if hasattr(record, 'operation') and hasattr(record, 'duration'):
            _performance_monitor.record_metric(record.operation, record.duration)

            # Check threshold and log warning if exceeded
            if _performance_monitor.check_threshold(record.operation, record.duration):
                threshold = _performance_monitor._thresholds.get(record.operation, 0)
                self.format(record)  # Ensure message is formatted
                print(f"PERFORMANCE WARNING: {record.operation} took {record.duration:.2f}s "
                      f"(threshold: {threshold:.2f}s)", file=sys.stderr)


@contextmanager
def performance_timer(operation: str, logger: Optional[logging.Logger] = None):
    """
    Context manager for timing operations and logging performance.

    Args:
        operation: Name of the operation being timed
        logger: Optional logger to use for logging

    Yields:
        Dictionary that will contain timing information
    """
    start_time = time.time()
    timing_info = {'operation': operation}

    try:
        yield timing_info
    finally:
        duration = time.time() - start_time
        timing_info['duration'] = duration

        # Record metric
        _performance_monitor.record_metric(operation, duration)

        # Log if logger provided
        if logger:
            logger.debug(f"{operation} completed in {duration:.3f}s",
                        extra={'operation': operation, 'duration': duration})

        # Check threshold and raise error if exceeded
        if _performance_monitor.check_threshold(operation, duration):
            threshold = _performance_monitor._thresholds.get(operation, 0)
            raise PerformanceError(
                f"{operation} exceeded performance threshold: {duration:.2f}s > {threshold:.2f}s",
                operation=operation,
                duration=duration
            )


def monitor_performance(operation: str):
    """
    Decorator for monitoring function performance.

    Args:
        operation: Name of the operation being monitored
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            with performance_timer(operation, logger):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def log_error(error: Exception, logger: logging.Logger, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Log an error with comprehensive context information.

    Args:
        error: Exception that occurred
        logger: Logger to use for logging
        context: Additional context information
    """
    # Record error for tracking
    _error_tracker.record_error(error, context)

    # Create error summary
    error_summary = create_error_summary(error)

    # Log with appropriate level
    if isinstance(error, MdqueryError):
        # Use WARNING for expected mdquery errors
        logger.warning(f"{error_summary['error_type']}: {error_summary['error_message']}",
                      extra=error_summary)
    else:
        # Use ERROR for unexpected errors
        logger.error(f"Unexpected error: {error_summary['error_message']}",
                    exc_info=True, extra=error_summary)


def get_logging_statistics() -> Dict[str, Any]:
    """
    Get comprehensive logging and performance statistics.

    Returns:
        Dictionary containing logging statistics
    """
    return {
        'performance_stats': _performance_monitor.get_statistics(),
        'error_stats': _error_tracker.get_error_statistics(),
        'logging_config': {
            'root_level': logging.getLogger().level,
            'handlers': [type(h).__name__ for h in logging.getLogger().handlers]
        }
    }