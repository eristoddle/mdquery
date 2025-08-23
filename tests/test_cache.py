"""
Unit tests for cache management system.

Tests cache validation, incremental indexing support, cleanup functionality,
and integration with the database system.
"""

import pytest
import tempfile
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from mdquery.cache import CacheManager, CacheError
from mdquery.database import DatabaseManager, DatabaseError


class TestCacheManager:
    """Test cases for CacheManager class."""

    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database path for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        yield db_path
        # Cleanup
        if db_path.exists():
            db_path.unlink()

    @pytest.fixture
    def db_manager(self, temp_db_path):
        """Create a database manager for testing."""
        db_manager = DatabaseManager(temp_db_path)
        db_manager.initialize_database()
        return db_manager

    @pytest.fixture
    def cache_manager(self, temp_db_path, db_manager):
        """Create a cache manager for testing."""
        return CacheManager(temp_db_path, db_manager)

    def test_init(self, temp_db_path):
        """Test CacheManager initialization."""
        cache_manager = CacheManager(temp_db_path)

        assert cache_manager.cache_path == temp_db_path
        assert cache_manager.max_cache_age_hours == 24
        assert cache_manager.validation_batch_size == 100

    def test_init_with_database_manager(self, temp_db_path, db_manager):
        """Test CacheManager initialization with existing database manager."""
        cache_manager = CacheManager(temp_db_path, db_manager)

        assert cache_manager.cache_path == temp_db_path
        assert cache_manager.db_manager == db_manager

    def test_initialize_cache_new_database(self, temp_db_path):
        """Test cache initialization with new database."""
        cache_manager = CacheManager(temp_db_path)

        # Remove the file if it exists
        if temp_db_path.exists():
            temp_db_path.unlink()

        cache_manager.initialize_cache()

        assert temp_db_path.exists()

        # Verify cache metadata table was created
        with cache_manager.db_manager.get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='cache_metadata'"
            )
            assert cursor.fetchone() is not None

    def test_initialize_cache_existing_database(self, cache_manager):
        """Test cache initialization with existing database."""
        # Initialize once
        cache_manager.initialize_cache()

        # Initialize again - should not fail
        cache_manager.initialize_cache()

        assert cache_manager.cache_path.exists()

    def test_initialize_cache_with_path_parameter(self, temp_db_path):
        """Test cache initialization with path parameter."""
        cache_manager = CacheManager(Path("/tmp/dummy"))

        # Remove the file if it exists
        if temp_db_path.exists():
            temp_db_path.unlink()

        cache_manager.initialize_cache(temp_db_path)

        assert cache_manager.cache_path == temp_db_path
        assert temp_db_path.exists()

    def test_initialize_cache_creates_parent_directory(self):
        """Test that cache initialization creates parent directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "subdir" / "cache.db"
            cache_manager = CacheManager(cache_path)

            cache_manager.initialize_cache()

            assert cache_path.exists()
            assert cache_path.parent.exists()

    def test_initialize_cache_failure(self, temp_db_path):
        """Test cache initialization failure handling."""
        cache_manager = CacheManager(temp_db_path)

        # Mock database manager to raise an exception
        with patch.object(cache_manager, 'db_manager') as mock_db:
            mock_db.initialize_database.side_effect = DatabaseError("Test error")

            with pytest.raises(CacheError, match="Failed to initialize cache"):
                cache_manager.initialize_cache()

    def test_is_cache_valid_no_file(self, temp_db_path):
        """Test cache validation when cache file doesn't exist."""
        cache_manager = CacheManager(temp_db_path)

        # Ensure file doesn't exist
        if temp_db_path.exists():
            temp_db_path.unlink()

        assert not cache_manager.is_cache_valid()

    def test_is_cache_valid_fresh_cache(self, cache_manager):
        """Test cache validation with fresh cache."""
        cache_manager.initialize_cache()

        assert cache_manager.is_cache_valid()

    def test_is_cache_valid_old_cache(self, cache_manager):
        """Test cache validation with old cache."""
        cache_manager.initialize_cache()

        # Mock old timestamp
        old_time = datetime.now() - timedelta(hours=25)
        with cache_manager.db_manager.get_connection() as conn:
            conn.execute("""
                UPDATE cache_metadata
                SET value = ?, updated_at = ?
                WHERE key = 'last_updated'
            """, (old_time.isoformat(), old_time.isoformat()))
            conn.commit()

        assert not cache_manager.is_cache_valid()

    def test_is_cache_valid_schema_invalid(self, cache_manager):
        """Test cache validation with invalid schema."""
        cache_manager.initialize_cache()

        # Mock schema validation failure
        with patch.object(cache_manager.db_manager, 'validate_schema', return_value=False):
            assert not cache_manager.is_cache_valid()

    def test_is_cache_valid_database_error(self, cache_manager):
        """Test cache validation with database error."""
        cache_manager.initialize_cache()

        # Mock database connection error
        with patch.object(cache_manager.db_manager, 'get_connection') as mock_conn:
            mock_conn.side_effect = DatabaseError("Connection failed")

            assert not cache_manager.is_cache_valid()

    def test_invalidate_file_existing(self, cache_manager):
        """Test file invalidation for existing file."""
        cache_manager.initialize_cache()

        # Add a test file to the database
        test_path = Path("/test/file.md")
        with cache_manager.db_manager.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO files (path, filename, directory, modified_date, file_size, content_hash)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (str(test_path), "file.md", "/test", datetime.now().isoformat(), 100, "hash123"))
            file_id = cursor.lastrowid

            # Add related data
            conn.execute("INSERT INTO frontmatter (file_id, key, value, value_type) VALUES (?, ?, ?, ?)",
                        (file_id, "title", "Test", "string"))
            conn.execute("INSERT INTO tags (file_id, tag, source) VALUES (?, ?, ?)",
                        (file_id, "test", "frontmatter"))
            conn.execute("INSERT INTO content_fts (file_id, title, content, headings) VALUES (?, ?, ?, ?)",
                        (file_id, "Test", "Content", ""))
            conn.commit()

        # Invalidate the file
        cache_manager.invalidate_file(test_path)

        # Verify file and related data are removed
        with cache_manager.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM files WHERE path = ?", (str(test_path),))
            assert cursor.fetchone()[0] == 0

            cursor = conn.execute("SELECT COUNT(*) FROM frontmatter WHERE file_id = ?", (file_id,))
            assert cursor.fetchone()[0] == 0

            cursor = conn.execute("SELECT COUNT(*) FROM content_fts WHERE file_id = ?", (file_id,))
            assert cursor.fetchone()[0] == 0

    def test_invalidate_file_nonexistent(self, cache_manager):
        """Test file invalidation for non-existent file."""
        cache_manager.initialize_cache()

        test_path = Path("/nonexistent/file.md")

        # Should not raise an error
        cache_manager.invalidate_file(test_path)

    def test_invalidate_file_database_error(self, cache_manager):
        """Test file invalidation with database error."""
        cache_manager.initialize_cache()

        test_path = Path("/test/file.md")

        # Mock database error
        with patch.object(cache_manager.db_manager, 'get_connection') as mock_conn:
            mock_conn.side_effect = DatabaseError("Connection failed")

            with pytest.raises(CacheError, match="Failed to invalidate file"):
                cache_manager.invalidate_file(test_path)

    def test_invalidate_directory(self, cache_manager):
        """Test directory invalidation."""
        cache_manager.initialize_cache()

        # Add test files to the database
        test_dir = Path("/test")
        test_files = [
            Path("/test/file1.md"),
            Path("/test/subdir/file2.md"),
            Path("/other/file3.md")
        ]

        with cache_manager.db_manager.get_connection() as conn:
            for file_path in test_files:
                conn.execute("""
                    INSERT INTO files (path, filename, directory, modified_date, file_size, content_hash)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (str(file_path), file_path.name, str(file_path.parent),
                     datetime.now().isoformat(), 100, f"hash_{file_path.name}"))
            conn.commit()

        # Invalidate the test directory
        count = cache_manager.invalidate_directory(test_dir)

        # Should have removed 2 files (file1.md and subdir/file2.md)
        assert count == 2

        # Verify only the /other/file3.md remains
        with cache_manager.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM files")
            assert cursor.fetchone()[0] == 1

            cursor = conn.execute("SELECT path FROM files")
            remaining_file = cursor.fetchone()[0]
            assert remaining_file == str(test_files[2])

    def test_cleanup_orphaned_entries(self, cache_manager):
        """Test cleanup of orphaned entries."""
        cache_manager.initialize_cache()

        # Create temporary files for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            existing_file = temp_path / "existing.md"
            existing_file.write_text("# Existing file")

            # Add files to database - one existing, one non-existent
            with cache_manager.db_manager.get_connection() as conn:
                # Existing file
                cursor = conn.execute("""
                    INSERT INTO files (path, filename, directory, modified_date, file_size, content_hash)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (str(existing_file), "existing.md", str(temp_path),
                     datetime.now().isoformat(), 100, "hash1"))
                existing_id = cursor.lastrowid

                # Non-existent file
                cursor = conn.execute("""
                    INSERT INTO files (path, filename, directory, modified_date, file_size, content_hash)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, ("/nonexistent/file.md", "file.md", "/nonexistent",
                     datetime.now().isoformat(), 100, "hash2"))
                orphaned_id = cursor.lastrowid

                # Add related data for both files
                for file_id in [existing_id, orphaned_id]:
                    conn.execute("INSERT INTO frontmatter (file_id, key, value, value_type) VALUES (?, ?, ?, ?)",
                                (file_id, "title", "Test", "string"))
                    conn.execute("INSERT INTO tags (file_id, tag, source) VALUES (?, ?, ?)",
                                (file_id, "test", "frontmatter"))
                    conn.execute("INSERT INTO links (file_id, link_text, link_target, link_type, is_internal) VALUES (?, ?, ?, ?, ?)",
                                (file_id, "Link", "target", "markdown", False))
                    conn.execute("INSERT INTO content_fts (file_id, title, content, headings) VALUES (?, ?, ?, ?)",
                                (file_id, "Test", "Content", ""))

                conn.commit()

            # Run cleanup
            stats = cache_manager.cleanup_orphaned_entries()

            # Verify statistics
            assert stats['files_checked'] == 2
            assert stats['files_removed'] == 1
            assert stats['orphaned_frontmatter'] == 1
            assert stats['orphaned_tags'] == 1
            assert stats['orphaned_links'] == 1
            assert stats['orphaned_fts'] == 1

            # Verify only existing file remains
            with cache_manager.db_manager.get_connection() as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM files")
                assert cursor.fetchone()[0] == 1

                cursor = conn.execute("SELECT path FROM files")
                remaining_file = cursor.fetchone()[0]
                assert remaining_file == str(existing_file)

    def test_cleanup_orphaned_entries_no_orphans(self, cache_manager):
        """Test cleanup when there are no orphaned entries."""
        cache_manager.initialize_cache()

        # Create temporary file
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            existing_file = temp_path / "existing.md"
            existing_file.write_text("# Existing file")

            # Add only existing file to database
            with cache_manager.db_manager.get_connection() as conn:
                conn.execute("""
                    INSERT INTO files (path, filename, directory, modified_date, file_size, content_hash)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (str(existing_file), "existing.md", str(temp_path),
                     datetime.now().isoformat(), 100, "hash1"))
                conn.commit()

            # Run cleanup
            stats = cache_manager.cleanup_orphaned_entries()

            # Verify no files were removed
            assert stats['files_checked'] == 1
            assert stats['files_removed'] == 0

    def test_cleanup_orphaned_entries_database_error(self, cache_manager):
        """Test cleanup with database error."""
        cache_manager.initialize_cache()

        # Mock database error
        with patch.object(cache_manager.db_manager, 'get_connection') as mock_conn:
            mock_conn.side_effect = DatabaseError("Connection failed")

            with pytest.raises(CacheError, match="Failed to cleanup orphaned entries"):
                cache_manager.cleanup_orphaned_entries()

    def test_get_cache_statistics(self, cache_manager):
        """Test getting cache statistics."""
        cache_manager.initialize_cache()

        # Add some test data
        with cache_manager.db_manager.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO files (path, filename, directory, modified_date, file_size, content_hash)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("/test/file.md", "file.md", "/test", datetime.now().isoformat(), 100, "hash1"))
            file_id = cursor.lastrowid

            conn.execute("INSERT INTO frontmatter (file_id, key, value, value_type) VALUES (?, ?, ?, ?)",
                        (file_id, "title", "Test", "string"))
            conn.execute("INSERT INTO tags (file_id, tag, source) VALUES (?, ?, ?)",
                        (file_id, "test", "frontmatter"))
            conn.execute("INSERT INTO links (file_id, link_text, link_target, link_type, is_internal) VALUES (?, ?, ?, ?, ?)",
                        (file_id, "Link", "target", "markdown", False))
            conn.execute("INSERT INTO content_fts (file_id, title, content, headings) VALUES (?, ?, ?, ?)",
                        (file_id, "Test", "Content", ""))
            conn.commit()

        stats = cache_manager.get_cache_statistics()

        assert stats['total_files'] == 1
        assert stats['frontmatter_entries'] == 1
        assert stats['tag_entries'] == 1
        assert stats['link_entries'] == 1
        assert stats['fts_entries'] == 1
        assert 'cache_path' in stats
        assert 'cache_size_bytes' in stats
        assert 'cache_age' in stats
        assert 'schema_valid' in stats

    def test_get_cache_statistics_error(self, cache_manager):
        """Test getting cache statistics with database error."""
        cache_manager.initialize_cache()

        # Mock database error
        with patch.object(cache_manager.db_manager, 'get_connection') as mock_conn:
            mock_conn.side_effect = DatabaseError("Connection failed")

            stats = cache_manager.get_cache_statistics()

            assert 'error' in stats

    def test_get_modified_files_since(self, cache_manager):
        """Test getting files modified since a specific time."""
        cache_manager.initialize_cache()

        # Add test files with different modification times
        base_time = datetime.now()
        old_time = base_time - timedelta(hours=2)
        new_time = base_time - timedelta(minutes=30)

        with cache_manager.db_manager.get_connection() as conn:
            # Old file
            conn.execute("""
                INSERT INTO files (path, filename, directory, modified_date, file_size, content_hash)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("/test/old.md", "old.md", "/test", old_time.isoformat(), 100, "hash1"))

            # New file
            conn.execute("""
                INSERT INTO files (path, filename, directory, modified_date, file_size, content_hash)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("/test/new.md", "new.md", "/test", new_time.isoformat(), 100, "hash2"))

            conn.commit()

        # Get files modified since 1 hour ago
        since_time = base_time - timedelta(hours=1)
        modified_files = cache_manager.get_modified_files_since(since_time)

        assert len(modified_files) == 1
        assert modified_files[0][0] == Path("/test/new.md")
        assert modified_files[0][1] == new_time

    def test_get_modified_files_since_error(self, cache_manager):
        """Test getting modified files with database error."""
        cache_manager.initialize_cache()

        # Mock database error
        with patch.object(cache_manager.db_manager, 'get_connection') as mock_conn:
            mock_conn.side_effect = DatabaseError("Connection failed")

            since_time = datetime.now() - timedelta(hours=1)
            modified_files = cache_manager.get_modified_files_since(since_time)

            assert modified_files == []

    def test_vacuum_database(self, cache_manager):
        """Test database vacuum operation."""
        cache_manager.initialize_cache()

        # Should not raise an error
        cache_manager.vacuum_database()

    def test_vacuum_database_error(self, cache_manager):
        """Test database vacuum with error."""
        cache_manager.initialize_cache()

        # Mock database error
        with patch.object(cache_manager.db_manager, 'get_connection') as mock_conn:
            mock_context = MagicMock()
            mock_context.__enter__.return_value.execute.side_effect = sqlite3.Error("Vacuum failed")
            mock_conn.return_value = mock_context

            with pytest.raises(CacheError, match="Failed to vacuum database"):
                cache_manager.vacuum_database()

    def test_context_manager(self, cache_manager):
        """Test CacheManager as context manager."""
        with cache_manager as cm:
            assert cm == cache_manager

        # Verify close was called
        # Note: We can't easily test this without mocking, but the context manager should work

    def test_close(self, cache_manager):
        """Test closing cache manager."""
        cache_manager.initialize_cache()

        # Mock the database manager close method
        with patch.object(cache_manager.db_manager, 'close') as mock_close:
            cache_manager.close()
            mock_close.assert_called_once()

    def test_cache_age_calculation(self, cache_manager):
        """Test cache age calculation methods."""
        cache_manager.initialize_cache()

        # Test getting cache age
        age = cache_manager._get_cache_age()
        assert age is not None
        assert isinstance(age, timedelta)
        assert age.total_seconds() < 60  # Should be very recent

        # Test getting last update time
        last_update = cache_manager._get_last_cache_update()
        assert last_update is not None
        assert isinstance(last_update, datetime)

    def test_cache_age_no_metadata(self, cache_manager):
        """Test cache age when no metadata exists."""
        cache_manager.initialize_cache()

        # Remove metadata
        with cache_manager.db_manager.get_connection() as conn:
            conn.execute("DELETE FROM cache_metadata WHERE key = 'last_updated'")
            conn.commit()

        age = cache_manager._get_cache_age()
        assert age is None

        last_update = cache_manager._get_last_cache_update()
        assert last_update is None

    def test_database_integrity_check(self, cache_manager):
        """Test database integrity checking."""
        cache_manager.initialize_cache()

        # Should pass for a fresh database
        assert cache_manager._check_database_integrity()

    def test_database_integrity_check_error(self, cache_manager):
        """Test database integrity check with error."""
        cache_manager.initialize_cache()

        # Mock database error
        with patch.object(cache_manager.db_manager, 'get_connection') as mock_conn:
            mock_conn.side_effect = DatabaseError("Connection failed")

            assert not cache_manager._check_database_integrity()

    def test_cleanup_orphaned_related_data(self, cache_manager):
        """Test cleanup of orphaned related data."""
        cache_manager.initialize_cache()

        # Add orphaned data directly (without corresponding files)
        with cache_manager.db_manager.get_connection() as conn:
            # Temporarily disable foreign key constraints to insert orphaned data
            conn.execute("PRAGMA foreign_keys = OFF")

            # Add orphaned frontmatter
            conn.execute("INSERT INTO frontmatter (file_id, key, value, value_type) VALUES (?, ?, ?, ?)",
                        (999, "title", "Orphaned", "string"))

            # Add orphaned tags
            conn.execute("INSERT INTO tags (file_id, tag, source) VALUES (?, ?, ?)",
                        (999, "orphaned", "frontmatter"))

            # Add orphaned links
            conn.execute("INSERT INTO links (file_id, link_text, link_target, link_type, is_internal) VALUES (?, ?, ?, ?, ?)",
                        (999, "Orphaned", "target", "markdown", False))

            # Add orphaned FTS entries
            conn.execute("INSERT INTO content_fts (file_id, title, content, headings) VALUES (?, ?, ?, ?)",
                        (999, "Orphaned", "Content", ""))

            conn.commit()

            # Re-enable foreign key constraints
            conn.execute("PRAGMA foreign_keys = ON")

            # Test the cleanup method
            stats = {'orphaned_frontmatter': 0, 'orphaned_tags': 0, 'orphaned_links': 0, 'orphaned_fts': 0}
            cache_manager._cleanup_orphaned_related_data(conn, stats)

            # Verify orphaned data was cleaned up
            assert stats['orphaned_frontmatter'] == 1
            assert stats['orphaned_tags'] == 1
            assert stats['orphaned_links'] == 1
            assert stats['orphaned_fts'] == 1

            # Verify data is actually removed
            cursor = conn.execute("SELECT COUNT(*) FROM frontmatter WHERE file_id = 999")
            assert cursor.fetchone()[0] == 0

            cursor = conn.execute("SELECT COUNT(*) FROM tags WHERE file_id = 999")
            assert cursor.fetchone()[0] == 0

            cursor = conn.execute("SELECT COUNT(*) FROM links WHERE file_id = 999")
            assert cursor.fetchone()[0] == 0

            cursor = conn.execute("SELECT COUNT(*) FROM content_fts WHERE file_id = 999")
            assert cursor.fetchone()[0] == 0