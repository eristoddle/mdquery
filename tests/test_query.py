"""
Unit tests for the SQL query engine.

Tests query validation, execution, result formatting, and error handling
for the mdquery query engine.
"""

import pytest
import sqlite3
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from mdquery.query import QueryEngine, QueryError, QueryValidationError, QueryExecutionError
from mdquery.database import DatabaseManager, DatabaseError
from mdquery.models import QueryResult


class TestQueryEngine:
    """Test cases for QueryEngine class."""

    @pytest.fixture
    def db_manager(self):
        """Create a test database manager with sample data."""
        # Use in-memory database for testing
        db_manager = DatabaseManager(":memory:")
        db_manager.initialize_database()

        # Insert sample data
        with db_manager.get_connection() as conn:
            # Sample files
            conn.execute("""
                INSERT INTO files (path, filename, directory, modified_date, created_date, file_size, content_hash, word_count, heading_count)
                VALUES
                ('test1.md', 'test1.md', '.', '2023-01-01 10:00:00', '2023-01-01 09:00:00', 1000, 'hash1', 100, 3),
                ('test2.md', 'test2.md', '.', '2023-01-02 10:00:00', '2023-01-02 09:00:00', 2000, 'hash2', 200, 5),
                ('subdir/test3.md', 'test3.md', 'subdir', '2023-01-03 10:00:00', '2023-01-03 09:00:00', 1500, 'hash3', 180, 4)
            """)

            # Sample frontmatter
            conn.execute("""
                INSERT INTO frontmatter (file_id, key, value, value_type)
                VALUES
                (1, 'title', 'Test Document 1', 'string'),
                (1, 'category', 'research', 'string'),
                (2, 'title', 'Test Document 2', 'string'),
                (2, 'category', 'blog', 'string'),
                (3, 'title', 'Test Document 3', 'string')
            """)

            # Sample tags
            conn.execute("""
                INSERT INTO tags (file_id, tag, source)
                VALUES
                (1, 'research', 'frontmatter'),
                (1, 'important', 'content'),
                (2, 'blog', 'frontmatter'),
                (3, 'draft', 'content')
            """)

            # Sample links
            conn.execute("""
                INSERT INTO links (file_id, link_text, link_target, link_type, is_internal)
                VALUES
                (1, 'Link to test2', 'test2.md', 'wikilink', 1),
                (2, 'External link', 'https://example.com', 'markdown', 0),
                (3, 'Link to test1', 'test1.md', 'wikilink', 1)
            """)

            # Sample FTS content
            conn.execute("""
                INSERT INTO content_fts (file_id, title, content, headings)
                VALUES
                (1, 'Test Document 1', 'This is test content about research and important topics', 'Introduction,Methods,Results'),
                (2, 'Test Document 2', 'This is blog content about various topics', 'Overview,Details'),
                (3, 'Test Document 3', 'This is draft content still being written', 'Draft,Notes,TODO')
            """)

            conn.commit()

        return db_manager

    @pytest.fixture
    def query_engine(self, db_manager):
        """Create a query engine with test database."""
        return QueryEngine(db_manager)

    def test_init(self, db_manager):
        """Test QueryEngine initialization."""
        engine = QueryEngine(db_manager)
        assert engine.db_manager == db_manager
        assert engine._query_timeout == 30.0
        assert engine._max_results == 10000

    def test_execute_simple_query(self, query_engine):
        """Test executing a simple SELECT query."""
        result = query_engine.execute_query("SELECT * FROM files ORDER BY id")

        assert isinstance(result, QueryResult)
        assert result.row_count == 3
        assert len(result.rows) == 3
        assert len(result.columns) > 0
        assert result.execution_time_ms > 0
        assert result.query == "SELECT * FROM files ORDER BY id"

        # Check first row data
        first_row = result.rows[0]
        assert first_row['filename'] == 'test1.md'
        assert first_row['word_count'] == 100

    def test_execute_query_with_where_clause(self, query_engine):
        """Test executing query with WHERE clause."""
        result = query_engine.execute_query("SELECT * FROM files WHERE word_count > 150")

        assert result.row_count == 2
        assert all(row['word_count'] > 150 for row in result.rows)

    def test_execute_query_with_join(self, query_engine):
        """Test executing query with JOIN."""
        query = """
        SELECT f.filename, t.tag
        FROM files f
        JOIN tags t ON f.id = t.file_id
        WHERE t.tag = 'research'
        """
        result = query_engine.execute_query(query)

        assert result.row_count == 1
        assert result.rows[0]['filename'] == 'test1.md'
        assert result.rows[0]['tag'] == 'research'

    def test_execute_fts_query(self, query_engine):
        """Test executing FTS5 full-text search query."""
        query = """
        SELECT f.filename, content_fts.content as content
        FROM content_fts
        JOIN files f ON content_fts.file_id = f.id
        WHERE content_fts MATCH 'research'
        """
        result = query_engine.execute_query(query)

        assert result.row_count == 1
        assert result.rows[0]['filename'] == 'test1.md'
        assert 'research' in result.rows[0]['content']

    def test_execute_query_with_view(self, query_engine):
        """Test executing query against a view."""
        result = query_engine.execute_query("SELECT * FROM files_with_metadata WHERE title IS NOT NULL")

        assert result.row_count == 3
        assert all(row['title'] is not None for row in result.rows)

    def test_execute_query_empty_result(self, query_engine):
        """Test executing query that returns no results."""
        result = query_engine.execute_query("SELECT * FROM files WHERE filename = 'nonexistent.md'")

        assert result.row_count == 0
        assert len(result.rows) == 0
        assert len(result.columns) > 0

    def test_validate_query_valid(self, query_engine):
        """Test validation of valid queries."""
        valid_queries = [
            "SELECT * FROM files",
            "SELECT filename, word_count FROM files WHERE word_count > 100",
            "SELECT f.*, t.tag FROM files f LEFT JOIN tags t ON f.id = t.file_id",
            "SELECT COUNT(*) FROM files",
            "SELECT * FROM files ORDER BY modified_date DESC LIMIT 10"
        ]

        for query in valid_queries:
            assert query_engine.validate_query(query) is True

    def test_validate_query_empty(self, query_engine):
        """Test validation of empty query."""
        with pytest.raises(QueryValidationError, match="Query cannot be empty"):
            query_engine.validate_query("")

        with pytest.raises(QueryValidationError, match="Query cannot be empty"):
            query_engine.validate_query("   ")

    def test_validate_query_dangerous_patterns(self, query_engine):
        """Test validation blocks dangerous SQL patterns."""
        dangerous_queries = [
            "DROP TABLE files",
            "DELETE FROM files",
            "INSERT INTO files VALUES (1, 'test')",
            "UPDATE files SET filename = 'hacked'",
            "SELECT * FROM files; DROP TABLE files;",
            "SELECT * FROM files -- comment",
            "SELECT * FROM files /* comment */",
            "PRAGMA table_info(files)"
        ]

        for query in dangerous_queries:
            with pytest.raises(QueryValidationError):
                query_engine.validate_query(query)

    def test_validate_query_non_select(self, query_engine):
        """Test validation blocks non-SELECT queries."""
        with pytest.raises(QueryValidationError):
            query_engine.validate_query("CREATE TABLE test (id INTEGER)")

    def test_validate_query_invalid_table(self, query_engine):
        """Test validation blocks invalid table references."""
        with pytest.raises(QueryValidationError, match="Invalid table references"):
            query_engine.validate_query("SELECT * FROM invalid_table")

    def test_validate_query_syntax_error(self, query_engine):
        """Test validation catches syntax errors."""
        with pytest.raises((QueryValidationError, DatabaseError)):
            query_engine.validate_query("SELECT * FROM files WHERE")

    def test_get_schema(self, query_engine):
        """Test getting database schema information."""
        schema = query_engine.get_schema()

        assert isinstance(schema, dict)
        assert 'version' in schema
        assert 'tables' in schema
        assert 'views' in schema
        assert 'indexes' in schema

        # Check that expected tables are present
        expected_tables = ['files', 'frontmatter', 'tags', 'links']
        for table in expected_tables:
            assert table in schema['tables']

    def test_format_results_json(self, query_engine):
        """Test formatting results as JSON."""
        result = query_engine.execute_query("SELECT filename, word_count FROM files LIMIT 2")
        json_output = query_engine.format_results(result, 'json')

        # Parse JSON to verify it's valid
        parsed = json.loads(json_output)
        assert 'rows' in parsed
        assert 'columns' in parsed
        assert 'row_count' in parsed
        assert parsed['row_count'] == 2

    def test_format_results_csv(self, query_engine):
        """Test formatting results as CSV."""
        result = query_engine.execute_query("SELECT filename, word_count FROM files LIMIT 2")
        csv_output = query_engine.format_results(result, 'csv')

        lines = csv_output.strip().split('\n')
        assert len(lines) == 3  # Header + 2 data rows
        assert 'filename,word_count' in lines[0]
        assert 'test1.md,100' in lines[1]

    def test_format_results_table(self, query_engine):
        """Test formatting results as ASCII table."""
        result = query_engine.execute_query("SELECT filename, word_count FROM files LIMIT 2")
        table_output = query_engine.format_results(result, 'table')

        assert '|' in table_output  # Table borders
        assert 'filename' in table_output
        assert 'word_count' in table_output
        assert 'test1.md' in table_output
        assert 'Rows: 2' in table_output
        assert 'Execution time:' in table_output

    def test_format_results_markdown(self, query_engine):
        """Test formatting results as Markdown table."""
        result = query_engine.execute_query("SELECT filename, word_count FROM files LIMIT 2")
        md_output = query_engine.format_results(result, 'markdown')

        lines = md_output.split('\n')
        assert '| filename | word_count |' in lines[0]
        assert '| --- | --- |' in lines[1]
        assert '| test1.md | 100 |' in lines[2]
        assert '**Results:** 2 rows' in md_output

    def test_format_results_unsupported_format(self, query_engine):
        """Test error handling for unsupported format."""
        result = query_engine.execute_query("SELECT * FROM files LIMIT 1")

        with pytest.raises(QueryError, match="Unsupported format type"):
            query_engine.format_results(result, 'xml')

    def test_format_results_empty(self, query_engine):
        """Test formatting empty results."""
        result = query_engine.execute_query("SELECT * FROM files WHERE filename = 'nonexistent'")

        json_output = query_engine.format_results(result, 'json')
        parsed = json.loads(json_output)
        assert parsed['row_count'] == 0

        csv_output = query_engine.format_results(result, 'csv')
        assert csv_output == ""

        table_output = query_engine.format_results(result, 'table')
        assert "No results found" in table_output

    def test_get_sample_queries(self, query_engine):
        """Test getting sample queries."""
        samples = query_engine.get_sample_queries()

        assert isinstance(samples, list)
        assert len(samples) > 0

        for sample in samples:
            assert 'name' in sample
            assert 'description' in sample
            assert 'query' in sample
            assert isinstance(sample['query'], str)

    def test_set_query_timeout(self, query_engine):
        """Test setting query timeout."""
        query_engine.set_query_timeout(60.0)
        assert query_engine._query_timeout == 60.0

        # Test minimum value
        query_engine.set_query_timeout(0.5)
        assert query_engine._query_timeout == 1.0

    def test_set_max_results(self, query_engine):
        """Test setting maximum results."""
        query_engine.set_max_results(5000)
        assert query_engine._max_results == 5000

        # Test minimum value
        query_engine.set_max_results(0)
        assert query_engine._max_results == 1

    def test_explain_query(self, query_engine):
        """Test query explanation."""
        explanation = query_engine.explain_query("SELECT * FROM files WHERE word_count > 100")

        assert isinstance(explanation, dict)
        assert 'query' in explanation
        assert 'plan' in explanation
        assert 'estimated_cost' in explanation
        assert isinstance(explanation['plan'], list)

    def test_explain_query_invalid(self, query_engine):
        """Test explanation of invalid query."""
        with pytest.raises(QueryValidationError):
            query_engine.explain_query("DROP TABLE files")

    def test_query_execution_error(self, query_engine):
        """Test handling of query execution errors."""
        # Mock database connection to raise an error during execution, not validation
        with patch.object(query_engine, 'validate_query'):  # Skip validation
            with patch.object(query_engine.db_manager, 'get_connection') as mock_conn:
                mock_conn.return_value.__enter__.return_value.execute.side_effect = sqlite3.Error("Test error")

                with pytest.raises(QueryExecutionError, match="Query execution failed"):
                    query_engine.execute_query("SELECT * FROM files")

    def test_max_results_limit(self, query_engine):
        """Test that results are limited to max_results."""
        # Set a low limit for testing
        query_engine.set_max_results(2)

        result = query_engine.execute_query("SELECT * FROM files")
        assert result.row_count == 2  # Limited to 2 even though there are 3 files

    def test_parameterized_query(self, query_engine):
        """Test executing parameterized queries."""
        # Note: This test demonstrates the interface, but SQLite parameter binding
        # would need to be implemented in the actual query execution
        result = query_engine.execute_query("SELECT * FROM files WHERE word_count > 150")
        assert result.row_count == 2  # 200 and 180 are both > 150

    def test_concurrent_queries(self, query_engine):
        """Test that multiple queries can be executed."""
        # Execute multiple queries to test connection handling
        result1 = query_engine.execute_query("SELECT COUNT(*) as count FROM files")
        result2 = query_engine.execute_query("SELECT COUNT(*) as count FROM tags")

        assert result1.rows[0]['count'] == 3
        assert result2.rows[0]['count'] == 4

    def test_query_with_aggregation(self, query_engine):
        """Test queries with aggregation functions."""
        result = query_engine.execute_query("""
            SELECT
                COUNT(*) as file_count,
                AVG(word_count) as avg_words,
                MAX(word_count) as max_words,
                MIN(word_count) as min_words
            FROM files
        """)

        assert result.row_count == 1
        row = result.rows[0]
        assert row['file_count'] == 3
        assert row['avg_words'] == 160.0  # (100 + 200 + 180) / 3
        assert row['max_words'] == 200
        assert row['min_words'] == 100

    def test_query_with_group_by(self, query_engine):
        """Test queries with GROUP BY."""
        result = query_engine.execute_query("""
            SELECT source, COUNT(*) as tag_count
            FROM tags
            GROUP BY source
            ORDER BY source
        """)

        assert result.row_count == 2
        assert result.rows[0]['source'] == 'content'
        assert result.rows[0]['tag_count'] == 2
        assert result.rows[1]['source'] == 'frontmatter'
        assert result.rows[1]['tag_count'] == 2


