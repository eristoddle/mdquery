"""
Integration tests for MCP server functionality and protocol compliance.

Tests the MCP server interface, tool functionality, error handling,
and concurrent request handling.
"""

import asyncio
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from mdquery.mcp import MDQueryMCPServer, MCPServer, MCPServerError
from mdquery.database import create_database
from mdquery.indexer import Indexer
from mdquery.query import QueryEngine
from mdquery.cache import CacheManager


class TestMCPServerIntegration:
    """Integration tests for MCP server functionality."""

    @pytest.fixture
    async def temp_db_path(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)

        yield db_path

        # Cleanup
        if db_path.exists():
            db_path.unlink()

    @pytest.fixture
    async def temp_cache_dir(self):
        """Create temporary cache directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    async def mcp_server(self, temp_db_path, temp_cache_dir):
        """Create MCP server instance for testing."""
        server = MDQueryMCPServer(db_path=temp_db_path, cache_dir=temp_cache_dir)
        yield server
        await server.shutdown()

    @pytest.fixture
    async def sample_markdown_files(self, tmp_path):
        """Create sample markdown files for testing."""
        # Create test directory structure
        test_dir = tmp_path / "test_notes"
        test_dir.mkdir()

        # Create sample files
        file1 = test_dir / "note1.md"
        file1.write_text("""---
title: "Test Note 1"
tags: [research, testing]
category: documentation
---

# Test Note 1

This is a test note with some content.

## Section 1

Some content here with a #hashtag.

[Link to note2](note2.md)
""")

        file2 = test_dir / "note2.md"
        file2.write_text("""---
title: "Test Note 2"
tags: [testing, examples]
author: "Test Author"
---

# Test Note 2

Another test note.

