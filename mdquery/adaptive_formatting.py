"""
Adaptive response formatting system for different AI assistant capabilities.

This module provides intelligent response formatting that adapts to different
AI assistants' capabilities, preferences, and limitations to ensure optimal
communication and usability across various MCP clients.
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable
import re

logger = logging.getLogger(__name__)


class AssistantType(Enum):
    """Known AI assistant types with different capabilities."""
    CLAUDE = "claude"
    GPT = "gpt"
    LLAMA = "llama"
    GEMINI = "gemini"
    GENERIC = "generic"


class ResponseFormat(Enum):
    """Supported response formats."""
    JSON = "json"
    MARKDOWN = "markdown"
    STRUCTURED_TEXT = "structured_text"
    COMPACT_JSON = "compact_json"
    VERBOSE_JSON = "verbose_json"
    CSV = "csv"
    TABLE = "table"


class VerbosityLevel(Enum):
    """Response verbosity levels."""
    MINIMAL = "minimal"
    NORMAL = "normal"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"


@dataclass
class AssistantCapabilities:
    """Capabilities and preferences of an AI assistant."""
    assistant_type: AssistantType
    max_response_length: Optional[int] = None
    preferred_formats: List[ResponseFormat] = field(default_factory=list)
    supports_markdown: bool = True
    supports_tables: bool = True
    supports_json: bool = True
    supports_structured_output: bool = True
    preferred_verbosity: VerbosityLevel = VerbosityLevel.NORMAL
    chunk_large_responses: bool = False
    max_chunk_size: int = 8000
    include_metadata: bool = True
    include_examples: bool = True
    include_suggestions: bool = True
    supports_interactive_elements: bool = False
    timezone_aware: bool = True
    supports_unicode: bool = True


@dataclass
class FormattingContext:
    """Context information for response formatting."""
    tool_name: str
    request_parameters: Dict[str, Any]
    client_id: str
    assistant_capabilities: AssistantCapabilities
    content_size: int
    content_type: str
    user_preferences: Optional[Dict[str, Any]] = None
    response_format_hint: Optional[ResponseFormat] = None


class ResponseFormatter:
    """
    Adaptive response formatter for different AI assistants.

    Automatically adjusts response format, verbosity, and structure
    based on the assistant's capabilities and the content being returned.
    """

    def __init__(self):
        """Initialize the response formatter."""
        self._assistant_profiles = self._initialize_assistant_profiles()
        self._formatting_rules = self._initialize_formatting_rules()

    def _initialize_assistant_profiles(self) -> Dict[AssistantType, AssistantCapabilities]:
        """Initialize known assistant capability profiles."""
        return {
            AssistantType.CLAUDE: AssistantCapabilities(
                assistant_type=AssistantType.CLAUDE,
                max_response_length=100000,
                preferred_formats=[ResponseFormat.MARKDOWN, ResponseFormat.JSON, ResponseFormat.STRUCTURED_TEXT],
                supports_markdown=True,
                supports_tables=True,
                supports_json=True,
                supports_structured_output=True,
                preferred_verbosity=VerbosityLevel.DETAILED,
                chunk_large_responses=True,
                max_chunk_size=8000,
                include_metadata=True,
                include_examples=True,
                include_suggestions=True,
                supports_interactive_elements=False,
                timezone_aware=True,
                supports_unicode=True
            ),

            AssistantType.GPT: AssistantCapabilities(
                assistant_type=AssistantType.GPT,
                max_response_length=32000,
                preferred_formats=[ResponseFormat.JSON, ResponseFormat.MARKDOWN],
                supports_markdown=True,
                supports_tables=True,
                supports_json=True,
                supports_structured_output=True,
                preferred_verbosity=VerbosityLevel.NORMAL,
                chunk_large_responses=True,
                max_chunk_size=6000,
                include_metadata=True,
                include_examples=False,
                include_suggestions=True,
                supports_interactive_elements=False,
                timezone_aware=True,
                supports_unicode=True
            ),

            AssistantType.LLAMA: AssistantCapabilities(
                assistant_type=AssistantType.LLAMA,
                max_response_length=16000,
                preferred_formats=[ResponseFormat.STRUCTURED_TEXT, ResponseFormat.JSON],
                supports_markdown=True,
                supports_tables=False,
                supports_json=True,
                supports_structured_output=False,
                preferred_verbosity=VerbosityLevel.NORMAL,
                chunk_large_responses=True,
                max_chunk_size=4000,
                include_metadata=False,
                include_examples=False,
                include_suggestions=False,
                supports_interactive_elements=False,
                timezone_aware=False,
                supports_unicode=True
            ),

            AssistantType.GEMINI: AssistantCapabilities(
                assistant_type=AssistantType.GEMINI,
                max_response_length=50000,
                preferred_formats=[ResponseFormat.JSON, ResponseFormat.MARKDOWN, ResponseFormat.TABLE],
                supports_markdown=True,
                supports_tables=True,
                supports_json=True,
                supports_structured_output=True,
                preferred_verbosity=VerbosityLevel.DETAILED,
                chunk_large_responses=False,
                max_chunk_size=10000,
                include_metadata=True,
                include_examples=True,
                include_suggestions=True,
                supports_interactive_elements=True,
                timezone_aware=True,
                supports_unicode=True
            ),

            AssistantType.GENERIC: AssistantCapabilities(
                assistant_type=AssistantType.GENERIC,
                max_response_length=8000,
                preferred_formats=[ResponseFormat.JSON],
                supports_markdown=False,
                supports_tables=False,
                supports_json=True,
                supports_structured_output=False,
                preferred_verbosity=VerbosityLevel.MINIMAL,
                chunk_large_responses=True,
                max_chunk_size=2000,
                include_metadata=False,
                include_examples=False,
                include_suggestions=False,
                supports_interactive_elements=False,
                timezone_aware=False,
                supports_unicode=False
            )
        }

    def _initialize_formatting_rules(self) -> Dict[str, Callable]:
        """Initialize formatting rules for different content types."""
        return {
            'query_results': self._format_query_results,
            'analysis_results': self._format_analysis_results,
            'performance_stats': self._format_performance_stats,
            'error_response': self._format_error_response,
            'status_response': self._format_status_response,
            'list_response': self._format_list_response,
            'large_dataset': self._format_large_dataset,
            'generic_response': self._format_generic_response
        }

    def detect_assistant_type(self, client_info: Dict[str, Any]) -> AssistantType:
        """
        Detect assistant type from client information.

        Args:
            client_info: Information about the client/assistant

        Returns:
            Detected assistant type
        """
        # Try to detect from user agent or client identifier
        client_string = str(client_info).lower()

        if 'claude' in client_string or 'anthropic' in client_string:
            return AssistantType.CLAUDE
        elif 'gpt' in client_string or 'openai' in client_string:
            return AssistantType.GPT
        elif 'llama' in client_string or 'meta' in client_string:
            return AssistantType.LLAMA
        elif 'gemini' in client_string or 'google' in client_string or 'bard' in client_string:
            return AssistantType.GEMINI
        else:
            return AssistantType.GENERIC

    def get_assistant_capabilities(self, assistant_type: AssistantType) -> AssistantCapabilities:
        """Get capabilities for a specific assistant type."""
        return self._assistant_profiles.get(assistant_type, self._assistant_profiles[AssistantType.GENERIC])

    def create_formatting_context(self,
                                tool_name: str,
                                request_parameters: Dict[str, Any],
                                content: Any,
                                client_id: str = "unknown",
                                assistant_type: Optional[AssistantType] = None,
                                format_hint: Optional[str] = None) -> FormattingContext:
        """Create formatting context for response adaptation."""

        # Detect assistant type if not provided
        if assistant_type is None:
            assistant_type = self.detect_assistant_type({"client_id": client_id})

        capabilities = self.get_assistant_capabilities(assistant_type)

        # Determine content characteristics
        content_str = str(content) if content else ""
        content_size = len(content_str)

        # Determine content type
        content_type = self._classify_content_type(tool_name, content)

        # Parse format hint
        response_format_hint = None
        if format_hint:
            try:
                response_format_hint = ResponseFormat(format_hint.lower())
            except ValueError:
                pass

        return FormattingContext(
            tool_name=tool_name,
            request_parameters=request_parameters,
            client_id=client_id,
            assistant_capabilities=capabilities,
            content_size=content_size,
            content_type=content_type,
            response_format_hint=response_format_hint
        )

    def format_response(self,
                       content: Any,
                       formatting_context: FormattingContext) -> str:
        """
        Format response adaptively based on context and capabilities.

        Args:
            content: Content to format
            formatting_context: Formatting context with assistant capabilities

        Returns:
            Formatted response string
        """
        try:
            # Select appropriate formatting rule
            content_type = formatting_context.content_type
            formatter = self._formatting_rules.get(content_type, self._format_generic_response)

            # Apply formatting
            formatted_content = formatter(content, formatting_context)

            # Apply post-processing
            final_response = self._apply_post_processing(formatted_content, formatting_context)

            return final_response

        except Exception as e:
            logger.error(f"Error formatting response: {e}")
            # Fallback to basic JSON
            return json.dumps({
                "error": "Response formatting failed",
                "content": str(content)[:1000],  # Truncate for safety
                "original_error": str(e)
            }, indent=2)

    def _classify_content_type(self, tool_name: str, content: Any) -> str:
        """Classify content type for appropriate formatting."""
        if "query" in tool_name.lower():
            return "query_results"
        elif "analysis" in tool_name.lower() or "analyze" in tool_name.lower():
            return "analysis_results"
        elif "performance" in tool_name.lower() or "stats" in tool_name.lower():
            return "performance_stats"
        elif "error" in str(content).lower():
            return "error_response"
        elif "success" in str(content).lower() or "status" in tool_name.lower():
            return "status_response"
        elif isinstance(content, (list, tuple)):
            return "list_response"
        elif self._is_large_dataset(content):
            return "large_dataset"
        else:
            return "generic_response"

    def _is_large_dataset(self, content: Any) -> bool:
        """Check if content represents a large dataset."""
        if isinstance(content, dict):
            if 'rows' in content and isinstance(content['rows'], list):
                return len(content['rows']) > 100
            if 'results' in content and isinstance(content['results'], list):
                return len(content['results']) > 100
        elif isinstance(content, list):
            return len(content) > 100

        return len(str(content)) > 10000

    def _format_query_results(self, content: Any, context: FormattingContext) -> str:
        """Format query results based on assistant capabilities."""
        capabilities = context.assistant_capabilities

        if not isinstance(content, dict):
            content_dict = {"results": content}
        else:
            content_dict = content.copy()

        # Determine format based on capabilities and preferences
        if context.response_format_hint:
            target_format = context.response_format_hint
        elif ResponseFormat.MARKDOWN in capabilities.preferred_formats and capabilities.supports_tables:
            target_format = ResponseFormat.MARKDOWN
        elif ResponseFormat.VERBOSE_JSON in capabilities.preferred_formats:
            target_format = ResponseFormat.VERBOSE_JSON
        else:
            target_format = ResponseFormat.JSON

        if target_format == ResponseFormat.MARKDOWN and 'rows' in content_dict:
            return self._format_as_markdown_table(content_dict, context)
        elif target_format == ResponseFormat.VERBOSE_JSON:
            return self._format_as_verbose_json(content_dict, context)
        else:
            return self._format_as_compact_json(content_dict, context)

    def _format_analysis_results(self, content: Any, context: FormattingContext) -> str:
        """Format analysis results with appropriate detail level."""
        capabilities = context.assistant_capabilities

        if not isinstance(content, dict):
            try:
                content_dict = json.loads(str(content))
            except:
                content_dict = {"analysis": str(content)}
        else:
            content_dict = content.copy()

        # Add metadata and suggestions based on capabilities
        if capabilities.include_metadata:
            content_dict['metadata'] = {
                'tool': context.tool_name,
                'verbosity': capabilities.preferred_verbosity.value,
                'timestamp': self._get_timestamp(capabilities.timezone_aware)
            }

        if capabilities.include_suggestions and 'recommendations' not in content_dict:
            content_dict['usage_suggestions'] = self._generate_usage_suggestions(context)

        # Format based on verbosity preference
        if capabilities.preferred_verbosity == VerbosityLevel.COMPREHENSIVE:
            return self._format_comprehensive_analysis(content_dict, context)
        elif capabilities.preferred_verbosity == VerbosityLevel.DETAILED:
            return self._format_detailed_analysis(content_dict, context)
        elif capabilities.preferred_verbosity == VerbosityLevel.MINIMAL:
            return self._format_minimal_analysis(content_dict, context)
        else:
            return json.dumps(content_dict, indent=2, default=str)

    def _format_performance_stats(self, content: Any, context: FormattingContext) -> str:
        """Format performance statistics appropriately."""
        capabilities = context.assistant_capabilities

        if isinstance(content, str):
            try:
                content_dict = json.loads(content)
            except:
                content_dict = {"stats": content}
        elif isinstance(content, dict):
            content_dict = content.copy()
        else:
            content_dict = {"performance_data": str(content)}

        # Add performance interpretation for detailed assistants
        if capabilities.preferred_verbosity in [VerbosityLevel.DETAILED, VerbosityLevel.COMPREHENSIVE]:
            content_dict = self._add_performance_interpretation(content_dict)

        return json.dumps(content_dict, indent=2, default=str)

    def _format_error_response(self, content: Any, context: FormattingContext) -> str:
        """Format error responses with appropriate detail."""
        capabilities = context.assistant_capabilities

        if isinstance(content, dict):
            error_dict = content.copy()
        else:
            error_dict = {"error": str(content)}

        # Add helpful context for assistants that support it
        if capabilities.include_suggestions:
            error_dict['suggestions'] = self._generate_error_suggestions(error_dict, context)

        return json.dumps(error_dict, indent=2, default=str)

    def _format_status_response(self, content: Any, context: FormattingContext) -> str:
        """Format status/success responses."""
        capabilities = context.assistant_capabilities

        if isinstance(content, dict):
            status_dict = content.copy()
        else:
            status_dict = {"status": str(content)}

        # Add timestamp for detailed assistants
        if capabilities.include_metadata:
            status_dict['timestamp'] = self._get_timestamp(capabilities.timezone_aware)

        return json.dumps(status_dict, indent=2, default=str)

    def _format_list_response(self, content: Any, context: FormattingContext) -> str:
        """Format list/array responses."""
        capabilities = context.assistant_capabilities

        if isinstance(content, (list, tuple)):
            items = list(content)
        elif isinstance(content, dict) and 'items' in content:
            items = content['items']
        else:
            items = [content]

        # Limit items for assistants with size constraints
        if capabilities.chunk_large_responses and len(items) > 50:
            limited_items = items[:50]
            result_dict = {
                "items": limited_items,
                "metadata": {
                    "total_items": len(items),
                    "displayed_items": len(limited_items),
                    "truncated": True
                }
            }
        else:
            result_dict = {
                "items": items,
                "metadata": {
                    "total_items": len(items),
                    "displayed_items": len(items),
                    "truncated": False
                }
            }

        return json.dumps(result_dict, indent=2, default=str)

    def _format_large_dataset(self, content: Any, context: FormattingContext) -> str:
        """Format large datasets with appropriate chunking."""
        capabilities = context.assistant_capabilities

        # Apply aggressive chunking for large datasets
        if capabilities.chunk_large_responses:
            return self._chunk_response(json.dumps(content, default=str), capabilities.max_chunk_size)
        else:
            return json.dumps(content, indent=2, default=str)

    def _format_generic_response(self, content: Any, context: FormattingContext) -> str:
        """Generic response formatting fallback."""
        capabilities = context.assistant_capabilities

        if isinstance(content, (dict, list)):
            if capabilities.supports_json:
                return json.dumps(content, indent=2, default=str)
            else:
                return str(content)
        else:
            return str(content)

    def _format_as_markdown_table(self, content: Dict[str, Any], context: FormattingContext) -> str:
        """Format query results as markdown table."""
        if 'rows' not in content or not content['rows']:
            return "No results found."

        rows = content['rows']
        columns = content.get('columns', list(rows[0].keys()) if rows else [])

        # Create markdown table
        lines = []

        # Header
        header = "| " + " | ".join(str(col) for col in columns) + " |"
        separator = "| " + " | ".join("---" for _ in columns) + " |"
        lines.extend([header, separator])

        # Limit rows for readability
        max_rows = 50 if context.assistant_capabilities.chunk_large_responses else len(rows)
        displayed_rows = rows[:max_rows]

        # Data rows
        for row in displayed_rows:
            row_data = []
            for col in columns:
                value = row.get(col, '')
                # Truncate long values
                str_value = str(value)
                if len(str_value) > 50:
                    str_value = str_value[:47] + "..."
                row_data.append(str_value)

            row_line = "| " + " | ".join(row_data) + " |"
            lines.append(row_line)

        # Add summary
        if len(rows) > max_rows:
            lines.append(f"\n*Showing {max_rows} of {len(rows)} results*")

        lines.append(f"\n**Total Results:** {len(rows)}")

        return "\n".join(lines)

    def _format_as_verbose_json(self, content: Dict[str, Any], context: FormattingContext) -> str:
        """Format as verbose JSON with metadata."""
        result = content.copy()

        # Add verbose metadata
        result['response_metadata'] = {
            'tool': context.tool_name,
            'client_id': context.client_id,
            'assistant_type': context.assistant_capabilities.assistant_type.value,
            'content_size': context.content_size,
            'timestamp': self._get_timestamp(context.assistant_capabilities.timezone_aware)
        }

        return json.dumps(result, indent=2, default=str, ensure_ascii=False)

    def _format_as_compact_json(self, content: Dict[str, Any], context: FormattingContext) -> str:
        """Format as compact JSON."""
        return json.dumps(content, separators=(',', ':'), default=str, ensure_ascii=False)

    def _apply_post_processing(self, content: str, context: FormattingContext) -> str:
        """Apply post-processing based on assistant capabilities."""
        capabilities = context.assistant_capabilities

        # Handle chunking for large responses
        if capabilities.chunk_large_responses and len(content) > capabilities.max_chunk_size:
            return self._chunk_response(content, capabilities.max_chunk_size)

        # Handle Unicode support
        if not capabilities.supports_unicode:
            content = content.encode('ascii', 'ignore').decode('ascii')

        # Truncate if necessary
        if capabilities.max_response_length and len(content) > capabilities.max_response_length:
            truncation_msg = "\n\n[Response truncated due to length limits]"
            max_content_length = capabilities.max_response_length - len(truncation_msg)
            content = content[:max_content_length] + truncation_msg

        return content

    def _chunk_response(self, content: str, chunk_size: int) -> str:
        """Chunk large responses into manageable pieces."""
        if len(content) <= chunk_size:
            return content

        # For JSON content, try to chunk at logical boundaries
        if content.strip().startswith('{'):
            return self._chunk_json_response(content, chunk_size)
        else:
            # Simple text chunking
            chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
            chunked_content = chunks[0]
            if len(chunks) > 1:
                chunked_content += f"\n\n[Content chunked: showing part 1 of {len(chunks)}]"
            return chunked_content

    def _chunk_json_response(self, content: str, chunk_size: int) -> str:
        """Chunk JSON response intelligently."""
        try:
            data = json.loads(content)

            # If it's a list, chunk the list
            if isinstance(data, list):
                chunk_count = max(1, len(content) // chunk_size)
                items_per_chunk = max(1, len(data) // chunk_count)
                first_chunk = data[:items_per_chunk]

                result = {
                    "data": first_chunk,
                    "metadata": {
                        "chunk_info": f"Showing {len(first_chunk)} of {len(data)} items",
                        "total_items": len(data),
                        "chunked": True
                    }
                }
                return json.dumps(result, indent=2, default=str)

            # For other data types, return truncated version
            return json.dumps(data, indent=2, default=str)[:chunk_size]

        except json.JSONDecodeError:
            # Fallback to simple text chunking
            return content[:chunk_size]

    def _get_timestamp(self, timezone_aware: bool) -> str:
        """Get timestamp string."""
        from datetime import datetime
        if timezone_aware:
            return datetime.now().isoformat()
        else:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _generate_usage_suggestions(self, context: FormattingContext) -> List[str]:
        """Generate usage suggestions based on context."""
        suggestions = []

        tool_name = context.tool_name

        if "query" in tool_name:
            suggestions.extend([
                "Try adding LIMIT clause to control result size",
                "Use ORDER BY to sort results",
                "Consider using FTS for text searches"
            ])
        elif "analysis" in tool_name:
            suggestions.extend([
                "Use different grouping strategies for varied insights",
                "Adjust content quality filters for better results",
                "Combine multiple analysis types for comprehensive understanding"
            ])

        return suggestions[:3]  # Limit to 3 suggestions

    def _generate_error_suggestions(self, error_dict: Dict[str, Any], context: FormattingContext) -> List[str]:
        """Generate error recovery suggestions."""
        error_msg = str(error_dict.get('error', '')).lower()
        suggestions = []

        if 'timeout' in error_msg:
            suggestions.append("Try reducing the scope of your query or request")
        if 'syntax' in error_msg:
            suggestions.append("Check your SQL syntax and table names")
        if 'permission' in error_msg:
            suggestions.append("Verify you have access to the requested resources")

        if not suggestions:
            suggestions.append("Review the error message and adjust your request accordingly")

        return suggestions

    def _add_performance_interpretation(self, stats_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Add performance interpretation to statistics."""
        result = stats_dict.copy()

        # Add interpretation section
        result['interpretation'] = {
            'status': 'unknown',
            'recommendations': []
        }

        # Analyze performance metrics if available
        if 'avg_execution_time' in stats_dict:
            avg_time = stats_dict['avg_execution_time']
            if avg_time < 0.5:
                result['interpretation']['status'] = 'excellent'
            elif avg_time < 2.0:
                result['interpretation']['status'] = 'good'
            else:
                result['interpretation']['status'] = 'needs_attention'
                result['interpretation']['recommendations'].append('Consider query optimization')

        return result

    def _format_comprehensive_analysis(self, content: Dict[str, Any], context: FormattingContext) -> str:
        """Format analysis with comprehensive detail."""
        # Add detailed explanations and context
        enhanced_content = content.copy()
        enhanced_content['detailed_explanation'] = "Comprehensive analysis includes all available insights and recommendations."
        return json.dumps(enhanced_content, indent=2, default=str)

    def _format_detailed_analysis(self, content: Dict[str, Any], context: FormattingContext) -> str:
        """Format analysis with detailed information."""
        return json.dumps(content, indent=2, default=str)

    def _format_minimal_analysis(self, content: Dict[str, Any], context: FormattingContext) -> str:
        """Format analysis with minimal information."""
        # Extract only key results
        minimal_content = {}

        for key in ['summary', 'results', 'key_insights', 'main_findings']:
            if key in content:
                minimal_content[key] = content[key]

        if not minimal_content:
            minimal_content = {'summary': 'Analysis completed', 'results': content}

        return json.dumps(minimal_content, separators=(',', ':'), default=str)


def create_response_formatter() -> ResponseFormatter:
    """Create a response formatter instance."""
    return ResponseFormatter()