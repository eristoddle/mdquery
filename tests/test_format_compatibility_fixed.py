"""
Integration tests for different markdown format compatibility.
Tests mdquery against Obsidian, Joplin, Jekyll, and generic markdown formats.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from mdquery.indexer import Indexer
from mdquery.query import QueryEngine
from mdquery.cache import CacheManager
from mdquery.database import DatabaseManager


class TestFormatCompatibility:
    """Test compatibility with different markdown formats."""

    @pytest.fixture
    def test_data_dir(self):
        """Get the test data directory."""
        return Path(__file__).parent / "test_data"

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "test.db"
            cache_manager = CacheManager(cache_path)
            cache_manager.initialize_cache()
            db_manager = DatabaseManager(cache_path)
            yield db_manager, cache_manager

    def test_obsidian_format_compatibility(self, test_data_dir, temp_db):
        """Test compatibility with Obsidian vault format."""
        db_manager, cache_manager = temp_db
        obsidian_dir = test_data_dir / "obsidian"

        # Index Obsidian files
        indexer = Indexer(database_manager=db_manager, cache_manager=cache_manager)
        indexer.index_directory(obsidian_dir)

        # Test query engine
        query_engine = QueryEngine(database_manager=db_manager)

        # Test wikilink extraction
        result = query_engine.execute_query(
            "SELECT * FROM links WHERE link_type = 'wikilink'"
        )
        assert len(result.rows) > 0, "Should find wikilinks in Obsidian files"

        # Test nested tag extraction
        result = query_engine.execute_query(
            "SELECT * FROM tags WHERE tag LIKE '%/%'"
        )
        assert len(result.rows) > 0, "Should find nested tags in Obsidian files"

        # Test daily notes pattern
        result = query_engine.execute_query(
            "SELECT * FROM files WHERE filename LIKE '____-__-__.md'"
        )
        assert len(result.rows) > 0, "Should find daily note files"

        # Test MOC (Map of Content) detection
        result = query_engine.execute_query(
            "SELECT * FROM frontmatter WHERE key = 'type' AND value = 'moc'"
        )
        assert len(result.rows) > 0, "Should find MOC files"

    def test_joplin_format_compatibility(self, test_data_dir, temp_db):
        """Test compatibility with Joplin export format."""
        db_manager, cache_manager = temp_db
        joplin_dir = test_data_dir / "joplin"

        # Index Joplin files
        indexer = Indexer(database_manager=db_manager, cache_manager=cache_manager)
        indexer.index_directory(joplin_dir)

        # Test query engine
        query_engine = QueryEngine(database_manager=db_manager)

        # Test Joplin ID extraction (should be in content)
        result = query_engine.execute_query(
            "SELECT * FROM content_fts WHERE content MATCH 'id:'"
        )
        assert len(result.rows) > 0, "Should find Joplin IDs in content"

        # Test timestamp format in content
        result = query_engine.execute_query(
            "SELECT * FROM content_fts WHERE content MATCH 'Created:'"
        )
        assert len(result.rows) > 0, "Should find Joplin timestamps"

        # Test tag extraction from content
        result = query_engine.execute_query(
            "SELECT * FROM content_fts WHERE content MATCH 'Tags:'"
        )
        assert len(result.rows) > 0, "Should find Joplin tags in content"

    def test_jekyll_format_compatibility(self, test_data_dir, temp_db):
        """Test compatibility with Jekyll site format."""
        db_manager, cache_manager = temp_db
        jekyll_dir = test_data_dir / "jekyll"

        # Index Jekyll files
        indexer = Indexer(database_manager=db_manager, cache_manager=cache_manager)
        indexer.index_directory(jekyll_dir)

        # Test query engine
        query_engine = QueryEngine(database_manager=db_manager)

        # Test Jekyll post format
        result = query_engine.execute_query(
            "SELECT * FROM frontmatter WHERE key = 'layout' AND value = 'post'"
        )
        assert len(result.rows) > 0, "Should find Jekyll posts"

        # Test Jekyll categories
        result = query_engine.execute_query(
            "SELECT * FROM frontmatter WHERE key = 'categories'"
        )
        assert len(result.rows) > 0, "Should find Jekyll categories"

        # Test Jekyll collections
        result = query_engine.execute_query(
            "SELECT * FROM files WHERE directory LIKE '%_projects%'"
        )
        assert len(result.rows) > 0, "Should find Jekyll collection files"

        # Test liquid tags (should be preserved in content)
        result = query_engine.execute_query(
            "SELECT * FROM content_fts WHERE content MATCH 'highlight'"
        )
        assert len(result.rows) > 0, "Should find liquid tags in content"

    def test_generic_markdown_compatibility(self, test_data_dir, temp_db):
        """Test compatibility with generic markdown files."""
        db_manager, cache_manager = temp_db
        generic_dir = test_data_dir / "generic"

        # Index generic files
        indexer = Indexer(database_manager=db_manager, cache_manager=cache_manager)
        indexer.index_directory(generic_dir)

        # Test query engine
        query_engine = QueryEngine(database_manager=db_manager)

        # Test files without frontmatter
        result = query_engine.execute_query(
            "SELECT * FROM files WHERE filename = 'simple-note.md'"
        )
        assert len(result.rows) == 1, "Should index files without frontmatter"

        # Test files with standard frontmatter
        result = query_engine.execute_query(
            "SELECT * FROM frontmatter WHERE key = 'title' AND value LIKE '%Frontmatter%'"
        )
        assert len(result.rows) > 0, "Should parse standard YAML frontmatter"

        # Test various frontmatter types
        result = query_engine.execute_query(
            "SELECT * FROM frontmatter WHERE value_type = 'array'"
        )
        assert len(result.rows) > 0, "Should detect array values in frontmatter"

        result = query_engine.execute_query(
            "SELECT * FROM frontmatter WHERE value_type = 'boolean'"
        )
        assert len(result.rows) > 0, "Should detect boolean values in frontmatter"


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "test.db"
            cache_manager = CacheManager(cache_path)
            cache_manager.initialize_cache()
            db_manager = DatabaseManager(cache_path)
            yield db_manager, cache_manager

    def test_edge_case_files(self, temp_db):
        """Test handling of edge case files."""
        db_manager, cache_manager = temp_db
        test_data_dir = Path(__file__).parent / "test_data" / "edge_cases"

        # Index edge case files
        indexer = Indexer(database_manager=db_manager, cache_manager=cache_manager)
        indexer.index_directory(test_data_dir)

        query_engine = QueryEngine(database_manager=db_manager)

        # Test empty file handling
        result = query_engine.execute_query(
            "SELECT * FROM files WHERE filename = 'empty-file.md'"
        )
        assert len(result.rows) == 1, "Should index empty files"
        assert result.rows[0]['word_count'] == 0, "Empty file should have 0 word count"

        # Test frontmatter-only file
        result = query_engine.execute_query(
            "SELECT * FROM files WHERE filename = 'frontmatter-only.md'"
        )
        assert len(result.rows) == 1, "Should index frontmatter-only files"

        # Test malformed frontmatter handling
        result = query_engine.execute_query(
            "SELECT * FROM files WHERE filename = 'malformed-frontmatter.md'"
        )
        assert len(result.rows) == 1, "Should handle malformed frontmatter gracefully"

        # Should still extract content even with malformed frontmatter
        result = query_engine.execute_query(
            "SELECT * FROM content_fts WHERE content MATCH 'Malformed' AND file_id IN "
            "(SELECT id FROM files WHERE filename = 'malformed-frontmatter.md')"
        )
        assert len(result.rows) > 0, "Should extract content despite malformed frontmatter"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])