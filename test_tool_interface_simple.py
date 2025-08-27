#!/usr/bin/env python3
"""
Test the tool interface components directly.
"""

import sys
import json
from pathlib import Path

# Add the mdquery module to the path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from mdquery.tool_interface import (
        ToolRegistry,
        ConsistentToolMixin,
        ParameterValidator,
        ParameterSpec,
        ParameterType,
        ToolSpec,
        ToolCategory,
        ResponseType
    )

    def test_tool_registry():
        """Test the tool registry functionality."""
        print("=== Testing Tool Registry ===")

        registry = ToolRegistry()

        # Check if standard tools are registered
        tools = list(registry.tools.keys())
        print(f"✓ Tool registry initialized with {len(tools)} tools")

        expected_tools = ["query_markdown", "comprehensive_tag_analysis", "get_performance_stats", "index_directory"]
        for tool_name in expected_tools:
            if tool_name in tools:
                print(f"✓ Tool '{tool_name}' is registered")
            else:
                print(f"✗ Tool '{tool_name}' is missing")

        # Test tool retrieval
        query_tool = registry.get_tool_spec("query_markdown")
        if query_tool:
            print(f"✓ Retrieved tool spec: {query_tool.name}")
            print(f"  - Category: {query_tool.category.value}")
            print(f"  - Parameters: {len(query_tool.parameters)}")
        else:
            print("✗ Failed to retrieve query_markdown tool spec")

    def test_parameter_validation():
        """Test parameter validation."""
        print("\n=== Testing Parameter Validation ===")

        # Create a test parameter spec
        param_spec = ParameterSpec(
            name="test_param",
            param_type=ParameterType.STRING,
            description="Test parameter",
            required=True
        )

        # Test valid parameter
        is_valid, error = ParameterValidator.validate_parameter("test_value", param_spec)
        if is_valid:
            print("✓ Valid string parameter passed validation")
        else:
            print(f"✗ Valid parameter failed: {error}")

        # Test missing required parameter
        is_valid, error = ParameterValidator.validate_parameter(None, param_spec)
        if not is_valid:
            print("✓ Missing required parameter correctly rejected")
        else:
            print("✗ Missing required parameter incorrectly accepted")

    def test_tool_validation():
        """Test tool validation."""
        print("\n=== Testing Tool Validation ===")

        registry = ToolRegistry()

        # Test valid tool call
        is_valid, errors = registry.validate_tool_call(
            "query_markdown",
            {"sql": "SELECT * FROM files LIMIT 5", "format": "json"}
        )

        if is_valid:
            print("✓ Valid tool call passed validation")
        else:
            print(f"✗ Valid tool call failed: {errors}")

        # Test invalid tool call
        is_valid, errors = registry.validate_tool_call(
            "query_markdown",
            {"invalid_param": "test"}  # Missing required 'sql' parameter
        )

        if not is_valid:
            print("✓ Invalid tool call correctly rejected")
            print(f"  - Errors: {', '.join(errors)}")
        else:
            print("✗ Invalid tool call incorrectly accepted")

    class MockServer(ConsistentToolMixin):
        """Mock server for testing mixin."""
        def __init__(self):
            super().__init__()
            self.response_formatter = None

    def test_consistent_tool_mixin():
        """Test the ConsistentToolMixin."""
        print("\n=== Testing ConsistentToolMixin ===")

        try:
            server = MockServer()

            # Test tool documentation
            docs = server.get_tool_documentation()
            docs_data = json.loads(docs)

            if "tool_categories" in docs_data:
                print("✓ Tool documentation generated successfully")
                print(f"  - Total tools: {docs_data.get('total_tools', 0)}")
            else:
                print("✗ Tool documentation format incorrect")

            # Test specific tool documentation
            query_docs = server.get_tool_documentation("query_markdown")
            query_data = json.loads(query_docs)

            if "tool" in query_data and query_data["tool"] == "query_markdown":
                print("✓ Specific tool documentation works")
            else:
                print("✗ Specific tool documentation failed")

        except Exception as e:
            print(f"✗ ConsistentToolMixin test failed: {e}")

    def main():
        """Run all tests."""
        print("Testing Tool Interface Components\n")

        test_tool_registry()
        test_parameter_validation()
        test_tool_validation()
        test_consistent_tool_mixin()

        print("\n=== Test Summary ===")
        print("Tool interface component tests completed.")
        print("If all tests show ✓, the integration is working correctly.")

    if __name__ == "__main__":
        main()

except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the mdquery project directory.")