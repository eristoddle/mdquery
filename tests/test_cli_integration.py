"""
Integration tests for CLI application interface.

Tests the complete CLI workflow including indexing, querying, and schema inspection
with various output formats and error handling scenarios.
"""

import json
import tempfile
import shutil
from pathlib import Path
from click.testing import CliRunner
import pytest

from mdquery.cli import cli


class TestCLIIntegration:
    """Integration tests for CLI commands and workflows."""

    def setup_method(self):
        """Set up test environment with sample markdown files."""
        self.runner = CliRunner()

        # Create temporary directory for test files
        self.temp_dir = Path(tempfile.mkdtemp())

        # Create sample markdown files
        self.create_sample_files()

    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def create_sample_files(self):
        """Create sample markdown files for testing."""
        # File 1: Blog post with frontmatter
        blog_post = self.temp_dir / "blog-post.md"
        blog_post.write_text("""---
title: "My First Blog Post"
date: 2024-01-15
tags: [blog, tutorial, python]
category: programming
published: true
---

# My First Blog Post

This is a sample blog post about **Python programming**.

## Getting Started

Here are some basic concepts:

- Variables and data types
- Control structures
- Functions and modules

Check out the [Python documentation](https://docs.python.org) for more info.

#python #tutorial
""")

        # File 2: Research note
        research_note = self.temp_dir / "research-note.md"
        research_note.write_text("""---
title: "Research on Machine Learning"
author: "John Doe"
tags: [research, ml, ai]
status: draft
---

# Machine Learning Research

This note contains research findings on machine learning algorithms.

## Key Findings

1. Deep learning shows promise
2. Data quality is crucial
3. Model interpretability matters

See also: [[related-paper.md]]

#research #machinelearning
""")

        # File 3: Simple note without frontmatter
        simple_note = self.temp_dir / "simple-note.md"
        simple_note.write_text("""# Simple Note

This is a simple markdown file without frontmatter.

It contains some basic content and a few tags: #simple #test

Links to [external site](https://example.com) and [[internal-link]].
""")

        # File 4: Empty file
        empty_file = self.temp_dir / "empty.md"
        empty_file.write_text("")

        # Create subdirectory with additional file
        subdir = self.temp_dir / "subdir"
        subdir.mkdir()

        sub_note = subdir / "sub-note.md"
        sub_note.write_text("""---
title: "Subdirectory Note"
tags: [subdir, nested]
---

# Subdirectory Note

This file is in a subdirectory.

#nested #organization
""")

    def test_cli_help(self):
        """Test CLI help output."""
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'mdquery - Universal markdown querying tool' in result.output
        assert 'query' in result.output
        assert 'index' in result.output
        assert 'schema' in result.output

    def test_command_help(self):
        """Test individual command help."""
        # Test query command help
        result = self.runner.invoke(cli, ['query', '--help'])
        assert result.exit_code == 0
        assert 'Execute a SQL query' in result.output

        # Test index command help
        result = self.runner.invoke(cli, ['index', '--help'])
        assert result.exit_code == 0
        assert 'Index markdown files' in result.output

        # Test schema command help
        result = self.runner.invoke(cli, ['schema', '--help'])
        assert result.exit_code == 0
        assert 'Display database schema' in result.output

    def test_index_directory_basic(self):
        """Test basic directory indexing."""
        result = self.runner.invoke(cli, ['index', str(self.temp_dir)])
        assert result.exit_code == 0
        assert 'Indexing complete' in result.output
        assert 'Files processed: 5' in result.output
        assert 'Total files in index: 5' in result.output

    def test_index_directory_non_recursive(self):
        """Test non-recursive directory indexing."""
        result = self.runner.invoke(cli, ['index', str(self.temp_dir), '--no-recursive'])
        assert result.exit_code == 0
        assert 'Indexing complete' in result.output
        assert 'Files processed: 4' in result.output  # Should skip subdirectory file

    def test_index_directory_incremental(self):
        """Test incremental indexing."""
        # First, do a full index
        result = self.runner.invoke(cli, ['index', str(self.temp_dir)])
        assert result.exit_code == 0

        # Then do incremental (should skip unchanged files)
        result = self.runner.invoke(cli, ['index', str(self.temp_dir), '--incremental'])
        assert result.exit_code == 0
        assert 'Files skipped: 5' in result.output

    def test_index_directory_rebuild(self):
        """Test rebuilding index."""
        # First, do a full index
        result = self.runner.invoke(cli, ['index', str(self.temp_dir)])
        assert result.exit_code == 0

        # Then rebuild
        result = self.runner.invoke(cli, ['index', str(self.temp_dir), '--rebuild'])
        assert result.exit_code == 0
        assert 'Rebuilding index' in result.output

    def test_index_directory_sync(self):
        """Test synchronizing index."""
        # First, do a full index
        result = self.runner.invoke(cli, ['index', str(self.temp_dir)])
        assert result.exit_code == 0

        # Then sync
        result = self.runner.invoke(cli, ['index', str(self.temp_dir), '--sync'])
        assert result.exit_code == 0
        assert 'Synchronizing index' in result.output
        assert 'Files unchanged: 5' in result.output

    def test_index_nonexistent_directory(self):
        """Test indexing nonexistent directory."""
        result = self.runner.invoke(cli, ['index', '/nonexistent/directory'])
        assert result.exit_code == 1
        assert 'Directory does not exist' in result.output

    def test_query_basic_table_format(self):
        """Test basic query with table format."""
        # First index the directory
        self.runner.invoke(cli, ['index', str(self.temp_dir)])

        # Query all files
        result = self.runner.invoke(cli, [
            'query',
            'SELECT filename, word_count FROM files ORDER BY filename',
            '--directory', str(self.temp_dir)
        ])
        assert result.exit_code == 0
        assert 'blog-post.md' in result.output
        assert 'research-note.md' in result.output
        assert 'simple-note.md' in result.output
        assert 'Rows:' in result.output

    def test_query_json_format(self):
        """Test query with JSON output format."""
        # First index the directory
        self.runner.invoke(cli, ['index', str(self.temp_dir)])

        # Query with JSON format
        result = self.runner.invoke(cli, [
            'query',
            'SELECT filename FROM files WHERE filename = "blog-post.md"',
            '--directory', str(self.temp_dir),
            '--format', 'json'
        ])
        assert result.exit_code == 0

        # Parse JSON output
        output_data = json.loads(result.output)
        assert 'rows' in output_data
        assert len(output_data['rows']) == 1
        assert output_data['rows'][0]['filename'] == 'blog-post.md'

    def test_query_csv_format(self):
        """Test query with CSV output format."""
        # First index the directory
        self.runner.invoke(cli, ['index', str(self.temp_dir)])

        # Query with CSV format
        result = self.runner.invoke(cli, [
            'query',
            'SELECT filename, word_count FROM files ORDER BY filename LIMIT 2',
            '--directory', str(self.temp_dir),
            '--format', 'csv'
        ])
        assert result.exit_code == 0
        assert 'filename,word_count' in result.output
        assert 'blog-post.md' in result.output

    def test_query_markdown_format(self):
        """Test query with Markdown output format."""
        # First index the directory
        self.runner.invoke(cli, ['index', str(self.temp_dir)])

        # Query with Markdown format
        result = self.runner.invoke(cli, [
            'query',
            'SELECT filename FROM files LIMIT 1',
            '--directory', str(self.temp_dir),
            '--format', 'markdown'
        ])
        assert result.exit_code == 0
        assert '| filename |' in result.output
        assert '| --- |' in result.output
        assert '**Results:**' in result.output

    def test_query_with_limit(self):
        """Test query with result limit."""
        # First index the directory
        self.runner.invoke(cli, ['index', str(self.temp_dir)])

        # Query with limit
        result = self.runner.invoke(cli, [
            'query',
            'SELECT filename FROM files',
            '--directory', str(self.temp_dir),
            '--limit', '2',
            '--format', 'json'
        ])
        assert result.exit_code == 0

        output_data = json.loads(result.output)
        assert len(output_data['rows']) <= 2

    def test_query_complex_with_joins(self):
        """Test complex query with joins."""
        # First index the directory
        self.runner.invoke(cli, ['index', str(self.temp_dir)])

        # Query with joins
        result = self.runner.invoke(cli, [
            'query',
            'SELECT f.filename, COUNT(t.tag) as tag_count FROM files f LEFT JOIN tags t ON f.id = t.file_id GROUP BY f.id ORDER BY f.filename',
            '--directory', str(self.temp_dir),
            '--format', 'json'
        ])
        assert result.exit_code == 0

        output_data = json.loads(result.output)
        assert len(output_data['rows']) > 0
        # Check that files with tags have tag_count > 0
        for row in output_data['rows']:
            if row['filename'] in ['blog-post.md', 'research-note.md']:
                assert row['tag_count'] > 0

    def test_query_no_index(self):
        """Test query without existing index."""
        result = self.runner.invoke(cli, [
            'query',
            'SELECT * FROM files',
            '--directory', str(self.temp_dir)
        ])
        assert result.exit_code == 1
        assert 'No index found' in result.output

    def test_query_invalid_sql(self):
        """Test query with invalid SQL."""
        # First index the directory
        self.runner.invoke(cli, ['index', str(self.temp_dir)])

        # Invalid SQL query
        result = self.runner.invoke(cli, [
            'query',
            'INVALID SQL QUERY',
            '--directory', str(self.temp_dir)
        ])
        assert result.exit_code == 1
        assert 'Error executing query' in result.output

    def test_query_dangerous_sql(self):
        """Test query with dangerous SQL patterns."""
        # First index the directory
        self.runner.invoke(cli, ['index', str(self.temp_dir)])

        # Dangerous SQL query
        result = self.runner.invoke(cli, [
            'query',
            'DROP TABLE files',
            '--directory', str(self.temp_dir)
        ])
        assert result.exit_code == 1
        assert 'Error executing query' in result.output

    def test_schema_basic(self):
        """Test basic schema display."""
        # First index the directory
        self.runner.invoke(cli, ['index', str(self.temp_dir)])

        # Get schema
        result = self.runner.invoke(cli, [
            'schema',
            '--directory', str(self.temp_dir)
        ])
        assert result.exit_code == 0
        assert 'Database Schema' in result.output
        assert 'Tables:' in result.output
        assert 'files:' in result.output
        assert 'frontmatter:' in result.output
        assert 'tags:' in result.output
        assert 'links:' in result.output

    def test_schema_specific_table(self):
        """Test schema for specific table."""
        # First index the directory
        self.runner.invoke(cli, ['index', str(self.temp_dir)])

        # Get schema for files table
        result = self.runner.invoke(cli, [
            'schema',
            '--table', 'files',
            '--directory', str(self.temp_dir)
        ])
        assert result.exit_code == 0
        assert 'Table: files' in result.output
        assert 'Columns:' in result.output
        assert 'path:' in result.output
        assert 'filename:' in result.output

    def test_schema_json_format(self):
        """Test schema with JSON format."""
        # First index the directory
        self.runner.invoke(cli, ['index', str(self.temp_dir)])

        # Get schema in JSON format
        result = self.runner.invoke(cli, [
            'schema',
            '--directory', str(self.temp_dir),
            '--format', 'json'
        ])
        assert result.exit_code == 0

        # Parse JSON output
        schema_data = json.loads(result.output)
        assert 'version' in schema_data
        assert 'tables' in schema_data
        assert 'files' in schema_data['tables']

    def test_schema_no_index(self):
        """Test schema without existing index."""
        result = self.runner.invoke(cli, [
            'schema',
            '--directory', str(self.temp_dir)
        ])
        assert result.exit_code == 1
        assert 'No index found' in result.output

    def test_examples_command(self):
        """Test examples command."""
        # First index the directory
        self.runner.invoke(cli, ['index', str(self.temp_dir)])

        # Get examples
        result = self.runner.invoke(cli, [
            'examples',
            '--directory', str(self.temp_dir)
        ])
        assert result.exit_code == 0
        assert 'Example Queries' in result.output
        assert 'All files' in result.output
        assert 'SELECT * FROM files' in result.output

    def test_remove_command(self):
        """Test remove command."""
        # First index the directory
        self.runner.invoke(cli, ['index', str(self.temp_dir)])

        # Remove a file from index
        file_to_remove = self.temp_dir / "simple-note.md"
        result = self.runner.invoke(cli, [
            'remove',
            str(file_to_remove),
            '--directory', str(self.temp_dir)
        ])
        assert result.exit_code == 0
        assert 'Removed' in result.output

        # Verify file is no longer in index
        query_result = self.runner.invoke(cli, [
            'query',
            'SELECT COUNT(*) as count FROM files WHERE filename = "simple-note.md"',
            '--directory', str(self.temp_dir),
            '--format', 'json'
        ])
        assert query_result.exit_code == 0
        output_data = json.loads(query_result.output)
        assert output_data['rows'][0]['count'] == 0

    def test_verbose_logging(self):
        """Test verbose logging option."""
        result = self.runner.invoke(cli, [
            '--verbose',
            'index',
            str(self.temp_dir)
        ])
        assert result.exit_code == 0
        # Verbose mode should still work, just with more logging

    def test_debug_logging(self):
        """Test debug logging option."""
        result = self.runner.invoke(cli, [
            '--debug',
            'index',
            str(self.temp_dir)
        ])
        assert result.exit_code == 0
        # Debug mode should still work, just with debug logging

    def test_workflow_end_to_end(self):
        """Test complete workflow from indexing to querying."""
        # Step 1: Index directory
        index_result = self.runner.invoke(cli, ['index', str(self.temp_dir)])
        assert index_result.exit_code == 0

        # Step 2: Check schema
        schema_result = self.runner.invoke(cli, [
            'schema',
            '--directory', str(self.temp_dir)
        ])
        assert schema_result.exit_code == 0

        # Step 3: Query files with tags
        query_result = self.runner.invoke(cli, [
            'query',
            'SELECT f.filename, GROUP_CONCAT(t.tag) as tags FROM files f LEFT JOIN tags t ON f.id = t.file_id GROUP BY f.id HAVING tags IS NOT NULL',
            '--directory', str(self.temp_dir),
            '--format', 'json'
        ])
        assert query_result.exit_code == 0

        output_data = json.loads(query_result.output)
        assert len(output_data['rows']) > 0

        # Step 4: Search content
        search_result = self.runner.invoke(cli, [
            'query',
            'SELECT f.filename FROM content_fts c JOIN files f ON c.file_id = f.id WHERE c.content MATCH "python"',
            '--directory', str(self.temp_dir),
            '--format', 'json'
        ])
        assert search_result.exit_code == 0

        search_data = json.loads(search_result.output)
        # Should find files containing "python"
        filenames = [row['filename'] for row in search_data['rows']]
        assert 'blog-post.md' in filenames

    def test_error_handling_file_permissions(self):
        """Test error handling for file permission issues."""
        # This test might not work on all systems, so we'll skip if we can't create the scenario
        try:
            # Create a directory we can't read
            restricted_dir = self.temp_dir / "restricted"
            restricted_dir.mkdir()
            restricted_file = restricted_dir / "test.md"
            restricted_file.write_text("# Test")

            # Try to make directory unreadable (might not work on all systems)
            import os
            try:
                os.chmod(restricted_dir, 0o000)

                # Try to index - should handle permission error gracefully
                result = self.runner.invoke(cli, ['index', str(self.temp_dir)])
                # Should still succeed for other files, just log warnings for restricted ones
                assert result.exit_code == 0

            finally:
                # Restore permissions for cleanup
                os.chmod(restricted_dir, 0o755)

        except (OSError, PermissionError):
            # Skip this test if we can't manipulate permissions
            pytest.skip("Cannot test permission errors on this system")

    def test_large_query_results(self):
        """Test handling of large query results."""
        # First index the directory
        self.runner.invoke(cli, ['index', str(self.temp_dir)])

        # Query that might return large results (though our test data is small)
        result = self.runner.invoke(cli, [
            'query',
            'SELECT * FROM files',
            '--directory', str(self.temp_dir),
            '--format', 'json'
        ])
        assert result.exit_code == 0

        output_data = json.loads(result.output)
        assert 'rows' in output_data
        assert 'execution_time_ms' in output_data

    def test_query_timeout(self):
        """Test query timeout functionality."""
        # First index the directory
        self.runner.invoke(cli, ['index', str(self.temp_dir)])

        # Simple query with very short timeout (should still work for our small dataset)
        result = self.runner.invoke(cli, [
            'query',
            'SELECT * FROM files',
            '--directory', str(self.temp_dir),
            '--timeout', '0.1'  # 100ms timeout
        ])
        # Should still work for our small test dataset
        assert result.exit_code == 0

    def test_invalid_format_option(self):
        """Test invalid format option handling."""
        # First index the directory
        self.runner.invoke(cli, ['index', str(self.temp_dir)])

        # Try invalid format
        result = self.runner.invoke(cli, [
            'query',
            'SELECT * FROM files',
            '--directory', str(self.temp_dir),
            '--format', 'invalid'
        ])
        assert result.exit_code == 2  # Click validation error
        assert 'Invalid value' in result.output

    def test_nonexistent_directory_query(self):
        """Test querying nonexistent directory."""
        result = self.runner.invoke(cli, [
            'query',
            'SELECT * FROM files',
            '--directory', '/nonexistent/directory'
        ])
        assert result.exit_code == 1
        assert 'Directory does not exist' in result.output

    def test_empty_query_results(self):
        """Test handling of queries that return no results."""
        # First index the directory
        self.runner.invoke(cli, ['index', str(self.temp_dir)])

        # Query that returns no results
        result = self.runner.invoke(cli, [
            'query',
            'SELECT * FROM files WHERE filename = "nonexistent.md"',
            '--directory', str(self.temp_dir)
        ])
        assert result.exit_code == 0
        assert 'No results found' in result.output or 'Rows: 0' in result.output