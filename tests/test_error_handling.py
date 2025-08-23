"""
Comprehensive tests for error handling and logging in mdquery.

This module tests all error scenarios, edge cases, and logging functionality
to ensure robust error handling throughout the system.
"""

import pytest
import tempfile
import sqlite3
import os
import stat
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import logging

from mdquery.exceptions import (
    MdqueryError, FileSystemError, FileAccessError, FileCorruptedError,
    DirectoryNotFoundError, IndexingError, ParsingError, DatabaseError,
    DatabaseConnectionError, DatabaseCorruptionError, SchemaError,
    QueryError, QueryValidationError, QueryExecutionError, QueryTimeoutError,
    CacheError, ConfigurationError, PerformanceError, ResourceError,
    MCPError, format_error_context, create_error_summary
)
from mdquery.logging_config import (
    PerformanceMonitor, ErrorTracker, setup_logging, performance_timer,
    monitor_performance, log_error, get_logging_statistics
)
from mdquery.database import DatabaseManager
from mdquery.indexer import Indexer
from mdquery.query import QueryEngine


class TestExceptions:
    """Test custom exception hierarchy."""

    def test_base_exception(self):
        """Test base MdqueryError exception."""
        context = {'key': 'value', 'number': 42}
        error = MdqueryError("Test error", context)

        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.context == context

    def test_file_system_errors(self):
        """Test file system related errors."""
        file_path = Path("/test/file.md")

        # FileAccessError
        error = FileAccessError("Cannot access file", file_path)
        assert error.file_path == file_path
        assert "Cannot access file" in str(error)

        # FileCorruptedError
        error = FileCorruptedError("File is corrupted", file_path)
        assert error.file_path == file_path

        # DirectoryNotFoundError
        error = DirectoryNotFoundError("Directory not found", file_path)
        assert error.file_path == file_path

    def test_parsing_error(self):
        """Test parsing error with parser type."""
        file_path = Path("/test/file.md")
        error = ParsingError("Parse failed", file_path, "frontmatter")

        assert error.file_path == file_path
        assert error.parser_type == "frontmatter"

    def test_query_errors(self):
        """Test query related errors."""
        query = "SELECT * FROM files"

        # QueryValidationError
        error = QueryValidationError("Invalid query", query)
        assert error.query == query

        # QueryExecutionError
        error = QueryExecutionError("Execution failed", query)
        assert error.query == query

        # QueryTimeoutError
        error = QueryTimeoutError("Query timed out", query)
        assert error.query == query

    def test_performance_error(self):
        """Test performance error with timing info."""
        error = PerformanceError("Too slow", "file_indexing", 5.5)

        assert error.operation == "file_indexing"
        assert error.duration == 5.5

    def test_resource_error(self):
        """Test resource error with resource type."""
        error = ResourceError("Out of memory", "memory")

        assert error.resource_type == "memory"

    def test_format_error_context(self):
        """Test error context formatting."""
        # Error with file path
        error = FileAccessError("Test", Path("/test/file.md"))
        context = format_error_context(error)
        assert "file=/test/file.md" in context

        # Error with query
        error = QueryError("Test", "SELECT * FROM files")
        context = format_error_context(error)
        assert "query=SELECT * FROM files" in context

        # Error with custom context
        error = MdqueryError("Test", {"custom": "value"})
        context = format_error_context(error)
        assert "custom=value" in context

    def test_create_error_summary(self):
        """Test error summary creation."""
        # MdqueryError
        error = FileAccessError("Test error", Path("/test/file.md"))
        summary = create_error_summary(error)

        assert summary["error_type"] == "FileAccessError"
        assert summary["error_message"] == "Test error"
        assert summary["is_mdquery_error"] is True
        assert summary["file_path"] == "/test/file.md"

        # Regular exception
        error = ValueError("Regular error")
        summary = create_error_summary(error)

        assert summary["error_type"] == "ValueError"
        assert summary["is_mdquery_error"] is False


