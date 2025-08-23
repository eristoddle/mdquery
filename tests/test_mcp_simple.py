"""
Simple MCP server tests to verify basic functionality.
"""

import asyncio
import json
import pytest
import tempfile
from pathlib import Path

from mdquery.mcp import MDQueryMCPServer, MCPServerError
from mcp.server.fastmcp.exceptions import ToolError


@pytest.mark.asyncio
async def test_mcp_server_basic_functionality():
    """Test basic MCP server functionality."""
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)

    try:
        # Create server
        server = MDQueryMCPServer(db_path=db_path)

        # Test initialization
        await server._ensure_initialized()
        assert server.db_manager is not None
        assert server.query_engine is not None
        assert server.indexer is not None

        # Test schema tool
        result = await server.server.call_tool("get_schema", {})
        # FastMCP returns a tuple (content, metadata)
        content, metadata = result
        schema_data = json.loads(metadata['result'])
        assert "tables" in schema_data
        assert "files" in schema_data["tables"]

        # Test query tool (should work even with empty database)
        result = await server.server.call_tool(
            "query_markdown",
            {"sql": "SELECT COUNT(*) as count FROM files", "format": "json"}
        )
        # FastMCP returns a tuple (content, metadata)
        content, metadata = result
        query_data = json.loads(metadata['result'])
        assert "rows" in query_data

        # Cleanup
        await server.shutdown()

    finally:
        # Cleanup database file
        if db_path.exists():
            db_path.unlink()


@pytest.mark.asyncio
async def test_mcp_server_with_files():
    """Test MCP server with actual markdown files."""
    # Create temporary database and files
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)

    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir)

        # Create test markdown file
        test_file = test_dir / "test.md"
        test_file.write_text("""---
title: "Test Note"
tags: [test]
---

# Test Note

This is a test note.
""")

        try:
            # Create server
            server = MDQueryMCPServer(db_path=db_path)

            # Index the directory
            result = await server.server.call_tool(
                "index_directory",
                {"path": str(test_dir), "recursive": True, "incremental": False}
            )

            content, metadata = result
            index_data = json.loads(metadata['result'])
            assert "statistics" in index_data
            assert index_data["statistics"]["files_processed"] == 1

            # Query the indexed file
            result = await server.server.call_tool(
                "query_markdown",
                {"sql": "SELECT filename, title FROM files_with_metadata", "format": "json"}
            )

            content, metadata = result
            query_data = json.loads(metadata['result'])
            assert len(query_data["rows"]) == 1
            assert query_data["rows"][0]["filename"] == "test.md"

            # Get file content
            result = await server.server.call_tool(
                "get_file_content",
                {"file_path": str(test_file), "include_parsed": True}
            )

            content, metadata = result
            content_data = json.loads(metadata['result'])
            assert "content" in content_data
            assert "Test Note" in content_data["content"]
            assert "parsed" in content_data

            # Cleanup
            await server.shutdown()

        finally:
            # Cleanup database file
            if db_path.exists():
                db_path.unlink()


@pytest.mark.asyncio
async def test_mcp_server_error_handling():
    """Test MCP server error handling."""
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)

    try:
        # Create server
        server = MDQueryMCPServer(db_path=db_path)

        # Test invalid SQL query - should raise ToolError (wrapped MCPServerError)
        with pytest.raises(ToolError):
            await server.server.call_tool(
                "query_markdown",
                {"sql": "INVALID SQL", "format": "json"}
            )

        # Test nonexistent file - should raise ToolError (wrapped MCPServerError)
        with pytest.raises(ToolError):
            await server.server.call_tool(
                "get_file_content",
                {"file_path": "/nonexistent/file.md"}
            )

        # Test nonexistent directory - should raise ToolError (wrapped MCPServerError)
        with pytest.raises(ToolError):
            await server.server.call_tool(
                "index_directory",
                {"path": "/nonexistent/directory"}
            )

        # Cleanup
        await server.shutdown()

    finally:
        # Cleanup database file
        if db_path.exists():
            db_path.unlink()


@pytest.mark.asyncio
async def test_mcp_server_concurrent_operations():
    """Test concurrent operations on MCP server."""
    # Create temporary database and files
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)

    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir)

        # Create multiple test files
        for i in range(3):
            test_file = test_dir / f"test{i}.md"
            test_file.write_text(f"""---
title: "Test Note {i}"
tags: [test{i}]
---

# Test Note {i}

This is test note {i}.
""")

        try:
            # Create server
            server = MDQueryMCPServer(db_path=db_path)

            # Index the directory
            await server.server.call_tool(
                "index_directory",
                {"path": str(test_dir), "recursive": True, "incremental": False}
            )

            # Run multiple concurrent queries
            tasks = []
            for i in range(5):
                task = server.server.call_tool(
                    "query_markdown",
                    {"sql": f"SELECT COUNT(*) as count FROM files", "format": "json"}
                )
                tasks.append(task)

            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # All should succeed
            for result in results:
                assert not isinstance(result, Exception)
                content, metadata = result
                query_data = json.loads(metadata['result'])
                assert query_data["rows"][0]["count"] == 3

            # Cleanup
            await server.shutdown()

        finally:
            # Cleanup database file
            if db_path.exists():
                db_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__])