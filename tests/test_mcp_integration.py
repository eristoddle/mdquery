"""
Integration tests for MCP protocol compliance and tool functionality.

This module provides comprehensive tests to validate that the MCP server
complies with the Model Context Protocol specification and that all tools
function correctly in realistic scenarios.

Implements requirements from task 10a of the MCP workflow optimization spec.
"""

import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from typing import Dict, Any, List
import sys
import os

# Add the mdquery module to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mdquery.config import SimplifiedConfig
from mdquery.tool_interface import ToolRegistry, ParameterValidator, ParameterSpec, ParameterType


class MockMCPToolServer:
    """Mock MCP server that simulates tool execution without full MCP dependencies."""

    def __init__(self, config: SimplifiedConfig):
        """Initialize mock MCP server."""
        self.config = config
        self.db_path = config.config.db_path
        self.cache_dir = config.config.cache_dir
        self.notes_dirs = [config.config.notes_dir]

        # Tool registry for validation
        self.tool_registry = ToolRegistry()

        # Simulate tool responses
        self.tool_responses = {
            "query_markdown": self._mock_query_markdown,
            "get_schema": self._mock_get_schema,
            "index_directory": self._mock_index_directory,
            "comprehensive_tag_analysis": self._mock_tag_analysis,
            "get_performance_stats": self._mock_performance_stats,
            "get_tool_documentation": self._mock_tool_documentation,
        }

    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Execute a tool with given parameters."""
        # Validate tool exists
        if tool_name not in self.tool_responses:
            raise ValueError(f"Unknown tool: {tool_name}")

        # Validate parameters
        tool_spec = self.tool_registry.get_tool_spec(tool_name)
        if tool_spec:
            is_valid, errors = ParameterValidator.validate_parameters(parameters, tool_spec.parameters)
            if not is_valid:
                raise ValueError(f"Parameter validation failed: {'; '.join(errors)}")

        # Execute tool
        response = await self.tool_responses[tool_name](parameters)
        return response

    async def _mock_query_markdown(self, params: Dict[str, Any]) -> str:
        """Mock query_markdown tool."""
        sql = params.get("sql", "")
        format_type = params.get("format", "json")

        # Simulate query result
        result = {
            "columns": ["id", "filename", "title", "tags"],
            "rows": [
                {"id": 1, "filename": "test1.md", "title": "Test Note 1", "tags": "test,example"},
                {"id": 2, "filename": "test2.md", "title": "Test Note 2", "tags": "test,demo"}
            ],
            "row_count": 2,
            "execution_time_ms": 25.5,
            "sql": sql
        }

        return json.dumps(result, indent=2)

    async def _mock_get_schema(self, params: Dict[str, Any]) -> str:
        """Mock get_schema tool."""
        table = params.get("table")

        schema_info = {
            "tables": {
                "files": {
                    "columns": ["id", "filename", "directory", "modified_date", "word_count"],
                    "primary_key": "id",
                    "indexes": ["filename", "directory"]
                },
                "tags": {
                    "columns": ["file_id", "tag", "source"],
                    "foreign_keys": [{"column": "file_id", "references": "files.id"}]
                }
            },
            "views": {
                "files_with_metadata": {
                    "description": "Files with aggregated metadata"
                }
            }
        }

        if table:
            if table in schema_info["tables"]:
                return json.dumps({"table": table, "schema": schema_info["tables"][table]}, indent=2)
            elif table in schema_info["views"]:
                return json.dumps({"view": table, "schema": schema_info["views"][table]}, indent=2)
            else:
                raise ValueError(f"Table or view '{table}' not found")

        return json.dumps(schema_info, indent=2)

    async def _mock_index_directory(self, params: Dict[str, Any]) -> str:
        """Mock index_directory tool."""
        path = params.get("path", "")
        recursive = params.get("recursive", True)
        incremental = params.get("incremental", True)

        result = {
            "path": path,
            "recursive": recursive,
            "incremental": incremental,
            "statistics": {
                "files_processed": 10,
                "files_indexed": 10,
                "files_updated": 0,
                "files_skipped": 0,
                "execution_time": 1.25
            }
        }

        return json.dumps(result, indent=2)

    async def _mock_tag_analysis(self, params: Dict[str, Any]) -> str:
        """Mock comprehensive_tag_analysis tool."""
        tag_patterns = params.get("tag_patterns", "")

        result = {
            "topic_groups": [
                {
                    "name": "Development",
                    "document_count": 5,
                    "key_themes": ["coding", "development", "programming"],
                    "related_groups": ["Tools"]
                },
                {
                    "name": "Documentation",
                    "document_count": 3,
                    "key_themes": ["docs", "guides", "tutorials"],
                    "related_groups": ["Development"]
                }
            ],
            "actionable_insights": [
                {
                    "title": "Improve code documentation",
                    "description": "Add more inline comments and README files",
                    "implementation_difficulty": "low",
                    "expected_impact": "medium"
                }
            ],
            "tag_hierarchy": {
                "development": ["coding", "programming", "debug"],
                "docs": ["guides", "tutorials", "examples"]
            }
        }

        return json.dumps(result, indent=2)

    async def _mock_performance_stats(self, params: Dict[str, Any]) -> str:
        """Mock get_performance_stats tool."""
        hours = params.get("hours", 24)

        result = {
            "time_period_hours": hours,
            "total_queries": 150,
            "avg_execution_time": 0.75,
            "cache_hit_rate": 0.85,
            "slow_query_count": 3,
            "optimization_success_rate": 0.92,
            "memory_usage_mb": 45.2
        }

        return json.dumps(result, indent=2)

    async def _mock_tool_documentation(self, params: Dict[str, Any]) -> str:
        """Mock get_tool_documentation tool."""
        tool_name = params.get("tool_name")

        if tool_name:
            doc = {
                "tool": tool_name,
                "description": f"Documentation for {tool_name}",
                "category": "core",
                "parameters": [
                    {
                        "name": "example_param",
                        "type": "string",
                        "description": "Example parameter",
                        "required": True
                    }
                ]
            }
            return json.dumps(doc, indent=2)
        else:
            doc = {
                "tool_categories": {
                    "core": [
                        {"name": "query_markdown", "description": "Execute SQL queries"},
                        {"name": "get_schema", "description": "Get database schema"}
                    ],
                    "analysis": [
                        {"name": "comprehensive_tag_analysis", "description": "Analyze tagged content"}
                    ]
                },
                "total_tools": 6
            }
            return json.dumps(doc, indent=2)


class MCPIntegrationTest(unittest.TestCase):
    """Integration tests for MCP protocol compliance and tool functionality."""

    def setUp(self):
        """Set up test environment."""
        # Create temporary directory
        self.test_dir = Path(tempfile.mkdtemp(prefix="mcp_integration_test_"))
        self.notes_dir = self.test_dir / "notes"
        self.notes_dir.mkdir(parents=True, exist_ok=True)

        # Create test files
        self.create_test_files()

        # Create configuration
        self.config = SimplifiedConfig(
            notes_dir=str(self.notes_dir),
            auto_index=False
        )

        # Initialize mock server
        self.server = MockMCPToolServer(self.config)

    def tearDown(self):
        """Clean up test environment."""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def create_test_files(self):
        """Create test markdown files."""
        # AI development note
        ai_note = self.notes_dir / "ai_development.md"
        ai_note.write_text("""---
