"""
Integration tests for the file indexing engine with real markdown files.
"""

import tempfile
import pytest
from pathlib import Path

from mdquery.database import DatabaseManager
from mdquery.indexer import Indexer


class TestIndexerIntegration:
    """Integration tests for the complete indexing workflow."""

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

    def create_sample_files(self, base_dir: Path):
        """Create a collection of sample markdown files for testing."""

        # Obsidian-style note
        obsidian_note = base_dir / "notes" / "obsidian-note.md"
        obsidian_note.parent.mkdir(parents=True, exist_ok=True)
        obsidian_note.write_text("""---
title: Obsidian Note Example
tags: [obsidian, note-taking, productivity]
created: 2024-01-15
---

# Obsidian Note Example

This is an example of an [[Obsidian]] note with #productivity and #workflow tags.

## Features

- Supports [[wikilinks]] and #hashtags
- Has frontmatter with metadata
- Links to [external resources](https://obsidian.md)

### Nested Tags

Using nested tags like #productivity/tools and #workflow/automation.
""")

        # Jekyll blog post
        jekyll_post = base_dir / "blog" / "_posts" / "2024-01-15-jekyll-post.md"
        jekyll_post.parent.mkdir(parents=True, exist_ok=True)
        jekyll_post.write_text("""---
layout: post
title: "Jekyll Blog Post"
date: 2024-01-15 10:30:00 -0500
categories: [web, blogging]
tags: [jekyll, static-site, github-pages]
author: John Doe
description: "A sample Jekyll blog post demonstrating frontmatter and content structure"
---

# Jekyll Blog Post

This is a sample Jekyll blog post with proper frontmatter.

## Content Structure

Jekyll uses YAML frontmatter to define metadata:

- Layout templates
- Publication dates
- Categories and tags
- Author information

## Links and References

Check out the [Jekyll documentation](https://jekyllrb.com/docs/) for more information.

### Code Example

```yaml
---
layout: post
title: "My Post"
---
```

This post demonstrates #blogging and #web-development concepts.
""")

        # Joplin note
        joplin_note = base_dir / "joplin" / "research-note.md"
        joplin_note.parent.mkdir(parents=True, exist_ok=True)
        joplin_note.write_text("""# Research Note

Created: 2024-01-15T15:30:00Z
Updated: 2024-01-15T16:45:00Z
Tags: research, machine-learning, ai

## Machine Learning Research

This note contains research findings on #machine-learning and #artificial-intelligence.

### Key Papers

1. [Attention Is All You Need](https://arxiv.org/abs/1706.03762)
2. [BERT: Pre-training of Deep Bidirectional Transformers](https://arxiv.org/abs/1810.04805)

### Implementation Notes

The transformer architecture revolutionized #nlp and #deep-learning.

#### Code References

See the [[transformer-implementation]] note for code examples.
""")

        # Generic markdown file
        generic_md = base_dir / "docs" / "README.md"
        generic_md.parent.mkdir(parents=True, exist_ok=True)
        generic_md.write_text("""# Project Documentation

This is a generic markdown file without frontmatter.

## Overview

This project demonstrates markdown parsing capabilities across different formats:

- **Obsidian**: Wikilinks and hashtags
- **Jekyll**: YAML frontmatter and liquid tags
- **Joplin**: Timestamp metadata and simple tags
- **Generic**: Standard markdown syntax

## Features

### Link Support

- Standard links: [GitHub](https://github.com)
- Reference links: [Documentation][docs]
- Auto-links: <https://example.com>

### Tag Support

Using #documentation and #markdown tags for organization.

### Content Analysis

This file contains multiple headings, links, and tags for comprehensive testing.

[docs]: https://docs.example.com "Documentation"
""")

        return {
            'obsidian': obsidian_note,
            'jekyll': jekyll_post,
            'joplin': joplin_note,
            'generic': generic_md
        }

    def test_complete_indexing_workflow(self, indexer, temp_dir):
        """Test the complete indexing workflow with various file types."""

        # Create sample files
        files = self.create_sample_files(temp_dir)

        # Index the entire directory
        stats = indexer.index_directory(temp_dir, recursive=True)

        # Verify indexing statistics
        assert stats['files_processed'] == 4
        assert stats['errors'] == 0
        assert indexer.get_file_count() == 4

        # Verify database content
        with indexer.db_manager.get_connection() as conn:

            # Check files table
            cursor = conn.execute("SELECT filename, word_count, heading_count FROM files ORDER BY filename")
            file_records = cursor.fetchall()

            assert len(file_records) == 4

            # All files should have content
            for record in file_records:
                assert record['word_count'] > 0
                assert record['heading_count'] > 0

            # Check frontmatter extraction
            cursor = conn.execute("""
                SELECT f.filename, fm.key, fm.value
                FROM files f
                JOIN frontmatter fm ON f.id = fm.file_id
                WHERE f.filename = 'obsidian-note.md'
                ORDER BY fm.key
            """)
            obsidian_fm = cursor.fetchall()

            # Should have frontmatter from Obsidian file
            assert len(obsidian_fm) > 0
            fm_keys = [record['key'] for record in obsidian_fm]
            assert 'title' in fm_keys
            assert 'tags' in fm_keys

            # Check tag extraction
            cursor = conn.execute("""
                SELECT DISTINCT tag FROM tags
                ORDER BY tag
            """)
            all_tags = [record['tag'] for record in cursor.fetchall()]

            # Should have tags from various sources
            assert 'obsidian' in all_tags
            assert 'productivity' in all_tags
            assert 'jekyll' in all_tags
            assert 'machine-learning' in all_tags
            assert 'documentation' in all_tags

            # Check link extraction
            cursor = conn.execute("""
                SELECT link_target, link_type, is_internal
                FROM links
                ORDER BY link_target
            """)
            links = cursor.fetchall()

            # Should have various types of links
            link_targets = [record['link_target'] for record in links]
            assert 'https://obsidian.md' in link_targets
            assert 'https://jekyllrb.com/docs/' in link_targets
            assert 'Obsidian' in link_targets  # Wikilink

            # Check FTS5 content
            cursor = conn.execute("""
                SELECT COUNT(*) as count FROM content_fts
                WHERE content MATCH 'markdown'
            """)
            fts_count = cursor.fetchone()['count']
            assert fts_count > 0  # Should find "markdown" in content

    def test_incremental_indexing(self, indexer, temp_dir):
        """Test incremental indexing with file modifications."""

        # Create initial file
        test_file = temp_dir / "test.md"
        test_file.write_text("""---
title: Original Title
tags: [original]
---

# Original Content

This is the original content with #original-tag.
""")

        # Initial indexing
        indexer.index_file(test_file)

        # Verify initial state
        with indexer.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT word_count FROM files WHERE filename = 'test.md'")
            original_word_count = cursor.fetchone()['word_count']

            cursor = conn.execute("SELECT COUNT(*) as count FROM tags WHERE tag = 'original'")
            original_tag_count = cursor.fetchone()['count']
            assert original_tag_count == 1

        # Modify the file
        import time
        time.sleep(0.1)  # Ensure different timestamp
        test_file.write_text("""---
title: Updated Title
tags: [updated, modified]
---

# Updated Content

This is the updated content with #updated-tag and #modified-tag.

## Additional Section

More content to increase word count significantly.
""")

        # Re-index the file
        indexer.index_file(test_file)

        # Verify changes
        with indexer.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT word_count FROM files WHERE filename = 'test.md'")
            new_word_count = cursor.fetchone()['word_count']
            assert new_word_count > original_word_count

            # Old tags should be replaced
            cursor = conn.execute("SELECT COUNT(*) as count FROM tags WHERE tag = 'original'")
            old_tag_count = cursor.fetchone()['count']
            assert old_tag_count == 0

            # New tags should be present
            cursor = conn.execute("SELECT COUNT(*) as count FROM tags WHERE tag = 'updated'")
            new_tag_count = cursor.fetchone()['count']
            assert new_tag_count == 1

    def test_error_resilience(self, indexer, temp_dir):
        """Test indexing resilience with problematic files."""

        # Create valid file
        valid_file = temp_dir / "valid.md"
        valid_file.write_text("# Valid File\n\nThis is a valid markdown file.")

        # Create file with encoding issues
        problematic_file = temp_dir / "problematic.md"
        with open(problematic_file, 'wb') as f:
            f.write("# File with encoding issues\n\nSome text with special chars: ".encode('utf-8'))
            f.write(b'\xe9\xf1\xff')  # Some problematic bytes

        # Create empty file
        empty_file = temp_dir / "empty.md"
        empty_file.write_text("")

        # Index directory - should handle errors gracefully
        stats = indexer.index_directory(temp_dir)

        # Should process at least the valid files
        assert stats['files_processed'] >= 1
        assert indexer.get_file_count() >= 1

        # Verify valid file was indexed
        with indexer.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT filename FROM files WHERE filename = 'valid.md'")
            result = cursor.fetchone()
            assert result is not None

    def test_large_collection_performance(self, indexer, temp_dir):
        """Test performance with a larger collection of files."""

        # Create multiple files
        num_files = 50
        for i in range(num_files):
            file_path = temp_dir / f"file_{i:03d}.md"
            content = f"""---
title: "Document {i}"
number: {i}
tags: [test, batch-{i // 10}]
---

# Document {i}

This is document number {i} in the test collection.

## Content Section

Some content with #tag-{i} and links to [Document {i-1}](file_{i-1:03d}.md) if it exists.

### Details

- Item 1 for document {i}
- Item 2 with more text
- Item 3 with even more descriptive text to increase word count

The document contains various elements for comprehensive testing.
"""
            file_path.write_text(content)

        # Index all files
        import time
        start_time = time.time()
        stats = indexer.index_directory(temp_dir)
        end_time = time.time()

        indexing_time = end_time - start_time

        # Verify results
        assert stats['files_processed'] == num_files
        assert stats['errors'] == 0
        assert indexer.get_file_count() == num_files

        # Performance should be reasonable (less than 10 seconds for 50 files)
        assert indexing_time < 10.0

        # Verify database integrity
        with indexer.db_manager.get_connection() as conn:
            # Check that all files have content
            cursor = conn.execute("SELECT COUNT(*) as count FROM files WHERE word_count > 0")
            files_with_content = cursor.fetchone()['count']
            assert files_with_content == num_files

            # Check that tags were extracted
            cursor = conn.execute("SELECT COUNT(DISTINCT tag) as count FROM tags")
            unique_tags = cursor.fetchone()['count']
            assert unique_tags > 10  # Should have many unique tags

            # Check FTS5 functionality
            cursor = conn.execute("SELECT COUNT(*) as count FROM content_fts WHERE content MATCH 'document'")
            fts_matches = cursor.fetchone()['count']
            assert fts_matches > 0