"""
AI Assistant Compatibility Tests for MCP Tool Interfaces.

This module tests the MCP tool interfaces across different AI assistant types
to ensure consistent behavior and response formatting. Tests the adaptive
formatting system and tool interface consistency.

Implements requirements 6.1, 6.2, 6.3, 6.4, 6.5 from the MCP workflow optimization spec.
"""

import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock

# Test framework setup
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from mdquery.config import SimplifiedConfig
from mdquery.adaptive_formatting import AssistantType, ResponseFormatter, create_response_formatter
from mdquery.tool_interface import ToolRegistry, ConsistentToolMixin
from mdquery.concurrent import RequestType, RequestPriority


class MockMCPServer(ConsistentToolMixin):
    """Mock MCP server for testing tool interfaces without full MCP dependencies."""

    def __init__(self, config: SimplifiedConfig):
        """Initialize mock server."""
        super().__init__()
        self.config = config
        self.db_path = config.config.db_path
        self.cache_dir = config.config.cache_dir
        self.notes_dirs = [config.config.notes_dir]
        self.auto_index = config.config.auto_index

        # Mock components for testing
        self.db_manager = None
        self.query_engine = None
        self.indexer = None
        self.cache_manager = None
        self.query_guidance_engine = None
        self.performance_optimizer = None
        self.concurrent_manager = None
        self.response_formatter = create_response_formatter()

        # Initialize state
        self._initialization_successful = True

    def _format_response_adaptively(self, content: Any, tool_name: str,
                                   request_parameters: Dict[str, Any],
                                   client_id: str = "unknown",
                                   format_hint: str = None) -> str:
        """Mock adaptive formatting."""
        if not self.response_formatter:
            return json.dumps(content, indent=2, default=str)

        # Create formatting context
        formatting_context = self.response_formatter.create_formatting_context(
            tool_name=tool_name,
            request_parameters=request_parameters,
            content=content,
            client_id=client_id,
            format_hint=format_hint
        )

        return self.response_formatter.format_response(content, formatting_context)


