"""
File indexing engine for scanning and processing markdown files.
"""

import hashlib
import logging
import os
import psutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from .database import DatabaseManager
from .models import FileMetadata, ParsedContent
from .parsers.frontmatter import FrontmatterParser
from .parsers.markdown import MarkdownParser
from .parsers.tags import TagParser
from .parsers.links import LinkParser
from .parsers.obsidian import ObsidianParser
from .cache import CacheManager
from .exceptions import (
    IndexingError, FileAccessError, FileCorruptedError, DirectoryNotFoundError,
    ParsingError, ResourceError, PerformanceError
)
from .logging_config import performance_timer, monitor_performance, log_error

logger = logging.getLogger(__name__)


class Indexer:
    """Main indexing engine for processing markdown files and populating the database."""

    def __init__(self, database_manager: DatabaseManager, cache_manager: Optional[CacheManager] = None):
        """
        Initialize the indexer with database manager and parsers.

        Args:
            database_manager: Database manager instance for database operations
            cache_manager: Optional cache manager for incremental indexing support
        """
        self.db_manager = database_manager
        self.cache_manager = cache_manager

        # Initialize parsers
        self.frontmatter_parser = FrontmatterParser()
        self.markdown_parser = MarkdownParser()
        self.tag_parser = TagParser()
        self.link_parser = LinkParser()
        self.obsidian_parser = ObsidianParser()

        # Supported file extensions
        self.markdown_extensions = {'.md', '.markdown', '.mdown', '.mkd', '.mkdn', '.mdx'}

        # Statistics tracking
        self.stats = {
            'files_processed': 0,
            'files_updated': 0,
            'files_skipped': 0,
            'errors': 0
        }

    @monitor_performance('directory_indexing')
    def index_directory(self, path: Path, recursive: bool = True) -> Dict[str, int]:
        """
        Recursively scan directory and index all markdown files.

        Args:
            path: Directory path to scan
            recursive: Whether to scan subdirectories

        Returns:
            Dictionary with indexing statistics

        Raises:
            DirectoryNotFoundError: If directory doesn't exist or can't be accessed
            ResourceError: If system resources are insufficient
        """
        if not path.exists():
            raise DirectoryNotFoundError(f"Directory does not exist: {path}", file_path=path)

        if not path.is_dir():
            raise DirectoryNotFoundError(f"Path is not a directory: {path}", file_path=path)

        # Check available memory and disk space
        self._check_system_resources()

        logger.info(f"Starting directory indexing: {path} (recursive={recursive})")

        # Reset statistics
        self.stats = {
            'files_processed': 0,
            'files_updated': 0,
            'files_skipped': 0,
            'errors': 0
        }

        try:
            # Scan for markdown files
            with performance_timer('directory_scan', logger):
                markdown_files = self._scan_directory(path, recursive)

            logger.info(f"Found {len(markdown_files)} markdown files to process")

            # Process each file with error handling
            for file_path in markdown_files:
                try:
                    if self._should_index_file(file_path):
                        self.index_file(file_path)
                        self.stats['files_processed'] += 1
                    else:
                        self.stats['files_skipped'] += 1
                        logger.debug(f"Skipped file (no changes): {file_path}")
                except (FileAccessError, FileCorruptedError, ParsingError) as e:
                    self.stats['errors'] += 1
                    log_error(e, logger, {'operation': 'file_indexing', 'file_path': str(file_path)})
                except Exception as e:
                    self.stats['errors'] += 1
                    # Wrap unexpected errors
                    wrapped_error = IndexingError(f"Unexpected error indexing file: {e}", file_path=file_path)
                    log_error(wrapped_error, logger, {'operation': 'file_indexing', 'file_path': str(file_path)})

            logger.info(f"Directory indexing complete. Stats: {self.stats}")
            return self.stats.copy()

        except PerformanceError:
            # Re-raise performance errors
            raise
        except Exception as e:
            # Wrap any other unexpected errors
            wrapped_error = IndexingError(f"Directory indexing failed: {e}", context={'directory': str(path)})
            log_error(wrapped_error, logger)
            raise wrapped_error from e

    @monitor_performance('file_indexing')
    def index_file(self, file_path: Path) -> bool:
        """
        Index a single markdown file.

        Args:
            file_path: Path to the markdown file to index

        Returns:
            True if file was indexed successfully, False otherwise

        Raises:
            FileAccessError: If file doesn't exist or can't be accessed
            FileCorruptedError: If file is corrupted or can't be processed
            ParsingError: If file parsing fails
        """
        if not file_path.exists():
            raise FileAccessError(f"File does not exist: {file_path}", file_path=file_path)

        if not file_path.is_file():
            raise FileAccessError(f"Path is not a file: {file_path}", file_path=file_path)

        if file_path.suffix.lower() not in self.markdown_extensions:
            raise FileAccessError(f"File is not a markdown file: {file_path}", file_path=file_path)

        logger.debug(f"Indexing file: {file_path}")

        try:
            # Extract file metadata with error handling
            try:
                file_metadata = self._extract_file_metadata(file_path)
            except (OSError, PermissionError) as e:
                raise FileAccessError(f"Cannot access file metadata: {e}", file_path=file_path) from e

            # Read and parse file content with error handling
            try:
                content = self._read_file_content(file_path)
            except (OSError, PermissionError) as e:
                raise FileAccessError(f"Cannot read file content: {e}", file_path=file_path) from e
            except UnicodeDecodeError as e:
                raise FileCorruptedError(f"Cannot decode file content: {e}", file_path=file_path) from e

            try:
                parsed_content = self._parse_content(content, file_path)
            except Exception as e:
                raise ParsingError(f"Failed to parse file content: {e}", file_path=file_path) from e

            # Store in database with error handling
            try:
                self._store_file_data(file_metadata, parsed_content)
            except Exception as e:
                raise IndexingError(f"Failed to store file data: {e}", file_path=file_path) from e

            logger.debug(f"Successfully indexed: {file_path}")
            return True

        except (FileAccessError, FileCorruptedError, ParsingError, IndexingError):
            # Re-raise known errors
            raise
        except Exception as e:
            # Wrap unexpected errors
            raise IndexingError(f"Unexpected error indexing file: {e}", file_path=file_path) from e

    def update_index(self, file_path: Path) -> bool:
        """
        Update index for a single file (same as index_file for now).

        Args:
            file_path: Path to the markdown file to update

        Returns:
            True if file was updated successfully, False otherwise
        """
        return self.index_file(file_path)

    def rebuild_index(self, directory: Path) -> Dict[str, int]:
        """
        Rebuild the entire index for a directory.

        Args:
            directory: Directory to rebuild index for

        Returns:
            Dictionary with rebuild statistics
        """
        logger.info(f"Rebuilding index for directory: {directory}")

        # Clear existing data for this directory
        self._clear_directory_data(directory)

        # Reindex everything
        return self.index_directory(directory, recursive=True)

    def _scan_directory(self, path: Path, recursive: bool) -> List[Path]:
        """
        Scan directory for markdown files with comprehensive error handling.

        Args:
            path: Directory to scan
            recursive: Whether to scan subdirectories

        Returns:
            List of markdown file paths

        Raises:
            DirectoryNotFoundError: If directory cannot be accessed
        """
        markdown_files = []
        errors_encountered = []

        try:
            if recursive:
                # Use rglob for recursive scanning
                for ext in self.markdown_extensions:
                    pattern = f"**/*{ext}"
                    try:
                        markdown_files.extend(path.rglob(pattern))
                    except PermissionError as e:
                        error_msg = f"Permission denied accessing files with pattern {pattern}: {e}"
                        errors_encountered.append(error_msg)
                        logger.warning(error_msg)
                    except OSError as e:
                        error_msg = f"OS error scanning for pattern {pattern}: {e}"
                        errors_encountered.append(error_msg)
                        logger.warning(error_msg)
            else:
                # Use glob for non-recursive scanning
                for ext in self.markdown_extensions:
                    pattern = f"*{ext}"
                    try:
                        markdown_files.extend(path.glob(pattern))
                    except PermissionError as e:
                        error_msg = f"Permission denied accessing files with pattern {pattern}: {e}"
                        errors_encountered.append(error_msg)
                        logger.warning(error_msg)
                    except OSError as e:
                        error_msg = f"OS error scanning for pattern {pattern}: {e}"
                        errors_encountered.append(error_msg)
                        logger.warning(error_msg)

        except PermissionError as e:
            raise DirectoryNotFoundError(f"Permission denied accessing directory {path}: {e}", file_path=path) from e
        except OSError as e:
            raise DirectoryNotFoundError(f"OS error accessing directory {path}: {e}", file_path=path) from e
        except Exception as e:
            raise DirectoryNotFoundError(f"Unexpected error scanning directory {path}: {e}", file_path=path) from e

        # Filter out non-files with error handling
        valid_files = []
        for file_path in markdown_files:
            try:
                if file_path.is_file():
                    valid_files.append(file_path)
            except (OSError, PermissionError) as e:
                logger.warning(f"Cannot access file {file_path}: {e}")
                continue

        valid_files.sort()

        if errors_encountered:
            logger.info(f"Directory scan completed with {len(errors_encountered)} access errors")

        return valid_files

    def _should_index_file(self, file_path: Path) -> bool:
        """
        Check if a file should be indexed based on modification time and content hash.

        Args:
            file_path: Path to check

        Returns:
            True if file should be indexed, False if it's up to date
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT modified_date, content_hash FROM files WHERE path = ?",
                    (str(file_path),)
                )
                result = cursor.fetchone()

                if not result:
                    # File not in database, should index
                    return True

                # Check modification time
                db_modified = datetime.fromisoformat(result['modified_date'])
                file_modified = datetime.fromtimestamp(file_path.stat().st_mtime)

                if file_modified > db_modified:
                    # File has been modified, should index
                    return True

                # Check content hash as additional verification
                current_hash = self._calculate_content_hash(file_path)
                if current_hash != result['content_hash']:
                    # Content has changed, should index
                    return True

                # File is up to date
                return False

        except Exception as e:
            logger.warning(f"Error checking file status {file_path}: {e}")
            # If we can't determine status, err on the side of indexing
            return True

    def _extract_file_metadata(self, file_path: Path) -> FileMetadata:
        """
        Extract file system metadata.

        Args:
            file_path: Path to extract metadata from

        Returns:
            FileMetadata object
        """
        stat = file_path.stat()

        return FileMetadata(
            path=file_path,
            filename=file_path.name,
            directory=str(file_path.parent),
            modified_date=datetime.fromtimestamp(stat.st_mtime),
            created_date=datetime.fromtimestamp(stat.st_ctime) if hasattr(stat, 'st_birthtime') else None,
            file_size=stat.st_size,
            content_hash=self._calculate_content_hash(file_path)
        )

    def _calculate_content_hash(self, file_path: Path) -> str:
        """
        Calculate SHA-256 hash of file content.

        Args:
            file_path: Path to file

        Returns:
            Hexadecimal hash string
        """
        hasher = hashlib.sha256()

        try:
            with open(file_path, 'rb') as f:
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            # Return a hash of the file path as fallback
            hasher.update(str(file_path).encode('utf-8'))

        return hasher.hexdigest()

    def _check_system_resources(self) -> None:
        """
        Check system resources before starting intensive operations.

        Raises:
            ResourceError: If system resources are insufficient
        """
        try:
            # Check available memory (require at least 100MB)
            memory = psutil.virtual_memory()
            if memory.available < 100 * 1024 * 1024:  # 100MB
                raise ResourceError(
                    f"Insufficient memory: {memory.available / 1024 / 1024:.1f}MB available, need at least 100MB",
                    resource_type="memory"
                )

            # Check disk space (require at least 50MB)
            disk = psutil.disk_usage('/')
            if disk.free < 50 * 1024 * 1024:  # 50MB
                raise ResourceError(
                    f"Insufficient disk space: {disk.free / 1024 / 1024:.1f}MB available, need at least 50MB",
                    resource_type="disk"
                )

        except psutil.Error as e:
            logger.warning(f"Could not check system resources: {e}")
            # Don't fail if we can't check resources

    def _read_file_content(self, file_path: Path) -> str:
        """
        Read file content with encoding detection and error handling.

        Args:
            file_path: Path to file

        Returns:
            File content as string

        Raises:
            FileAccessError: If file cannot be accessed
            FileCorruptedError: If file cannot be decoded
        """
        # Check file size (warn if > 10MB)
        try:
            file_size = file_path.stat().st_size
            if file_size > 10 * 1024 * 1024:  # 10MB
                logger.warning(f"Large file detected: {file_path} ({file_size / 1024 / 1024:.1f}MB)")
        except OSError as e:
            raise FileAccessError(f"Cannot access file stats: {e}", file_path=file_path) from e

        # Try UTF-8 first, then fall back to latin-1
        encodings = ['utf-8', 'utf-8-sig', 'latin-1']
        last_error = None

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                logger.debug(f"Successfully read {file_path} with {encoding} encoding")
                return content
            except UnicodeDecodeError as e:
                last_error = e
                continue
            except (OSError, PermissionError) as e:
                raise FileAccessError(f"Cannot read file: {e}", file_path=file_path) from e
            except Exception as e:
                raise FileAccessError(f"Unexpected error reading file: {e}", file_path=file_path) from e

        # If we get here, all encodings failed
        raise FileCorruptedError(
            f"Cannot decode file with any supported encoding (tried: {', '.join(encodings)}): {last_error}",
            file_path=file_path
        ) from last_error

    def _parse_content(self, content: str, file_path: Optional[Path] = None) -> ParsedContent:
        """
        Parse markdown content using all parsers including Obsidian-specific features.

        Args:
            content: Raw markdown content
            file_path: Optional file path for Obsidian context

        Returns:
            ParsedContent object with all parsed data including Obsidian features
        """
        # Parse frontmatter first
        frontmatter = self.frontmatter_parser.parse(content)

        # Get content without frontmatter
        content_without_fm = self.frontmatter_parser.get_content_without_frontmatter(content)

        # Sanitize content for parsing (handle templates, etc.)
        sanitized_content = self.obsidian_parser.sanitize_content_for_parsing(content_without_fm)

        # Parse markdown content
        parsed_md = self.markdown_parser.parse(sanitized_content)

        # Extract tags from both frontmatter and content (enhanced for Obsidian)
        all_tags = self.tag_parser.parse_all_tags(frontmatter, content_without_fm)
        obsidian_tags = self.obsidian_parser.parse_obsidian_tags(content_without_fm)

        # Extract links (both standard and Obsidian)
        standard_links = self.link_parser.parse(content_without_fm)
        enhanced_links = self.obsidian_parser.extract_enhanced_links(content_without_fm)

        # Parse Obsidian-specific features
        obsidian_features = self.obsidian_parser.parse_obsidian_features(content_without_fm, file_path)

        # Get title from frontmatter or first heading
        title = None
        if frontmatter:
            # Look for title in frontmatter
            for key, value_data in frontmatter.items():
                if key.lower() == 'title':
                    if isinstance(value_data, dict) and 'value' in value_data:
                        title = str(value_data['value'])
                    else:
                        title = str(value_data)
                    break

        # If no title in frontmatter, use first heading
        if not title and parsed_md.headings:
            title = parsed_md.headings[0].text

        # Combine tags from all sources
        all_tag_list = []
        all_tag_list.extend(all_tags.get('frontmatter', []))
        all_tag_list.extend(all_tags.get('content', []))
        all_tag_list.extend(obsidian_tags)

        # Combine links from all sources
        all_links = standard_links + enhanced_links

        return ParsedContent(
            frontmatter=frontmatter,
            content=parsed_md.sanitized_content,
            title=title,
            headings=[h.text for h in parsed_md.headings],
            tags=list(set(all_tag_list)),  # Remove duplicates
            links=all_links,
            obsidian_features=obsidian_features
        )

    def _store_file_data(self, file_metadata: FileMetadata, parsed_content: ParsedContent) -> None:
        """
        Store file data and parsed content in database.

        Args:
            file_metadata: File metadata
            parsed_content: Parsed content data
        """
        with self.db_manager.get_connection() as conn:
            # Update file metadata (including word count and heading count)
            file_metadata.word_count = len(parsed_content.content.split()) if parsed_content.content else 0
            file_metadata.heading_count = len(parsed_content.headings)

            # Insert or replace file record
            cursor = conn.execute("""
                INSERT OR REPLACE INTO files
                (path, filename, directory, modified_date, created_date, file_size,
                 content_hash, word_count, heading_count, indexed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(file_metadata.path),
                file_metadata.filename,
                file_metadata.directory,
                file_metadata.modified_date.isoformat(),
                file_metadata.created_date.isoformat() if file_metadata.created_date else None,
                file_metadata.file_size,
                file_metadata.content_hash,
                file_metadata.word_count,
                file_metadata.heading_count,
                datetime.now().isoformat()
            ))

            file_id = cursor.lastrowid

            # If this was an update, get the existing file_id
            if cursor.rowcount == 0:
                cursor = conn.execute("SELECT id FROM files WHERE path = ?", (str(file_metadata.path),))
                result = cursor.fetchone()
                if result:
                    file_id = result['id']

            # Clear existing related data
            conn.execute("DELETE FROM frontmatter WHERE file_id = ?", (file_id,))
            conn.execute("DELETE FROM tags WHERE file_id = ?", (file_id,))
            conn.execute("DELETE FROM links WHERE file_id = ?", (file_id,))
            conn.execute("DELETE FROM content_fts WHERE file_id = ?", (file_id,))

            # Clear Obsidian-specific data
            self._clear_obsidian_data(conn, file_id)

            # Insert frontmatter data
            for key, value_data in parsed_content.frontmatter.items():
                if isinstance(value_data, dict) and 'value' in value_data:
                    value = str(value_data['value']) if value_data['value'] is not None else None
                    value_type = value_data.get('type', 'string')
                else:
                    value = str(value_data) if value_data is not None else None
                    value_type = 'string'

                conn.execute("""
                    INSERT INTO frontmatter (file_id, key, value, value_type)
                    VALUES (?, ?, ?, ?)
                """, (file_id, key, value, value_type))

            # Insert tags
            # Re-parse to get source information, but also include any tags from parsed_content
            tag_sources = self.tag_parser.parse_all_tags(parsed_content.frontmatter, parsed_content.content)

            # Keep track of inserted tags to avoid duplicates
            inserted_tags = set()

            for tag in tag_sources.get('frontmatter', []):
                if tag not in inserted_tags:
                    conn.execute("""
                        INSERT INTO tags (file_id, tag, source)
                        VALUES (?, ?, ?)
                    """, (file_id, tag, 'frontmatter'))
                    inserted_tags.add(tag)

            for tag in tag_sources.get('content', []):
                if tag not in inserted_tags:
                    conn.execute("""
                        INSERT INTO tags (file_id, tag, source)
                        VALUES (?, ?, ?)
                    """, (file_id, tag, 'content'))
                    inserted_tags.add(tag)

            # Also insert any tags that were directly provided in parsed_content.tags
            # but not found by the parser (in case they were manually added)
            for tag in parsed_content.tags:
                if tag not in inserted_tags:
                    conn.execute("""
                        INSERT INTO tags (file_id, tag, source)
                        VALUES (?, ?, ?)
                    """, (file_id, tag, 'unknown'))
                    inserted_tags.add(tag)

            # Insert links
            for link in parsed_content.links:
                conn.execute("""
                    INSERT INTO links (file_id, link_text, link_target, link_type, is_internal)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    file_id,
                    link.get('link_text'),
                    link['link_target'],
                    link['link_type'],
                    link['is_internal']
                ))

            # Insert Obsidian-specific data
            self._store_obsidian_data(conn, file_id, parsed_content.obsidian_features)

            # Insert FTS5 content
            headings_text = ' '.join(parsed_content.headings) if parsed_content.headings else ''
            conn.execute("""
                INSERT INTO content_fts (file_id, title, content, headings)
                VALUES (?, ?, ?, ?)
            """, (
                file_id,
                parsed_content.title or '',
                parsed_content.content or '',
                headings_text
            ))

            conn.commit()

    def _clear_directory_data(self, directory: Path) -> None:
        """
        Clear all data for files in a directory.

        Args:
            directory: Directory to clear data for
        """
        with self.db_manager.get_connection() as conn:
            # Delete files and related data (cascading deletes will handle related tables)
            conn.execute(
                "DELETE FROM files WHERE directory = ? OR directory LIKE ?",
                (str(directory), f"{directory}%")
            )
            conn.commit()

    def get_indexing_stats(self) -> Dict[str, int]:
        """
        Get current indexing statistics.

        Returns:
            Dictionary with statistics
        """
        return self.stats.copy()

    def get_file_count(self) -> int:
        """
        Get total number of indexed files.

        Returns:
            Number of files in database
        """
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM files")
            return cursor.fetchone()[0]

    def incremental_index_directory(self, path: Path, recursive: bool = True) -> Dict[str, int]:
        """
        Perform incremental indexing of a directory, only processing modified files.

        Args:
            path: Directory path to scan
            recursive: Whether to scan subdirectories

        Returns:
            Dictionary with indexing statistics

        Raises:
            IndexingError: If directory doesn't exist or can't be accessed
        """
        if not path.exists():
            raise IndexingError(f"Directory does not exist: {path}")

        if not path.is_dir():
            raise IndexingError(f"Path is not a directory: {path}")

        logger.info(f"Starting incremental directory indexing: {path} (recursive={recursive})")

        # Reset statistics
        self.stats = {
            'files_processed': 0,
            'files_updated': 0,
            'files_skipped': 0,
            'errors': 0
        }

        # Clean up orphaned entries first if cache manager is available
        if self.cache_manager:
            cleanup_stats = self.cache_manager.cleanup_orphaned_entries()
            logger.info(f"Cleanup completed: {cleanup_stats}")

        # Scan for markdown files
        markdown_files = self._scan_directory(path, recursive)
        logger.info(f"Found {len(markdown_files)} markdown files to process")

        # Process each file, but only if it needs updating
        for file_path in markdown_files:
            try:
                if self._should_index_file(file_path):
                    self.index_file(file_path)
                    self.stats['files_updated'] += 1
                else:
                    self.stats['files_skipped'] += 1
                    logger.debug(f"Skipped file (no changes): {file_path}")

                self.stats['files_processed'] += 1

            except Exception as e:
                self.stats['errors'] += 1
                logger.error(f"Error indexing file {file_path}: {e}")

        # Update cache timestamp if cache manager is available
        if self.cache_manager:
            self.cache_manager._update_cache_timestamp()

        logger.info(f"Incremental directory indexing complete. Stats: {self.stats}")
        return self.stats.copy()

    def remove_file_from_index(self, file_path: Path) -> bool:
        """
        Remove a file from the index.

        Args:
            file_path: Path to file to remove from index

        Returns:
            True if file was removed, False if file was not in index
        """
        try:
            if self.cache_manager:
                self.cache_manager.invalidate_file(file_path)
                return True
            else:
                # Fallback to direct database removal
                with self.db_manager.get_connection() as conn:
                    cursor = conn.execute("SELECT id FROM files WHERE path = ?", (str(file_path),))
                    result = cursor.fetchone()

                    if result:
                        file_id = result['id']
                        conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
                        conn.execute("DELETE FROM content_fts WHERE file_id = ?", (file_id,))
                        conn.commit()
                        logger.debug(f"Removed file from index: {file_path}")
                        return True
                    else:
                        logger.debug(f"File not found in index: {file_path}")
                        return False

        except Exception as e:
            logger.error(f"Error removing file from index {file_path}: {e}")
            return False

    def get_indexed_files_in_directory(self, directory: Path) -> List[Path]:
        """
        Get list of all files currently indexed in a directory.

        Args:
            directory: Directory to check

        Returns:
            List of file paths currently in the index
        """
        indexed_files = []

        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT path FROM files WHERE directory = ? OR directory LIKE ?",
                    (str(directory), f"{directory}%")
                )

                for row in cursor.fetchall():
                    indexed_files.append(Path(row['path']))

        except Exception as e:
            logger.error(f"Error getting indexed files for directory {directory}: {e}")

        return indexed_files

    def sync_directory_index(self, directory: Path, recursive: bool = True) -> Dict[str, int]:
        """
        Synchronize the index with the current state of a directory.

        This method:
        1. Removes files from index that no longer exist on disk
        2. Adds/updates files that are new or modified
        3. Provides comprehensive sync statistics

        Args:
            directory: Directory to synchronize
            recursive: Whether to sync subdirectories

        Returns:
            Dictionary with sync statistics
        """
        logger.info(f"Starting directory sync: {directory} (recursive={recursive})")

        sync_stats = {
            'files_added': 0,
            'files_updated': 0,
            'files_removed': 0,
            'files_unchanged': 0,
            'errors': 0
        }

        try:
            # Get currently indexed files in this directory
            indexed_files = set(self.get_indexed_files_in_directory(directory))

            # Get current files on disk
            current_files = set(self._scan_directory(directory, recursive))

            # Files to remove (in index but not on disk)
            files_to_remove = indexed_files - current_files
            for file_path in files_to_remove:
                if self.remove_file_from_index(file_path):
                    sync_stats['files_removed'] += 1
                    logger.debug(f"Removed deleted file from index: {file_path}")

            # Files to check for updates (on disk)
            for file_path in current_files:
                try:
                    if file_path in indexed_files:
                        # File exists in index, check if it needs updating
                        if self._should_index_file(file_path):
                            self.index_file(file_path)
                            sync_stats['files_updated'] += 1
                            logger.debug(f"Updated modified file: {file_path}")
                        else:
                            sync_stats['files_unchanged'] += 1
                    else:
                        # New file, add to index
                        self.index_file(file_path)
                        sync_stats['files_added'] += 1
                        logger.debug(f"Added new file to index: {file_path}")

                except Exception as e:
                    sync_stats['errors'] += 1
                    logger.error(f"Error syncing file {file_path}: {e}")

            # Update cache timestamp if cache manager is available
            if self.cache_manager:
                self.cache_manager._update_cache_timestamp()

            logger.info(f"Directory sync complete. Stats: {sync_stats}")
            return sync_stats

        except Exception as e:
            logger.error(f"Error during directory sync: {e}")
            sync_stats['errors'] += 1
            return sync_stats    def
_clear_obsidian_data(self, conn, file_id: int) -> None:
        """Clear all Obsidian-specific data for a file."""
        obsidian_tables = [
            'obsidian_links',
            'obsidian_embeds',
            'obsidian_templates',
            'obsidian_callouts',
            'obsidian_blocks',
            'obsidian_dataview',
            'obsidian_graph'
        ]

        for table in obsidian_tables:
            try:
                conn.execute(f"DELETE FROM {table} WHERE file_id = ?", (file_id,))
            except Exception as e:
                # Table might not exist in older schema versions
                logger.debug(f"Could not clear {table}: {e}")

    def _store_obsidian_data(self, conn, file_id: int, obsidian_features: Dict[str, Any]) -> None:
        """Store Obsidian-specific features in the database."""
        if not obsidian_features:
            return

        try:
            # Store wikilinks
            wikilinks = obsidian_features.get('wikilinks', [])
            for link in wikilinks:
                conn.execute("""
                    INSERT INTO obsidian_links
                    (file_id, link_text, link_target, obsidian_type, section, block_id, has_alias)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    file_id,
                    link.get('link_text'),
                    link.get('link_target'),
                    link.get('obsidian_type', 'page'),
                    link.get('section'),
                    link.get('block_id'),
                    link.get('has_alias', False)
                ))

            # Store embeds
            embeds = obsidian_features.get('embeds', [])
            for embed in embeds:
                conn.execute("""
                    INSERT INTO obsidian_embeds
                    (file_id, embed_target, embed_alias, embed_type)
                    VALUES (?, ?, ?, ?)
                """, (
                    file_id,
                    embed.get('embed_target'),
                    embed.get('embed_alias'),
                    embed.get('embed_type', 'page')
                ))

            # Store templates
            templates = obsidian_features.get('templates', [])
            for template in templates:
                conn.execute("""
                    INSERT INTO obsidian_templates
                    (file_id, template_name, template_arg, start_pos, end_pos)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    file_id,
                    template.get('template_name'),
                    template.get('template_arg'),
                    template.get('start_pos', 0),
                    template.get('end_pos', 0)
                ))

            # Store callouts
            callouts = obsidian_features.get('callouts', [])
            for callout in callouts:
                conn.execute("""
                    INSERT INTO obsidian_callouts
                    (file_id, callout_type, callout_title, line_number)
                    VALUES (?, ?, ?, ?)
                """, (
                    file_id,
                    callout.get('callout_type'),
                    callout.get('callout_title'),
                    callout.get('line_number', 0)
                ))

            # Store block references
            block_refs = obsidian_features.get('block_references', [])
            for block_ref in block_refs:
                conn.execute("""
                    INSERT INTO obsidian_blocks
                    (file_id, block_id, line_number)
                    VALUES (?, ?, ?)
                """, (
                    file_id,
                    block_ref.get('block_id'),
                    block_ref.get('line_number', 0)
                ))

            # Store dataview queries
            dataview_queries = obsidian_features.get('dataview_queries', [])
            for query in dataview_queries:
                conn.execute("""
                    INSERT INTO obsidian_dataview
                    (file_id, query_content, line_number, start_pos, end_pos)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    file_id,
                    query.get('query_content'),
                    query.get('line_number', 0),
                    query.get('start_pos', 0),
                    query.get('end_pos', 0)
                ))

            # Store graph connections
            graph_connections = obsidian_features.get('graph_connections', {})
            if isinstance(graph_connections, dict):
                outgoing_links = graph_connections.get('outgoing_links', [])
                connection_strength = graph_connections.get('connection_strength', {})

                for target in outgoing_links:
                    strength = connection_strength.get(target, 1)
                    conn.execute("""
                        INSERT INTO obsidian_graph
                        (source_file_id, target_name, connection_type, connection_strength)
                        VALUES (?, ?, ?, ?)
                    """, (
                        file_id,
                        target,
                        'wikilink',
                        strength
                    ))

                # Store embeds as stronger connections
                embeds_list = graph_connections.get('embeds', [])
                for target in embeds_list:
                    strength = connection_strength.get(target, 2)
                    conn.execute("""
                        INSERT INTO obsidian_graph
                        (source_file_id, target_name, connection_type, connection_strength)
                        VALUES (?, ?, ?, ?)
                    """, (
                        file_id,
                        target,
                        'embed',
                        strength
                    ))

        except Exception as e:
            logger.warning(f"Error storing Obsidian data: {e}")
            # Don't fail the entire indexing process for Obsidian features