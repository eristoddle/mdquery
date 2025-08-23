"""
Link parser for extracting and categorizing links from markdown content.
"""

import re
from typing import Dict, List, Optional, Union
from urllib.parse import urlparse


class LinkParser:
    """Parser for extracting and categorizing links from markdown content."""

    def __init__(self):
        """Initialize the link parser with regex patterns."""
        # Standard markdown links: [text](url)
        # Match everything between parentheses, handling nested parens with a greedy approach
        self.markdown_link_pattern = re.compile(
            r'\[([^\]]*)\]\(([^)]+(?:\([^)]*\)[^)]*)*)\)',
            re.MULTILINE
        )

        # Wikilinks: [[page]] and [[page|alias]]
        self.wikilink_pattern = re.compile(
            r'\[\[([^|\]]+)(?:\|([^\]]+))?\]\]',
            re.MULTILINE
        )

        # Reference links: [text][ref] (we'll need to find the reference definitions)
        self.reference_link_pattern = re.compile(
            r'\[([^\]]+)\]\[([^\]]*)\]',
            re.MULTILINE
        )

        # Reference definitions: [ref]: url "title"
        self.reference_def_pattern = re.compile(
            r'^\s*\[([^\]]+)\]:\s*([^\s]+)(?:\s+"([^"]*)")?',
            re.MULTILINE
        )

        # Auto-links: <url>
        self.autolink_pattern = re.compile(
            r'<(https?://[^>]+)>',
            re.MULTILINE
        )

    def parse(self, content: str) -> List[Dict[str, Union[str, bool]]]:
        """
        Extract and categorize all links from markdown content.

        Args:
            content: Markdown content to scan for links

        Returns:
            List of link dictionaries with text, target, type, and is_internal fields
        """
        links = []

        # Parse reference definitions first (needed for reference links)
        reference_defs = self._parse_reference_definitions(content)

        # Extract different types of links
        links.extend(self._parse_markdown_links(content))
        links.extend(self._parse_wikilinks(content))
        links.extend(self._parse_reference_links(content, reference_defs))
        links.extend(self._parse_autolinks(content))

        return links

    def _parse_markdown_links(self, content: str) -> List[Dict[str, Union[str, bool]]]:
        """Parse standard markdown links [text](url)."""
        links = []

        # Use a simpler approach: find [text]( and then manually parse the URL part
        i = 0
        while i < len(content):
            # Find the start of a potential markdown link
            start = content.find('[', i)
            if start == -1:
                break

            # Find the closing bracket
            bracket_end = content.find(']', start + 1)
            if bracket_end == -1:
                i = start + 1
                continue

            # Check if this is followed by an opening parenthesis
            if bracket_end + 1 >= len(content) or content[bracket_end + 1] != '(':
                i = start + 1
                continue

            # Extract the link text
            link_text = content[start + 1:bracket_end]

            # Find the matching closing parenthesis, handling nested parentheses
            paren_start = bracket_end + 2
            paren_count = 1
            paren_end = paren_start

            while paren_end < len(content) and paren_count > 0:
                if content[paren_end] == '(':
                    paren_count += 1
                elif content[paren_end] == ')':
                    paren_count -= 1
                paren_end += 1

            if paren_count == 0:
                # Successfully found matching parenthesis
                link_target = content[paren_start:paren_end - 1].strip()

                if link_target:  # Skip empty targets
                    links.append({
                        'link_text': link_text,
                        'link_target': link_target,
                        'link_type': 'markdown',
                        'is_internal': self._is_internal_link(link_target)
                    })

                i = paren_end
            else:
                i = start + 1

        return links

    def _parse_wikilinks(self, content: str) -> List[Dict[str, Union[str, bool]]]:
        """Parse wikilinks [[page]] and [[page|alias]]."""
        links = []

        for match in self.wikilink_pattern.finditer(content):
            page = match.group(1).strip()
            alias = match.group(2)

            # Skip empty pages
            if not page:
                continue

            link_text = alias.strip() if alias else page

            links.append({
                'link_text': link_text,
                'link_target': page,
                'link_type': 'wikilink',
                'is_internal': True  # Wikilinks are always internal
            })

        return links

    def _parse_reference_links(self, content: str, reference_defs: Dict[str, str]) -> List[Dict[str, Union[str, bool]]]:
        """Parse reference links [text][ref]."""
        links = []

        for match in self.reference_link_pattern.finditer(content):
            link_text = match.group(1).strip()
            ref_key = match.group(2).strip() or link_text.lower()

            # Look up the reference definition
            link_target = reference_defs.get(ref_key.lower())

            if link_target:
                links.append({
                    'link_text': link_text,
                    'link_target': link_target,
                    'link_type': 'reference',
                    'is_internal': self._is_internal_link(link_target)
                })

        return links

    def _parse_autolinks(self, content: str) -> List[Dict[str, Union[str, bool]]]:
        """Parse auto-links <url>."""
        links = []

        for match in self.autolink_pattern.finditer(content):
            link_target = match.group(1).strip()

            links.append({
                'link_text': None,  # Auto-links don't have separate text
                'link_target': link_target,
                'link_type': 'autolink',
                'is_internal': False  # Auto-links are always external URLs
            })

        return links

    def _parse_reference_definitions(self, content: str) -> Dict[str, str]:
        """Parse reference definitions [ref]: url."""
        reference_defs = {}

        for match in self.reference_def_pattern.finditer(content):
            ref_key = match.group(1).strip().lower()
            url = match.group(2).strip()

            reference_defs[ref_key] = url

        return reference_defs

    def _is_internal_link(self, target: str) -> bool:
        """
        Determine if a link target is internal or external.

        Args:
            target: Link target URL or path

        Returns:
            True if the link is internal, False if external
        """
        # Empty targets are considered internal
        if not target:
            return True

        # Parse the URL
        parsed = urlparse(target)

        # If it has a scheme (http, https, ftp, etc.), it's external
        if parsed.scheme:
            return False

        # If it starts with //, it's a protocol-relative external URL
        if target.startswith('//'):
            return False

        # If it contains @ (email), it's external
        if '@' in target and target.startswith('mailto:'):
            return False

        # Everything else is considered internal (relative paths, anchors, etc.)
        return True

    def get_internal_links(self, content: str) -> List[Dict[str, Union[str, bool]]]:
        """Get only internal links from content."""
        all_links = self.parse(content)
        return [link for link in all_links if link['is_internal']]

    def get_external_links(self, content: str) -> List[Dict[str, Union[str, bool]]]:
        """Get only external links from content."""
        all_links = self.parse(content)
        return [link for link in all_links if not link['is_internal']]

    def get_wikilinks(self, content: str) -> List[Dict[str, Union[str, bool]]]:
        """Get only wikilinks from content."""
        all_links = self.parse(content)
        return [link for link in all_links if link['link_type'] == 'wikilink']

    def get_link_targets(self, content: str) -> List[str]:
        """Get a list of all unique link targets."""
        all_links = self.parse(content)
        targets = set()
        for link in all_links:
            targets.add(link['link_target'])
        return sorted(list(targets))

    def count_links_by_type(self, content: str) -> Dict[str, int]:
        """Count links by type."""
        all_links = self.parse(content)
        counts = {
            'markdown': 0,
            'wikilink': 0,
            'reference': 0,
            'autolink': 0,
            'internal': 0,
            'external': 0
        }

        for link in all_links:
            link_type = link['link_type']
            counts[link_type] += 1

            if link['is_internal']:
                counts['internal'] += 1
            else:
                counts['external'] += 1

        return counts