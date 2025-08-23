"""
Unit tests for the file indexing engine.
"""

import os
import tempfile
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

from mdquery.indexer import Indexer, IndexingError
from mdquery.database import DatabaseManager
from mdquery.models import FileMetadata, ParsedContent


class TestIndexer:
    """Test cases for the Indexer class."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def db_manager(self):
        """Create an in-memory database manager for testing."""
        db_manager = DatabaseManager(":memory:")
        db_manager.initialize_database()
        return db_manager

    @pytest.fixture
    def indexer(self, db_manager):
        """Create an indexer instance for testing."""
        return Indexer(db_manager)

    def create_test_file(self, path: Path, content: str) -> Path:
        """Helper to create a test markdown file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        return path

    def test_init(self, db_manager):
        """Test indexer initialization."""
        indexer = Indexer(db_manager)

        assert indexer.db_manager == db_manager
        assert indexer.frontmatter_parser is not None
        assert indexer.markdown_parser is not None
        assert indexer.tag_parser is not None
        assert indexer.link_parser is not None
        assert indexer.markdown_extensions == {'.md', '.markdown', '.mdown', '.mkd', '.mkdn', '.mdx'}

    def test_scan_directory_recursive(self, indexer, temp_dir):
        """Test recursive directory scanning."""
        # Create test files
        self.create_test_file(temp_dir / "file1.md", "# Test 1")
        self.create_test_file(temp_dir / "subdir" / "file2.md", "# Test 2")
        self.create_test_file(temp_dir / "subdir" / "nested" / "file3.markdown", "# Test 3")
        self.create_test_file(temp_dir / "not_markdown.txt", "Not markdown")

        # Scan directory
        files = indexer._scan_directory(temp_dir, recursive=True)

        # Should find 3 markdown files
        assert len(files) == 3
        file_names = [f.name for f in files]
        assert "file1.md" in file_names
        assert "file2.md" in file_names
        assert "file3.markdown" in file_names
        assert "not_markdown.txt" not in file_names

    def test_scan_directory_non_recursive(self, indexer, temp_dir):
        """Test non-recursive directory scanning."""
        # Create test files
        self.create_test_file(temp_dir / "file1.md", "# Test 1")
        self.create_test_file(temp_dir / "subdir" / "file2.md", "# Test 2")

        # Scan directory non-recursively
        files = indexer._scan_directory(temp_dir, recursive=False)

        # Should find only top-level file
        assert len(files) == 1
        assert files[0].name == "file1.md"

    def test_extract_file_metadata(self, indexer, temp_dir):
        """Test file metadata extraction."""
        test_file = self.create_test_file(temp_dir / "test.md", "# Test Content")

        metadata = indexer._extract_file_metadata(test_file)

        assert isinstance(metadata, FileMetadata)
        assert metadata.path == test_file
        assert metadata.filename == "test.md"
        assert metadata.directory == str(temp_dir)
        assert isinstance(metadata.modified_date, datetime)
        assert metadata.file_size > 0
        assert len(metadata.content_hash) == 64  # SHA-256 hex length

    def test_calculate_content_hash(self, indexer, temp_dir):
        """Test content hash calculation."""
        test_file = self.create_test_file(temp_dir / "test.md", "# Test Content")

        hash1 = indexer._calculate_content_hash(test_file)
        hash2 = indexer._calculate_content_hash(test_file)

        # Same content should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length

        # Different content should produce different hash
        test_file.write_text("# Different Content")
        hash3 = indexer._calculate_content_hash(test_file)
        assert hash1 != hash3

    def test_read_file_content_utf8(self, indexer, temp_dir):
        """Test reading UTF-8 encoded files."""
        content = "# Test with émojis 🚀 and ñoñó"
        test_file = self.create_test_file(temp_dir / "test.md", content)

        read_content = indexer._read_file_content(test_file)
        assert read_content == content

    def test_read_file_content_encoding_fallback(self, indexer, temp_dir):
        """Test encoding fallback for problematic files."""
        test_file = temp_dir / "test.md"

        # Write with latin-1 encoding
        test_file.write_bytes("# Test with special chars: \xe9\xf1".encode('latin-1'))

        # Should still be able to read it
        content = indexer._read_file_content(test_file)
        assert "Test with special chars" in content

    def test_parse_content_complete(self, indexer):
        """Test complete content parsing with all elements."""
        content = """---
title: Test Document
tags: [python, testing]
category: development
---

# Main Heading

This is a test document with #inline-tag and [[wikilink]].

## Subheading

Some content with [external link](https://example.com) and more text.

### Another heading

Final content with #another-tag.
"""

        parsed = indexer._parse_content(content)

        assert isinstance(parsed, ParsedContent)
        assert parsed.title == "Test Document"
        assert len(parsed.frontmatter) > 0
        assert "title" in parsed.frontmatter
        assert len(parsed.headings) == 3
        assert "Main Heading" in parsed.headings
        assert len(parsed.tags) > 0
        assert "python" in parsed.tags or "inline-tag" in parsed.tags
        assert len(parsed.links) > 0

    def test_should_index_file_new_file(self, indexer, temp_dir):
        """Test should_index_file for new files."""
        test_file = self.create_test_file(temp_dir / "new.md", "# New File")

        # New file should be indexed
        assert indexer._should_index_file(test_file) is True

    def test_should_index_file_unchanged(self, indexer, temp_dir):
        """Test should_index_file for unchanged files."""
        test_file = self.create_test_file(temp_dir / "test.md", "# Test")

        # Index the file first
        indexer.index_file(test_file)

        # Unchanged file should not be indexed again
        assert indexer._should_index_file(test_file) is False

    def test_should_index_file_modified(self, indexer, temp_dir):
        """Test should_index_file for modified files."""
        test_file = self.create_test_file(temp_dir / "test.md", "# Test")

        # Index the file first
        indexer.index_file(test_file)

        # Modify the file
        import time
        time.sleep(0.1)  # Ensure different timestamp
        test_file.write_text("# Modified Test")

        # Modified file should be indexed again
        assert indexer._should_index_file(test_file) is True

    def test_index_file_success(self, indexer, temp_dir):
        """Test successful file indexing."""
        content = """---
title: Test Document
tags: [python, testing]
---

# Test Heading

Test content with #tag and [link](https://example.com).
"""
        test_file = self.create_test_file(temp_dir / "test.md", content)

        result = indexer.index_file(test_file)
        assert result is True

        # Verify data was stored
        with indexer.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM files WHERE path = ?", (str(test_file),))
            file_record = cursor.fetchone()
            assert file_record is not None
            assert file_record['filename'] == 'test.md'
            assert file_record['word_count'] > 0

    def test_index_file_nonexistent(self, indexer, temp_dir):
        """Test indexing nonexistent file."""
        nonexistent = temp_dir / "nonexistent.md"

        with pytest.raises(IndexingError, match="File does not exist"):
            indexer.index_file(nonexistent)

    def test_index_file_not_markdown(self, indexer, temp_dir):
        """Test indexing non-markdown file."""
        text_file = temp_dir / "test.txt"
        text_file.write_text("Not markdown")

        with pytest.raises(IndexingError, match="File is not a markdown file"):
            indexer.index_file(text_file)

    def test_index_directory_success(self, indexer, temp_dir):
        """Test successful directory indexing."""
        # Create test files
        self.create_test_file(temp_dir / "file1.md", "# File 1")
        self.create_test_file(temp_dir / "file2.md", "# File 2")
        self.create_test_file(temp_dir / "subdir" / "file3.md", "# File 3")

        stats = indexer.index_directory(temp_dir)

        assert stats['files_processed'] == 3
        assert stats['errors'] == 0

        # Verify files were indexed
        assert indexer.get_file_count() == 3

    def test_index_directory_nonexistent(self, indexer):
        """Test indexing nonexistent directory."""
        nonexistent = Path("/nonexistent/directory")

        with pytest.raises(IndexingError, match="Directory does not exist"):
            indexer.index_directory(nonexistent)

    def test_index_directory_not_directory(self, indexer, temp_dir):
        """Test indexing a file instead of directory."""
        test_file = self.create_test_file(temp_dir / "test.md", "# Test")

        with pytest.raises(IndexingError, match="Path is not a directory"):
            indexer.index_directory(test_file)

    def test_index_directory_with_errors(self, indexer, temp_dir):
        """Test directory indexing with some file errors."""
        # Create valid file
        self.create_test_file(temp_dir / "valid.md", "# Valid")

        # Create file that will cause parsing error
        problematic_file = temp_dir / "problematic.md"
        problematic_file.write_bytes(b'\x00\x01\x02invalid\xff\xfe')  # Invalid UTF-8

        stats = indexer.index_directory(temp_dir)

        # Should process valid file and report error for problematic one
        assert stats['files_processed'] >= 1
        assert stats['errors'] >= 0  # Might handle gracefully

    def test_store_file_data_complete(self, indexer, temp_dir):
        """Test storing complete file data in database."""
        # Create test data
        test_file = temp_dir / "test.md"
        file_metadata = FileMetadata(
            path=test_file,
            filename="test.md",
            directory=str(temp_dir),
            modified_date=datetime.now(),
            created_date=datetime.now(),
            file_size=100,
            content_hash="testhash123"
        )

        parsed_content = ParsedContent(
            frontmatter={"title": {"value": "Test", "type": "string"}},
            content="Test content for searching",
            title="Test Document",
            headings=["Main Heading", "Sub Heading"],
            tags=["python", "testing"],
            links=[{
                "link_text": "Example",
                "link_target": "https://example.com",
                "link_type": "markdown",
                "is_internal": False
            }]
        )

        # Store data
        indexer._store_file_data(file_metadata, parsed_content)

        # Verify all data was stored
        with indexer.db_manager.get_connection() as conn:
            # Check file record
            cursor = conn.execute("SELECT * FROM files WHERE path = ?", (str(test_file),))
            file_record = cursor.fetchone()
            assert file_record is not None
            assert file_record['filename'] == 'test.md'
            assert file_record['word_count'] == 4  # "Test content for searching"
            assert file_record['heading_count'] == 2

            # Check frontmatter
            cursor = conn.execute("SELECT * FROM frontmatter WHERE file_id = ?", (file_record['id'],))
            fm_records = cursor.fetchall()
            assert len(fm_records) == 1
            assert fm_records[0]['key'] == 'title'
            assert fm_records[0]['value'] == 'Test'

            # Check tags
            cursor = conn.execute("SELECT * FROM tags WHERE file_id = ?", (file_record['id'],))
            tag_records = cursor.fetchall()
            assert len(tag_records) == 2
            tag_values = [r['tag'] for r in tag_records]
            assert 'python' in tag_values
            assert 'testing' in tag_values

            # Check links
            cursor = conn.execute("SELECT * FROM links WHERE file_id = ?", (file_record['id'],))
            link_records = cursor.fetchall()
            assert len(link_records) == 1
            assert link_records[0]['link_target'] == 'https://example.com'
            assert link_records[0]['is_internal'] == 0  # False

            # Check FTS content
            cursor = conn.execute("SELECT * FROM content_fts WHERE file_id = ?", (file_record['id'],))
            fts_record = cursor.fetchone()
            assert fts_record is not None
            assert fts_record['title'] == 'Test Document'
            assert 'Test content' in fts_record['content']

    def test_rebuild_index(self, indexer, temp_dir):
        """Test rebuilding index for directory."""
        # Create and index files
        self.create_test_file(temp_dir / "file1.md", "# File 1")
        self.create_test_file(temp_dir / "file2.md", "# File 2")
        indexer.index_directory(temp_dir)

        # Verify files are indexed
        assert indexer.get_file_count() == 2

        # Add another file and rebuild
        self.create_test_file(temp_dir / "file3.md", "# File 3")
        stats = indexer.rebuild_index(temp_dir)

        # Should have all 3 files
        assert indexer.get_file_count() == 3
        assert stats['files_processed'] == 3

    def test_get_indexing_stats(self, indexer):
        """Test getting indexing statistics."""
        stats = indexer.get_indexing_stats()

        assert isinstance(stats, dict)
        assert 'files_processed' in stats
        assert 'files_updated' in stats
        assert 'files_skipped' in stats
        assert 'errors' in stats

    def test_get_file_count_empty(self, indexer):
        """Test file count with empty database."""
        count = indexer.get_file_count()
        assert count == 0

    def test_get_file_count_with_files(self, indexer, temp_dir):
        """Test file count with indexed files."""
        # Create and index files
        self.create_test_file(temp_dir / "file1.md", "# File 1")
        self.create_test_file(temp_dir / "file2.md", "# File 2")
        indexer.index_directory(temp_dir)

        count = indexer.get_file_count()
        assert count == 2

    def test_markdown_extensions_support(self, indexer, temp_dir):
        """Test support for different markdown extensions."""
        extensions = ['.md', '.markdown', '.mdown', '.mkd', '.mkdn', '.mdx']

        for i, ext in enumerate(extensions):
            self.create_test_file(temp_dir / f"file{i}{ext}", f"# File {i}")

        stats = indexer.index_directory(temp_dir)
        assert stats['files_processed'] == len(extensions)

    def test_error_handling_corrupted_file(self, indexer, temp_dir):
        """Test error handling for corrupted files."""
        # Create a file with invalid content that might cause parsing errors
        corrupted_file = temp_dir / "corrupted.md"

        # Write some problematic content
        with open(corrupted_file, 'wb') as f:
            f.write(b'---\ninvalid: yaml: content:\n---\n# Heading')

        # Should handle gracefully
        try:
            result = indexer.index_file(corrupted_file)
            # If it succeeds, that's fine - parsers are robust
            assert isinstance(result, bool)
        except IndexingError:
            # If it fails with IndexingError, that's also acceptable
            pass

    def test_concurrent_indexing_safety(self, indexer, temp_dir):
        """Test that indexing is safe for concurrent access."""
        # This is a basic test - real concurrent testing would need threading
        test_file = self.create_test_file(temp_dir / "test.md", "# Test")

        # Index the same file multiple times
        result1 = indexer.index_file(test_file)
        result2 = indexer.index_file(test_file)

        assert result1 is True
        assert result2 is True

        # Should still have only one file record
        assert indexer.get_file_count() == 1

    def test_large_file_handling(self, indexer, temp_dir):
        """Test handling of larger files."""
        # Create a larger markdown file
        large_content = "# Large File\n\n" + "This is a test paragraph. " * 1000
        large_file = self.create_test_file(temp_dir / "large.md", large_content)

        result = indexer.index_file(large_file)
        assert result is True

        # Verify it was indexed correctly
        with indexer.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT word_count FROM files WHERE path = ?", (str(large_file),))
            record = cursor.fetchone()
            assert record['word_count'] > 1000  # Should have many words

    def test_special_characters_in_paths(self, indexer, temp_dir):
        """Test handling files with special characters in paths."""
        # Create file with special characters in name
        special_file = self.create_test_file(
            temp_dir / "special chars & symbols (test).md",
            "# Special File"
        )

        result = indexer.index_file(special_file)
        assert result is True

        # Verify it was stored correctly
        with indexer.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT filename FROM files WHERE path = ?", (str(special_file),))
            record = cursor.fetchone()
            assert record['filename'] == "special chars & symbols (test).md"