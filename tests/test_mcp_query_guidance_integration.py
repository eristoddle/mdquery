"""
Integration tests for MCP query guidance tools.

Tests the MCP server integration of the query guidance system
to ensure all tools work correctly through the MCP interface.
"""

import pytest
import json
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from mdquery.mcp import MDQueryMCPServer
from mdquery.config import SimplifiedConfig


class TestMCPQueryGuidanceIntegration:
    """Test MCP server integration for query guidance tools."""

    @pytest.fixture
    def mcp_server(self, tmp_path):
        """Create a test MCP server with simplified configuration."""
        # Create test notes directory
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()

        # Create a simple test file
        test_file = notes_dir / "test.md"
        test_file.write_text("""---
title: Test Note
tags: [ai, llm, coding]
---

# Test Note

This is a test note about AI development.

#mcp #agent #automation
""")

        # Create simplified config
        config = SimplifiedConfig(
            notes_dir=str(notes_dir),
            auto_index=True
        )

        # Create MCP server
        server = MDQueryMCPServer(config=config)

        # Mock the server.run method to avoid actually starting the server
        server.run = AsyncMock()

        return server

    @pytest.mark.asyncio
    async def test_get_query_guidance_tool(self, mcp_server):
        """Test the get_query_guidance MCP tool."""
        # Initialize the server components
        await mcp_server._ensure_initialized()

        # Find the get_query_guidance tool
        guidance_tool = None
        for tool_name, tool_func in mcp_server.server._tools.items():
            if tool_name == "get_query_guidance":
                guidance_tool = tool_func
                break

        assert guidance_tool is not None, "get_query_guidance tool not found"

        # Test the tool with tag analysis
        result = await guidance_tool(
            analysis_type="tag-analysis",
            content_description="AI development notes"
        )

        # Parse the JSON result
        result_data = json.loads(result)

        # Verify the structure
        assert "analysis_type" in result_data
        assert "suggested_queries" in result_data
        assert "optimization_tips" in result_data
        assert "common_patterns" in result_data
        assert "syntax_reference" in result_data
        assert "examples" in result_data

        assert result_data["analysis_type"] == "tag-analysis"
        assert len(result_data["suggested_queries"]) > 0
        assert len(result_data["optimization_tips"]) > 0
        assert len(result_data["examples"]) > 0

        # Check that tag-related templates are included
        tag_templates = [t for t in result_data["suggested_queries"] if "tag" in t["name"].lower()]
        assert len(tag_templates) > 0

    @pytest.mark.asyncio
    async def test_get_query_templates_tool(self, mcp_server):
        """Test the get_query_templates MCP tool."""
        # Initialize the server components
        await mcp_server._ensure_initialized()

        # Find the get_query_templates tool
        templates_tool = None
        for tool_name, tool_func in mcp_server.server._tools.items():
            if tool_name == "get_query_templates":
                templates_tool = tool_func
                break

        assert templates_tool is not None, "get_query_templates tool not found"

        # Test the tool with category filter
        result = await templates_tool(category="tag-analysis")

        # Parse the JSON result
        result_data = json.loads(result)

        # Verify the structure
        assert "filter_category" in result_data
        assert "template_count" in result_data
        assert "templates" in result_data

        assert result_data["filter_category"] == "tag-analysis"
        assert result_data["template_count"] > 0
        assert len(result_data["templates"]) > 0

        # Verify template structure
        for template in result_data["templates"]:
            assert "name" in template
            assert "description" in template
            assert "category" in template
            assert "sql_template" in template
            assert "parameters" in template
            assert "complexity" in template
            assert template["category"] == "tag-analysis"

    @pytest.mark.asyncio
    async def test_get_query_optimization_suggestions_tool(self, mcp_server):
        """Test the get_query_optimization_suggestions MCP tool."""
        # Initialize the server components
        await mcp_server._ensure_initialized()

        # Find the optimization tool
        optimization_tool = None
        for tool_name, tool_func in mcp_server.server._tools.items():
            if tool_name == "get_query_optimization_suggestions":
                optimization_tool = tool_func
                break

        assert optimization_tool is not None, "get_query_optimization_suggestions tool not found"

        # Test with a query that needs optimization
        bad_query = "SELECT * FROM files WHERE content LIKE '%python%'"
        result = await optimization_tool(query=bad_query)

        # Parse the JSON result
        result_data = json.loads(result)

        # Verify the structure
        assert "analyzed_query" in result_data
        assert "suggestion_count" in result_data
        assert "suggestions" in result_data

        assert result_data["analyzed_query"] == bad_query
        assert result_data["suggestion_count"] > 0
        assert len(result_data["suggestions"]) > 0

        # Verify suggestion structure
        for suggestion in result_data["suggestions"]:
            assert "issue" in suggestion
            assert "suggestion" in suggestion
            assert "example_before" in suggestion
            assert "example_after" in suggestion
            assert "performance_impact" in suggestion

        # Should suggest FTS for this query
        fts_suggestion = next((s for s in result_data["suggestions"] if 'fts' in s["suggestion"].lower()), None)
        assert fts_suggestion is not None

    @pytest.mark.asyncio
    async def test_get_query_syntax_reference_tool(self, mcp_server):
        """Test the get_query_syntax_reference MCP tool."""
        # Initialize the server components
        await mcp_server._ensure_initialized()

        # Find the syntax reference tool
        syntax_tool = None
        for tool_name, tool_func in mcp_server.server._tools.items():
            if tool_name == "get_query_syntax_reference":
                syntax_tool = tool_func
                break

        assert syntax_tool is not None, "get_query_syntax_reference tool not found"

        # Test the tool
        result = await syntax_tool()

        # Parse the JSON result
        result_data = json.loads(result)

        # Verify the structure
        assert "syntax_reference" in result_data
        assert "common_patterns" in result_data
        assert "quick_reference" in result_data

        # Check syntax reference structure
        syntax_ref = result_data["syntax_reference"]
        assert "tables" in syntax_ref
        assert "operators" in syntax_ref
        assert "functions" in syntax_ref
        assert "fts_syntax" in syntax_ref

        # Check that expected tables are documented
        tables = syntax_ref["tables"]
        expected_tables = ["files", "tags", "frontmatter", "links", "content_fts"]
        for table in expected_tables:
            assert table in tables

        # Check quick reference
        quick_ref = result_data["quick_reference"]
        assert "basic_query" in quick_ref
        assert "tag_search" in quick_ref
        assert "text_search" in quick_ref

    @pytest.mark.asyncio
    async def test_workflow_analysis_guidance(self, mcp_server):
        """Test getting guidance specifically for workflow analysis."""
        # Initialize the server components
        await mcp_server._ensure_initialized()

        # Find the get_query_guidance tool
        guidance_tool = None
        for tool_name, tool_func in mcp_server.server._tools.items():
            if tool_name == "get_query_guidance":
                guidance_tool = tool_func
                break

        assert guidance_tool is not None

        # Test with workflow analysis
        result = await guidance_tool(
            analysis_type="workflow",
            content_description="AI development process analysis"
        )

        # Parse the JSON result
        result_data = json.loads(result)

        # Should include workflow-specific templates
        workflow_templates = [t for t in result_data["suggested_queries"] if "workflow" in t["category"].lower()]
        assert len(workflow_templates) > 0

        # Should include workflow-specific tips
        workflow_tips = [tip for tip in result_data["optimization_tips"] if "workflow" in tip.lower()]
        assert len(workflow_tips) > 0

    @pytest.mark.asyncio
    async def test_template_complexity_filtering(self, mcp_server):
        """Test filtering templates by complexity level."""
        # Initialize the server components
        await mcp_server._ensure_initialized()

        # Find the get_query_templates tool
        templates_tool = None
        for tool_name, tool_func in mcp_server.server._tools.items():
            if tool_name == "get_query_templates":
                templates_tool = tool_func
                break

        assert templates_tool is not None

        # Test basic complexity
        result = await templates_tool(complexity="basic")
        result_data = json.loads(result)

        assert result_data["filter_complexity"] == "basic"
        assert len(result_data["templates"]) > 0

        # All templates should be basic complexity
        for template in result_data["templates"]:
            assert template["complexity"] == "basic"

        # Test advanced complexity
        result = await templates_tool(complexity="advanced")
        result_data = json.loads(result)

        assert result_data["filter_complexity"] == "advanced"

        # All templates should be advanced complexity
        for template in result_data["templates"]:
            assert template["complexity"] == "advanced"

    @pytest.mark.asyncio
    async def test_optimization_for_good_query(self, mcp_server):
        """Test optimization suggestions for a well-optimized query."""
        # Initialize the server components
        await mcp_server._ensure_initialized()

        # Find the optimization tool
        optimization_tool = None
        for tool_name, tool_func in mcp_server.server._tools.items():
            if tool_name == "get_query_optimization_suggestions":
                optimization_tool = tool_func
                break

        assert optimization_tool is not None

        # Test with a well-optimized query
        good_query = """SELECT f.filename, COUNT(t.tag) as tag_count
                       FROM files f
                       JOIN tags t ON f.id = t.file_id
                       WHERE t.tag IN ('ai', 'llm')
                       GROUP BY f.id
                       ORDER BY tag_count DESC
                       LIMIT 20"""

        result = await optimization_tool(query=good_query)
        result_data = json.loads(result)

        # Should have few or no suggestions, or include general tips
        if result_data["suggestion_count"] == 0:
            assert "general_tips" in result_data
            assert len(result_data["general_tips"]) > 0
        else:
            # Any suggestions should be minor
            assert result_data["suggestion_count"] <= 2


if __name__ == "__main__":
    pytest.main([__file__])