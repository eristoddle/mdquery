"""
SQL query engine for mdquery.

This module provides SQL query execution, validation, and result formatting
for the mdquery system. It includes SQL injection protection, query optimization,
and multiple output formats.
"""

import sqlite3
import re
import json
import csv
import io
import time
import logging
from typing import Any, Dict, List, Optional, Union, Set
from pathlib import Path
from dataclasses import asdict

from .models import QueryResult
from .database import DatabaseManager, DatabaseError

logger = logging.getLogger(__name__)


class QueryError(Exception):
    """Custom exception for query-related errors."""
    pass


class QueryValidationError(QueryError):
    """Exception raised when query validation fails."""
    pass


class QueryExecutionError(QueryError):
    """Exception raised when query execution fails."""
pass


class QueryEngine:
    """
    SQL query engine with validation, execution, and formatting capabilities.

    Provides secure SQL query execution against the mdquery SQLite database
    with FTS5 support, result formatting, and comprehensive error handling.
    """

    # Allowed SQL keywords for basic validation
    ALLOWED_KEYWORDS = {
        'SELECT', 'FROM', 'WHERE', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER',
        'ON', 'AND', 'OR', 'NOT', 'IN', 'LIKE', 'BETWEEN', 'IS', 'NULL',
        'ORDER', 'BY', 'GROUP', 'HAVING', 'LIMIT', 'OFFSET', 'AS', 'DISTINCT',
        'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END',
        'UNION', 'INTERSECT', 'EXCEPT', 'ASC', 'DESC', 'MATCH', 'FTS'
    }

    # Dangerous SQL patterns that should be blocked
    DANGEROUS_PATTERNS = [
        r'\b(DROP|DELETE|INSERT|UPDATE|ALTER|CREATE|REPLACE)\b',
        r'\b(PRAGMA|ATTACH|DETACH)\b',
        r'--',  # SQL comments
        r'/\*.*?\*/',  # Multi-line comments
        r';.*',  # Multiple statements
        r'\bEXEC\b',
        r'\bEXECUTE\b',
        r'\bSP_\w+\b',  # Stored procedures
    ]

    # Available tables and views for validation
    AVAILABLE_TABLES = {
        'files', 'frontmatter', 'tags', 'links', 'content_fts',
        'files_with_metadata', 'tag_summary', 'link_summary'
    }

    def __init__(self, database_manager: DatabaseManager):
        """
        Initialize query engine.

        Args:
            database_manager: Database manager instance
        """
        self.db_manager = database_manager
        self._query_timeout = 30.0  # 30 second timeout
        self._max_results = 10000  # Maximum number of results

    def execute_query(self, sql: str, params: Optional[Dict[str, Any]] = None) -> QueryResult:
        """
        Execute SQL query with validation and error handling.

        Args:
            sql: SQL query string
            params: Optional query parameters for parameterized queries

        Returns:
            QueryResult: Query execution results

        Raises:
            QueryValidationError: If query validation fails
            QueryExecutionError: If query execution fails
        """
        # Validate query
        self.validate_query(sql)

        # Execute query with timing
        start_time = time.time()

        try:
            with self.db_manager.get_connection() as conn:
                # Set query timeout
                conn.execute(f"PRAGMA busy_timeout = {int(self._query_timeout * 1000)}")

                # Execute query
                if params:
                    cursor = conn.execute(sql, params)
                else:
                    cursor = conn.execute(sql)

                # Fetch results
                rows = cursor.fetchall()

                # Convert sqlite3.Row objects to dictionaries
                result_rows = [dict(row) for row in rows]

                # Get column names
                columns = [description[0] for description in cursor.description] if cursor.description else []

                # Check result size limit
                if len(result_rows) > self._max_results:
                    logger.warning(f"Query returned {len(result_rows)} rows, truncating to {self._max_results}")
                    result_rows = result_rows[:self._max_results]

                execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds

                return QueryResult(
                    rows=result_rows,
                    columns=columns,
                    row_count=len(result_rows),
                    execution_time_ms=execution_time,
                    query=sql
                )

        except sqlite3.Error as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Query execution failed after {execution_time:.2f}ms: {e}")
            raise QueryExecutionError(f"Query execution failed: {e}") from e

    def validate_query(self, sql: str) -> bool:
        """
        Validate SQL query for security and syntax.

        Args:
            sql: SQL query string to validate

        Returns:
            True if query is valid

        Raises:
            QueryValidationError: If query validation fails
        """
        if not sql or not sql.strip():
            raise QueryValidationError("Query cannot be empty")

        # Normalize query for validation
        normalized_sql = sql.upper().strip()

        # Check for dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, normalized_sql, re.IGNORECASE):
                raise QueryValidationError(f"Query contains dangerous pattern: {pattern}")

        # Must start with SELECT
        if not normalized_sql.startswith('SELECT'):
            raise QueryValidationError("Only SELECT queries are allowed")

        # Check for multiple statements
        if ';' in sql.rstrip(';'):
            raise QueryValidationError("Multiple statements are not allowed")

        # Validate table/view references
        self._validate_table_references(sql)

        # Basic syntax validation using SQLite parser
        try:
            with self.db_manager.get_connection() as conn:
                # Use EXPLAIN to validate syntax without executing
                conn.execute(f"EXPLAIN {sql}")
        except sqlite3.Error as e:
            raise QueryValidationError(f"Invalid SQL syntax: {e}") from e

        return True

    def _validate_table_references(self, sql: str) -> None:
        """
        Validate that all table references in the query are allowed.

        Args:
            sql: SQL query string

        Raises:
            QueryValidationError: If invalid table references are found
        """
        # Extract table names from FROM and JOIN clauses
        # This is a simplified approach - a full SQL parser would be more robust
        from_pattern = r'\bFROM\s+(\w+)'
        join_pattern = r'\bJOIN\s+(\w+)'

        tables_found = set()

        for match in re.finditer(from_pattern, sql, re.IGNORECASE):
            tables_found.add(match.group(1).lower())

        for match in re.finditer(join_pattern, sql, re.IGNORECASE):
            tables_found.add(match.group(1).lower())

        # Check if all referenced tables are allowed
        invalid_tables = tables_found - self.AVAILABLE_TABLES
        if invalid_tables:
            raise QueryValidationError(f"Invalid table references: {', '.join(invalid_tables)}")

    def get_schema(self) -> Dict[str, Any]:
        """
        Get database schema information for query building.

        Returns:
            Dictionary containing schema information
        """
        return self.db_manager.get_schema_info()

    def format_results(self, result: QueryResult, format_type: str = 'json') -> str:
        """
        Format query results in the specified format.

        Args:
            result: Query result to format
            format_type: Output format ('json', 'csv', 'table', 'markdown')

        Returns:
            Formatted result string

        Raises:
            QueryError: If format type is not supported
        """
        if format_type.lower() == 'json':
            return self._format_json(result)
        elif format_type.lower() == 'csv':
            return self._format_csv(result)
        elif format_type.lower() == 'table':
            return self._format_table(result)
        elif format_type.lower() == 'markdown':
            return self._format_markdown(result)
        else:
            raise QueryError(f"Unsupported format type: {format_type}")

    def _format_json(self, result: QueryResult) -> str:
        """Format results as JSON."""
        return json.dumps(result.to_dict(), indent=2, default=str)

    def _format_csv(self, result: QueryResult) -> str:
        """Format results as CSV."""
        if not result.rows:
            return ""

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=result.columns)
        writer.writeheader()

        for row in result.rows:
            # Convert None values to empty strings for CSV
            csv_row = {k: (v if v is not None else '') for k, v in row.items()}
            writer.writerow(csv_row)

        return output.getvalue()

    def _format_table(self, result: QueryResult) -> str:
        """Format results as ASCII table."""
        if not result.rows:
            return "No results found."

        # Calculate column widths
        col_widths = {}
        for col in result.columns:
            col_widths[col] = len(col)
            for row in result.rows:
                value = str(row.get(col, ''))
                col_widths[col] = max(col_widths[col], len(value))

        # Build table
        lines = []

        # Header
        header_line = "| " + " | ".join(col.ljust(col_widths[col]) for col in result.columns) + " |"
        separator_line = "|-" + "-|-".join("-" * col_widths[col] for col in result.columns) + "-|"

        lines.append(header_line)
        lines.append(separator_line)

        # Data rows
        for row in result.rows:
            row_line = "| " + " | ".join(
                str(row.get(col, '')).ljust(col_widths[col])
                for col in result.columns
            ) + " |"
            lines.append(row_line)

        # Footer with metadata
        lines.append("")
        lines.append(f"Rows: {result.row_count}")
        lines.append(f"Execution time: {result.execution_time_ms:.2f}ms")

        return "\n".join(lines)

    def _format_markdown(self, result: QueryResult) -> str:
        """Format results as Markdown table."""
        if not result.rows:
            return "No results found."

        lines = []

        # Header
        header_line = "| " + " | ".join(result.columns) + " |"
        separator_line = "| " + " | ".join("---" for _ in result.columns) + " |"

        lines.append(header_line)
        lines.append(separator_line)

        # Data rows
        for row in result.rows:
            row_line = "| " + " | ".join(
                str(row.get(col, '')) for col in result.columns
            ) + " |"
            lines.append(row_line)

        # Footer with metadata
        lines.append("")
        lines.append(f"**Results:** {result.row_count} rows")
        lines.append(f"**Execution time:** {result.execution_time_ms:.2f}ms")

        return "\n".join(lines)

    def get_sample_queries(self) -> List[Dict[str, str]]:
        """
        Get sample queries for documentation and testing.

        Returns:
            List of sample queries with descriptions
        """
        return [
            {
                "name": "All files",
                "description": "Get all indexed markdown files",
                "query": "SELECT * FROM files ORDER BY modified_date DESC"
            },
            {
                "name": "Files with metadata",
                "description": "Get files with common frontmatter fields",
                "query": "SELECT * FROM files_with_metadata WHERE title IS NOT NULL"
            },
            {
                "name": "Search content",
                "description": "Full-text search across all content",
                "query": "SELECT f.path, f.title, snippet(content_fts, 1, '<mark>', '</mark>', '...', 32) as snippet FROM content_fts JOIN files f ON content_fts.file_id = f.id WHERE content_fts MATCH 'search term'"
            },
            {
                "name": "Files by tag",
                "description": "Find files with specific tags",
                "query": "SELECT DISTINCT f.* FROM files f JOIN tags t ON f.id = t.file_id WHERE t.tag = 'research'"
            },
            {
                "name": "Tag statistics",
                "description": "Get tag usage statistics",
                "query": "SELECT * FROM tag_summary ORDER BY file_count DESC LIMIT 10"
            },
            {
                "name": "Recent files",
                "description": "Get recently modified files",
                "query": "SELECT path, filename, modified_date FROM files WHERE modified_date > datetime('now', '-7 days') ORDER BY modified_date DESC"
            },
            {
                "name": "Large files",
                "description": "Find files with high word counts",
                "query": "SELECT path, filename, word_count FROM files WHERE word_count > 1000 ORDER BY word_count DESC"
            },
            {
                "name": "Broken links",
                "description": "Find potentially broken internal links",
                "query": "SELECT f.path, l.link_target FROM files f JOIN links l ON f.id = l.file_id WHERE l.is_internal = 1 AND l.link_target NOT IN (SELECT path FROM files)"
            }
        ]

    def set_query_timeout(self, timeout_seconds: float) -> None:
        """
        Set query execution timeout.

        Args:
            timeout_seconds: Timeout in seconds
        """
        self._query_timeout = max(1.0, timeout_seconds)

    def set_max_results(self, max_results: int) -> None:
        """
        Set maximum number of results to return.

        Args:
            max_results: Maximum number of results
        """
        self._max_results = max(1, max_results)

    def explain_query(self, sql: str) -> Dict[str, Any]:
        """
        Get query execution plan for optimization.

        Args:
            sql: SQL query to explain

        Returns:
            Dictionary containing query plan information
        """
        self.validate_query(sql)

        try:
            with self.db_manager.get_connection() as conn:
                # Get query plan
                cursor = conn.execute(f"EXPLAIN QUERY PLAN {sql}")
                plan_rows = cursor.fetchall()

                plan = [dict(row) for row in plan_rows]

                return {
                    "query": sql,
                    "plan": plan,
                    "estimated_cost": self._estimate_query_cost(plan)
                }

        except sqlite3.Error as e:
            raise QueryExecutionError(f"Failed to explain query: {e}") from e

    def _estimate_query_cost(self, plan: List[Dict[str, Any]]) -> str:
        """
        Estimate query cost based on execution plan.

        Args:
            plan: Query execution plan

        Returns:
            Cost estimate description
        """
        # Simple cost estimation based on plan operations
        has_scan = any("SCAN" in str(row.get("detail", "")) for row in plan)
        has_index = any("INDEX" in str(row.get("detail", "")) for row in plan)

        if has_scan and not has_index:
            return "HIGH - Full table scan detected"
        elif has_index:
            return "LOW - Using indexes"
        else:
            return "MEDIUM - Mixed operations"