class TestQueryValidation:
    """Test cases for query validation functionality."""

    def test_dangerous_pattern_detection(self):
        """Test detection of dangerous SQL patterns."""
        engine = QueryEngine(Mock())

        dangerous_patterns = [
            "SELECT * FROM files; DROP TABLE files;",
            "SELECT * FROM files WHERE 1=1 -- comment",
            "SELECT * FROM files /* comment */ WHERE 1=1",
            "PRAGMA table_info(files)",
            "ATTACH DATABASE 'test.db' AS test"
        ]

        for pattern in dangerous_patterns:
            with pytest.raises(QueryValidationError):
                engine.validate_query(pattern)

    def test_table_reference_validation(self):
        """Test validation of table references."""
        engine = QueryEngine(Mock())

        # Valid table references
        valid_queries = [
            "SELECT * FROM files",
            "SELECT * FROM files_with_metadata",
            "SELECT * FROM content_fts",
            "SELECT f.*, t.tag FROM files f JOIN tags t ON f.id = t.file_id"
        ]

        for query in valid_queries:
            # Should not raise exception for table reference validation
            # (may still fail on syntax validation due to mocked database)
            try:
                engine._validate_table_references(query)
            except QueryValidationError as e:
                if "Invalid table references" in str(e):
                    pytest.fail(f"Valid query rejected: {query}")

    def test_keyword_validation(self):
        """Test that allowed keywords are properly recognized."""
        engine = QueryEngine(Mock())

        # All these keywords should be allowed
        allowed_keywords = [
            'SELECT', 'FROM', 'WHERE', 'JOIN', 'LEFT', 'RIGHT', 'INNER',
            'ON', 'AND', 'OR', 'NOT', 'IN', 'LIKE', 'BETWEEN', 'IS', 'NULL',
            'ORDER', 'BY', 'GROUP', 'HAVING', 'LIMIT', 'OFFSET', 'AS',
            'DISTINCT', 'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'MATCH'
        ]

        for keyword in allowed_keywords:
            assert keyword in engine.ALLOWED_KEYWORDS


