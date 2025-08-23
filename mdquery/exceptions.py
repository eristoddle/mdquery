"""
Comprehensive exception hierarchy for mdquery.

This module defines all custom exceptions used throughout the mdquery system,
providing clear error categorization and context for debugging and user feedback.
"""

from typing import Optional, Any, Dict
from pathlib import Path


class MdqueryError(Exception):
    """Base exception for all mdquery-related errors."""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        """
        Initialize base exception.

        Args:
            message: Error message
            context: Optional context information for debugging
        """
        super().__init__(message)
        self.context = context or {}
        self.message = message


class FileSystemError(MdqueryError):
    """Base class for file system related errors."""

    def __init__(self, message: str, file_path: Optional[Path] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize file system error.

        Args:
            message: Error message
            file_path: Path that caused the error
            context: Optional context information
        """
        super().__init__(message, context)
        self.file_path = file_path


class FileAccessError(FileSystemError):
    """Raised when file cannot be accessed due to permissions or other issues."""
    pass


class FileCorruptedError(FileSystemError):
    """Raised when file is corrupted or cannot be parsed."""
    pass


class DirectoryNotFoundError(FileSystemError):
    """Raised when specified directory does not exist."""
    pass


class IndexingError(MdqueryError):
    """Base class for indexing-related errors."""

    def __init__(self, message: str, file_path: Optional[Path] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize indexing error.

        Args:
            message: Error message
            file_path: File that caused the indexing error
            context: Optional context information
        """
        super().__init__(message, context)
        self.file_path = file_path


class ParsingError(IndexingError):
    """Raised when markdown or frontmatter parsing fails."""

    def __init__(self, message: str, file_path: Optional[Path] = None,
                 parser_type: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize parsing error.

        Args:
            message: Error message
            file_path: File that failed to parse
            parser_type: Type of parser that failed (frontmatter, markdown, etc.)
            context: Optional context information
        """
        super().__init__(message, file_path, context)
        self.parser_type = parser_type


class DatabaseError(MdqueryError):
    """Base class for database-related errors."""
    pass


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""
    pass


class DatabaseCorruptionError(DatabaseError):
    """Raised when database corruption is detected."""
    pass


class SchemaError(DatabaseError):
    """Raised when database schema issues are detected."""
    pass


class QueryError(MdqueryError):
    """Base class for query-related errors."""

    def __init__(self, message: str, query: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize query error.

        Args:
            message: Error message
            query: SQL query that caused the error
            context: Optional context information
        """
        super().__init__(message, context)
        self.query = query


class QueryValidationError(QueryError):
    """Raised when query validation fails."""
    pass


class QueryExecutionError(QueryError):
    """Raised when query execution fails."""
    pass


class QueryTimeoutError(QueryError):
    """Raised when query execution times out."""
    pass


class CacheError(MdqueryError):
    """Base class for cache-related errors."""
    pass


class CacheCorruptionError(CacheError):
    """Raised when cache corruption is detected."""
    pass


class ConfigurationError(MdqueryError):
    """Raised when configuration issues are detected."""
    pass


class PerformanceError(MdqueryError):
    """Raised when performance thresholds are exceeded."""

    def __init__(self, message: str, operation: Optional[str] = None,
                 duration: Optional[float] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize performance error.

        Args:
            message: Error message
            operation: Operation that exceeded performance threshold
            duration: Duration of the operation in seconds
            context: Optional context information
        """
        super().__init__(message, context)
        self.operation = operation
        self.duration = duration


class ResourceError(MdqueryError):
    """Raised when system resources are exhausted."""

    def __init__(self, message: str, resource_type: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize resource error.

        Args:
            message: Error message
            resource_type: Type of resource that was exhausted (memory, disk, etc.)
            context: Optional context information
        """
        super().__init__(message, context)
        self.resource_type = resource_type


class MCPError(MdqueryError):
    """Base class for MCP server related errors."""
    pass


class MCPProtocolError(MCPError):
    """Raised when MCP protocol violations occur."""
    pass


class MCPTimeoutError(MCPError):
    """Raised when MCP operations timeout."""
    pass


def format_error_context(error: MdqueryError) -> str:
    """
    Format error context for logging and debugging.

    Args:
        error: MdqueryError instance

    Returns:
        Formatted context string
    """
    context_parts = []

    # Add file path if available
    if hasattr(error, 'file_path') and error.file_path:
        context_parts.append(f"file={error.file_path}")

    # Add query if available
    if hasattr(error, 'query') and error.query:
        # Truncate long queries
        query = error.query[:100] + "..." if len(error.query) > 100 else error.query
        context_parts.append(f"query={query}")

    # Add parser type if available
    if hasattr(error, 'parser_type') and error.parser_type:
        context_parts.append(f"parser={error.parser_type}")

    # Add operation if available
    if hasattr(error, 'operation') and error.operation:
        context_parts.append(f"operation={error.operation}")

    # Add duration if available
    if hasattr(error, 'duration') and error.duration:
        context_parts.append(f"duration={error.duration:.2f}s")

    # Add resource type if available
    if hasattr(error, 'resource_type') and error.resource_type:
        context_parts.append(f"resource={error.resource_type}")

    # Add custom context
    if error.context:
        for key, value in error.context.items():
            context_parts.append(f"{key}={value}")

    return " | ".join(context_parts) if context_parts else "no context"


def create_error_summary(error: Exception) -> Dict[str, Any]:
    """
    Create a structured error summary for logging and monitoring.

    Args:
        error: Exception instance

    Returns:
        Dictionary containing error summary
    """
    summary = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "is_mdquery_error": isinstance(error, MdqueryError)
    }

    if isinstance(error, MdqueryError):
        summary["context"] = error.context
        summary["formatted_context"] = format_error_context(error)

        # Add specific attributes based on error type
        if hasattr(error, 'file_path'):
            summary["file_path"] = str(error.file_path) if error.file_path else None
        if hasattr(error, 'query'):
            summary["query"] = error.query
        if hasattr(error, 'parser_type'):
            summary["parser_type"] = error.parser_type
        if hasattr(error, 'operation'):
            summary["operation"] = error.operation
        if hasattr(error, 'duration'):
            summary["duration"] = error.duration
        if hasattr(error, 'resource_type'):
            summary["resource_type"] = error.resource_type

    return summary