"""
End-to-end integration tests for complete mdquery workflows.
Tests the full pipeline from indexing to querying across different interfaces.
"""

import pytest
import tempfile
import subprocess
import json
import os
from pathlib import Path

from mdquery.indexer import Indexer
from mdquery.query import QueryEngine
from mdquery.cache import CacheManager
from mdquery.cli import cli


class TestEndToEndWorkflows:
    """Test complete workflows from start to finish."""

    @pytest.fixture
    def test_data_dir(self):
        """Get the test data directory."""
        return Path(__file__).parent / "test_data"

    @pytest.fixture
    def temp_workspace(self, test_data_dir):
        """Create a temporary workspace with test data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)

            # Copy test data to workspace
            import shutil
            for format_dir in ["obsidian", "joplin", "jekyll", "generic"]:
                src_dir = test_data_dir / format_dir
                if src_dir.exists():
                    dst_dir = workspace / format_dir
                    shutil.copytree(src_dir, dst_dir)

            yield workspace

    def test_complete_cli_workflow(self, temp_workspace):
        """Test complete workflow using CLI interface."""
        from click.testing import CliRunner

        runner = CliRunner()

        # Test indexing command
        result = runner.invoke(cli, [
            'index',
            str(temp_workspace),
            '--cache-path', str(temp_workspace / 'test.db')
        ])
        assert result.exit_code == 0, f"Index command failed: {result.output}"

        # Test basic query
        result = runner.invoke(cli, [
            'query',
            'SELECT COUNT(*) as total FROM files',
            '--cache-path', str(temp_workspace / 'test.db'),
            '--format', 'json'
        ])
        assert result.exit_code == 0, f"Query command failed: {result.output}"

        # Parse JSON output
        output_data = json.loads(result.output)
        assert output_data['total'] > 0, "Should find indexed files"

        # Test schema command
        result = runner.invoke(cli, [
            'schema',
            '--cache-path', str(temp_workspace / 'test.db')
        ])
        assert result.exit_code == 0, f"Schema command failed: {result.output}"
        assert 'files' in result.output, "Schema should show files table"

    def test_research_workflow(self, temp_workspace):
        """Test a typical research workflow."""
        # Initialize components
        cache_path = temp_workspace / "research.db"
        cache_manager = CacheManager(cache_path)
        cache_manager.initialize_cache()

        indexer = Indexer(cache_manager=cache_manager)
        query_engine = QueryEngine(cache_manager=cache_manager)

        # Index all research materials
        indexer.index_directory(temp_workspace)

        # Research workflow: Find all research-related content
        research_query = """
            SELECT f.filename, f.directory, t.tag, fm.value as title
            FROM files f
            LEFT JOIN tags t ON f.id = t.file_id
            LEFT JOIN frontmatter fm ON f.id = fm.file_id AND fm.key = 'title'
            WHERE t.tag LIKE '%research%' OR fm.value LIKE '%Research%'
            ORDER BY f.modified_date DESC
        """

        result = query_engine.execute_query(research_query)
        assert len(result.rows) > 0, "Should find research-related content"

        # Find related content through tags
        related_query = """
            SELECT DISTINCT f2.filename, f2.directory
            FROM files f1
            JOIN tags t1 ON f1.id = t1.file_id
            JOIN tags t2 ON t1.tag = t2.tag
            JOIN files f2 ON t2.file_id = f2.id
            WHERE f1.filename = 'Research Project.md' AND f1.id != f2.id
        """

        result = query_engine.execute_query(related_query)
        # May or may not find related content depending on test data

        # Content analysis: Find key themes
        themes_query = """
            SELECT tag, COUNT(*) as frequency
            FROM tags
            GROUP BY tag
            ORDER BY frequency DESC
            LIMIT 10
        """

        result = query_engine.execute_query(themes_query)
        assert len(result.rows) > 0, "Should identify key themes"

        # Export findings for further processing
        export_query = """
            SELECT
                f.filename,
                f.directory,
                GROUP_CONCAT(DISTINCT t.tag) as tags,
                fm_title.value as title,
                fm_author.value as author
            FROM files f
            LEFT JOIN tags t ON f.id = t.file_id
            LEFT JOIN frontmatter fm_title ON f.id = fm_title.file_id AND fm_title.key = 'title'
            LEFT JOIN frontmatter fm_author ON f.id = fm_author.file_id AND fm_author.key = 'author'
            GROUP BY f.id
            ORDER BY f.filename
        """

        result = query_engine.execute_query(export_query)
        assert len(result.rows) > 0, "Should export structured findings"

    def test_content_analysis_workflow(self, temp_workspace):
        """Test content analysis and SEO workflow."""
        # Initialize components
        cache_path = temp_workspace / "analysis.db"
        cache_manager = CacheManager(cache_path)
        cache_manager.initialize_cache()

        indexer = Indexer(cache_manager=cache_manager)
        query_engine = QueryEngine(cache_manager=cache_manager)

        # Index content
        indexer.index_directory(temp_workspace)

        # Content analysis: Find files without titles
        missing_titles_query = """
            SELECT f.filename, f.directory
            FROM files f
            LEFT JOIN frontmatter fm ON f.id = fm.file_id AND fm.key = 'title'
            WHERE fm.value IS NULL
        """

        result = query_engine.execute_query(missing_titles_query)
        # Some files may not have titles

        # SEO analysis: Find posts with categories and tags
        seo_query = """
            SELECT
                f.filename,
                fm_title.value as title,
                fm_desc.value as description,
                GROUP_CONCAT(DISTINCT t.tag) as tags,
                f.word_count
            FROM files f
            LEFT JOIN frontmatter fm_title ON f.id = fm_title.file_id AND fm_title.key = 'title'
            LEFT JOIN frontmatter fm_desc ON f.id = fm_desc.file_id AND fm_desc.key = 'description'
            LEFT JOIN tags t ON f.id = t.file_id
            WHERE f.directory LIKE '%_posts%' OR f.directory LIKE '%jekyll%'
            GROUP BY f.id
        """

        result = query_engine.execute_query(seo_query)
        # Should find Jekyll posts if they exist

        # Content structure analysis
        structure_query = """
            SELECT
                AVG(word_count) as avg_words,
                MIN(word_count) as min_words,
                MAX(word_count) as max_words,
                COUNT(*) as total_files
            FROM files
            WHERE word_count > 0
        """

        result = query_engine.execute_query(structure_query)
        assert len(result.rows) == 1, "Should provide content statistics"
        assert result.rows[0]['total_files'] > 0, "Should analyze file statistics"

    def test_cross_system_migration_workflow(self, temp_workspace):
        """Test workflow for migrating between different markdown systems."""
        # Initialize components
        cache_path = temp_workspace / "migration.db"
        cache_manager = CacheManager(cache_path)
        cache_manager.initialize_cache()

        indexer = Indexer(cache_manager=cache_manager)
        query_engine = QueryEngine(cache_manager=cache_manager)

        # Index all systems
        indexer.index_directory(temp_workspace)

        # Migration analysis: Find Obsidian-specific features
        obsidian_features_query = """
            SELECT
                f.filename,
                f.directory,
                COUNT(DISTINCT l.link_target) as wikilink_count,
                COUNT(DISTINCT CASE WHEN t.tag LIKE '%/%' THEN t.tag END) as nested_tag_count
            FROM files f
            LEFT JOIN links l ON f.id = l.file_id AND l.link_type = 'wikilink'
            LEFT JOIN tags t ON f.id = t.file_id
            WHERE f.directory LIKE '%obsidian%'
            GROUP BY f.id
            HAVING wikilink_count > 0 OR nested_tag_count > 0
        """

        result = query_engine.execute_query(obsidian_features_query)
        # Should find Obsidian-specific features if they exist

        # Find all unique tags across systems for normalization
        tag_analysis_query = """
            SELECT
                tag,
                COUNT(*) as usage_count,
                GROUP_CONCAT(DISTINCT SUBSTR(f.directory, 1, 10)) as systems
            FROM tags t
            JOIN files f ON t.file_id = f.id
            GROUP BY tag
            ORDER BY usage_count DESC
        """

        result = query_engine.execute_query(tag_analysis_query)
        assert len(result.rows) > 0, "Should analyze tag usage across systems"

        # Find broken links that need fixing
        link_analysis_query = """
            SELECT
                f.filename,
                f.directory,
                l.link_target,
                l.link_type
            FROM files f
            JOIN links l ON f.id = l.file_id
            WHERE l.is_internal = 1
            ORDER BY f.filename, l.link_target
        """

        result = query_engine.execute_query(link_analysis_query)
        # May find internal links that need validation

    def test_incremental_update_workflow(self, temp_workspace):
        """Test incremental updates and cache management."""
        # Initialize components
        cache_path = temp_workspace / "incremental.db"
        cache_manager = CacheManager(cache_path)
        cache_manager.initialize_cache()

        indexer = Indexer(cache_manager=cache_manager)
        query_engine = QueryEngine(cache_manager=cache_manager)

        # Initial indexing
        indexer.index_directory(temp_workspace)

        initial_count_result = query_engine.execute_query("SELECT COUNT(*) as count FROM files")
        initial_count = initial_count_result.rows[0]['count']

        # Add a new file
        new_file = temp_workspace / "new_file.md"
        new_file.write_text("""---
