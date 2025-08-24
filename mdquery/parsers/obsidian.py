"""
Obsidian-specific parser for enhanced vault compatibility.

This parser extends the existing parsers to handle Obsidian-specific features
including wikilinks, backlinks, template syntax, and graph structure mapping.
"""

import re
from typing import Dict, List, Set, Optional, Any, Tuple
from pathlib import Path

from .links import LinkParser
from .tags import TagParser
from .frontmatter import FrontmatterParser


class ObsidianParser:
    """
    Enhanced parser for Obsidian vault compatibility.

    Handles Obsidian-specific features:
    - Wikilinks with aliases: [[Page|Alias]]
    - Block references: [[Page#^block-id]]
    - Section references: [[Page#Section]]
    - Embedded content: ![[Page]]
    - Template syntax: {{template}}
    - Callouts: > [!note] Title
    - Dataview queries: ```dataview
    """

    def __init__(self):
        """Initialize the Obsidian parser with enhanced patterns."""
        # Initialize base parsers
        self.link_parser = LinkParser()
        self.tag_parser = TagParser()
        self.frontmatter_parser = FrontmatterParser()

        # Enhanced wikilink patterns for Obsidian
        # Standard wikilinks: [[Page]] or [[Page|Alias]] (no # in page name)
        self.wikilink_pattern = re.compile(
            r'\[\[([^|\]#]+)(?:\|([^\]]+))?\]\]',
            re.MULTILINE
        )

        # Wikilinks with section references: [[Page#Section]] (but not block refs starting with ^)
        self.wikilink_section_pattern = re.compile(
            r'\[\[([^|\]#]+)#([^|\^\]]+?)(?:\|([^\]]+))?\]\]',
            re.MULTILINE
        )

        # Wikilinks with block references: [[Page#^block-id]]
        self.wikilink_block_pattern = re.compile(
            r'\[\[([^|\]#]+)#\^([^|\]]+?)(?:\|([^\]]+))?\]\]',
            re.MULTILINE
        )

        # Embedded content: ![[Page]] or ![[Page|Alias]]
        self.embed_pattern = re.compile(
            r'!\[\[([^|\]#]+)(?:\|([^\]]+))?\]\]',
            re.MULTILINE
        )

        # Template syntax: {{template}} or {{template:arg}}
        self.template_pattern = re.compile(
            r'\{\{([^}:]+)(?::([^}]+))?\}\}',
            re.MULTILINE
        )

        # Callout syntax: > [!type] Title (title must be on same line)
        self.callout_pattern = re.compile(
            r'^\s*>\s*\[!([^\]]+)\](?:\s+([^\n\r]+?))?$',
            re.MULTILINE
        )

        # Block references (for creating): ^block-id
        self.block_reference_pattern = re.compile(
            r'\^([a-zA-Z0-9-]+)$',
            re.MULTILINE
        )

        # Dataview query blocks
        self.dataview_pattern = re.compile(
            r'```dataview\s*\n(.*?)\n```',
            re.DOTALL
        )

        # Tag patterns (enhanced for Obsidian nested tags)
        self.obsidian_tag_pattern = re.compile(
            r'#([a-zA-Z][a-zA-Z0-9_/-]*(?:/[a-zA-Z][a-zA-Z0-9_-]*)*)',
            re.MULTILINE
        )

    def parse_obsidian_features(self, content: str, file_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Parse all Obsidian-specific features from content.

        Args:
            content: Markdown content to parse
            file_path: Optional file path for context

        Returns:
            Dictionary containing all parsed Obsidian features
        """
        return {
            'wikilinks': self.parse_wikilinks(content),
            'embeds': self.parse_embeds(content),
            'templates': self.parse_templates(content),
            'callouts': self.parse_callouts(content),
            'block_references': self.parse_block_references(content),
            'dataview_queries': self.parse_dataview_queries(content),
            'backlinks': self.find_backlinks(content, file_path),
            'graph_connections': self.build_graph_connections(content, file_path)
        }

    def parse_wikilinks(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse all types of wikilinks including section and block references.

        Args:
            content: Content to parse

        Returns:
            List of wikilink dictionaries with enhanced metadata
        """
        wikilinks = []

        # Standard wikilinks: [[Page]] or [[Page|Alias]] (no # in page name)
        for match in self.wikilink_pattern.finditer(content):
            page = match.group(1).strip()
            alias = match.group(2)

            # Skip if this contains # (it's a section/block reference)
            if page and '#' not in page:
                wikilinks.append({
                    'link_text': alias.strip() if alias else page,
                    'link_target': page,
                    'link_type': 'wikilink',
                    'is_internal': True,
                    'obsidian_type': 'page',
                    'section': None,
                    'block_id': None,
                    'has_alias': alias is not None
                })

        # Section references: [[Page#Section]]
        for match in self.wikilink_section_pattern.finditer(content):
            page = match.group(1).strip()
            section = match.group(2).strip()
            alias = match.group(3)

            if page and section:
                display_text = alias.strip() if alias else f"{page}#{section}"
                wikilinks.append({
                    'link_text': display_text,
                    'link_target': page,
                    'link_type': 'wikilink',
                    'is_internal': True,
                    'obsidian_type': 'section',
                    'section': section,
                    'block_id': None,
                    'has_alias': alias is not None
                })

        # Block references: [[Page#^block-id]]
        for match in self.wikilink_block_pattern.finditer(content):
            page = match.group(1).strip()
            block_id = match.group(2).strip()
            alias = match.group(3)

            if page and block_id:
                display_text = alias.strip() if alias else f"{page}#^{block_id}"
                wikilinks.append({
                    'link_text': display_text,
                    'link_target': page,
                    'link_type': 'wikilink',
                    'is_internal': True,
                    'obsidian_type': 'block',
                    'section': None,
                    'block_id': block_id,
                    'has_alias': alias is not None
                })

        return wikilinks

    def parse_embeds(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse embedded content references.

        Args:
            content: Content to parse

        Returns:
            List of embed dictionaries
        """
        embeds = []

        for match in self.embed_pattern.finditer(content):
            page = match.group(1).strip()
            alias = match.group(2)

            if page:
                embeds.append({
                    'embed_target': page,
                    'embed_alias': alias.strip() if alias else None,
                    'embed_type': 'page'
                })

        return embeds

    def parse_templates(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse template syntax and mark template areas to avoid parsing errors.

        Args:
            content: Content to parse

        Returns:
            List of template dictionaries
        """
        templates = []

        for match in self.template_pattern.finditer(content):
            template_name = match.group(1).strip()
            template_arg = match.group(2)

            templates.append({
                'template_name': template_name,
                'template_arg': template_arg.strip() if template_arg else None,
                'start_pos': match.start(),
                'end_pos': match.end()
            })

        return templates

    def parse_callouts(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse Obsidian callout syntax.

        Args:
            content: Content to parse

        Returns:
            List of callout dictionaries
        """
        callouts = []

        for match in self.callout_pattern.finditer(content):
            callout_type = match.group(1).strip()
            callout_title = match.group(2)

            callouts.append({
                'callout_type': callout_type,
                'callout_title': callout_title.strip() if callout_title else None,
                'line_number': content[:match.start()].count('\n') + 1
            })

        return callouts

    def parse_block_references(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse block reference definitions.

        Args:
            content: Content to parse

        Returns:
            List of block reference dictionaries
        """
        block_refs = []

        for match in self.block_reference_pattern.finditer(content):
            block_id = match.group(1).strip()
            line_number = content[:match.start()].count('\n') + 1

            block_refs.append({
                'block_id': block_id,
                'line_number': line_number
            })

        return block_refs

    def parse_dataview_queries(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse Dataview query blocks.

        Args:
            content: Content to parse

        Returns:
            List of dataview query dictionaries
        """
        queries = []

        for match in self.dataview_pattern.finditer(content):
            query_content = match.group(1).strip()
            line_number = content[:match.start()].count('\n') + 1

            queries.append({
                'query_content': query_content,
                'line_number': line_number,
                'start_pos': match.start(),
                'end_pos': match.end()
            })

        return queries

    def find_backlinks(self, content: str, file_path: Optional[Path] = None) -> List[str]:
        """
        Find potential backlinks (pages that might link to this file).

        Args:
            content: Content to analyze
            file_path: Path of the current file

        Returns:
            List of potential backlink targets
        """
        backlinks = []

        if file_path:
            # Get the filename without extension as potential link target
            filename_stem = file_path.stem
            backlinks.append(filename_stem)

            # Also consider the full filename
            backlinks.append(file_path.name)

        # Extract any aliases from frontmatter that could be link targets
        frontmatter = self.frontmatter_parser.parse(content)
        if frontmatter:
            for key, value_data in frontmatter.items():
                if key.lower() in ('alias', 'aliases'):
                    if isinstance(value_data, dict) and 'value' in value_data:
                        value = value_data['value']
                        if isinstance(value, list):
                            backlinks.extend([str(alias) for alias in value if alias])
                        elif isinstance(value, str):
                            backlinks.append(value)

        return list(set(backlinks))  # Remove duplicates

    def build_graph_connections(self, content: str, file_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Build graph structure mapping for relationship analysis.

        Args:
            content: Content to analyze
            file_path: Path of the current file

        Returns:
            Dictionary with graph connection information
        """
        connections = {
            'outgoing_links': [],
            'potential_backlinks': [],
            'embeds': [],
            'connection_strength': {}
        }

        # Get all wikilinks as outgoing connections
        wikilinks = self.parse_wikilinks(content)
        for link in wikilinks:
            target = link['link_target']
            connections['outgoing_links'].append(target)

            # Calculate connection strength based on frequency
            if target in connections['connection_strength']:
                connections['connection_strength'][target] += 1
            else:
                connections['connection_strength'][target] = 1

        # Get embeds as strong connections (separate from wikilinks)
        embeds = self.parse_embeds(content)
        embed_targets = set()
        for embed in embeds:
            target = embed['embed_target']
            connections['embeds'].append(target)
            embed_targets.add(target)

            # Embeds are stronger connections (but don't double-count if already in wikilinks)
            if target not in connections['connection_strength']:
                connections['connection_strength'][target] = 2
            else:
                # Add embed bonus to existing connection
                connections['connection_strength'][target] += 1

        # Get potential backlinks
        connections['potential_backlinks'] = self.find_backlinks(content, file_path)

        return connections

    def sanitize_content_for_parsing(self, content: str) -> str:
        """
        Sanitize content by temporarily removing or marking template syntax
        to avoid parsing errors in other parsers.

        Args:
            content: Content to sanitize

        Returns:
            Sanitized content with templates marked
        """
        # Replace template syntax with placeholders to avoid parsing issues
        templates = self.parse_templates(content)
        sanitized = content

        # Replace templates with safe placeholders (in reverse order to maintain positions)
        for template in reversed(templates):
            start_pos = template['start_pos']
            end_pos = template['end_pos']
            placeholder = f"[TEMPLATE:{template['template_name']}]"
            sanitized = sanitized[:start_pos] + placeholder + sanitized[end_pos:]

        # Replace dataview queries with placeholders
        queries = self.parse_dataview_queries(content)
        for query in reversed(queries):
            start_pos = query['start_pos']
            end_pos = query['end_pos']
            placeholder = "[DATAVIEW_QUERY]"
            sanitized = sanitized[:start_pos] + placeholder + sanitized[end_pos:]

        return sanitized

    def parse_obsidian_tags(self, content: str) -> List[str]:
        """
        Parse tags using Obsidian-specific patterns that support deeper nesting.

        Args:
            content: Content to parse

        Returns:
            List of normalized tags
        """
        tags = set()

        # Use the enhanced tag pattern for Obsidian
        matches = self.obsidian_tag_pattern.findall(content)

        for match in matches:
            # Normalize the tag
            normalized_tag = self._normalize_obsidian_tag(match)
            if normalized_tag:
                tags.add(normalized_tag)

        return sorted(list(tags))

    def _normalize_obsidian_tag(self, tag: str) -> str:
        """
        Normalize an Obsidian tag according to Obsidian conventions.

        Args:
            tag: Raw tag string

        Returns:
            Normalized tag string, or empty string if invalid
        """
        if not tag or not isinstance(tag, str):
            return ""

        # Remove leading/trailing whitespace and hash symbols
        tag = tag.strip().lstrip('#')

        # Skip empty tags
        if not tag:
            return ""

        # Convert to lowercase for consistency (Obsidian is case-insensitive)
        tag = tag.lower()

        # Obsidian allows spaces in tags, but we'll normalize them to hyphens
        tag = re.sub(r'\s+', '-', tag)

        # Validate nested tags - each segment must be valid
        if '/' in tag:
            segments = tag.split('/')
            valid_segments = []
            for segment in segments:
                # Clean segment
                segment = segment.strip('-')
                if segment and len(segment) >= 1 and segment[0].isalpha():
                    valid_segments.append(segment)
                else:
                    return ""  # Invalid segment makes whole tag invalid

            if not valid_segments:
                return ""

            tag = '/'.join(valid_segments)

        # Ensure tag starts with a letter and is at least 2 characters
        if not tag or not tag[0].isalpha() or len(tag) < 2:
            return ""

        return tag

    def extract_enhanced_links(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract all links including standard markdown and Obsidian wikilinks.

        Args:
            content: Content to parse

        Returns:
            Combined list of all link types with enhanced metadata
        """
        all_links = []

        # Get standard markdown links
        markdown_links = self.link_parser.parse(content)
        all_links.extend(markdown_links)

        # Get Obsidian wikilinks with enhanced metadata
        wikilinks = self.parse_wikilinks(content)
        all_links.extend(wikilinks)

        return all_links

    def get_obsidian_metadata(self, content: str, file_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Get comprehensive Obsidian-specific metadata for a file.

        Args:
            content: File content
            file_path: Optional file path

        Returns:
            Dictionary with all Obsidian metadata
        """
        return {
            'obsidian_features': self.parse_obsidian_features(content, file_path),
            'enhanced_tags': self.parse_obsidian_tags(content),
            'enhanced_links': self.extract_enhanced_links(content),
            'graph_data': self.build_graph_connections(content, file_path),
            'has_templates': len(self.parse_templates(content)) > 0,
            'has_dataview': len(self.parse_dataview_queries(content)) > 0,
            'has_callouts': len(self.parse_callouts(content)) > 0
        }