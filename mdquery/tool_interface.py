"""
Consistent tool interface system for MCP server compatibility.

This module provides standardized interfaces, parameter validation, and response
formatting to ensure consistent behavior across different MCP clients and AI assistants.
Implements requirements 6.1, 6.2, 6.3, 6.4, 6.5 from the MCP workflow optimization spec.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable, get_type_hints
from functools import wraps
import inspect
from datetime import datetime

logger = logging.getLogger(__name__)


class ParameterType(Enum):
    """Standard parameter types for MCP tools."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    FILE_PATH = "file_path"
    DIRECTORY_PATH = "directory_path"
    DATE = "date"
    FORMAT = "format"
    TAG_PATTERNS = "tag_patterns"
    COMMA_SEPARATED = "comma_separated"


class ToolCategory(Enum):
    """Categories for organizing MCP tools."""
    CORE = "core"                    # Basic query and schema operations
    INDEXING = "indexing"            # File indexing and management
    ANALYSIS = "analysis"            # Content and workflow analysis
    RESEARCH = "research"            # Research and citation tools
    PERFORMANCE = "performance"     # Performance monitoring and optimization
    SYSTEM = "system"               # System status and configuration
    TESTING = "testing"             # Testing and validation tools


class ResponseType(Enum):
    """Standard response types."""
    JSON = "json"
    TABLE = "table"
    REPORT = "report"
    STATUS = "status"
    STATISTICS = "statistics"
    LIST = "list"
    ERROR = "error"


@dataclass
class ParameterSpec:
    """Specification for a tool parameter."""
    name: str
    param_type: ParameterType
    description: str
    required: bool = True
    default: Optional[Any] = None
    allowed_values: Optional[List[str]] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    pattern: Optional[str] = None
    examples: Optional[List[str]] = None


@dataclass
class ToolSpec:
    """Complete specification for an MCP tool."""
    name: str
    description: str
    category: ToolCategory
    response_type: ResponseType
    parameters: List[ParameterSpec] = field(default_factory=list)
    examples: Optional[List[Dict[str, Any]]] = None
    performance_notes: Optional[str] = None
    requires_indexing: bool = False
    concurrent_safe: bool = True
    long_running: bool = False


@dataclass
class ToolResponse:
    """Standardized tool response structure."""
    success: bool
    data: Any
    message: Optional[str] = None
    execution_time_ms: Optional[float] = None
    tool_name: Optional[str] = None
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    warnings: Optional[List[str]] = None
    suggestions: Optional[List[str]] = None


