"""
Integration tests for the SQL query engine with the full mdquery system.

Tests the query engine working with real indexer and database components.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from mdquery.database import DatabaseManager
from mdquery.query import QueryEngine
from mdquery.indexer import Indexer
from mdquery.models import FileMetadata, ParsedContent


class TestQueryEngineIntegration:
    """Integration tests for QueryEngine with other components."""

    @pytest.fixture
    def integrated_system(self):
        """Create an integrated system with database, indexer, and query engine."""
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            db_path = Path(tmp_file.name)

        # Initialize components
        db_manager = DatabaseManager(db_path)
        db_manager.initialize_database()
        indexer = Indexer(db_manager)
        query_engine = QueryEngine(db_manager)

        # Add sample data
        sample_metadata = FileMetadata(
            path=Path('test.md'),
            filename='test.md',
            directory='.',
            modified_date=datetime(2023, 1, 1, 10, 0, 0),
            created_date=datetime(2023, 1, 1, 9, 0, 0),
            file_size=1000,
            content_hash='testhash',
            word_count=100,
            heading_count=2
        )

        sample_content = ParsedContent(
            frontmatter={'title': 'Test Document', 'category': 'test'},
            content='This is test content for integration testing.',
            title='Test Document',
            headings=['Introduction', 'Conclusion'],
            tags=['test', 'integration'],
            links=[{'link_text': 'Example', 'link_target': 'https://example.com', 'link_type': 'markdown', 'is_internal': False}]
        )

        indexer._store_file_data(sample_metadata, sample_content)

        yield {
            'db_manager': db_manager,
            'indexer': indexer,
            'query_engine': query_engine,
            'db_path': db_path
        }

        # Cleanup
        db_manager.close()
        if db_path.exists():
            db_path.unlink()

    def test_query_indexed_data(self, integrated_system):
        """Test querying data that was indexed by the indexer."""
        query_engine = integrated_system['query_engine']

        # Query files
        result = query_engine.execute_query("SELECT * FROM files")
        assert result.row_count == 1
        assert result.rows[0]['filename'] == 'test.md'
        assert result.rows[0]['word_count'] == 7  # Actual word count from content

        # Query frontmatter
        result = query_engine.execute_query("""
            SELECT key, value FROM frontmatter ORDER BY key
        """)
        assert result.row_count == 2
        keys = [row['key'] for row in result.rows]
        assert 'title' in keys
        assert 'category' in keys

    def test_fts_search_integration(self, integrated_system):
        """Test full-text search on indexed content."""
        query_engine = integrated_system['query_engine']

        # Search for content
        result = query_engine.execute_query("""
            SELECT f.filename
            FROM content_fts
            JOIN files f ON content_fts.file_id = f.id
            WHERE content_fts MATCH 'integration'
        """)
        assert result.row_count == 1
        assert result.rows[0]['filename'] == 'test.md'

    def test_view_queries_integration(self, integrated_system):
        """Test querying the unified views."""
        query_engine = integrated_system['query_engine']

        # Query files with metadata view
        result = query_engine.execute_query("SELECT * FROM files_with_metadata")
        assert result.row_count == 1
        row = result.rows[0]
        assert row['filename'] == 'test.md'
        assert row['title'] == 'Test Document'
        assert 'test' in row['tags'] and 'integration' in row['tags']  # Tags are concatenated

    def test_tag_and_link_queries(self, integrated_system):
        """Test querying tags and links."""
        query_engine = integrated_system['query_engine']

        # Query tags
        result = query_engine.execute_query("SELECT * FROM tag_summary ORDER BY tag")
        assert result.row_count == 2
        tags = [row['tag'] for row in result.rows]
        assert 'test' in tags
        assert 'integration' in tags

        # Query links
        result = query_engine.execute_query("SELECT * FROM link_summary")
        assert result.row_count == 1
        assert result.rows[0]['link_target'] == 'https://example.com'
        assert result.rows[0]['is_internal'] == 0

    def test_complex_join_queries(self, integrated_system):
        """Test complex queries with multiple joins."""
        query_engine = integrated_system['query_engine']

        # Complex query joining files, frontmatter, and tags
        result = query_engine.execute_query("""
            SELECT
                f.filename,
                fm.value as title,
                GROUP_CONCAT(t.tag) as all_tags
            FROM files f
            LEFT JOIN frontmatter fm ON f.id = fm.file_id AND fm.key = 'title'
            LEFT JOIN tags t ON f.id = t.file_id
            GROUP BY f.id, f.filename, fm.value
        """)

        assert result.row_count == 1
        row = result.rows[0]
        assert row['filename'] == 'test.md'
        assert row['title'] == 'Test Document'
        assert 'test' in row['all_tags']
        assert 'integration' in row['all_tags']

    def test_aggregation_queries_integration(self, integrated_system):
        """Test aggregation queries on real data."""
        query_engine = integrated_system['query_engine']

        # Aggregation query
        result = query_engine.execute_query("""
            SELECT
                COUNT(*) as total_files,
                SUM(word_count) as total_words,
                COUNT(DISTINCT directory) as directories
            FROM files
        """)

        assert result.row_count == 1
        row = result.rows[0]
        assert row['total_files'] == 1
        assert row['total_words'] == 7  # Actual word count
        assert row['directories'] == 1

    def test_result_formatting_integration(self, integrated_system):
        """Test result formatting with real data."""
        query_engine = integrated_system['query_engine']

        result = query_engine.execute_query("SELECT filename, word_count FROM files")

        # Test all formats
        json_output = query_engine.format_results(result, 'json')
        assert '"filename": "test.md"' in json_output

        csv_output = query_engine.format_results(result, 'csv')
        assert 'filename,word_count' in csv_output
        assert 'test.md,7' in csv_output

        table_output = query_engine.format_results(result, 'table')
        assert 'test.md' in table_output
        assert 'Rows: 1' in table_output

        md_output = query_engine.format_results(result, 'markdown')
        assert '| test.md | 7 |' in md_output

    def test_schema_validation_integration(self, integrated_system):
        """Test schema validation with real database."""
        query_engine = integrated_system['query_engine']
        db_manager = integrated_system['db_manager']

        # Validate schema
        assert db_manager.validate_schema() is True

        # Get schema info
        schema = query_engine.get_schema()
        assert schema['version'] == 1
        assert 'files' in schema['tables']
        assert 'files_with_metadata' in schema['views']

    def test_query_performance_integration(self, integrated_system):
        """Test query performance tracking."""
        query_engine = integrated_system['query_engine']

        result = query_engine.execute_query("SELECT COUNT(*) FROM files")

        # Should have execution time
        assert result.execution_time_ms > 0
        assert result.execution_time_ms < 1000  # Should be fast for small data

    def test_error_handling_integration(self, integrated_system):
        """Test error handling in integrated system."""
        query_engine = integrated_system['query_engine']

        # Test invalid query
        with pytest.raises(Exception):  # Could be QueryValidationError or QueryExecutionError
            query_engine.execute_query("SELECT * FROM nonexistent_table")

        # Test dangerous query
        with pytest.raises(Exception):
            query_engine.execute_query("DROP TABLE files")

    def test_multiple_files_integration(self, integrated_system):
        """Test with multiple indexed files."""
        indexer = integrated_system['indexer']
        query_engine = integrated_system['query_engine']

        # Add another file
        metadata2 = FileMetadata(
            path=Path('test2.md'),
            filename='test2.md',
            directory='subdir',
            modified_date=datetime(2023, 1, 2, 10, 0, 0),
            created_date=datetime(2023, 1, 2, 9, 0, 0),
            file_size=800,
            content_hash='testhash2',
            word_count=80,
            heading_count=1
        )

        content2 = ParsedContent(
            frontmatter={'title': 'Second Document', 'category': 'example'},
            content='This is another test document for verification.',
            title='Second Document',
            headings=['Overview'],
            tags=['example', 'test'],
            links=[]
        )

        indexer._store_file_data(metadata2, content2)

        # Query multiple files
        result = query_engine.execute_query("SELECT COUNT(*) as count FROM files")
        assert result.rows[0]['count'] == 2

        # Query by directory
        result = query_engine.execute_query("SELECT filename FROM files WHERE directory = 'subdir'")
        assert result.row_count == 1
        assert result.rows[0]['filename'] == 'test2.md'

        # Query common tags
        result = query_engine.execute_query("""
            SELECT tag, COUNT(*) as count
            FROM tags
            WHERE tag = 'test'
            GROUP BY tag
        """)
        assert result.row_count == 1
        assert result.rows[0]['count'] == 2  # Both files have 'test' tag