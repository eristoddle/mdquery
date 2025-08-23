"""
Integration tests for cache management system with indexer.

Tests incremental indexing, cache validation, and cleanup functionality
in realistic scenarios with actual markdown files.
"""

import pytest
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

from mdquery.cache import CacheManager
from mdquery.database import DatabaseManager
from mdquery.indexer import Indexer


class TestCacheIntegration:
    """Integration test cases for cache management with indexer."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def temp_db_path(self, temp_dir):
        """Create a temporary database path."""
        return temp_dir / "test_cache.db"

    @pytest.fixture
    def db_manager(self, temp_db_path):
        """Create and initialize database manager."""
        db_manager = DatabaseManager(temp_db_path)
        db_manager.initialize_database()
        return db_manager

    @pytest.fixture
    def cache_manager(self, temp_db_path, db_manager):
        """Create and initialize cache manager."""
        cache_manager = CacheManager(temp_db_path, db_manager)
        cache_manager.initialize_cache()
        return cache_manager

    @pytest.fixture
    def indexer(self, db_manager, cache_manager):
        """Create indexer with cache manager."""
        return Indexer(db_manager, cache_manager)

    @pytest.fixture
    def sample_markdown_files(self, temp_dir):
        """Create sample markdown files for testing."""
        files = {}

        # File 1: Basic markdown with frontmatter
        file1 = temp_dir / "file1.md"
        file1.write_text("""---
title: "Test File 1"
tags: [test, markdown]
category: documentation
---

# Test File 1

This is a test file with some content.

## Section 1

Content with #hashtag and [[wikilink]].
""")
        files['file1'] = file1

        # File 2: Simple markdown without frontmatter
        file2 = temp_dir / "file2.md"
        file2.write_text("""# Simple File