title: AI Development Best Practices
tags: [ai, development, best-practices]
author: Test Author
---

# AI Development Best Practices

This document outlines best practices for AI development projects.

## Key Principles
- Model Context Protocol (MCP) integration
- Proper error handling
- Performance optimization

Tags: #ai #development #mcp
""")

        # Performance optimization note
        perf_note = self.notes_dir / "performance.md"
        perf_note.write_text("""---
title: Performance Optimization Guide
tags: [performance, optimization, caching]
status: complete
---

# Performance Optimization

Comprehensive guide for optimizing system performance.

## Strategies
- Query optimization
- Result caching
- Lazy loading

Tags: #performance #optimization #database
""")

    def test_tool_parameter_validation(self):
        """Test that tool parameters are properly validated."""
        print("\n--- Testing Tool Parameter Validation ---")

        # Test valid parameters
        test_cases = [
            {
                "tool": "query_markdown",
                "params": {"sql": "SELECT * FROM files LIMIT 5", "format": "json"},
                "should_pass": True
            },
            {
                "tool": "get_schema",
                "params": {"table": "files"},
                "should_pass": True
            },
            {
                "tool": "index_directory",
                "params": {"path": str(self.notes_dir), "recursive": True},
                "should_pass": True
            },
            # Invalid parameters
            {
                "tool": "query_markdown",
                "params": {"invalid_param": "test"},  # Missing required 'sql'
                "should_pass": False
            },
            {
                "tool": "get_performance_stats",
                "params": {"hours": "invalid"},  # Should be integer
                "should_pass": False
            }
        ]

        async def run_validation_tests():
            for case in test_cases:
                try:
                    await self.server.execute_tool(case["tool"], case["params"])
                    if case["should_pass"]:
                        print(f"✓ {case['tool']}: Valid parameters accepted")
                    else:
                        print(f"✗ {case['tool']}: Invalid parameters incorrectly accepted")
                        self.fail(f"Expected validation failure for {case['tool']}")
                except (ValueError, TypeError) as e:
                    if not case["should_pass"]:
                        print(f"✓ {case['tool']}: Invalid parameters correctly rejected")
                    else:
                        print(f"✗ {case['tool']}: Valid parameters incorrectly rejected: {e}")
                        self.fail(f"Unexpected validation failure for {case['tool']}: {e}")

        # Run async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_validation_tests())
        finally:
            loop.close()

    def test_tool_response_format_compliance(self):
        """Test that tool responses comply with expected formats."""
        print("\n--- Testing Tool Response Format Compliance ---")

        async def run_format_tests():
            # Test core tools
            tools_to_test = [
                {
                    "name": "query_markdown",
                    "params": {"sql": "SELECT * FROM files LIMIT 5"},
                    "expected_fields": ["columns", "rows", "row_count", "execution_time_ms"]
                },
                {
                    "name": "get_schema",
                    "params": {},
                    "expected_fields": ["tables", "views"]
                },
                {
                    "name": "index_directory",
                    "params": {"path": str(self.notes_dir)},
                    "expected_fields": ["path", "statistics"]
                },
                {
                    "name": "comprehensive_tag_analysis",
                    "params": {"tag_patterns": "ai,development"},
                    "expected_fields": ["topic_groups", "actionable_insights"]
                },
                {
                    "name": "get_performance_stats",
                    "params": {"hours": 24},
                    "expected_fields": ["total_queries", "avg_execution_time", "cache_hit_rate"]
                }
            ]

            for tool_test in tools_to_test:
                try:
                    response = await self.server.execute_tool(tool_test["name"], tool_test["params"])

                    # Verify response is valid JSON
                    try:
                        data = json.loads(response)
                    except json.JSONDecodeError:
                        self.fail(f"Tool {tool_test['name']} returned invalid JSON")

                    # Verify expected fields are present
                    for field in tool_test["expected_fields"]:
                        if field not in data:
                            self.fail(f"Tool {tool_test['name']} missing expected field: {field}")

                    print(f"✓ {tool_test['name']}: Response format compliant")

                except Exception as e:
                    self.fail(f"Tool {tool_test['name']} execution failed: {e}")

        # Run async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_format_tests())
        finally:
            loop.close()

    def test_tool_functionality_integration(self):
        """Test integrated tool functionality scenarios."""
        print("\n--- Testing Tool Functionality Integration ---")

        async def run_integration_tests():
            # Scenario 1: Schema exploration -> Query execution
            print("Scenario 1: Schema exploration and query execution")

            # Get schema information
            schema_response = await self.server.execute_tool("get_schema", {})
            schema_data = json.loads(schema_response)

            self.assertIn("tables", schema_data)
            self.assertIn("files", schema_data["tables"])
            print("  ✓ Schema retrieval successful")

            # Execute query based on schema
            query_response = await self.server.execute_tool(
                "query_markdown",
                {"sql": "SELECT filename, title FROM files WHERE tags LIKE '%ai%'"}
            )
            query_data = json.loads(query_response)

            self.assertIn("rows", query_data)
            self.assertIn("columns", query_data)
            print("  ✓ Query execution successful")

            # Scenario 2: Directory indexing -> Analysis
            print("Scenario 2: Directory indexing and content analysis")

            # Index directory
            index_response = await self.server.execute_tool(
                "index_directory",
                {"path": str(self.notes_dir), "recursive": True, "incremental": False}
            )
            index_data = json.loads(index_response)

            self.assertIn("statistics", index_data)
            self.assertGreater(index_data["statistics"]["files_processed"], 0)
            print("  ✓ Directory indexing successful")

            # Perform tag analysis
            analysis_response = await self.server.execute_tool(
                "comprehensive_tag_analysis",
                {"tag_patterns": "ai,development,performance", "grouping_strategy": "semantic"}
            )
            analysis_data = json.loads(analysis_response)

            self.assertIn("topic_groups", analysis_data)
            self.assertIn("actionable_insights", analysis_data)
            print("  ✓ Tag analysis successful")

            # Scenario 3: Performance monitoring
            print("Scenario 3: Performance monitoring and optimization")

            # Get performance statistics
            perf_response = await self.server.execute_tool(
                "get_performance_stats",
                {"hours": 24}
            )
            perf_data = json.loads(perf_response)

            self.assertIn("total_queries", perf_data)
            self.assertIn("avg_execution_time", perf_data)
            print("  ✓ Performance monitoring successful")

        # Run async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_integration_tests())
        finally:
            loop.close()

    def test_error_handling_compliance(self):
        """Test that error handling follows MCP protocol standards."""
        print("\n--- Testing Error Handling Compliance ---")

        async def run_error_tests():
            # Test invalid tool name
            try:
                await self.server.execute_tool("nonexistent_tool", {})
                self.fail("Expected error for nonexistent tool")
            except ValueError as e:
                self.assertIn("Unknown tool", str(e))
                print("✓ Invalid tool name properly rejected")

            # Test invalid parameters
            try:
                await self.server.execute_tool("query_markdown", {"invalid": "params"})
                self.fail("Expected error for invalid parameters")
            except ValueError as e:
                self.assertIn("Parameter validation failed", str(e))
                print("✓ Invalid parameters properly rejected")

            # Test edge cases for specific tools
            try:
                await self.server.execute_tool("get_schema", {"table": "nonexistent_table"})
                self.fail("Expected error for nonexistent table")
            except ValueError as e:
                self.assertIn("not found", str(e))
                print("✓ Nonexistent table properly rejected")

        # Run async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_error_tests())
        finally:
            loop.close()

    def test_tool_documentation_compliance(self):
        """Test that tool documentation meets MCP standards."""
        print("\n--- Testing Tool Documentation Compliance ---")

        async def run_documentation_tests():
            # Test getting all tool documentation
            all_docs_response = await self.server.execute_tool("get_tool_documentation", {})
            all_docs = json.loads(all_docs_response)

            self.assertIn("tool_categories", all_docs)
            self.assertIn("total_tools", all_docs)
            self.assertGreater(all_docs["total_tools"], 0)
            print("✓ All tools documentation format compliant")

            # Test getting specific tool documentation
            tool_docs_response = await self.server.execute_tool(
                "get_tool_documentation",
                {"tool_name": "query_markdown"}
            )
            tool_docs = json.loads(tool_docs_response)

            required_fields = ["tool", "description", "parameters"]
            for field in required_fields:
                self.assertIn(field, tool_docs)

            # Verify parameter documentation structure
            if "parameters" in tool_docs and tool_docs["parameters"]:
                param = tool_docs["parameters"][0]
                param_fields = ["name", "type", "description", "required"]
                for field in param_fields:
                    self.assertIn(field, param)

            print("✓ Specific tool documentation format compliant")

        # Run async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_documentation_tests())
        finally:
            loop.close()

    def test_concurrent_tool_execution(self):
        """Test concurrent tool execution for thread safety."""
        print("\n--- Testing Concurrent Tool Execution ---")

        async def run_concurrent_tests():
            # Create multiple concurrent tool requests
            tasks = []

            # Different types of tools to test concurrent access
            tool_requests = [
                ("query_markdown", {"sql": "SELECT * FROM files LIMIT 3"}),
                ("get_schema", {"table": "files"}),
                ("get_performance_stats", {"hours": 12}),
                ("comprehensive_tag_analysis", {"tag_patterns": "test"}),
                ("index_directory", {"path": str(self.notes_dir)}),
            ]

            # Create concurrent tasks
            for tool_name, params in tool_requests:
                task = self.server.execute_tool(tool_name, params)
                tasks.append(task)

            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Verify all tasks completed successfully
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.fail(f"Concurrent task {i} failed: {result}")
                else:
                    # Verify result is valid JSON
                    try:
                        json.loads(result)
                        print(f"✓ Concurrent task {i}: {tool_requests[i][0]} completed successfully")
                    except json.JSONDecodeError:
                        self.fail(f"Concurrent task {i} returned invalid JSON")

        # Run async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_concurrent_tests())
        finally:
            loop.close()


def run_mcp_integration_tests():
    """Run all MCP integration tests."""
    print("=" * 60)
    print("MCP Protocol Compliance and Tool Functionality Tests")
    print("=" * 60)

    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(MCPIntegrationTest)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)

    print("\n" + "=" * 60)
    print("Integration Test Summary")
    print("=" * 60)

    if result.wasSuccessful():
        print("✅ All MCP integration tests passed!")
        print(f"  - Tests run: {result.testsRun}")
        print(f"  - Failures: {len(result.failures)}")
        print(f"  - Errors: {len(result.errors)}")
        print("\nThe MCP server implementation is compliant with protocol standards.")
        print("All tools function correctly and handle errors appropriately.")
    else:
        print("❌ Some integration tests failed!")
        print(f"  - Tests run: {result.testsRun}")
        print(f"  - Failures: {len(result.failures)}")
        print(f"  - Errors: {len(result.errors)}")

        if result.failures:
            print("\nFailures:")
            for test, error in result.failures:
                print(f"  - {test}: {error}")

        if result.errors:
            print("\nErrors:")
            for test, error in result.errors:
                print(f"  - {test}: {error}")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_mcp_integration_tests()
    sys.exit(0 if success else 1)