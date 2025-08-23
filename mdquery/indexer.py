"""
File indexing engine for scanning and processing markdown files.
"""

import hashlib
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from .database import DatabaseManager
from .models import FileMetadata, ParsedContent
from .parsers.frontmatter import FrontmatterParser
from .parsers.markdown import MarkdownParser
from .parsers.tags import TagParser
from .parsers.links import LinkParser

logger = logging.getLogger(__name__)


class IndexingError(Exception):
    """Custom exception for indexing-related errors."""
    pass


class Indexer:
    """Main indexing engine for processing markdown files and populating the database."""

    def __init__(self, database_manager: DatabaseManager):
        """
        Initialize the indexer with database manager and parsers.

        Args:
            database_manager: Database manager instance for database operations
        """
        self.db_manager = database_manager

        # Initialize parsers
        self.frontmatter_parser = FrontmatterParser()
        self.markdown_parser = MarkdownParser()
        self.tag_parser = TagParser()
        self.link_parser = LinkParser()

        # Supported file extensions
        self.markdown_extensions = {'.md', '.markdown', '.mdown', '.mkd', '.mkdn', '.mdx'}

        # Statistics tracking
        self.stats = {
            'files_processed': 0,
            'files_updated': 0,
            'files_skipped': 0,
            'errors': 0
        }

    def index_directory(self, path: Path, recursive: bool = True) -> Dict[str, int]:
        """
        Recursively scan directory and index all markdown files.

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

        logger.info(f"Starting directory indexing: {path} (recursive={recursive})")

        # Reset statistics
        self.stats = {
            'files_processed': 0,
            'files_updated': 0,
            'files_skipped': 0,
            'errors': 0
        }

        # Scan for markdown files
        markdown_files = self._scan_directory(path, recursive)
        logger.info(f"Found {len(markdown_files)} markdown files to process")

        # Process each file
        for file_path in markdown_files:
            try:
                if self._should_index_file(file_path):
                    self.index_file(file_path)
                    self.stats['files_processed'] += 1
                else:
                    self.stats['files_skipped'] += 1
                    logger.debug(f"Skipped file (no changes): {file_path}")
            except Exception as e:
                self.stats['errors'] += 1
                logger.error(f"Error indexing file {file_path}: {e}")

        logger.info(f"Directory indexing complete. Stats: {self.stats}")
        return self.stats.copy()

    def index_file(self, file_path: Path) -> bool:
        """
        Index a single markdown file.

        Args:
            file_path: Path to the markdown file to index

        Returns:
            True if file was indexed successfully, False otherwise

        Raises:
            IndexingError: If file doesn't exist or can't be processed
        """
        if not file_path.exists():
            raise IndexingError(f"File does not exist: {file_path}")

        if not file_path.is_file():
            raise IndexingError(f"Path is not a file: {file_path}")

        if file_path.suffix.lower() not in self.markdown_extensions:
            raise IndexingError(f"File is not a markdown file: {file_path}")

        logger.debug(f"Indexing file: {file_path}")

        try:
            # Extract file metadata
            file_metadata = self._extract_file_metadata(file_path)

            # Read and parse file content
            content = self._read_file_content(file_path)
            parsed_content = self._parse_content(content)

            # Store in database
            self._store_file_data(file_metadata, parsed_content)

            logger.debug(f"Successfully indexed: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to index file {file_path}: {e}")
            raise IndexingError(f"Failed to index file {file_path}: {e}") from e

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
        Scan directory for markdown files.

        Args:
            path: Directory to scan
            recursive: Whether to scan subdirectories

        Returns:
            List of markdown file paths
        """
        markdown_files = []

        try:
            if recursive:
                # Use rglob for recursive scanning
                for ext in self.markdown_extensions:
                    pattern = f"**/*{ext}"
                    markdown_files.extend(path.rglob(pattern))
            else:
                # Use glob for non-recursive scanning
                for ext in self.markdown_extensions:
                    pattern = f"*{ext}"
                    markdown_files.extend(path.glob(pattern))

        except PermissionError as e:
            logger.warning(f"Permission denied accessing directory {path}: {e}")
        except Exception as e:
            logger.error(f"Error scanning directory {path}: {e}")

        # Filter out non-files and sort
        markdown_files = [f for f in markdown_files if f.is_file()]
        markdown_files.sort()

        return markdown_files

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

    def _read_file_content(self, file_path: Path) -> str:
        """
        Read file content with encoding detection.

        Args:
            file_path: Path to file

        Returns:
            File content as string
        """
        # Try UTF-8 first, then fall back to latin-1
        encodings = ['utf-8', 'utf-8-sig', 'latin-1']

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                logger.debug(f"Successfully read {file_path} with {encoding} encoding")
                return content
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.error(f"Error reading file {file_path}: {e}")
                raise IndexingError(f"Cannot read file {file_path}: {e}")

        raise IndexingError(f"Cannot decode file {file_path} with any supported encoding")

    def _parse_content(self, content: str) -> ParsedContent:
        """
        Parse markdown content using all parsers.

        Args:
            content: Raw markdown content

        Returns:
            ParsedContent object with all parsed data
        """
        # Parse frontmatter first
        frontmatter = self.frontmatter_parser.parse(content)

        # Get content without frontmatter
        content_without_fm = self.frontmatter_parser.get_content_without_frontmatter(content)

        # Parse markdown content
        parsed_md = self.markdown_parser.parse(content_without_fm)

        # Extract tags from both frontmatter and content
        all_tags = self.tag_parser.parse_all_tags(frontmatter, content_without_fm)

        # Extract links
        links = self.link_parser.parse(content_without_fm)

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

        return ParsedContent(
            frontmatter=frontmatter,
            content=parsed_md.sanitized_content,
            title=title,
            headings=[h.text for h in parsed_md.headings],
            tags=list(set(all_tag_list)),  # Remove duplicates
            links=links
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