title: New Test File
tags: [test, new]
---

# New Test File

This is a newly added file for testing incremental updates.
""")

        # Incremental update
        indexer.index_directory(temp_workspace)

        updated_count_result = query_engine.execute_query("SELECT COUNT(*) as count FROM files")
        updated_count = updated_count_result.rows[0]['count']

        assert updated_count == initial_count + 1, "Should detect and index new file"

        # Verify new file is queryable
        new_file_result = query_engine.execute_query(
            "SELECT * FROM files WHERE filename = 'new_file.md'"
        )
        assert len(new_file_result.rows) == 1, "New file should be queryable"

        # Modify existing file
        existing_file = list(temp_workspace.rglob("*.md"))[0]
        if existing_file != new_file:
            content = existing_file.read_text()
            existing_file.write_text(content + "\n\n## Updated Section\n\nThis content was added.")

            # Update index
            indexer.index_directory(temp_workspace)

            # Verify update was detected
            final_count_result = query_engine.execute_query("SELECT COUNT(*) as count FROM files")
            final_count = final_count_result.rows[0]['count']

            assert final_count == updated_count, "File count should remain same after update"

        # Test cache cleanup
        new_file.unlink()  # Delete the new file

        # Update index (should remove deleted file)
        indexer.index_directory(temp_workspace)

        cleanup_count_result = query_engine.execute_query("SELECT COUNT(*) as count FROM files")
        cleanup_count = cleanup_count_result.rows[0]['count']

        assert cleanup_count == initial_count, "Should remove deleted file from index"


class TestErrorHandling:
    """Test error handling in end-to-end workflows."""

    def test_invalid_directory_handling(self):
        """Test handling of invalid directories."""
        from click.testing import CliRunner

        runner = CliRunner()

        # Test with non-existent directory
        result = runner.invoke(cli, [
            'index',
            '/non/existent/directory'
        ])
        assert result.exit_code != 0, "Should fail with non-existent directory"

    def test_invalid_query_handling(self):
        """Test handling of invalid SQL queries."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "test.db"
            cache_manager = CacheManager(cache_path)
            cache_manager.initialize_cache()

            query_engine = QueryEngine(cache_manager=cache_manager)

            # Test invalid SQL
            with pytest.raises(Exception):
                query_engine.execute_query("INVALID SQL SYNTAX")

            # Test SQL injection attempt
            with pytest.raises(Exception):
                query_engine.execute_query("SELECT * FROM files; DROP TABLE files;")

    def test_corrupted_file_handling(self, temp_workspace):
        """Test handling of corrupted or binary files."""
        # Create a binary file
        binary_file = temp_workspace / "binary.md"
        binary_file.write_bytes(b'\x00\x01\x02\x03\x04\x05')

        # Create a file with invalid encoding
        invalid_file = temp_workspace / "invalid.md"
        with open(invalid_file, 'wb') as f:
            f.write("Valid start".encode('utf-8'))
            f.write(b'\xff\xfe\xfd')  # Invalid UTF-8 bytes
            f.write("Valid end".encode('utf-8'))

        # Initialize components
        cache_path = temp_workspace / "error_test.db"
        cache_manager = CacheManager(cache_path)
        cache_manager.initialize_cache()

        indexer = Indexer(cache_manager=cache_manager)

        # Should handle errors gracefully
        indexer.index_directory(temp_workspace)

        query_engine = QueryEngine(cache_manager=cache_manager)
        result = query_engine.execute_query("SELECT COUNT(*) as count FROM files")

        # Should still index valid files
        assert result.rows[0]['count'] > 0, "Should index valid files despite errors"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])