class TestPerformanceMonitor:
    """Test performance monitoring functionality."""

    def test_record_metric(self):
        """Test metric recording."""
        monitor = PerformanceMonitor()

        monitor.record_metric("test_operation", 1.5)
        monitor.record_metric("test_operation", 2.0)

        stats = monitor.get_statistics("test_operation")
        assert stats["count"] == 2
        assert stats["avg_duration"] == 1.75
        assert stats["min_duration"] == 1.5
        assert stats["max_duration"] == 2.0

    def test_threshold_checking(self):
        """Test performance threshold checking."""
        monitor = PerformanceMonitor()
        monitor.set_threshold("test_operation", 2.0)

        # Below threshold
        assert not monitor.check_threshold("test_operation", 1.5)

        # Above threshold
        assert monitor.check_threshold("test_operation", 2.5)

    def test_statistics_with_thresholds(self):
        """Test statistics with threshold violations."""
        monitor = PerformanceMonitor()
        monitor.set_threshold("test_operation", 2.0)

        # Record some metrics
        monitor.record_metric("test_operation", 1.0)  # Below threshold
        monitor.record_metric("test_operation", 2.5)  # Above threshold
        monitor.record_metric("test_operation", 3.0)  # Above threshold

        stats = monitor.get_statistics("test_operation")
        assert stats["threshold_violations"] == 2

    def test_metric_limit(self):
        """Test that metrics are limited to prevent memory issues."""
        monitor = PerformanceMonitor()

        # Record more than the limit
        for i in range(1200):
            monitor.record_metric("test_operation", i)

        stats = monitor.get_statistics("test_operation")
        assert stats["count"] == 1000  # Should be limited to 1000


class TestErrorTracker:
    """Test error tracking functionality."""

    def test_record_error(self):
        """Test error recording."""
        tracker = ErrorTracker()

        error = ValueError("Test error")
        tracker.record_error(error)

        stats = tracker.get_error_statistics()
        assert stats["total_errors"] == 1
        assert "ValueError" in stats["error_types"]

    def test_error_statistics(self):
        """Test error statistics generation."""
        tracker = ErrorTracker()

        # Record different types of errors
        tracker.record_error(ValueError("Error 1"))
        tracker.record_error(ValueError("Error 2"))
        tracker.record_error(TypeError("Error 3"))

        stats = tracker.get_error_statistics()
        assert stats["total_errors"] == 3
        assert stats["error_types"]["ValueError"] == 2
        assert stats["error_types"]["TypeError"] == 1

    def test_error_limit(self):
        """Test that errors are limited to prevent memory issues."""
        tracker = ErrorTracker(max_errors=10)

        # Record more than the limit
        for i in range(15):
            tracker.record_error(ValueError(f"Error {i}"))

        stats = tracker.get_error_statistics()
        assert stats["total_errors"] == 10  # Should be limited


class TestPerformanceTimer:
    """Test performance timing context manager."""

    def test_performance_timer_success(self):
        """Test successful performance timing."""
        with patch('mdquery.logging_config._performance_monitor') as mock_monitor:
            with performance_timer("test_operation") as timing_info:
                # Simulate some work
                pass

            assert timing_info["operation"] == "test_operation"
            assert "duration" in timing_info
            mock_monitor.record_metric.assert_called_once()

    def test_performance_timer_with_logger(self):
        """Test performance timing with logger."""
        logger = Mock()

        with patch('mdquery.logging_config._performance_monitor') as mock_monitor:
            with performance_timer("test_operation", logger):
                pass

            logger.debug.assert_called_once()

    def test_performance_timer_threshold_exceeded(self):
        """Test performance timer when threshold is exceeded."""
        with patch('mdquery.logging_config._performance_monitor') as mock_monitor:
            mock_monitor.check_threshold.return_value = True
            mock_monitor._thresholds = {"test_operation": 1.0}

            with pytest.raises(PerformanceError):
                with performance_timer("test_operation"):
                    pass


class TestMonitorPerformanceDecorator:
    """Test performance monitoring decorator."""

    def test_monitor_performance_decorator(self):
        """Test performance monitoring decorator."""
        with patch('mdquery.logging_config._performance_monitor') as mock_monitor:
            @monitor_performance("test_operation")
            def test_function():
                return "result"

            result = test_function()

            assert result == "result"
            mock_monitor.record_metric.assert_called_once()


class TestDatabaseErrorHandling:
    """Test database error handling scenarios."""

    def test_database_connection_error(self):
        """Test database connection error handling."""
        # Test with invalid database path
        with pytest.raises(DatabaseConnectionError):
            db_manager = DatabaseManager(Path("/invalid/path/db.sqlite"))
            with db_manager.get_connection():
                pass

    def test_database_corruption_detection(self):
        """Test database corruption detection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"

            # Create a corrupted database file
            with open(db_path, 'w') as f:
                f.write("This is not a valid SQLite database")

            db_manager = DatabaseManager(db_path)

            with pytest.raises((DatabaseConnectionError, DatabaseCorruptionError)):
                with db_manager.get_connection():
                    pass

    def test_database_locked_retry(self):
        """Test database locked retry mechanism."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"

            # Create a valid database first
            db_manager = DatabaseManager(db_path)
            db_manager.initialize_database()

            # Mock sqlite3.connect to raise OperationalError
            with patch('sqlite3.connect') as mock_connect:
                mock_connect.side_effect = [
                    sqlite3.OperationalError("database is locked"),
                    sqlite3.OperationalError("database is locked"),
                    MagicMock()  # Success on third try
                ]

                # This should succeed after retries
                db_manager._connection = None  # Reset connection
                connection = db_manager._create_connection()
                assert connection is not None


