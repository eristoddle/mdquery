"""
Cache management system using SQLite for persistence and validation.

This module provides cache management functionality for the mdquery system,
including SQLite database persistence, cache validation, incremental indexing
support, and cleanup of deleted files and orphaned entries.
"""

import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from .database import DatabaseManager, DatabaseError

logger = logging.getLogger(__name__)


class CacheError(Exception):
    """Custom exception for cache-related errors."""
    pass


class CacheManager:
    """
    Manages SQLite database lifecycle and file change detection.

    Provides functionality for cache validation, incremental indexing,
    and cleanup of orphaned entries to maintain database consistency.
    """

    def __init__(self, cache_path: Path, database_manager: Optional[DatabaseManager] = None):
        """
        Initialize cache manager with database path.

        Args:
            cache_path: Path to SQLite database file
            database_manager: Optional database manager instance. If None, creates new one.
        """
        self.cache_path = cache_path
        self.db_manager = database_manager or DatabaseManager(cache_path)

        # Cache validation settings
        self.max_cache_age_hours = 24  # Consider cache stale after 24 hours
        self.validation_batch_size = 100  # Process files in batches for validation

    def initialize_cache(self, cache_path: Optional[Path] = None) -> None:
        """
        Initialize SQLite database with required schema.

        Args:
            cache_path: Optional path where database should be created.
                       If None, uses the path from initialization.

        Raises:
            CacheError: If cache initialization fails
        """
        if cache_path:
            self.cache_path = cache_path
            self.db_manager = DatabaseManager(cache_path)

        try:
            # Ensure parent directory exists
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)

            # Initialize database schema
            self.db_manager.initialize_database()

            # Create cache metadata table for tracking cache state
            self._create_cache_metadata_table()

            # Set initial cache timestamp
            self._update_cache_timestamp()

            logger.info(f"Cache initialized successfully at: {self.cache_path}")

        except Exception as e:
            raise CacheError(f"Failed to initialize cache: {e}") from e

    def is_cache_valid(self) -> bool:
        """
        Check if cache is valid and up to date.

        Validates cache by checking:
        1. Database file exists and is accessible
        2. Schema is current version
        3. Cache age is within acceptable limits
        4. No database corruption

        Returns:
            True if cache can be used without rebuilding
        """
        try:
            # Check if cache file exists
            if not self.cache_path.exists():
                logger.debug("Cache file does not exist")
                return False

            # Check if database is accessible
            with self.db_manager.get_connection() as conn:
                # Verify basic connectivity
                conn.execute("SELECT 1").fetchone()

            # Validate schema integrity
            if not self.db_manager.validate_schema():
                logger.warning("Cache schema validation failed")
                return False

            # Check cache age
            cache_age = self._get_cache_age()
            if cache_age and cache_age > timedelta(hours=self.max_cache_age_hours):
                logger.info(f"Cache is too old ({cache_age}), marking as invalid")
                return False

            # Check for database corruption
            if not self._check_database_integrity():
                logger.warning("Database integrity check failed")
                return False

            logger.debug("Cache validation passed")
            return True

        except Exception as e:
            logger.error(f"Cache validation failed: {e}")
            return False

    def invalidate_file(self, file_path: Path) -> None:
        """
        Mark a specific file as needing re-indexing by removing it from cache.

        Args:
            file_path: Path to file that should be re-indexed

        Raises:
            CacheError: If file invalidation fails
        """
        try:
            with self.db_manager.get_connection() as conn:
                # Get file ID first
                cursor = conn.execute(
                    "SELECT id FROM files WHERE path = ?",
                    (str(file_path),)
                )
                result = cursor.fetchone()

                if result:
                    file_id = result['id']

                    # Delete file and all related data (cascading deletes will handle related tables)
                    conn.execute("DELETE FROM files WHERE id = ?", (file_id,))

                    # Also remove from FTS5 table explicitly
                    conn.execute("DELETE FROM content_fts WHERE file_id = ?", (file_id,))

                    conn.commit()
                    logger.debug(f"Invalidated file from cache: {file_path}")
                else:
                    logger.debug(f"File not found in cache, nothing to invalidate: {file_path}")

        except Exception as e:
            raise CacheError(f"Failed to invalidate file {file_path}: {e}") from e

    def invalidate_directory(self, directory_path: Path) -> int:
        """
        Invalidate all files in a directory and its subdirectories.

        Args:
            directory_path: Path to directory to invalidate

        Returns:
            Number of files invalidated

        Raises:
            CacheError: If directory invalidation fails
        """
        try:
            with self.db_manager.get_connection() as conn:
                # Count files to be deleted
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM files WHERE directory = ? OR directory LIKE ?",
                    (str(directory_path), f"{directory_path}%")
                )
                count = cursor.fetchone()[0]

                if count > 0:
                    # Delete files and related data
                    conn.execute(
                        "DELETE FROM files WHERE directory = ? OR directory LIKE ?",
                        (str(directory_path), f"{directory_path}%")
                    )
                    conn.commit()
                    logger.info(f"Invalidated {count} files from directory: {directory_path}")

                return count

        except Exception as e:
            raise CacheError(f"Failed to invalidate directory {directory_path}: {e}") from e

    def cleanup_orphaned_entries(self) -> Dict[str, int]:
        """
        Clean up orphaned entries for files that no longer exist on disk.

        Scans the database for files that are no longer present in the file system
        and removes their entries from all tables.

        Returns:
            Dictionary with cleanup statistics

        Raises:
            CacheError: If cleanup operation fails
        """
        stats = {
            'files_checked': 0,
            'files_removed': 0,
            'orphaned_frontmatter': 0,
            'orphaned_tags': 0,
            'orphaned_links': 0,
            'orphaned_fts': 0
        }

        try:
            with self.db_manager.get_connection() as conn:
                # Get all file paths from database
                cursor = conn.execute("SELECT id, path FROM files")
                db_files = cursor.fetchall()

                orphaned_file_ids = []

                for row in db_files:
                    file_id, file_path = row['id'], row['path']
                    stats['files_checked'] += 1

                    # Check if file still exists
                    if not Path(file_path).exists():
                        orphaned_file_ids.append(file_id)
                        logger.debug(f"Found orphaned file: {file_path}")

                if orphaned_file_ids:
                    # Count orphaned entries in related tables before deletion
                    for file_id in orphaned_file_ids:
                        cursor = conn.execute("SELECT COUNT(*) FROM frontmatter WHERE file_id = ?", (file_id,))
                        stats['orphaned_frontmatter'] += cursor.fetchone()[0]

                        cursor = conn.execute("SELECT COUNT(*) FROM tags WHERE file_id = ?", (file_id,))
                        stats['orphaned_tags'] += cursor.fetchone()[0]

                        cursor = conn.execute("SELECT COUNT(*) FROM links WHERE file_id = ?", (file_id,))
                        stats['orphaned_links'] += cursor.fetchone()[0]

                        cursor = conn.execute("SELECT COUNT(*) FROM content_fts WHERE file_id = ?", (file_id,))
                        stats['orphaned_fts'] += cursor.fetchone()[0]

                    # Delete orphaned files (cascading deletes will handle related tables)
                    placeholders = ','.join('?' * len(orphaned_file_ids))
                    conn.execute(f"DELETE FROM files WHERE id IN ({placeholders})", orphaned_file_ids)

                    # Explicitly clean FTS5 table
                    conn.execute(f"DELETE FROM content_fts WHERE file_id IN ({placeholders})", orphaned_file_ids)

                    stats['files_removed'] = len(orphaned_file_ids)
                    conn.commit()

                    logger.info(f"Cleaned up {stats['files_removed']} orphaned files")

                # Additional cleanup: remove any remaining orphaned entries in related tables
                self._cleanup_orphaned_related_data(conn, stats)

                return stats

        except Exception as e:
            raise CacheError(f"Failed to cleanup orphaned entries: {e}") from e

    def get_cache_statistics(self) -> Dict[str, any]:
        """
        Get comprehensive cache statistics.

        Returns:
            Dictionary containing cache size, file counts, and other metrics
        """
        try:
            with self.db_manager.get_connection() as conn:
                stats = {}

                # Basic file statistics
                cursor = conn.execute("SELECT COUNT(*) FROM files")
                stats['total_files'] = cursor.fetchone()[0]

                cursor = conn.execute("SELECT COUNT(*) FROM frontmatter")
                stats['frontmatter_entries'] = cursor.fetchone()[0]

                cursor = conn.execute("SELECT COUNT(*) FROM tags")
                stats['tag_entries'] = cursor.fetchone()[0]

                cursor = conn.execute("SELECT COUNT(*) FROM links")
                stats['link_entries'] = cursor.fetchone()[0]

                cursor = conn.execute("SELECT COUNT(*) FROM content_fts")
                stats['fts_entries'] = cursor.fetchone()[0]

                # Cache metadata
                stats['cache_path'] = str(self.cache_path)
                stats['cache_size_bytes'] = self.cache_path.stat().st_size if self.cache_path.exists() else 0
                stats['cache_age'] = self._get_cache_age()
                stats['last_updated'] = self._get_last_cache_update()

                # Database integrity
                stats['schema_valid'] = self.db_manager.validate_schema()

                return stats

        except Exception as e:
            logger.error(f"Failed to get cache statistics: {e}")
            return {'error': str(e)}

    def get_modified_files_since(self, since_time: datetime) -> List[Tuple[Path, datetime]]:
        """
        Get list of files that have been modified since a given time.

        Args:
            since_time: Datetime to compare against

        Returns:
            List of tuples containing (file_path, modification_time)
        """
        modified_files = []

        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT path, modified_date FROM files WHERE modified_date > ?",
                    (since_time.isoformat(),)
                )

                for row in cursor.fetchall():
                    file_path = Path(row['path'])
                    mod_time = datetime.fromisoformat(row['modified_date'])
                    modified_files.append((file_path, mod_time))

        except Exception as e:
            logger.error(f"Failed to get modified files: {e}")

        return modified_files

    def vacuum_database(self) -> None:
        """
        Vacuum the database to reclaim space and optimize performance.

        Raises:
            CacheError: If vacuum operation fails
        """
        try:
            with self.db_manager.get_connection() as conn:
                # VACUUM cannot be run inside a transaction
                conn.isolation_level = None
                conn.execute("VACUUM")
                conn.isolation_level = ""

            logger.info("Database vacuum completed successfully")

        except Exception as e:
            raise CacheError(f"Failed to vacuum database: {e}") from e

    def _create_cache_metadata_table(self) -> None:
        """Create table for tracking cache metadata."""
        with self.db_manager.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def _update_cache_timestamp(self) -> None:
        """Update the cache timestamp to current time."""
        with self.db_manager.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO cache_metadata (key, value, updated_at)
                VALUES ('last_updated', ?, ?)
            """, (datetime.now().isoformat(), datetime.now().isoformat()))
            conn.commit()

    def _get_cache_age(self) -> Optional[timedelta]:
        """Get the age of the cache."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT value FROM cache_metadata WHERE key = 'last_updated'"
                )
                result = cursor.fetchone()

                if result:
                    last_updated = datetime.fromisoformat(result['value'])
                    return datetime.now() - last_updated

        except Exception as e:
            logger.debug(f"Could not determine cache age: {e}")

        return None

    def _get_last_cache_update(self) -> Optional[datetime]:
        """Get the timestamp of the last cache update."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT value FROM cache_metadata WHERE key = 'last_updated'"
                )
                result = cursor.fetchone()

                if result:
                    return datetime.fromisoformat(result['value'])

        except Exception as e:
            logger.debug(f"Could not get last cache update: {e}")

        return None

    def _check_database_integrity(self) -> bool:
        """Check database integrity using SQLite's integrity_check."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("PRAGMA integrity_check")
                result = cursor.fetchone()
                return result[0] == "ok"

        except Exception as e:
            logger.error(f"Database integrity check failed: {e}")
            return False

    def _cleanup_orphaned_related_data(self, conn: sqlite3.Connection, stats: Dict[str, int]) -> None:
        """Clean up any remaining orphaned entries in related tables."""

        # Clean up frontmatter entries without corresponding files
        cursor = conn.execute("""
            DELETE FROM frontmatter
            WHERE file_id NOT IN (SELECT id FROM files)
        """)
        additional_fm = cursor.rowcount
        if additional_fm > 0:
            stats['orphaned_frontmatter'] += additional_fm
            logger.debug(f"Cleaned up {additional_fm} additional orphaned frontmatter entries")

        # Clean up tag entries without corresponding files
        cursor = conn.execute("""
            DELETE FROM tags
            WHERE file_id NOT IN (SELECT id FROM files)
        """)
        additional_tags = cursor.rowcount
        if additional_tags > 0:
            stats['orphaned_tags'] += additional_tags
            logger.debug(f"Cleaned up {additional_tags} additional orphaned tag entries")

        # Clean up link entries without corresponding files
        cursor = conn.execute("""
            DELETE FROM links
            WHERE file_id NOT IN (SELECT id FROM files)
        """)
        additional_links = cursor.rowcount
        if additional_links > 0:
            stats['orphaned_links'] += additional_links
            logger.debug(f"Cleaned up {additional_links} additional orphaned link entries")

        # Clean up FTS entries without corresponding files
        cursor = conn.execute("""
            DELETE FROM content_fts
            WHERE file_id NOT IN (SELECT id FROM files)
        """)
        additional_fts = cursor.rowcount
        if additional_fts > 0:
            stats['orphaned_fts'] += additional_fts
            logger.debug(f"Cleaned up {additional_fts} additional orphaned FTS entries")

    def close(self) -> None:
        """Close the cache manager and database connections."""
        if self.db_manager:
            self.db_manager.close()
            logger.debug("Cache manager closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()