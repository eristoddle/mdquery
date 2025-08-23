"""
Tag parser for extracting tags from frontmatter and inline content.
"""

from typing import Any, Dict, List


class TagParser:
    """Parser for extracting tags from both frontmatter and content."""

    def parse_frontmatter_tags(self, frontmatter: Dict[str, Any]) -> List[str]:
        """
        Extract tags from frontmatter arrays.

        Args:
            frontmatter: Parsed frontmatter dictionary

        Returns:
            List of normalized tag strings
        """
        # Implementation will be added in task 5
        return []

    def parse_inline_tags(self, content: str) -> List[str]:
        """
        Extract inline hashtags from markdown content.

        Args:
            content: Markdown content to scan for tags

        Returns:
            List of normalized tag strings
        """
        # Implementation will be added in task 5
        return []