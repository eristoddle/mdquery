#!/usr/bin/env python3
"""
Test script to verify the consistent tool interface integration.

This script tests the integration of ConsistentToolMixin with the MCP server
and validates the tool documentation endpoint functionality.
"""

import sys
import asyncio
import json
import tempfile
from pathlib import Path

# Add the mdquery module to the path
sys.path.insert(0, str(Path(__file__).parent))

from mdquery.mcp import MDQueryMCPServer
from mdquery.config import SimplifiedConfig, create_simplified_config


class TestToolInterfaceIntegration:
    """Test the consistent tool interface integration."""

    def __init__(self):
        """Initialize test environment."""
        self.test_dir = None
        self.server = None

    async def setup(self):
        """Set up test environment."""
        print("Setting up test environment...")

        # Create temporary directory for testing
        self.test_dir = Path(tempfile.mkdtemp(prefix="mdquery_tool_interface_test_"))
        notes_dir = self.test_dir / "notes"
        notes_dir.mkdir(parents=True, exist_ok=True)

        # Create a simple test file
        test_file = notes_dir / "test.md"
        test_file.write_text("""---
title: Test Note
tags: [test, interface]
---

# Test Note

This is a test note for validating the tool interface system.

Tags: #test #interface #mcp
""")

        # Create configuration
        config = create_simplified_config(str(notes_dir))

        # Initialize MCP server
        self.server = MDQueryMCPServer(config=config)
        print(f"Created test environment in: {self.test_dir}")

    async def test_tool_registry_initialization(self):
        """Test that the tool registry is properly initialized."""
        print("\n--- Testing Tool Registry Initialization ---")

        # Check if tool_registry is available
        if hasattr(self.server, 'tool_registry'):
            print("✓ Tool registry is available")

            # Check if standard tools are registered
            tools = self.server.tool_registry.tools
            print(f"✓ Tool registry contains {len(tools)} tools")

            # Check for specific tools
            expected_tools = ["query_markdown", "comprehensive_tag_analysis", "get_performance_stats"]
            for tool_name in expected_tools:
                if tool_name in tools:
                    print(f"✓ Tool '{tool_name}' is registered")
                else:
                    print(f"✗ Tool '{tool_name}' is missing")

        else:
            print("✗ Tool registry is not available")

    async def test_tool_documentation_endpoint(self):
        """Test the tool documentation endpoint."""
        print("\n--- Testing Tool Documentation Endpoint ---")

        try:
            # Test getting documentation for all tools
            print("Getting documentation for all tools...")
            all_docs = self.server.get_tool_documentation()
            all_docs_data = json.loads(all_docs)

            print(f"✓ All tools documentation retrieved: {all_docs_data.get('total_tools', 0)} tools")

            # Test getting documentation for a specific tool
            print("Getting documentation for 'query_markdown' tool...")
            specific_docs = self.server.get_tool_documentation("query_markdown")
            specific_docs_data = json.loads(specific_docs)

            if "tool" in specific_docs_data and specific_docs_data["tool"] == "query_markdown":
                print("✓ Specific tool documentation retrieved successfully")
                print(f"  - Description: {specific_docs_data.get('description', 'N/A')}")
                print(f"  - Category: {specific_docs_data.get('category', 'N/A')}")
                print(f"  - Parameters: {len(specific_docs_data.get('parameters', []))}")
            else:
                print("✗ Specific tool documentation format is incorrect")

        except Exception as e:
            print(f"✗ Tool documentation test failed: {e}")

    async def test_tool_interface_validation(self):
        """Test the tool interface validation system."""
        print("\n--- Testing Tool Interface Validation ---")

        try:
            # Test valid parameters
            print("Testing valid parameter validation...")
            is_valid, errors = self.server.validate_tool_interface(
                "query_markdown",
                {"sql": "SELECT * FROM files LIMIT 5", "format": "json"}
            )

            if is_valid:
                print("✓ Valid parameters passed validation")
            else:
                print(f"✗ Valid parameters failed validation: {errors}")

            # Test invalid parameters
            print("Testing invalid parameter validation...")
            is_valid, errors = self.server.validate_tool_interface(
                "query_markdown",
                {"invalid_param": "test"}  # Missing required 'sql' parameter
            )

            if not is_valid:
                print("✓ Invalid parameters correctly rejected")
                print(f"  - Errors: {errors}")
            else:
                print("✗ Invalid parameters incorrectly accepted")

            # Test unknown tool
            print("Testing unknown tool validation...")
            is_valid, errors = self.server.validate_tool_interface(
                "unknown_tool",
                {"param": "value"}
            )

            if not is_valid:
                print("✓ Unknown tool correctly rejected")
            else:
                print("✗ Unknown tool incorrectly accepted")

        except Exception as e:
            print(f"✗ Tool interface validation test failed: {e}")

    async def test_adaptive_formatting_integration(self):
        """Test integration with adaptive formatting system."""
        print("\n--- Testing Adaptive Formatting Integration ---")

        try:
            # Check if response_formatter is available
            if hasattr(self.server, 'response_formatter') and self.server.response_formatter:
                print("✓ Response formatter is available")

                # Test formatting a simple response
                sample_data = {"test": "data", "count": 42}
                formatted = self.server._format_response_adaptively(
                    content=sample_data,
                    tool_name="test_tool",
                    request_parameters={},
                    client_id="test_client"
                )

                if formatted:
                    print("✓ Adaptive formatting works")
                    print(f"  - Formatted length: {len(formatted)} characters")
                else:
                    print("✗ Adaptive formatting returned empty result")

            else:
                print("⚠ Response formatter not available (might be initialized lazily)")

        except Exception as e:
            print(f"✗ Adaptive formatting integration test failed: {e}")

    async def cleanup(self):
        """Clean up test environment."""
        print(f"\nCleaning up test environment: {self.test_dir}")

        if self.server:
            await self.server.shutdown()

        if self.test_dir and self.test_dir.exists():
            import shutil
            shutil.rmtree(self.test_dir)


async def main():
    """Run all tests."""
    test = TestToolInterfaceIntegration()

    try:
        await test.setup()
        await test.test_tool_registry_initialization()
        await test.test_tool_documentation_endpoint()
        await test.test_tool_interface_validation()
        await test.test_adaptive_formatting_integration()

        print("\n=== Test Summary ===")
        print("Consistent tool interface integration tests completed.")
        print("Check the output above for specific test results.")

    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await test.cleanup()


if __name__ == "__main__":
    asyncio.run(main())