class ParameterValidator:
    """Validates tool parameters according to specifications."""

    @staticmethod
    def validate_parameter(value: Any, spec: ParameterSpec) -> tuple[bool, Optional[str]]:
        """
        Validate a parameter value against its specification.

        Returns:
            (is_valid, error_message)
        """
        # Check required parameters
        if spec.required and (value is None or value == ""):
            return False, f"Parameter '{spec.name}' is required"

        # If not required and value is None/empty, it's valid
        if not spec.required and (value is None or value == ""):
            return True, None

        # Type validation
        if spec.param_type == ParameterType.STRING:
            if not isinstance(value, str):
                return False, f"Parameter '{spec.name}' must be a string"

        elif spec.param_type == ParameterType.INTEGER:
            try:
                int_value = int(value)
                if spec.min_value is not None and int_value < spec.min_value:
                    return False, f"Parameter '{spec.name}' must be >= {spec.min_value}"
                if spec.max_value is not None and int_value > spec.max_value:
                    return False, f"Parameter '{spec.name}' must be <= {spec.max_value}"
            except (ValueError, TypeError):
                return False, f"Parameter '{spec.name}' must be an integer"

        elif spec.param_type == ParameterType.FLOAT:
            try:
                float_value = float(value)
                if spec.min_value is not None and float_value < spec.min_value:
                    return False, f"Parameter '{spec.name}' must be >= {spec.min_value}"
                if spec.max_value is not None and float_value > spec.max_value:
                    return False, f"Parameter '{spec.name}' must be <= {spec.max_value}"
            except (ValueError, TypeError):
                return False, f"Parameter '{spec.name}' must be a number"

        elif spec.param_type == ParameterType.BOOLEAN:
            if not isinstance(value, bool) and str(value).lower() not in ['true', 'false', '1', '0']:
                return False, f"Parameter '{spec.name}' must be a boolean (true/false)"

        elif spec.param_type == ParameterType.FORMAT:
            if spec.allowed_values and value not in spec.allowed_values:
                return False, f"Parameter '{spec.name}' must be one of: {', '.join(spec.allowed_values)}"

        # Value constraints
        if spec.allowed_values and value not in spec.allowed_values:
            return False, f"Parameter '{spec.name}' must be one of: {', '.join(spec.allowed_values)}"

        # Pattern validation for strings
        if spec.pattern and isinstance(value, str):
            import re
            if not re.match(spec.pattern, value):
                return False, f"Parameter '{spec.name}' does not match required pattern"

        return True, None

    @staticmethod
    def validate_parameters(parameters: Dict[str, Any], specs: List[ParameterSpec]) -> tuple[bool, List[str]]:
        """
        Validate all parameters for a tool.

        Returns:
            (all_valid, list_of_errors)
        """
        errors = []

        # Create spec lookup
        spec_map = {spec.name: spec for spec in specs}

        # Validate each parameter
        for param_name, param_value in parameters.items():
            if param_name in spec_map:
                is_valid, error_msg = ParameterValidator.validate_parameter(param_value, spec_map[param_name])
                if not is_valid:
                    errors.append(error_msg)

        # Check for missing required parameters
        for spec in specs:
            if spec.required and spec.name not in parameters:
                errors.append(f"Required parameter '{spec.name}' is missing")

        return len(errors) == 0, errors


