#!/usr/bin/env python3
"""
Demo script for cache management system functionality.

This script demonstrates the cache management features including:
- Cache initialization and validation
- Incremental indexing
- Cache cleanup and maintenance
- Performance benefits of caching
"""

import tempfile
import time
from pathlib import Path

from mdquery.database import DatabaseManager
from mdquery.cache import CacheManager
from mdquery.indexer import Indexer


def create_sample_files(directory: Path, count: int = 10):
    """Create sample markdown files for testing."""
    print(f"Creating {count} sample markdown files...")

    for i in range(count):
        file_path = directory / f"sample_{i:03d}.md"
        content = f"""---
title: "Sample File {i}"
tags: [sample, test, file{i % 3}]
category: demo
number: {i}
---

# Sample File {i}

This is sample file number {i} for demonstrating cache functionality.

## Content Section

Some content with #hashtag{i % 5} and [[wikilink_{i}]].

### Subsection

More content with [external link](https://example.com/{i}).

Content includes various elements:
- Lists
- **Bold text**
- *Italic text*
- `Code snippets`

File created for cache management demonstration.
"""
        file_path.write_text(content)

    print(f"Created {count} files in {directory}")


def demonstrate_cache_functionality():
    """Demonstrate cache management functionality."""
    print("=== Cache Management System Demo ===\n")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        cache_db_path = temp_path / "demo_cache.db"

        print(f"Working directory: {temp_path}")
        print(f"Cache database: {cache_db_path}\n")

        # Create sample files
        create_sample_files(temp_path, 15)

        # Initialize database and cache
        print("1. Initializing database and cache...")
        db_manager = DatabaseManager(cache_db_path)
        db_manager.initialize_database()

        cache_manager = CacheManager(cache_db_path, db_manager)
        cache_manager.initialize_cache()

        indexer = Indexer(db_manager, cache_manager)

        print(f"   Cache initialized: {cache_manager.is_cache_valid()}")

        # Initial indexing
        print("\n2. Performing initial indexing...")
        start_time = time.time()
        stats = indexer.index_directory(temp_path)
        initial_time = time.time() - start_time

        print(f"   Files processed: {stats['files_processed']}")
        print(f"   Errors: {stats['errors']}")
        print(f"   Time taken: {initial_time:.3f} seconds")

        # Show cache statistics
        print("\n3. Cache statistics after initial indexing:")
        cache_stats = cache_manager.get_cache_statistics()
        print(f"   Total files: {cache_stats['total_files']}")
        print(f"   Frontmatter entries: {cache_stats['frontmatter_entries']}")
        print(f"   Tag entries: {cache_stats['tag_entries']}")
        print(f"   Link entries: {cache_stats['link_entries']}")
        print(f"   Cache size: {cache_stats['cache_size_bytes']} bytes")
        print(f"   Cache age: {cache_stats['cache_age']}")

        # Incremental indexing (no changes)
        print("\n4. Performing incremental indexing (no changes)...")
        start_time = time.time()
        stats = indexer.incremental_index_directory(temp_path)
        incremental_time = time.time() - start_time

        print(f"   Files processed: {stats['files_processed']}")
        print(f"   Files updated: {stats['files_updated']}")
        print(f"   Files skipped: {stats['files_skipped']}")
        print(f"   Time taken: {incremental_time:.3f} seconds")
        print(f"   Speed improvement: {initial_time / incremental_time:.1f}x faster")

        # Modify a file and test incremental indexing
        print("\n5. Modifying a file and testing incremental indexing...")
        modified_file = temp_path / "sample_005.md"
        original_content = modified_file.read_text()
        modified_content = original_content + "\n\n## New Section\n\nThis content was added to test incremental indexing."

        # Wait a moment to ensure different timestamp
        time.sleep(0.1)
        modified_file.write_text(modified_content)

        start_time = time.time()
        stats = indexer.incremental_index_directory(temp_path)
        incremental_modified_time = time.time() - start_time

        print(f"   Files processed: {stats['files_processed']}")
        print(f"   Files updated: {stats['files_updated']}")
        print(f"   Files skipped: {stats['files_skipped']}")
        print(f"   Time taken: {incremental_modified_time:.3f} seconds")

        # Add a new file
        print("\n6. Adding a new file...")
        new_file = temp_path / "new_file.md"
        new_file.write_text("""---
title: "Newly Added File"
tags: [new, added]
---

# Newly Added File

This file was added after initial indexing to test incremental functionality.
""")

        stats = indexer.incremental_index_directory(temp_path)
        print(f"   Files processed: {stats['files_processed']}")
        print(f"   Files updated: {stats['files_updated']}")
        print(f"   Files skipped: {stats['files_skipped']}")

        # Remove a file and test cleanup
        print("\n7. Removing a file and testing cleanup...")
        removed_file = temp_path / "sample_010.md"
        removed_file.unlink()

        cleanup_stats = cache_manager.cleanup_orphaned_entries()
        print(f"   Files checked: {cleanup_stats['files_checked']}")
        print(f"   Files removed: {cleanup_stats['files_removed']}")
        print(f"   Orphaned frontmatter: {cleanup_stats['orphaned_frontmatter']}")
        print(f"   Orphaned tags: {cleanup_stats['orphaned_tags']}")
        print(f"   Orphaned links: {cleanup_stats['orphaned_links']}")

        # Directory synchronization
        print("\n8. Testing directory synchronization...")

        # Make multiple changes
        (temp_path / "sample_001.md").unlink()  # Remove file
        (temp_path / "sample_002.md").write_text(
            (temp_path / "sample_002.md").read_text() + "\n\nSynchronization test."
        )  # Modify file
        (temp_path / "sync_test.md").write_text("# Sync Test\n\nFile for sync test.")  # Add file

        sync_stats = indexer.sync_directory_index(temp_path)
        print(f"   Files added: {sync_stats['files_added']}")
        print(f"   Files updated: {sync_stats['files_updated']}")
        print(f"   Files removed: {sync_stats['files_removed']}")
        print(f"   Files unchanged: {sync_stats['files_unchanged']}")
        print(f"   Errors: {sync_stats['errors']}")

        # Cache validation
        print("\n9. Cache validation...")
        print(f"   Cache is valid: {cache_manager.is_cache_valid()}")
        print(f"   Database integrity: {cache_manager._check_database_integrity()}")

        # Performance with larger dataset
        print("\n10. Testing performance with larger dataset...")
        large_dir = temp_path / "large_test"
        large_dir.mkdir()
        create_sample_files(large_dir, 50)

        start_time = time.time()
        stats = indexer.index_directory(large_dir)
        large_initial_time = time.time() - start_time

        start_time = time.time()
        stats = indexer.incremental_index_directory(large_dir)
        large_incremental_time = time.time() - start_time

        print(f"   Large dataset initial indexing: {large_initial_time:.3f} seconds")
        print(f"   Large dataset incremental indexing: {large_incremental_time:.3f} seconds")
        print(f"   Performance ratio: {large_initial_time / large_incremental_time:.1f}x")

        # Final statistics
        print("\n11. Final cache statistics:")
        final_stats = cache_manager.get_cache_statistics()
        print(f"   Total files indexed: {final_stats['total_files']}")
        print(f"   Total frontmatter entries: {final_stats['frontmatter_entries']}")
        print(f"   Total tag entries: {final_stats['tag_entries']}")
        print(f"   Total link entries: {final_stats['link_entries']}")
        print(f"   Final cache size: {final_stats['cache_size_bytes']} bytes")

        # Database vacuum
        print("\n12. Database maintenance...")
        print("   Performing database vacuum...")
        cache_manager.vacuum_database()

        vacuum_stats = cache_manager.get_cache_statistics()
        print(f"   Cache size after vacuum: {vacuum_stats['cache_size_bytes']} bytes")

        # Cleanup
        cache_manager.close()
        db_manager.close()

        print("\n=== Demo completed successfully! ===")
        print("\nKey benefits demonstrated:")
        print("- Fast incremental indexing (only processes changed files)")
        print("- Automatic cleanup of orphaned entries")
        print("- Cache validation and integrity checking")
        print("- Directory synchronization capabilities")
        print("- Performance optimization through caching")
        print("- Database maintenance and optimization")


if __name__ == "__main__":
    demonstrate_cache_functionality()