class TestResultFormatting:
    """Test cases for result formatting functionality."""

    @pytest.fixture
    def sample_result(self):
        """Create a sample QueryResult for testing."""
        return QueryResult(
            rows=[
                {'id': 1, 'name': 'test1', 'value': 100},
                {'id': 2, 'name': 'test2', 'value': 200},
                {'id': 3, 'name': None, 'value': 150}
            ],
            columns=['id', 'name', 'value'],
            row_count=3,
            execution_time_ms=15.5,
            query="SELECT * FROM test"
        )

    def test_json_formatting(self, sample_result):
        """Test JSON formatting with various data types."""
        engine = QueryEngine(Mock())
        json_output = engine._format_json(sample_result)

        parsed = json.loads(json_output)
        assert parsed['row_count'] == 3
        assert len(parsed['rows']) == 3
        assert parsed['rows'][0]['id'] == 1
        assert parsed['rows'][2]['name'] is None

    def test_csv_formatting(self, sample_result):
        """Test CSV formatting with None values."""
        engine = QueryEngine(Mock())
        csv_output = engine._format_csv(sample_result)

        lines = csv_output.strip().split('\n')
        assert len(lines) == 4  # Header + 3 data rows
        assert 'id,name,value' in lines[0]
        assert '3,,150' in lines[3]  # None converted to empty string

    def test_table_formatting(self, sample_result):
        """Test ASCII table formatting."""
        engine = QueryEngine(Mock())
        table_output = engine._format_table(sample_result)

        assert '| id | name  | value |' in table_output
        assert '|----|-------|-------|' in table_output
        assert '| 1  | test1 | 100   |' in table_output
        assert 'Rows: 3' in table_output
        assert 'Execution time: 15.50ms' in table_output

    def test_markdown_formatting(self, sample_result):
        """Test Markdown table formatting."""
        engine = QueryEngine(Mock())
        md_output = engine._format_markdown(sample_result)

        lines = md_output.split('\n')
        assert '| id | name | value |' in lines[0]
        assert '| --- | --- | --- |' in lines[1]
        assert '| 1 | test1 | 100 |' in lines[2]
        assert '**Results:** 3 rows' in md_output
        assert '**Execution time:** 15.50ms' in md_output

    def test_empty_result_formatting(self):
        """Test formatting of empty results."""
        empty_result = QueryResult(
            rows=[],
            columns=['id', 'name'],
            row_count=0,
            execution_time_ms=5.0,
            query="SELECT * FROM empty"
        )

        engine = QueryEngine(Mock())

        # JSON should still work
        json_output = engine._format_json(empty_result)
        parsed = json.loads(json_output)
        assert parsed['row_count'] == 0

        # CSV should be empty
        csv_output = engine._format_csv(empty_result)
        assert csv_output == ""

        # Table should show "No results found"
        table_output = engine._format_table(empty_result)
        assert "No results found" in table_output

        # Markdown should show "No results found"
        md_output = engine._format_markdown(empty_result)
        assert "No results found" in md_output