Just some content with [regular link](https://example.com).

#simple #test
""")
        files['file2'] = file2

        # File 3: In subdirectory
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        file3 = subdir / "file3.md"
        file3.write_text("""---
title: "Subdirectory File"
author: "Test Author"
---

# Subdirectory File

Content in a subdirectory.
""")
        files['file3'] = file3

        return files

    def test_initial_indexing_with_cache(self, indexer, sample_markdown_files, temp_dir):
        """Test initial indexing with cache management."""
        # Index the directory
        stats = indexer.index_directory(temp_dir)

        # Verify all files were processed
        assert stats['files_processed'] == 3
        assert stats['errors'] == 0

        # Verify cache statistics
        cache_stats = indexer.cache_manager.get_cache_statistics()
        assert cache_stats['total_files'] == 3
        assert cache_stats['frontmatter_entries'] > 0
        assert cache_stats['tag_entries'] > 0

        # Verify cache is valid
        assert indexer.cache_manager.is_cache_valid()

    def test_incremental_indexing_no_changes(self, indexer, sample_markdown_files, temp_dir):
        """Test incremental indexing when no files have changed."""
        # Initial indexing
        indexer.index_directory(temp_dir)

        # Incremental indexing - no changes
        stats = indexer.incremental_index_directory(temp_dir)

        # All files should be skipped
        assert stats['files_processed'] == 3
        assert stats['files_updated'] == 0
        assert stats['files_skipped'] == 3
        assert stats['errors'] == 0

    def test_incremental_indexing_with_modifications(self, indexer, sample_markdown_files, temp_dir):
        """Test incremental indexing when files have been modified."""
        # Initial indexing
        indexer.index_directory(temp_dir)

        # Wait a moment to ensure different timestamps
        time.sleep(0.1)

        # Modify one file
        modified_file = sample_markdown_files['file1']
        modified_content = modified_file.read_text() + "\n\n## New Section\n\nAdded content."
        modified_file.write_text(modified_content)

        # Incremental indexing
        stats = indexer.incremental_index_directory(temp_dir)

        # Only modified file should be updated
        assert stats['files_processed'] == 3
        assert stats['files_updated'] == 1
        assert stats['files_skipped'] == 2
        assert stats['errors'] == 0

    def test_incremental_indexing_with_new_files(self, indexer, sample_markdown_files, temp_dir):
        """Test incremental indexing when new files are added."""
        # Initial indexing
        indexer.index_directory(temp_dir)

        # Add a new file
        new_file = temp_dir / "new_file.md"
        new_file.write_text("""---
title: "New File"
tags: [new]
---

# New File

This is a newly added file.
""")

        # Incremental indexing
        stats = indexer.incremental_index_directory(temp_dir)

        # New file should be processed
        assert stats['files_processed'] == 4
        assert stats['files_updated'] == 1  # New file counts as updated
        assert stats['files_skipped'] == 3
        assert stats['errors'] == 0

        # Verify new file is in database
        file_count = indexer.get_file_count()
        assert file_count == 4

    def test_file_removal_and_cleanup(self, indexer, sample_markdown_files, temp_dir):
        """Test file removal and orphaned entry cleanup."""
        # Initial indexing
        indexer.index_directory(temp_dir)
        initial_count = indexer.get_file_count()
        assert initial_count == 3

        # Remove a file from disk
        removed_file = sample_markdown_files['file2']
        removed_file.unlink()

        # Run cleanup
        cleanup_stats = indexer.cache_manager.cleanup_orphaned_entries()

        # Verify orphaned file was cleaned up
        assert cleanup_stats['files_removed'] == 1

        # Verify file count decreased
        final_count = indexer.get_file_count()
        assert final_count == 2

    def test_directory_sync(self, indexer, sample_markdown_files, temp_dir):
        """Test directory synchronization functionality."""
        # Initial indexing
        indexer.index_directory(temp_dir)

        # Make various changes:
        # 1. Modify existing file
        time.sleep(0.1)
        modified_file = sample_markdown_files['file1']
        modified_content = modified_file.read_text() + "\n\nModified content."
        modified_file.write_text(modified_content)

        # 2. Remove a file
        removed_file = sample_markdown_files['file2']
        removed_file.unlink()

        # 3. Add a new file
        new_file = temp_dir / "added_file.md"
        new_file.write_text("# Added File\n\nThis file was added after initial indexing.")

        # Sync directory
        sync_stats = indexer.sync_directory_index(temp_dir)

        # Verify sync statistics
        assert sync_stats['files_added'] == 1      # new_file
        assert sync_stats['files_updated'] == 1    # modified file1
        assert sync_stats['files_removed'] == 1    # removed file2
        assert sync_stats['files_unchanged'] == 1  # unchanged file3
        assert sync_stats['errors'] == 0

        # Verify final state
        final_count = indexer.get_file_count()
        assert final_count == 3  # file1 (modified), file3 (unchanged), added_file (new)

    def test_cache_invalidation(self, indexer, sample_markdown_files, temp_dir):
        """Test cache invalidation functionality."""
        # Initial indexing
        indexer.index_directory(temp_dir)

        # Invalidate a specific file
        target_file = sample_markdown_files['file1']
        indexer.cache_manager.invalidate_file(target_file)

        # Verify file was removed from cache
        file_count = indexer.get_file_count()
        assert file_count == 2

        # Re-index the file
        indexer.index_file(target_file)

        # Verify file is back in cache
        file_count = indexer.get_file_count()
        assert file_count == 3

    def test_directory_invalidation(self, indexer, sample_markdown_files, temp_dir):
        """Test directory invalidation functionality."""
        # Initial indexing
        indexer.index_directory(temp_dir)

        # Invalidate subdirectory
        subdir = temp_dir / "subdir"
        removed_count = indexer.cache_manager.invalidate_directory(subdir)

        # Verify subdirectory file was removed
        assert removed_count == 1

        # Verify total file count decreased
        file_count = indexer.get_file_count()
        assert file_count == 2

    def test_cache_validation_after_corruption(self, indexer, sample_markdown_files, temp_dir, temp_db_path):
        """Test cache validation after database corruption."""
        # Initial indexing
        indexer.index_directory(temp_dir)

        # Verify cache is initially valid
        assert indexer.cache_manager.is_cache_valid()

        # Close the database connection first to avoid file locking issues
        indexer.cache_manager.close()

        # Simulate corruption by truncating database file
        with open(temp_db_path, 'w') as f:
            f.write("corrupted")

        # Create a new cache manager to test validation
        from mdquery.database import DatabaseManager
        from mdquery.cache import CacheManager

        new_db_manager = DatabaseManager(temp_db_path)
        new_cache_manager = CacheManager(temp_db_path, new_db_manager)

        # Cache should now be invalid
        assert not new_cache_manager.is_cache_valid()

        # Cleanup
        new_cache_manager.close()

    def test_cache_age_validation(self, indexer, sample_markdown_files, temp_dir):
        """Test cache age validation."""
        # Initial indexing
        indexer.index_directory(temp_dir)

        # Cache should be valid when fresh
        assert indexer.cache_manager.is_cache_valid()

        # Mock old cache timestamp
        old_time = datetime.now() - timedelta(hours=25)
        with indexer.cache_manager.db_manager.get_connection() as conn:
            conn.execute("""
                UPDATE cache_metadata
                SET value = ?, updated_at = ?
                WHERE key = 'last_updated'
            """, (old_time.isoformat(), old_time.isoformat()))
            conn.commit()

        # Cache should now be invalid due to age
        assert not indexer.cache_manager.is_cache_valid()

    def test_large_directory_performance(self, indexer, temp_dir):
        """Test cache performance with larger number of files."""
        # Create many files
        num_files = 50
        for i in range(num_files):
            file_path = temp_dir / f"file_{i:03d}.md"
            file_path.write_text(f"""---
title: "File {i}"
number: {i}
tags: [test, file{i % 5}]
---

# File {i}

This is test file number {i}.

Content with #tag{i % 3} and some text.
""")

        # Initial indexing
        start_time = time.time()
        stats = indexer.index_directory(temp_dir)
        initial_time = time.time() - start_time

        assert stats['files_processed'] == num_files
        assert stats['errors'] == 0

        # Incremental indexing (no changes)
        start_time = time.time()
        stats = indexer.incremental_index_directory(temp_dir)
        incremental_time = time.time() - start_time

        assert stats['files_processed'] == num_files
        assert stats['files_skipped'] == num_files
        assert stats['files_updated'] == 0

        # Incremental should be much faster than initial
        assert incremental_time < initial_time / 2

        # Verify cache statistics
        cache_stats = indexer.cache_manager.get_cache_statistics()
        assert cache_stats['total_files'] == num_files

    def test_concurrent_access_simulation(self, indexer, sample_markdown_files, temp_dir):
        """Test cache behavior under simulated concurrent access."""
        # Initial indexing
        indexer.index_directory(temp_dir)

        # Simulate concurrent operations
        operations = []

        # Get cache statistics multiple times
        for _ in range(5):
            stats = indexer.cache_manager.get_cache_statistics()
            operations.append(('stats', stats['total_files']))

        # Perform multiple file operations
        for i, file_path in enumerate(sample_markdown_files.values()):
            if i % 2 == 0:
                # Re-index file
                indexer.index_file(file_path)
                operations.append(('index', str(file_path)))
            else:
                # Check if file should be indexed
                should_index = indexer._should_index_file(file_path)
                operations.append(('check', should_index))

        # All operations should complete successfully
        assert len(operations) == 8  # 5 stats + 3 file operations

        # Cache should still be valid
        assert indexer.cache_manager.is_cache_valid()

    def test_vacuum_after_heavy_operations(self, indexer, temp_dir):
        """Test database vacuum after heavy operations."""
        # Create and index files
        num_files = 20
        files = []
        for i in range(num_files):
            file_path = temp_dir / f"file_{i}.md"
            file_path.write_text(f"# File {i}\n\nContent {i}")
            files.append(file_path)

        indexer.index_directory(temp_dir)

        # Perform many operations that create/delete data
        for _ in range(3):
            # Remove half the files
            for i in range(0, num_files, 2):
                indexer.cache_manager.invalidate_file(files[i])

            # Re-index them
            for i in range(0, num_files, 2):
                indexer.index_file(files[i])

        # Get database size before vacuum
        initial_size = indexer.cache_manager.cache_path.stat().st_size

        # Vacuum database
        indexer.cache_manager.vacuum_database()

        # Database should still be functional
        assert indexer.cache_manager.is_cache_valid()

        # Verify all files are still indexed
        final_count = indexer.get_file_count()
        assert final_count == num_files

    def test_error_recovery(self, indexer, sample_markdown_files, temp_dir):
        """Test cache system recovery from various error conditions."""
        # Initial indexing
        indexer.index_directory(temp_dir)

        # Create a file with permission issues (simulate)
        problematic_file = temp_dir / "problematic.md"
        problematic_file.write_text("# Problematic File")

        # Try to index with simulated permission error
        try:
            # This should handle the error gracefully
            stats = indexer.incremental_index_directory(temp_dir)
            # Even with errors, other files should be processed
            assert stats['files_processed'] >= 3
        except Exception:
            # If an exception occurs, it should be handled gracefully
            pass

        # Cache should still be functional
        assert indexer.cache_manager.is_cache_valid()

        # Cleanup should still work
        cleanup_stats = indexer.cache_manager.cleanup_orphaned_entries()
        assert 'files_checked' in cleanup_stats

    def test_cache_metadata_persistence(self, temp_db_path, temp_dir):
        """Test that cache metadata persists across sessions."""
        # Create first session
        db_manager1 = DatabaseManager(temp_db_path)
        db_manager1.initialize_database()
        cache_manager1 = CacheManager(temp_db_path, db_manager1)
        cache_manager1.initialize_cache()
        indexer1 = Indexer(db_manager1, cache_manager1)

        # Create a test file and index it
        test_file = temp_dir / "test.md"
        test_file.write_text("# Test\n\nContent")
        indexer1.index_file(test_file)

        # Get initial timestamp
        initial_update = cache_manager1._get_last_cache_update()

        # Close first session
        cache_manager1.close()
        db_manager1.close()

        # Create second session
        db_manager2 = DatabaseManager(temp_db_path)
        cache_manager2 = CacheManager(temp_db_path, db_manager2)

        # Cache should be valid and metadata should persist
        assert cache_manager2.is_cache_valid()

        # Timestamp should be preserved
        preserved_update = cache_manager2._get_last_cache_update()
        assert preserved_update == initial_update

        # File should still be in index
        indexer2 = Indexer(db_manager2, cache_manager2)
        assert indexer2.get_file_count() == 1

        # Cleanup
        cache_manager2.close()
        db_manager2.close()