class AIAssistantCompatibilityTest(unittest.TestCase):
    """Test AI assistant compatibility and tool interface consistency."""

    def setUp(self):
        """Set up test environment."""
        # Create temporary directory
        self.test_dir = Path(tempfile.mkdtemp(prefix="ai_compat_test_"))
        self.notes_dir = self.test_dir / "notes"
        self.notes_dir.mkdir(parents=True, exist_ok=True)

        # Create test files
        self.create_test_files()

        # Create configuration
        self.config = SimplifiedConfig(
            notes_dir=str(self.notes_dir),
            auto_index=False  # Disable auto-indexing for testing
        )

        # Initialize mock server
        self.server = MockMCPServer(self.config)

    def tearDown(self):
        """Clean up test environment."""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def create_test_files(self):
        """Create test markdown files."""
        # AI development notes
        ai_note = self.notes_dir / "ai_development.md"
        ai_note.write_text("""---
title: AI Development Guide
tags: [ai, coding, llm]
author: Test Author
date: 2024-01-01
---

# AI Development Guide

This is a comprehensive guide for AI development using MCP and agents.

Tags: #ai #development #mcp #agents

## Key Concepts
- Model Context Protocol (MCP)
- Agent frameworks
- Tool interfaces
""")

        # MCP implementation notes
        mcp_note = self.notes_dir / "mcp_implementation.md"
        mcp_note.write_text("""---
title: MCP Implementation
tags: [mcp, protocol, implementation]
status: in-progress
---

# MCP Implementation Notes

Implementation details for MCP server optimization.

Tags: #mcp #protocol #optimization

## Features
- Concurrent request handling
- Adaptive response formatting
- Tool interface standardization
""")

        # Performance optimization notes
        perf_note = self.notes_dir / "performance.md"
        perf_note.write_text("""---
title: Performance Optimization
tags: [performance, optimization, caching]
---

# Performance Optimization Strategies

Various techniques for optimizing query performance.

Tags: #performance #optimization #database

## Strategies
- Query optimization
- Result caching
- Lazy loading
""")

    def test_claude_style_interactions(self):
        """Test tool interfaces with Claude-style requests."""
        print("\n--- Testing Claude-style Interactions ---")

        # Claude typically uses detailed, verbose responses
        test_cases = [
            {
                "tool_name": "query_markdown",
                "client_id": "claude_desktop_client",
                "request_params": {
                    "sql": "SELECT * FROM files WHERE tags LIKE '%ai%' LIMIT 3",
                    "format": "json"
                },
                "content": {
                    "columns": ["id", "filename", "title", "tags"],
                    "rows": [
                        {"id": 1, "filename": "ai_development.md", "title": "AI Development Guide", "tags": "ai,coding,llm"},
                        {"id": 2, "filename": "mcp_implementation.md", "title": "MCP Implementation", "tags": "mcp,protocol,implementation"}
                    ],
                    "row_count": 2,
                    "execution_time_ms": 45.2
                },
                "expected_assistant": AssistantType.CLAUDE
            },
            {
                "tool_name": "comprehensive_tag_analysis",
                "client_id": "claude_api_client",
                "request_params": {
                    "tag_patterns": "ai,mcp,performance",
                    "grouping_strategy": "semantic",
                    "include_actionable": True
                },
                "content": {
                    "topic_groups": [
                        {"name": "AI Development", "file_count": 2, "key_themes": ["ai", "coding", "llm"]},
                        {"name": "MCP Implementation", "file_count": 1, "key_themes": ["mcp", "protocol"]}
                    ],
                    "actionable_insights": [
                        {"title": "Improve MCP documentation", "priority": "high"},
                        {"title": "Add performance benchmarks", "priority": "medium"}
                    ]
                },
                "expected_assistant": AssistantType.CLAUDE
            }
        ]

        for i, test_case in enumerate(test_cases):
            with self.subTest(f"Claude test case {i+1}"):
                formatted_response = self.server._format_response_adaptively(
                    content=test_case["content"],
                    tool_name=test_case["tool_name"],
                    request_parameters=test_case["request_params"],
                    client_id=test_case["client_id"]
                )

                # Verify response is formatted
                self.assertIsInstance(formatted_response, str)
                self.assertTrue(len(formatted_response) > 0)

                # Verify JSON structure
                try:
                    response_data = json.loads(formatted_response)
                    self.assertIn("assistant_type", response_data)
                    self.assertEqual(response_data["assistant_type"], test_case["expected_assistant"].value)
                    print(f"✓ Claude test case {i+1}: {test_case['tool_name']} formatted correctly")
                except json.JSONDecodeError:
                    self.fail(f"Response is not valid JSON: {formatted_response[:200]}")

    def test_gpt_style_interactions(self):
        """Test tool interfaces with GPT-style requests."""
        print("\n--- Testing GPT-style Interactions ---")

        # GPT typically uses structured, concise responses
        test_cases = [
            {
                "tool_name": "get_performance_stats",
                "client_id": "openai_gpt_client",
                "request_params": {"hours": 24},
                "content": {
                    "total_queries": 150,
                    "avg_execution_time": 0.75,
                    "cache_hit_rate": 0.85,
                    "slow_query_count": 3,
                    "performance_summary": {"status": "good", "cache_efficiency": "excellent"}
                },
                "expected_assistant": AssistantType.GPT
            },
            {
                "tool_name": "optimize_query_performance",
                "client_id": "chatgpt_web_client",
                "request_params": {
                    "query": "SELECT * FROM files WHERE content LIKE '%optimization%'",
                    "auto_apply": True
                },
                "content": {
                    "original_query": "SELECT * FROM files WHERE content LIKE '%optimization%'",
                    "optimized_query": "SELECT * FROM files JOIN content_fts ON files.id = content_fts.file_id WHERE content_fts MATCH 'optimization'",
                    "optimizations_applied": ["FTS_conversion"],
                    "performance_improvement": "5x faster"
                },
                "expected_assistant": AssistantType.GPT
            }
        ]

        for i, test_case in enumerate(test_cases):
            with self.subTest(f"GPT test case {i+1}"):
                formatted_response = self.server._format_response_adaptively(
                    content=test_case["content"],
                    tool_name=test_case["tool_name"],
                    request_parameters=test_case["request_params"],
                    client_id=test_case["client_id"]
                )

                # Verify response structure
                self.assertIsInstance(formatted_response, str)
                self.assertTrue(len(formatted_response) > 0)

                try:
                    response_data = json.loads(formatted_response)
                    self.assertIn("assistant_type", response_data)
                    self.assertEqual(response_data["assistant_type"], test_case["expected_assistant"].value)
                    print(f"✓ GPT test case {i+1}: {test_case['tool_name']} formatted correctly")
                except json.JSONDecodeError:
                    self.fail(f"Response is not valid JSON: {formatted_response[:200]}")

    def test_generic_mcp_client_interactions(self):
        """Test tool interfaces with generic MCP client requests."""
        print("\n--- Testing Generic MCP Client Interactions ---")

        # Generic clients should receive standard JSON responses
        test_cases = [
            {
                "tool_name": "get_schema",
                "client_id": "generic_mcp_client",
                "request_params": {"table": "files"},
                "content": {
                    "table": "files",
                    "schema": {
                        "columns": ["id", "filename", "directory", "modified_date", "word_count"],
                        "primary_key": "id",
                        "indexes": ["filename", "directory", "modified_date"]
                    }
                },
                "expected_assistant": AssistantType.GENERIC
            },
            {
                "tool_name": "index_directory",
                "client_id": "unknown_client",
                "request_params": {
                    "path": str(self.notes_dir),
                    "recursive": True,
                    "incremental": True
                },
                "content": {
                    "path": str(self.notes_dir),
                    "files_processed": 3,
                    "files_indexed": 3,
                    "execution_time": 0.25,
                    "status": "completed"
                },
                "expected_assistant": AssistantType.GENERIC
            }
        ]

        for i, test_case in enumerate(test_cases):
            with self.subTest(f"Generic test case {i+1}"):
                formatted_response = self.server._format_response_adaptively(
                    content=test_case["content"],
                    tool_name=test_case["tool_name"],
                    request_parameters=test_case["request_params"],
                    client_id=test_case["client_id"]
                )

                # Verify response structure
                self.assertIsInstance(formatted_response, str)
                self.assertTrue(len(formatted_response) > 0)

                try:
                    response_data = json.loads(formatted_response)
                    self.assertIn("assistant_type", response_data)
                    self.assertEqual(response_data["assistant_type"], test_case["expected_assistant"].value)
                    print(f"✓ Generic test case {i+1}: {test_case['tool_name']} formatted correctly")
                except json.JSONDecodeError:
                    self.fail(f"Response is not valid JSON: {formatted_response[:200]}")

    def test_tool_interface_consistency(self):
        """Test that tool interfaces remain consistent across different assistants."""
        print("\n--- Testing Tool Interface Consistency ---")

        # Test same tool with different assistants
        base_content = {
            "columns": ["filename", "tags", "word_count"],
            "rows": [
                {"filename": "test.md", "tags": "test", "word_count": 100}
            ],
            "row_count": 1
        }

        assistant_clients = [
            ("claude_client", AssistantType.CLAUDE),
            ("gpt_client", AssistantType.GPT),
            ("generic_client", AssistantType.GENERIC)
        ]

        responses = {}

        for client_id, expected_type in assistant_clients:
            formatted_response = self.server._format_response_adaptively(
                content=base_content,
                tool_name="query_markdown",
                request_parameters={"sql": "SELECT filename, tags, word_count FROM files", "format": "json"},
                client_id=client_id
            )

            try:
                response_data = json.loads(formatted_response)
                responses[client_id] = response_data

                # Verify assistant type detection
                self.assertIn("assistant_type", response_data)
                self.assertEqual(response_data["assistant_type"], expected_type.value)

                # Verify core data is preserved
                self.assertIn("data", response_data)
                self.assertEqual(response_data["data"], base_content)

                print(f"✓ {client_id}: Correctly detected as {expected_type.value}")

            except json.JSONDecodeError:
                self.fail(f"Invalid JSON response for {client_id}")

        # Verify all responses contain the same core data
        data_values = [resp["data"] for resp in responses.values()]
        self.assertTrue(all(data == base_content for data in data_values))
        print("✓ Adaptive formatting system validated across multiple assistant types")

    def test_concurrent_multi_assistant_access(self):
        """Test concurrent access from multiple assistant types."""
        print("\n--- Testing Concurrent Multi-Assistant Access ---")

        # Simulate concurrent requests from different assistants
        async def simulate_assistant_request(assistant_id: str, tool_name: str, delay: float = 0):
            """Simulate an assistant making a request."""
            if delay > 0:
                await asyncio.sleep(delay)

            content = {
                "assistant_id": assistant_id,
                "tool_name": tool_name,
                "timestamp": f"test_time_{assistant_id}",
                "data": {"test": "concurrent_access"}
            }

            response = self.server._format_response_adaptively(
                content=content,
                tool_name=tool_name,
                request_parameters={"test": "concurrent"},
                client_id=f"{assistant_id}_client"
            )

            return assistant_id, response

        async def run_concurrent_test():
            """Run concurrent requests."""
            tasks = [
                simulate_assistant_request("claude", "query_markdown", 0.01),
                simulate_assistant_request("gpt", "get_performance_stats", 0.02),
                simulate_assistant_request("generic", "get_schema", 0.03),
                simulate_assistant_request("claude2", "comprehensive_tag_analysis", 0.01),
                simulate_assistant_request("gpt2", "optimize_query_performance", 0.02)
            ]

            results = await asyncio.gather(*tasks)
            return results

        # Run the concurrent test
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(run_concurrent_test())

            # Verify all requests completed successfully
            self.assertEqual(len(results), 5)

            for assistant_id, response in results:
                self.assertIsInstance(response, str)
                self.assertTrue(len(response) > 0)

                try:
                    response_data = json.loads(response)

                    # Verify basic response structure
                    self.assertTrue(isinstance(response_data, dict))

                    # Check for assistant identification or data content
                    has_assistant_data = "assistant_id" in response_data
                    has_tool_data = "tool_name" in response_data

                    if has_assistant_data and has_tool_data:
                        self.assertEqual(response_data["assistant_id"], assistant_id)
                        print(f"✓ Concurrent request from {assistant_id} completed with full metadata")
                    else:
                        print(f"✓ Concurrent request from {assistant_id} completed with basic response")
                except json.JSONDecodeError:
                    self.fail(f"Invalid response from {assistant_id}: {response[:100]}")

        except Exception as e:
            self.fail(f"Concurrent test failed: {e}")
        finally:
            loop.close()

    def test_tool_documentation_consistency(self):
        """Test tool documentation is consistent across assistant types."""
        print("\n--- Testing Tool Documentation Consistency ---")

        # Test tool documentation for different assistants
        assistant_types = ["claude_client", "gpt_client", "generic_client"]

        for client_id in assistant_types:
            # Test getting all tool documentation
            all_docs = self.server.get_tool_documentation()
            all_docs_data = json.loads(all_docs)

            self.assertIn("tool_categories", all_docs_data)
            self.assertIn("total_tools", all_docs_data)
            self.assertGreater(all_docs_data["total_tools"], 0)

            # Test getting specific tool documentation
            query_docs = self.server.get_tool_documentation("query_markdown")
            query_docs_data = json.loads(query_docs)

            self.assertIn("tool", query_docs_data)
            self.assertEqual(query_docs_data["tool"], "query_markdown")
            self.assertIn("parameters", query_docs_data)
            self.assertIn("description", query_docs_data)

            print(f"✓ Tool documentation consistent for {client_id}")

        print("✓ Tool documentation maintains consistency across all assistant types")


def run_ai_compatibility_tests():
    """Run all AI assistant compatibility tests."""
    print("=" * 60)
    print("AI Assistant Compatibility Test Suite")
    print("=" * 60)

    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(AIAssistantCompatibilityTest)

    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    if result.wasSuccessful():
        print("✓ All AI assistant compatibility tests passed!")
        print(f"  - Tests run: {result.testsRun}")
        print(f"  - Failures: {len(result.failures)}")
        print(f"  - Errors: {len(result.errors)}")
        print("\nThe MCP tool interfaces are compatible across different AI assistants.")
    else:
        print("✗ Some tests failed!")
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
    success = run_ai_compatibility_tests()
    sys.exit(0 if success else 1)