class ToolRegistry:
    """Registry for managing consistent tool interfaces."""

    def __init__(self):
        """Initialize tool registry."""
        self.tools: Dict[str, ToolSpec] = {}
        self._initialize_standard_tools()

    def _initialize_standard_tools(self):
        """Initialize specifications for standard tools."""

        # Core tools
        self.register_tool(ToolSpec(
            name="query_markdown",
            description="Execute SQL query against markdown database",
            category=ToolCategory.CORE,
            response_type=ResponseType.JSON,
            parameters=[
                ParameterSpec("sql", ParameterType.STRING, "SQL query to execute"),
                ParameterSpec("format", ParameterType.FORMAT, "Output format",
                            required=False, default="json",
                            allowed_values=["json", "csv", "table", "markdown"])
            ],
            examples=[
                {"sql": "SELECT * FROM files LIMIT 5", "format": "json"},
                {"sql": "SELECT tag, COUNT(*) FROM tags GROUP BY tag", "format": "table"}
            ],
            concurrent_safe=True
        ))

        # Analysis tools
        self.register_tool(ToolSpec(
            name="comprehensive_tag_analysis",
            description="Generate comprehensive analysis of tagged content with intelligent grouping",
            category=ToolCategory.ANALYSIS,
            response_type=ResponseType.REPORT,
            parameters=[
                ParameterSpec("tag_patterns", ParameterType.COMMA_SEPARATED, "Comma-separated tag patterns"),
                ParameterSpec("grouping_strategy", ParameterType.STRING, "Content grouping strategy",
                            required=False, default="semantic",
                            allowed_values=["semantic", "tag-hierarchy", "temporal"]),
                ParameterSpec("include_actionable", ParameterType.BOOLEAN, "Include actionable insights",
                            required=False, default=True),
                ParameterSpec("include_theoretical", ParameterType.BOOLEAN, "Include theoretical insights",
                            required=False, default=True),
                ParameterSpec("remove_fluff", ParameterType.BOOLEAN, "Filter out low-quality content",
                            required=False, default=True),
                ParameterSpec("min_content_quality", ParameterType.FLOAT, "Minimum content quality score",
                            required=False, default=0.3, min_value=0.0, max_value=1.0)
            ],
            long_running=True,
            concurrent_safe=True
        ))

        # Performance tools
        self.register_tool(ToolSpec(
            name="get_performance_stats",
            description="Get performance statistics and monitoring data",
            category=ToolCategory.PERFORMANCE,
            response_type=ResponseType.STATISTICS,
            parameters=[
                ParameterSpec("hours", ParameterType.INTEGER, "Hours to look back for statistics",
                            required=False, default=24, min_value=1, max_value=168)
            ],
            concurrent_safe=True
        ))

        # Indexing tools
        self.register_tool(ToolSpec(
            name="index_directory",
            description="Index markdown files in a directory",
            category=ToolCategory.INDEXING,
            response_type=ResponseType.STATUS,
            parameters=[
                ParameterSpec("path", ParameterType.DIRECTORY_PATH, "Directory path to index"),
                ParameterSpec("recursive", ParameterType.BOOLEAN, "Scan subdirectories",
                            required=False, default=True),
                ParameterSpec("incremental", ParameterType.BOOLEAN, "Use incremental indexing",
                            required=False, default=True)
            ],
            long_running=True,
            requires_indexing=True,
            concurrent_safe=False  # Indexing should be serialized
        ))

    def register_tool(self, tool_spec: ToolSpec):
        """Register a tool specification."""
        self.tools[tool_spec.name] = tool_spec
        logger.debug(f"Registered tool: {tool_spec.name}")

    def get_tool_spec(self, tool_name: str) -> Optional[ToolSpec]:
        """Get tool specification by name."""
        return self.tools.get(tool_name)

    def get_tools_by_category(self, category: ToolCategory) -> List[ToolSpec]:
        """Get all tools in a specific category."""
        return [tool for tool in self.tools.values() if tool.category == category]

    def validate_tool_call(self, tool_name: str, parameters: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate a tool call against its specification."""
        tool_spec = self.get_tool_spec(tool_name)
        if not tool_spec:
            return False, [f"Unknown tool: {tool_name}"]

        return ParameterValidator.validate_parameters(parameters, tool_spec.parameters)


def consistent_tool(tool_spec: ToolSpec):
    """
    Decorator for creating consistent MCP tools.

    This decorator standardizes parameter validation, error handling,
    response formatting, and documentation.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            start_time = datetime.now()
            tool_name = tool_spec.name

            try:
                # Extract parameters from function signature
                sig = inspect.signature(func)
                bound_args = sig.bind(self, *args, **kwargs)
                bound_args.apply_defaults()

                # Remove 'self' from parameters
                parameters = dict(bound_args.arguments)
                parameters.pop('self', None)

                # Validate parameters
                is_valid, errors = ParameterValidator.validate_parameters(parameters, tool_spec.parameters)
                if not is_valid:
                    return self._format_error_response(
                        f"Parameter validation failed: {'; '.join(errors)}",
                        tool_name,
                        suggestions=["Check parameter types and required values"]
                    )

                # Execute the actual tool function
                result = await func(self, **parameters)

                # Calculate execution time
                execution_time = (datetime.now() - start_time).total_seconds() * 1000

                # Format successful response
                tool_response = ToolResponse(
                    success=True,
                    data=result,
                    execution_time_ms=execution_time,
                    tool_name=tool_name,
                    timestamp=start_time.isoformat()
                )

                return self._format_tool_response(tool_response, tool_spec.response_type)

            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                logger.error(f"Tool {tool_name} failed: {e}")

                return self._format_error_response(
                    str(e),
                    tool_name,
                    execution_time_ms=execution_time
                )

        # Store tool specification in function metadata
        wrapper._tool_spec = tool_spec
        wrapper._is_consistent_tool = True

        return wrapper
    return decorator


class ConsistentToolMixin:
    """
    Mixin class providing consistent tool interface functionality.

    This should be mixed into the MCP server class to provide
    standardized tool behavior.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the tool registry."""
        super().__init__(*args, **kwargs)
        self.tool_registry = ToolRegistry()

    def _format_tool_response(self, response: ToolResponse, response_type: ResponseType) -> str:
        """Format tool response according to type and client capabilities."""

        # Use adaptive formatting if available
        if hasattr(self, 'response_formatter') and self.response_formatter:
            return self._format_response_adaptively(
                content=response.data,
                tool_name=response.tool_name or "unknown",
                request_parameters={},
                client_id="mcp_client"
            )

        # Fallback formatting
        if response_type == ResponseType.JSON:
            return json.dumps({
                "success": response.success,
                "data": response.data,
                "metadata": {
                    "execution_time_ms": response.execution_time_ms,
                    "timestamp": response.timestamp,
                    "tool_name": response.tool_name
                }
            }, indent=2, default=str)

        elif response_type == ResponseType.STATUS:
            return json.dumps({
                "success": response.success,
                "message": response.message or "Operation completed successfully",
                "data": response.data,
                "timestamp": response.timestamp
            }, indent=2, default=str)

        elif response_type == ResponseType.STATISTICS:
            return json.dumps({
                "statistics": response.data,
                "metadata": {
                    "execution_time_ms": response.execution_time_ms,
                    "timestamp": response.timestamp,
                    "tool_name": response.tool_name
                }
            }, indent=2, default=str)

        else:
            # Default JSON formatting
            return json.dumps(response.data, indent=2, default=str)

    def _format_error_response(self, error_message: str, tool_name: str,
                             execution_time_ms: Optional[float] = None,
                             suggestions: Optional[List[str]] = None) -> str:
        """Format error response consistently."""

        error_response = {
            "success": False,
            "error": error_message,
            "tool_name": tool_name,
            "timestamp": datetime.now().isoformat()
        }

        if execution_time_ms is not None:
            error_response["execution_time_ms"] = execution_time_ms

        if suggestions:
            error_response["suggestions"] = suggestions

        return json.dumps(error_response, indent=2, default=str)

    def get_tool_documentation(self, tool_name: Optional[str] = None) -> str:
        """Get comprehensive tool documentation."""

        if tool_name:
            tool_spec = self.tool_registry.get_tool_spec(tool_name)
            if not tool_spec:
                return json.dumps({"error": f"Tool '{tool_name}' not found"}, indent=2)

            doc = {
                "tool": tool_spec.name,
                "description": tool_spec.description,
                "category": tool_spec.category.value,
                "response_type": tool_spec.response_type.value,
                "parameters": [],
                "examples": tool_spec.examples or [],
                "performance_notes": tool_spec.performance_notes,
                "concurrent_safe": tool_spec.concurrent_safe,
                "long_running": tool_spec.long_running
            }

            for param in tool_spec.parameters:
                param_doc = {
                    "name": param.name,
                    "type": param.param_type.value,
                    "description": param.description,
                    "required": param.required,
                    "default": param.default
                }

                if param.allowed_values:
                    param_doc["allowed_values"] = param.allowed_values
                if param.min_value is not None:
                    param_doc["min_value"] = param.min_value
                if param.max_value is not None:
                    param_doc["max_value"] = param.max_value
                if param.examples:
                    param_doc["examples"] = param.examples

                doc["parameters"].append(param_doc)

            return json.dumps(doc, indent=2, default=str)

        else:
            # Return documentation for all tools
            all_tools = {}

            for category in ToolCategory:
                category_tools = self.tool_registry.get_tools_by_category(category)
                if category_tools:
                    all_tools[category.value] = [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "parameter_count": len(tool.parameters),
                            "concurrent_safe": tool.concurrent_safe,
                            "long_running": tool.long_running
                        }
                        for tool in category_tools
                    ]

            return json.dumps({
                "tool_categories": all_tools,
                "total_tools": len(self.tool_registry.tools),
                "usage": "Use get_tool_documentation(tool_name) for detailed information about a specific tool"
            }, indent=2, default=str)

    def validate_tool_interface(self, tool_name: str, parameters: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate a tool interface call."""
        return self.tool_registry.validate_tool_call(tool_name, parameters)


def create_tool_registry() -> ToolRegistry:
    """Create a tool registry instance."""
    return ToolRegistry()