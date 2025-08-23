"""
Frontmatter parser for extracting YAML/JSON/TOML frontmatter from markdown files.
"""

import json
import re
from datetime import datetime, date
from typing import Any, Dict, List, Union

import frontmatter
import toml
import yaml


class FrontmatterParser:
    """Parser for extracting and processing frontmatter from markdown files."""

    def __init__(self):
        """Initialize the frontmatter parser."""
        # Date patterns for type inference
        self.date_patterns = [
            r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
            r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',  # ISO 8601 basic
            r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z?$',  # ISO 8601 with milliseconds
            r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',  # YYYY-MM-DD HH:MM:SS
        ]

    def parse(self, content: str) -> Dict[str, Any]:
        """
        Extract frontmatter from markdown content.

        Args:
            content: Raw markdown file content

        Returns:
            Dictionary of frontmatter fields with type inference
        """
        try:
            # Use python-frontmatter to extract frontmatter
            post = frontmatter.loads(content)

            if not post.metadata:
                return {}

            # Apply type inference to all frontmatter values
            typed_metadata = {}
            for key, value in post.metadata.items():
                typed_metadata[key] = self._infer_type(value)

            return typed_metadata

        except Exception as e:
            # If frontmatter parsing fails, try manual extraction
            return self._manual_parse(content)

    def _infer_type(self, value: Any) -> Dict[str, Any]:
        """
        Infer the type of a frontmatter value and return structured data.

        Args:
            value: Raw frontmatter value

        Returns:
            Dictionary with 'value', 'type', and optionally 'original' keys
        """
        if value is None:
            return {'value': None, 'type': 'null'}

        # Handle lists/arrays
        if isinstance(value, list):
            typed_items = [self._infer_type(item) for item in value]
            return {
                'value': [item['value'] for item in typed_items],
                'type': 'array',
                'item_types': [item['type'] for item in typed_items]
            }

        # Handle dictionaries/objects
        if isinstance(value, dict):
            typed_dict = {}
            for k, v in value.items():
                typed_dict[k] = self._infer_type(v)
            return {'value': typed_dict, 'type': 'object'}

        # Handle booleans (must come before numbers since bool is subclass of int)
        if isinstance(value, bool):
            return {'value': value, 'type': 'boolean'}

        # Handle numbers
        if isinstance(value, (int, float)):
            return {'value': value, 'type': 'number'}

        # Handle datetime objects (from frontmatter parsing)
        if isinstance(value, datetime):
            return {
                'value': value.isoformat(),
                'type': 'date',
                'parsed_date': value.isoformat()
            }

        # Handle date objects
        if hasattr(value, 'year') and hasattr(value, 'month') and hasattr(value, 'day'):
            # This catches date objects
            return {
                'value': str(value),
                'type': 'date',
                'parsed_date': value.isoformat() if hasattr(value, 'isoformat') else str(value)
            }

        # Handle strings and attempt further type inference
        if isinstance(value, str):
            return self._infer_string_type(value)

        # Fallback for unknown types
        return {'value': str(value), 'type': 'string', 'original': value}

    def _infer_string_type(self, value: str) -> Dict[str, Any]:
        """
        Infer the specific type of a string value.

        Args:
            value: String value to analyze

        Returns:
            Dictionary with type information
        """
        # Check for date patterns
        for pattern in self.date_patterns:
            if re.match(pattern, value):
                try:
                    # Try to parse as datetime
                    if 'T' in value:
                        # Handle ISO 8601 formats
                        clean_value = value.replace('Z', '+00:00')
                        # Handle milliseconds by removing them for parsing
                        if '.' in clean_value and clean_value.count('.') == 1:
                            parts = clean_value.split('.')
                            if len(parts) == 2 and ('+' in parts[1] or parts[1].isdigit()):
                                # Remove milliseconds but keep timezone
                                if '+' in parts[1]:
                                    clean_value = parts[0] + '+' + parts[1].split('+')[1]
                                else:
                                    clean_value = parts[0]
                        parsed_date = datetime.fromisoformat(clean_value)
                    elif ' ' in value:
                        parsed_date = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                    else:
                        parsed_date = datetime.strptime(value, '%Y-%m-%d')

                    return {
                        'value': value,
                        'type': 'date',
                        'parsed_date': parsed_date.isoformat()
                    }
                except ValueError:
                    pass

        # Check for boolean strings
        lower_value = value.lower()
        if lower_value in ('true', 'false', 'yes', 'no', 'on', 'off'):
            bool_value = lower_value in ('true', 'yes', 'on')
            return {
                'value': value,
                'type': 'boolean_string',
                'boolean_value': bool_value
            }

        # Check for numeric strings
        try:
            if '.' in value:
                float_value = float(value)
                return {
                    'value': value,
                    'type': 'number_string',
                    'numeric_value': float_value
                }
            else:
                int_value = int(value)
                return {
                    'value': value,
                    'type': 'number_string',
                    'numeric_value': int_value
                }
        except ValueError:
            pass

        # Default to string
        return {'value': value, 'type': 'string'}

    def _manual_parse(self, content: str) -> Dict[str, Any]:
        """
        Manually parse frontmatter when python-frontmatter fails.

        Handles YAML, JSON, and TOML formats.

        Args:
            content: Raw markdown content

        Returns:
            Dictionary of parsed frontmatter
        """
        content = content.strip()

        # Try YAML frontmatter (--- delimited)
        yaml_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if yaml_match:
            try:
                yaml_content = yaml_match.group(1)
                parsed = yaml.safe_load(yaml_content)
                if parsed:
                    return {k: self._infer_type(v) for k, v in parsed.items()}
            except yaml.YAMLError:
                pass

        # Try JSON frontmatter ({} delimited)
        json_match = re.match(r'^{\s*\n(.*?)\n}\s*\n', content, re.DOTALL)
        if json_match:
            try:
                json_content = '{' + json_match.group(1) + '}'
                parsed = json.loads(json_content)
                if parsed:
                    return {k: self._infer_type(v) for k, v in parsed.items()}
            except json.JSONDecodeError:
                pass

        # Try TOML frontmatter (+++ delimited)
        toml_match = re.match(r'^\+\+\+\s*\n(.*?)\n\+\+\+\s*\n', content, re.DOTALL)
        if toml_match:
            try:
                toml_content = toml_match.group(1)
                parsed = toml.loads(toml_content)
                if parsed:
                    return {k: self._infer_type(v) for k, v in parsed.items()}
            except toml.TomlDecodeError:
                pass

        return {}

    def get_content_without_frontmatter(self, content: str) -> str:
        """
        Extract the markdown content without frontmatter.

        Args:
            content: Raw markdown file content

        Returns:
            Markdown content with frontmatter removed
        """
        try:
            post = frontmatter.loads(content)
            return post.content
        except Exception:
            # Manual extraction if frontmatter library fails
            return self._manual_content_extraction(content)

    def _manual_content_extraction(self, content: str) -> str:
        """
        Manually extract content without frontmatter.

        Args:
            content: Raw markdown content

        Returns:
            Content without frontmatter
        """
        content = content.strip()

        # Remove YAML frontmatter
        yaml_match = re.match(r'^---\s*\n.*?\n---\s*\n', content, re.DOTALL)
        if yaml_match:
            return content[yaml_match.end():]

        # Remove JSON frontmatter
        json_match = re.match(r'^{\s*\n.*?\n}\s*\n', content, re.DOTALL)
        if json_match:
            return content[json_match.end():]

        # Remove TOML frontmatter
        toml_match = re.match(r'^\+\+\+\s*\n.*?\n\+\+\+\s*\n', content, re.DOTALL)
        if toml_match:
            return content[toml_match.end():]

        return content