[[note1]] is a wikilink reference.
""")

        return test_dir

    async def test_server_initialization(self, mcp_server):
        """Test MCP server initialization."""
        # Server should initialize components on first use
        await mcp_server._ensure_initialized()

        assert mcp_server.db_manager is not None
        assert mcp_server.query_engine is not None
        assert mcp_server.indexer is not None
        assert mcp_server.cache_manager is not None

    async def test_list_tools(self, mcp_server):
        """Test listing available tools."""
        # Check that tools are registered with FastMCP
        tools = mcp_server.server.list_tools()

        assert len(tools) == 4
        tool_names = [tool.name for tool in tools]
        assert "query_markdown" in tool_names
        assert "get_schema" in tool_names
        assert "index_directory" in tool_names
        assert "get_file_content" in tool_names

    async def test_index_directory_tool(self, mcp_server, sample_markdown_files):
        """Test index_directory tool functionality."""
        # Call the tool directly
        result = await mcp_server.server.call_tool(
            "index_directory",
            {
                "path": str(sample_markdown_files),
                "recursive": True,
                "incremental": False
            }
        )

        # Parse the result
        result_data = json.loads(result)
        assert "statistics" in result_data
        assert result_data["statistics"]["files_processed"] == 2

    async def test_query_markdown_tool(self, mcp_server, sample_markdown_files):
        """Test query_markdown tool functionality."""
        # First index the files
        await mcp_server.server.call_tool(
            "index_directory",
            {
                "path": str(sample_markdown_files),
                "recursive": True,
                "incremental": False
            }
        )

        # Test query
        result = await mcp_server.server.call_tool(
            "query_markdown",
            {
                "sql": "SELECT filename, title FROM files_with_metadata ORDER BY filename",
                "format": "json"
            }
        )

        # Parse the result
        result_data = json.loads(result)
        assert "rows" in result_data
        assert len(result_data["rows"]) == 2

    async def test_get_schema_tool(self, mcp_server):
        """Test get_schema tool functionality."""
        await mcp_server._ensure_initialized()

        # Test getting full schema
        result = await mcp_server.server.call_tool("get_schema", {})

        # Parse the result
        schema_data = json.loads(result)
        assert "tables" in schema_data
        assert "files" in schema_data["tables"]

    async def test_get_schema_tool_specific_table(self, mcp_server):
        """Test get_schema tool with specific table."""
        await mcp_server._ensure_initialized()

        # Test getting specific table schema
        result = await mcp_server.server.call_tool("get_schema", {"table": "files"})

        result_data = json.loads(result)
        assert "table" in result_data
        assert result_data["table"] == "files"

    async def test_get_file_content_tool(self, mcp_server, sample_markdown_files):
        """Test get_file_content tool functionality."""
        file_path = sample_markdown_files / "note1.md"

        # Test basic file content retrieval
        result = await mcp_server.server.call_tool(
            "get_file_content",
            {
                "file_path": str(file_path),
                "include_parsed": False
            }
        )

        result_data = json.loads(result)
        assert "content" in result_data
        assert "metadata" in result_data
        assert "Test Note 1" in result_data["content"]

    async def test_get_file_content_with_parsed_data(self, mcp_server, sample_markdown_files):
        """Test get_file_content tool with parsed data."""
        # First index the files
        await mcp_server.server.call_tool(
            "index_directory",
            {
                "path": str(sample_markdown_files),
                "recursive": True,
                "incremental": False
            }
        )

        file_path = sample_markdown_files / "note1.md"

        # Test with parsed data
        result = await mcp_server.server.call_tool(
            "get_file_content",
            {
                "file_path": str(file_path),
                "include_parsed": True
            }
        )

        result_data = json.loads(result)
        assert "parsed" in result_data
        assert "frontmatter" in result_data["parsed"]
        assert "tags" in result_data["parsed"]
        assert "links" in result_data["parsed"]

    async def test_error_handling_invalid_query(self, mcp_server):
        """Test error handling for invalid SQL queries."""
        await mcp_server._ensure_initialized()

        # Test invalid SQL - should raise exception
        with pytest.raises(MCPServerError):
            await mcp_server.server.call_tool(
                "query_markdown",
                {
                    "sql": "INVALID SQL QUERY",
                    "format": "json"
                }
            )

    async def test_error_handling_nonexistent_file(self, mcp_server):
        """Test error handling for nonexistent files."""
        # Should raise exception for nonexistent file
        with pytest.raises(MCPServerError):
            await mcp_server.server.call_tool(
                "get_file_content",
                {
                    "file_path": "/nonexistent/file.md",
                    "include_parsed": False
                }
            )

    async def test_error_handling_nonexistent_directory(self, mcp_server):
        """Test error handling for nonexistent directories."""
        # Should raise exception for nonexistent directory
        with pytest.raises(MCPServerError):
            await mcp_server.server.call_tool(
                "index_directory",
                {
                    "path": "/nonexistent/directory",
                    "recursive": True
                }
            )

    async def test_concurrent_requests(self, mcp_server, sample_markdown_files):
        """Test concurrent request handling."""
        await mcp_server._ensure_initialized()

        # Index files first
        await mcp_server.server.call_tool(
            "index_directory",
            {
                "path": str(sample_markdown_files),
                "recursive": True,
                "incremental": False
            }
        )

        # Create multiple concurrent requests
        tasks = []

        # Query tasks
        for i in range(5):
            task = mcp_server.server.call_tool(
                "query_markdown",
                {
                    "sql": f"SELECT * FROM files LIMIT {i+1}",
                    "format": "json"
                }
            )
            tasks.append(task)

        # Schema tasks
        for i in range(3):
            task = mcp_server.server.call_tool("get_schema", {})
            tasks.append(task)

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check that all requests completed successfully
        for result in results:
            assert not isinstance(result, Exception)

    async def test_thread_safety(self, mcp_server, sample_markdown_files):
        """Test thread safety of MCP server operations."""
        await mcp_server._ensure_initialized()

        # Create multiple tasks that modify and read data
        async def index_task():
            return await mcp_server.server.call_tool(
                "index_directory",
                {
                    "path": str(sample_markdown_files),
                    "recursive": True,
                    "incremental": False
                }
            )

        async def query_task():
            return await mcp_server.server.call_tool(
                "query_markdown",
                {
                    "sql": "SELECT COUNT(*) FROM files",
                    "format": "json"
                }
            )

        # Run indexing and querying concurrently
        index_result, query_result = await asyncio.gather(
            index_task(),
            query_task(),
            return_exceptions=True
        )

        # Both operations should complete without errors
        assert not isinstance(index_result, Exception)
        assert not isinstance(query_result, Exception)

    async def test_query_output_formats(self, mcp_server, sample_markdown_files):
        """Test different query output formats."""
        await mcp_server._ensure_initialized()

        # Index files first
        await mcp_server.server.call_tool(
            "index_directory",
            {
                "path": str(sample_markdown_files),
                "recursive": True,
                "incremental": False
            }
        )

        sql = "SELECT filename FROM files ORDER BY filename"

        # Test different formats
        formats = ["json", "csv", "table", "markdown"]

        for format_type in formats:
            result = await mcp_server.server.call_tool(
                "query_markdown",
                {
                    "sql": sql,
                    "format": format_type
                }
            )

            # Verify format-specific content
            if format_type == "json":
                # Should be valid JSON
                json.loads(result)
            elif format_type == "csv":
                # Should contain CSV headers
                assert "filename" in result
            elif format_type == "table":
                # Should contain table formatting
                assert "|" in result
            elif format_type == "markdown":
                # Should contain markdown table
                assert "|" in result and "---" in result

    async def test_incremental_indexing(self, mcp_server, sample_markdown_files):
        """Test incremental indexing functionality."""
        await mcp_server._ensure_initialized()

        # Initial indexing
        result1 = await mcp_server.server.call_tool(
            "index_directory",
            {
                "path": str(sample_markdown_files),
                "recursive": True,
                "incremental": False
            }
        )
        result1_data = json.loads(result1)

        # Incremental indexing (should skip unchanged files)
        result2 = await mcp_server.server.call_tool(
            "index_directory",
            {
                "path": str(sample_markdown_files),
                "recursive": True,
                "incremental": True
            }
        )
        result2_data = json.loads(result2)

        # Second run should process fewer files (or skip them)
        assert result2_data["statistics"]["files_skipped"] >= 0

    async def test_legacy_compatibility(self, temp_db_path, temp_cache_dir):
        """Test legacy MCPServer class compatibility."""
        legacy_server = MCPServer(db_path=temp_db_path, cache_dir=temp_cache_dir)

        # Test legacy methods
        schema = await legacy_server.get_schema()
        assert isinstance(schema, dict)

        content = await legacy_server.get_file_content("/nonexistent/file.md")
        assert "content" in content
        assert "metadata" in content

    async def test_server_shutdown(self, mcp_server):
        """Test proper server shutdown."""
        await mcp_server._ensure_initialized()

        # Verify components are initialized
        assert mcp_server.db_manager is not None

        # Shutdown server
        await mcp_server.shutdown()

        # Verify cleanup (executor should be shutdown)
        assert mcp_server.executor._shutdown

    @pytest.mark.parametrize("invalid_sql", [
        "DROP TABLE files",
        "DELETE FROM files",
        "INSERT INTO files VALUES (1, 'test')",
        "UPDATE files SET path = 'test'",
        "SELECT * FROM files; DROP TABLE files;",
        "SELECT * FROM nonexistent_table"
    ])
    async def test_sql_injection_protection(self, mcp_server, invalid_sql):
        """Test SQL injection protection."""
        await mcp_server._ensure_initialized()

        # Should raise exception for dangerous queries
        with pytest.raises(MCPServerError):
            await mcp_server.server.call_tool(
                "query_markdown",
                {
                    "sql": invalid_sql,
                    "format": "json"
                }
            )


class TestMCPServerProtocolCompliance:
    """Tests for MCP protocol compliance."""

    @pytest.fixture
    async def mcp_server(self, tmp_path):
        """Create MCP server for protocol testing."""
        db_path = tmp_path / "test.db"
        cache_dir = tmp_path / "cache"
        server = MDQueryMCPServer(db_path=db_path, cache_dir=cache_dir)
        yield server
        await server.shutdown()

    async def test_tool_schema_compliance(self, mcp_server):
        """Test that tool schemas comply with MCP specification."""
        tools = mcp_server.server.list_tools()

        for tool in tools:
            # Each tool should have required fields
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'description')

            # Tool should be callable
            assert callable(tool.func)

    async def test_tool_execution(self, mcp_server):
        """Test that tools can be executed properly."""
        await mcp_server._ensure_initialized()

        # Test with get_schema (simple case)
        result = await mcp_server.server.call_tool("get_schema", {})

        # Result should be a string (JSON)
        assert isinstance(result, str)

        # Should be valid JSON
        schema_data = json.loads(result)
        assert isinstance(schema_data, dict)


if __name__ == "__main__":
    pytest.main([__file__])