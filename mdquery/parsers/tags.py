"""
Tag parser for extracting tags from frontmatter and inline content.
"""

import re
from typing import Any, Dict, List, Set, Union


class TagParser:
    """Parser for extracting tags from both frontmatter and content."""

    def __init__(self):
        """Initialize the tag parser with regex patterns."""
        # Pattern for inline hashtags - must start with letter, can contain alphanumeric, underscore, hyphen, and forward slash
        # We'll do more validation in the normalization function
        self.hashtag_pattern = re.compile(
            r'#([a-zA-Z][a-zA-Z0-9_/-]*)',
            re.MULTILINE
        )

        # Common frontmatter keys that contain tags
        self.tag_keys = {'tags', 'tag', 'categories', 'category', 'keywords', 'topics'}

    def parse_frontmatter_tags(self, frontmatter: Dict[str, Any]) -> List[str]:
        """
        Extract tags from frontmatter arrays.

        Args:
            frontmatter: Parsed frontmatter dictionary

        Returns:
            List of normalized tag strings
        """
        tags = set()

        for key, value_data in frontmatter.items():
            # Check if this key is likely to contain tags
            if key.lower() in self.tag_keys:
                tags.update(self._extract_tags_from_value(value_data))

        return sorted(list(tags))

    def parse_inline_tags(self, content: str) -> List[str]:
        """
        Extract inline hashtags from markdown content.

        Args:
            content: Markdown content to scan for tags

        Returns:
            List of normalized tag strings
        """
        tags = set()

        # Find all hashtag matches
        matches = self.hashtag_pattern.findall(content)

        for match in matches:
            # Normalize the tag
            normalized_tag = self._normalize_tag(match)
            if normalized_tag:
                tags.add(normalized_tag)

        return sorted(list(tags))

    def parse_all_tags(self, frontmatter: Dict[str, Any], content: str) -> Dict[str, List[str]]:
        """
        Extract tags from both frontmatter and content.

        Args:
            frontmatter: Parsed frontmatter dictionary
            content: Markdown content to scan for tags

        Returns:
            Dictionary with 'frontmatter' and 'content' keys containing tag lists
        """
        return {
            'frontmatter': self.parse_frontmatter_tags(frontmatter),
            'content': self.parse_inline_tags(content)
        }

    def get_all_unique_tags(self, frontmatter: Dict[str, Any], content: str) -> List[str]:
        """
        Get all unique tags from both frontmatter and content combined.

        Args:
            frontmatter: Parsed frontmatter dictionary
            content: Markdown content to scan for tags

        Returns:
            Sorted list of all unique normalized tags
        """
        all_tags = set()

        # Add frontmatter tags
        all_tags.update(self.parse_frontmatter_tags(frontmatter))

        # Add inline tags
        all_tags.update(self.parse_inline_tags(content))

        return sorted(list(all_tags))

    def _extract_tags_from_value(self, value_data: Any) -> Set[str]:
        """
        Extract tags from a frontmatter value, handling different data structures.

        Args:
            value_data: Value from frontmatter (could be typed data from FrontmatterParser)

        Returns:
            Set of normalized tag strings
        """
        tags = set()

        # Handle typed frontmatter data from FrontmatterParser
        if isinstance(value_data, dict) and 'value' in value_data:
            actual_value = value_data['value']
            value_type = value_data.get('type', 'string')
        else:
            actual_value = value_data
            value_type = 'unknown'

        # Handle arrays/lists
        if isinstance(actual_value, list):
            for item in actual_value:
                if isinstance(item, str):
                    normalized = self._normalize_tag(item)
                    if normalized:
                        tags.add(normalized)
                elif isinstance(item, dict) and 'value' in item:
                    # Handle nested typed data
                    if isinstance(item['value'], str):
                        normalized = self._normalize_tag(item['value'])
                        if normalized:
                            tags.add(normalized)

        # Handle single string values
        elif isinstance(actual_value, str):
            # Check if it's a comma-separated list
            if ',' in actual_value:
                for tag in actual_value.split(','):
                    normalized = self._normalize_tag(tag.strip())
                    if normalized:
                        tags.add(normalized)
            else:
                normalized = self._normalize_tag(actual_value)
                if normalized:
                    tags.add(normalized)

        return tags

    def _normalize_tag(self, tag: str) -> str:
        """
        Normalize a tag string according to common conventions.

        Args:
            tag: Raw tag string

        Returns:
            Normalized tag string, or empty string if invalid
        """
        if not tag or not isinstance(tag, str):
            return ""

        # Remove leading/trailing whitespace and hash symbols
        tag = tag.strip().lstrip('#')

        # Skip empty tags or pure numbers
        if not tag or tag.isdigit():
            return ""

        # Convert to lowercase for consistency
        tag = tag.lower()

        # Replace spaces with hyphens (common convention)
        tag = re.sub(r'\s+', '-', tag)

        # Remove any characters that aren't alphanumeric, underscore, hyphen, or forward slash
        # Do this before other validations to clean up the string
        tag = re.sub(r'[^a-z0-9_/-]', '', tag)

        # Check if the original tag (before cleaning) ends with invalid characters
        # This helps reject tags like "invalid-" or "tag/"
        original_clean = re.sub(r'[^a-z0-9_/-]', '', tag)
        if original_clean.endswith('-') or original_clean.endswith('/') or original_clean.startswith('-') or original_clean.startswith('/'):
            return ""

        # Remove leading/trailing hyphens or slashes
        tag = tag.strip('-/')

        # Skip if empty after cleanup
        if not tag:
            return ""

        # Ensure tag starts with a letter (not a number or special character)
        if not tag[0].isalpha():
            return ""

        # Require at least 2 characters for a valid tag (avoid single letters)
        if len(tag) < 2:
            return ""

        # Validate nested tags - each segment must start with a letter and be at least 2 chars
        if '/' in tag:
            segments = tag.split('/')
            for segment in segments:
                if not segment or not segment[0].isalpha() or len(segment) < 2:
                    return ""
            # Remove empty segments and double slashes
            segments = [s for s in segments if s]
            if not segments:
                return ""
            tag = '/'.join(segments)

        return tag

    def expand_nested_tags(self, tags: List[str]) -> List[str]:
        """
        Expand nested tags to include parent tags.

        For example, 'programming/python' becomes ['programming', 'programming/python']

        Args:
            tags: List of tag strings

        Returns:
            Expanded list including parent tags
        """
        expanded = set(tags)

        for tag in tags:
            if '/' in tag:
                parts = tag.split('/')
                # Add all parent paths
                for i in range(1, len(parts)):
                    parent_tag = '/'.join(parts[:i])
                    if parent_tag:
                        expanded.add(parent_tag)

        return sorted(list(expanded))

    def get_tag_hierarchy(self, tags: List[str]) -> Dict[str, List[str]]:
        """
        Build a hierarchy of tags showing parent-child relationships.

        Args:
            tags: List of tag strings

        Returns:
            Dictionary mapping parent tags to their children
        """
        hierarchy = {}

        for tag in tags:
            if '/' in tag:
                parts = tag.split('/')
                for i in range(len(parts) - 1):
                    parent = '/'.join(parts[:i+1])
                    child = '/'.join(parts[:i+2])

                    if parent not in hierarchy:
                        hierarchy[parent] = []

                    if child not in hierarchy[parent]:
                        hierarchy[parent].append(child)

        return hierarchy