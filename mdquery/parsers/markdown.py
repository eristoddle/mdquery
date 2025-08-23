"""
Markdown content parser for extracting content, headings, and structure.
"""

from typing import List, Tuple


class MarkdownParser:
    """Parser for extracting content and structure from markdown body."""

    def parse(self, content: str) -> Tuple[str, List[str], int]:
        """
        Parse markdown content to extract text, headings, and word count.

        Args:
            content: Markdown content (without frontmatter)

        Returns:
            Tuple of (sanitized_content, headings_list, word_count)
        """
        # Implementation will be added in task 4
        return "", [], 0