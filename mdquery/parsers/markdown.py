"""
Markdown content parser for extracting content, headings, and structure.
"""

import re
from typing import Dict, List, Tuple, NamedTuple
from dataclasses import dataclass
import markdown
from markdown.extensions import toc


@dataclass
class HeadingInfo:
    """Information about a heading in the markdown content."""
    level: int
    text: str
    anchor: str
    line_number: int


class ParsedMarkdown(NamedTuple):
    """Result of parsing markdown content."""
    sanitized_content: str
    headings: List[HeadingInfo]
    word_count: int
    heading_hierarchy: Dict[str, List[str]]
    plain_text: str


class MarkdownParser:
    """Parser for extracting content and structure from markdown body."""

    def __init__(self):
        """Initialize the markdown parser with extensions."""
        self.md = markdown.Markdown(
            extensions=[
                'toc',
                'tables',
                'fenced_code',
                'codehilite',
                'attr_list',
                'def_list',
                'footnotes',
                'md_in_html'
            ],
            extension_configs={
                'toc': {
                    'anchorlink': True,
                    'permalink': True,
                }
            }
        )

    def parse(self, content: str) -> ParsedMarkdown:
        """
        Parse markdown content to extract text, headings, and word count.

        Args:
            content: Markdown content (without frontmatter)

        Returns:
            ParsedMarkdown with sanitized content, headings, word count, and hierarchy
        """
        if not content.strip():
            return ParsedMarkdown("", [], 0, {}, "")

        # Reset the markdown parser state
        self.md.reset()

        # Convert markdown to HTML to extract structure
        html_content = self.md.convert(content)

        # Extract headings from the TOC extension
        headings = self._extract_headings(content)

        # Create heading hierarchy
        hierarchy = self._build_heading_hierarchy(headings)

        # Extract plain text for word counting and FTS5 indexing
        plain_text = self._extract_plain_text(content)

        # Sanitize content for FTS5 (remove markdown syntax, keep text)
        sanitized_content = self._sanitize_for_fts5(plain_text)

        # Count words in plain text
        word_count = self._count_words(plain_text)

        return ParsedMarkdown(
            sanitized_content=sanitized_content,
            headings=headings,
            word_count=word_count,
            heading_hierarchy=hierarchy,
            plain_text=plain_text
        )

    def _extract_headings(self, content: str) -> List[HeadingInfo]:
        """Extract headings with their levels and text."""
        headings = []
        lines = content.split('\n')

        # Regex patterns for different heading styles
        atx_pattern = re.compile(r'^(#{1,6})\s+(.+?)(?:\s+#*)?$')  # # Heading
        setext_pattern1 = re.compile(r'^=+$')  # ===== (H1)
        setext_pattern2 = re.compile(r'^-+$')  # ----- (H2)

        for i, line in enumerate(lines):
            line = line.strip()

            # ATX-style headings (# ## ### etc.)
            match = atx_pattern.match(line)
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                anchor = self._create_anchor(text)
                headings.append(HeadingInfo(level, text, anchor, i + 1))
                continue

            # Setext-style headings (underlined)
            if i > 0 and line:
                prev_line = lines[i - 1].strip()
                if prev_line and setext_pattern1.match(line):
                    # H1 with === underline
                    anchor = self._create_anchor(prev_line)
                    headings.append(HeadingInfo(1, prev_line, anchor, i))
                elif prev_line and setext_pattern2.match(line):
                    # H2 with --- underline
                    anchor = self._create_anchor(prev_line)
                    headings.append(HeadingInfo(2, prev_line, anchor, i))

        return headings

    def _create_anchor(self, text: str) -> str:
        """Create URL-safe anchor from heading text."""
        # Remove markdown formatting
        text = re.sub(r'[*_`~]', '', text)
        # Convert to lowercase and replace spaces/special chars with hyphens
        anchor = re.sub(r'[^\w\s-]', '', text.lower())
        anchor = re.sub(r'[-\s]+', '-', anchor)
        return anchor.strip('-')

    def _build_heading_hierarchy(self, headings: List[HeadingInfo]) -> Dict[str, List[str]]:
        """Build a hierarchical structure of headings."""
        hierarchy = {}
        stack = []  # Stack to track current path

        for heading in headings:
            # Pop stack until we find the right parent level
            while stack and stack[-1]['level'] >= heading.level:
                stack.pop()

            # Create path from root to current heading
            path = [item['text'] for item in stack] + [heading.text]
            path_key = ' > '.join(path)

            # Store the full path
            hierarchy[heading.text] = path[:-1]  # Parent path

            # Add current heading to stack
            stack.append({'level': heading.level, 'text': heading.text})

        return hierarchy

    def _extract_plain_text(self, content: str) -> str:
        """Extract plain text from markdown, removing all formatting."""
        # Remove code blocks first (to avoid processing their content)
        content = re.sub(r'```[\s\S]*?```', ' ', content)
        content = re.sub(r'`([^`]+)`', r'\1', content)  # Keep inline code content

        # Remove HTML tags
        content = re.sub(r'<[^>]+>', ' ', content)

        # Remove markdown formatting
        content = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', content)  # Images
        content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)   # Links
        content = re.sub(r'\[([^\]]+)\]\[[^\]]*\]', r'\1', content) # Reference links
        content = re.sub(r'\[\[([^\]]+)\]\]', r'\1', content)       # Wikilinks
        content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)        # Bold
        content = re.sub(r'__([^_]+)__', r'\1', content)            # Bold alt
        content = re.sub(r'\*([^*]+)\*', r'\1', content)            # Italic
        content = re.sub(r'_([^_]+)_', r'\1', content)              # Italic alt
        content = re.sub(r'~~([^~]+)~~', r'\1', content)            # Strikethrough
        content = re.sub(r'^#{1,6}\s+', '', content, flags=re.MULTILINE)  # Headings
        content = re.sub(r'^[=-]+$', '', content, flags=re.MULTILINE)     # Setext underlines
        content = re.sub(r'^\s*[-*+]\s+', '', content, flags=re.MULTILINE)  # List bullets
        content = re.sub(r'^\s*\d+\.\s+', '', content, flags=re.MULTILINE)  # Numbered lists
        content = re.sub(r'^>\s*', '', content, flags=re.MULTILINE)         # Blockquotes
        content = re.sub(r'^\s*\|.*\|.*$', '', content, flags=re.MULTILINE) # Tables

        # Clean up whitespace
        content = re.sub(r'\n+', ' ', content)
        content = re.sub(r'\s+', ' ', content)

        return content.strip()

    def _sanitize_for_fts5(self, plain_text: str) -> str:
        """Sanitize text for FTS5 indexing."""
        # FTS5 has issues with certain characters, so we clean them up
        # Remove or replace problematic characters
        sanitized = plain_text

        # Replace smart quotes and similar characters
        sanitized = sanitized.replace('\u201c', '"').replace('\u201d', '"')  # Left and right double quotes
        sanitized = sanitized.replace('\u2018', "'").replace('\u2019', "'")  # Left and right single quotes
        sanitized = sanitized.replace('–', '-').replace('—', '-')
        sanitized = sanitized.replace('…', '...')

        # Remove control characters except newlines and tabs
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', sanitized)

        # Normalize whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized)

        return sanitized.strip()

    def _count_words(self, text: str) -> int:
        """Count words in the text."""
        if not text.strip():
            return 0

        # Split on whitespace and filter out empty strings
        words = [word for word in re.split(r'\s+', text.strip()) if word]
        return len(words)

    def get_heading_text_only(self, headings: List[HeadingInfo]) -> List[str]:
        """Extract just the heading text for simple queries."""
        return [heading.text for heading in headings]

    def get_headings_by_level(self, headings: List[HeadingInfo], level: int) -> List[HeadingInfo]:
        """Get all headings of a specific level."""
        return [h for h in headings if h.level == level]