class TestIndexerErrorHandling:
    """Test indexer error handling scenarios."""

    def test_directory_not_found(self):
        """Test handling of non-existent directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            db_manager = DatabaseManager(db_path)
            db_manager.initialize_database()

            indexer = Indexer(db_manager)

            with pytest.raises(DirectoryNotFoundError):
                indexer.index_directory(Path("/nonexistent/directory"))

    def test_permission_denied_directory(self):
        """Test handling of permission denied on directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            db_manager = DatabaseManager(db_path)
            db_manager.initialize_database()

            # Create a directory with no permissions
            restricted_dir = Path(temp_dir) / "restricted"
            restricted_dir.mkdir()

            try:
                # Remove all permissions
                os.chmod(restricted_dir, 0o000)

                indexer = Indexer(db_manager)

                with pytest.raises(DirectoryNotFoundError):
                    indexer.index_directory(restricted_dir)

            finally:
                # Restore permissions for cleanup
                os.chmod(restricted_dir, 0o755)

    def test_corrupted_file_handling(self):
        """Test handling of corrupted files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            db_manager = DatabaseManager(db_path)
            db_manager.initialize_database()

            # Create a file with invalid encoding
            corrupted_file = Path(temp_dir) / "corrupted.md"
            with open(corrupted_file, 'wb') as f:
                f.write(b'\xff\xfe\x00\x00invalid utf-8')

            indexer = Indexer(db_manager)

            with pytest.raises(FileCorruptedError):
                indexer.index_file(corrupted_file)

    def test_permission_denied_file(self):
        """Test handling of permission denied on file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            db_manager = DatabaseManager(db_path)
            db_manager.initialize_database()

            # Create a file with no read permissions
            restricted_file = Path(temp_dir) / "restricted.md"
            restricted_file.write_text("# Test file")

            try:
                # Remove read permissions
                os.chmod(restricted_file, 0o000)

                indexer = Indexer(db_manager)

                with pytest.raises(FileAccessError):
                    indexer.index_file(restricted_file)

            finally:
                # Restore permissions for cleanup
                os.chmod(restricted_file, 0o644)

    def test_large_file_warning(self):
        """Test warning for large files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            db_manager = DatabaseManager(db_path)
            db_manager.initialize_database()

            # Create a large file (simulate by mocking stat)
            large_file = Path(temp_dir) / "large.md"
            large_file.write_text("# Large file")

            indexer = Indexer(db_manager)

            with patch.object(Path, 'stat') as mock_stat:
                mock_stat.return_value.st_size = 15 * 1024 * 1024  # 15MB

                with patch('mdquery.indexer.logger') as mock_logger:
                    # This should succeed but log a warning
                    indexer.index_file(large_file)
                    mock_logger.warning.assert_called()

    @patch('psutil.virtual_memory')
    def test_insufficient_memory_error(self, mock_memory):
        """Test handling of insufficient memory."""
        # Mock low memory condition
        mock_memory.return_value.available = 50 * 1024 * 1024  # 50MB (below 100MB threshold)

        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            db_manager = DatabaseManager(db_path)
            db_manager.initialize_database()

            indexer = Indexer(db_manager)

            with pytest.raises(ResourceError) as exc_info:
                indexer.index_directory(Path(temp_dir))

            assert "memory" in str(exc_info.value)


class TestQueryErrorHandling:
    """Test query engine error handling scenarios."""

    def test_query_validation_errors(self):
        """Test various query validation errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            db_manager = DatabaseManager(db_path)
            db_manager.initialize_database()

            query_engine = QueryEngine(db_manager)

            # Empty query
            with pytest.raises(QueryValidationError):
                query_engine.validate_query("")

            # Dangerous query (DROP)
            with pytest.raises(QueryValidationError):
                query_engine.validate_query("DROP TABLE files")

            # Non-SELECT query
            with pytest.raises(QueryValidationError):
                query_engine.validate_query("INSERT INTO files VALUES (1, 'test')")

            # Multiple statements
            with pytest.raises(QueryValidationError):
                query_engine.validate_query("SELECT * FROM files; DROP TABLE files;")

            # Invalid table reference
            with pytest.raises(QueryValidationError):
                query_engine.validate_query("SELECT * FROM nonexistent_table")

    def test_query_execution_timeout(self):
        """Test query execution timeout."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            db_manager = DatabaseManager(db_path)
            db_manager.initialize_database()

            query_engine = QueryEngine(db_manager)
            query_engine.set_query_timeout(0.1)  # Very short timeout

            # Mock a slow query
            with patch.object(db_manager, 'get_connection') as mock_get_conn:
                mock_conn = MagicMock()
                mock_conn.__enter__.return_value = mock_conn
                mock_conn.execute.side_effect = sqlite3.OperationalError("database is locked")
                mock_get_conn.return_value = mock_conn

                with pytest.raises(QueryTimeoutError):
                    query_engine.execute_query("SELECT * FROM files")

    def test_query_result_size_limit(self):
        """Test query result size limiting."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            db_manager = DatabaseManager(db_path)
            db_manager.initialize_database()

            query_engine = QueryEngine(db_manager)
            query_engine.set_max_results(5)

            # Insert test data
            with db_manager.get_connection() as conn:
                for i in range(10):
                    conn.execute("""
                        INSERT INTO files (path, filename, directory, modified_date,
                                         file_size, content_hash, word_count, heading_count)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (f"/test{i}.md", f"test{i}.md", "/", "2024-01-01T00:00:00",
                          100, f"hash{i}", 10, 1))
                conn.commit()

            # Query should return limited results
            result = query_engine.execute_query("SELECT * FROM files")
            assert result.row_count == 5  # Limited to max_results


class TestLoggingConfiguration:
    """Test logging configuration and functionality."""

    def test_setup_logging_basic(self):
        """Test basic logging setup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"

            setup_logging(level="DEBUG", log_file=log_file)

            # Test that logging works
            logger = logging.getLogger("test")
            logger.info("Test message")

            # Check that log file was created
            assert log_file.exists()

    def test_setup_logging_structured(self):
        """Test structured logging setup."""
        setup_logging(structured=True)

        # Test that structured logging works
        logger = logging.getLogger("test")
        logger.info("Test message")

    def test_log_error_function(self):
        """Test log_error function."""
        logger = Mock()
        error = FileAccessError("Test error", Path("/test/file.md"))

        with patch('mdquery.logging_config._error_tracker') as mock_tracker:
            log_error(error, logger)

            mock_tracker.record_error.assert_called_once_with(error, None)
            logger.warning.assert_called_once()

    def test_get_logging_statistics(self):
        """Test logging statistics retrieval."""
        stats = get_logging_statistics()

        assert "performance_stats" in stats
        assert "error_stats" in stats
        assert "logging_config" in stats


class TestIntegrationErrorScenarios:
    """Test integrated error scenarios across multiple components."""

    def test_full_indexing_with_mixed_errors(self):
        """Test indexing with various file errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            db_manager = DatabaseManager(db_path)
            db_manager.initialize_database()

            # Create test files with various issues
            good_file = Path(temp_dir) / "good.md"
            good_file.write_text("# Good file\nThis is a valid markdown file.")

            # Corrupted file
            corrupted_file = Path(temp_dir) / "corrupted.md"
            with open(corrupted_file, 'wb') as f:
                f.write(b'\xff\xfe\x00\x00invalid')

            # Empty file
            empty_file = Path(temp_dir) / "empty.md"
            empty_file.write_text("")

            indexer = Indexer(db_manager)

            # Index directory - should handle errors gracefully
            stats = indexer.index_directory(Path(temp_dir))

            # Should have processed some files and encountered some errors
            assert stats['files_processed'] >= 1  # At least the good file
            assert stats['errors'] >= 1  # At least the corrupted file

    def test_query_with_database_issues(self):
        """Test querying with database connectivity issues."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            db_manager = DatabaseManager(db_path)
            db_manager.initialize_database()

            query_engine = QueryEngine(db_manager)

            # Mock database connection failure
            with patch.object(db_manager, 'get_connection') as mock_get_conn:
                mock_get_conn.side_effect = DatabaseConnectionError("Connection failed")

                with pytest.raises(QueryExecutionError):
                    query_engine.execute_query("SELECT * FROM files")

    def test_performance_monitoring_integration(self):
        """Test performance monitoring across operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            db_manager = DatabaseManager(db_path)
            db_manager.initialize_database()

            # Create test file
            test_file = Path(temp_dir) / "test.md"
            test_file.write_text("# Test\nContent")

            indexer = Indexer(db_manager)

            # Index file (should record performance metrics)
            indexer.index_file(test_file)

            # Check that performance metrics were recorded
            from mdquery.logging_config import get_performance_monitor
            monitor = get_performance_monitor()
            stats = monitor.get_statistics()

            # Should have recorded file indexing metrics
            assert len(stats) > 0


if __name__ == "__main__":
    pytest.main([__file__])