"""
Tests for Obsidian parser functionality.
"""

import pytest
from pathlib import Path
from mdquery.parsers.obsidian import ObsidianParser


class TestObsidianParser:
    """Test cases for ObsidianParser."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = ObsidianParser()

    def test_parse_wikilinks_basic(self):
        """Test parsing basic wikilinks."""
        content = """
        This is a [[Basic Link]] and another [[Page|With Alias]].
        """

        wikilinks = self.parser.parse_wikilinks(content)

        assert len(wikilinks) == 2

        # First link
        assert wikilinks[0]['link_text'] == 'Basic Link'
        assert wikilinks[0]['link_target'] == 'Basic Link'
        assert wikilinks[0]['obsidian_type'] == 'page'
        assert wikilinks[0]['has_alias'] is False

        # Second link with alias
        assert wikilinks[1]['link_text'] == 'With Alias'
        assert wikilinks[1]['link_target'] == 'Page'
        assert wikilinks[1]['obsidian_type'] == 'page'
        assert wikilinks[1]['has_alias'] is True

    def test_parse_wikilinks_sections(self):
        """Test parsing wikilinks with section references."""
        content = """
        Link to [[Page#Section]] and [[Another Page#Header|Custom Text]].
        """

        wikilinks = self.parser.parse_wikilinks(content)

        assert len(wikilinks) == 2

        # Section link
        assert wikilinks[0]['link_target'] == 'Page'
        assert wikilinks[0]['section'] == 'Section'
        assert wikilinks[0]['obsidian_type'] == 'section'

        # Section link with alias
        assert wikilinks[1]['link_target'] == 'Another Page'
        assert wikilinks[1]['section'] == 'Header'
        assert wikilinks[1]['link_text'] == 'Custom Text'
        assert wikilinks[1]['has_alias'] is True

    def test_parse_wikilinks_blocks(self):
        """Test parsing wikilinks with block references."""
        content = """
        Reference to [[Page#^block-123]] and [[Note#^abc-def|Block Link]].
        """

        wikilinks = self.parser.parse_wikilinks(content)

        assert len(wikilinks) == 2

        # Block reference
        assert wikilinks[0]['link_target'] == 'Page'
        assert wikilinks[0]['block_id'] == 'block-123'
        assert wikilinks[0]['obsidian_type'] == 'block'

        # Block reference with alias
        assert wikilinks[1]['link_target'] == 'Note'
        assert wikilinks[1]['block_id'] == 'abc-def'
        assert wikilinks[1]['link_text'] == 'Block Link'

    def test_parse_embeds(self):
        """Test parsing embedded content."""
        content = """
        Embed this: ![[Document]] and this with alias: ![[Image|Alt Text]].
        """

        embeds = self.parser.parse_embeds(content)

        assert len(embeds) == 2

        assert embeds[0]['embed_target'] == 'Document'
        assert embeds[0]['embed_alias'] is None

        assert embeds[1]['embed_target'] == 'Image'
        assert embeds[1]['embed_alias'] == 'Alt Text'

    def test_parse_templates(self):
        """Test parsing template syntax."""
        content = """
        Use template {{daily-note}} and {{meeting:project-x}}.
        """

        templates = self.parser.parse_templates(content)

        assert len(templates) == 2

        assert templates[0]['template_name'] == 'daily-note'
        assert templates[0]['template_arg'] is None

        assert templates[1]['template_name'] == 'meeting'
        assert templates[1]['template_arg'] == 'project-x'

    def test_parse_callouts(self):
        """Test parsing Obsidian callouts."""
        content = """
        > [!note] This is a note
        Some content here.

        > [!warning]
        Warning without title.

        > [!tip] Pro Tip
        """

        callouts = self.parser.parse_callouts(content)

        assert len(callouts) == 3

        assert callouts[0]['callout_type'] == 'note'
        assert callouts[0]['callout_title'] == 'This is a note'

        assert callouts[1]['callout_type'] == 'warning'
        assert callouts[1]['callout_title'] is None

        assert callouts[2]['callout_type'] == 'tip'
        assert callouts[2]['callout_title'] == 'Pro Tip'

    def test_parse_block_references(self):
        """Test parsing block reference definitions."""
        content = """
        This is some content. ^block-1

        Another paragraph here. ^my-block
        """

        block_refs = self.parser.parse_block_references(content)

        assert len(block_refs) == 2

        assert block_refs[0]['block_id'] == 'block-1'
        assert block_refs[1]['block_id'] == 'my-block'

    def test_parse_dataview_queries(self):
        """Test parsing Dataview query blocks."""
        content = """
        ```dataview
        LIST FROM #project
        WHERE status = "active"
        ```

        Some other content.

        ```dataview
        TABLE file.name, status
        FROM "Projects"
        ```
        """

        queries = self.parser.parse_dataview_queries(content)

        assert len(queries) == 2

        assert 'LIST FROM #project' in queries[0]['query_content']
        assert 'WHERE status = "active"' in queries[0]['query_content']

        assert 'TABLE file.name, status' in queries[1]['query_content']
        assert 'FROM "Projects"' in queries[1]['query_content']

    def test_parse_obsidian_tags(self):
        """Test parsing Obsidian-style tags with nesting."""
        content = """
        #simple-tag #nested/tag #deep/nested/structure
        #project/ai/development #status/in-progress
        """

        tags = self.parser.parse_obsidian_tags(content)

        expected_tags = [
            'deep/nested/structure',
            'nested/tag',
            'project/ai/development',
            'simple-tag',
            'status/in-progress'
        ]

        assert sorted(tags) == sorted(expected_tags)

    def test_sanitize_content_for_parsing(self):
        """Test content sanitization for template handling."""
        content = """
        Regular content here.
        {{template-name}}
        More content.
        {{complex:template:with:args}}

        ```dataview
        LIST FROM #tag
        ```

        Final content.
        """

        sanitized = self.parser.sanitize_content_for_parsing(content)

        # Templates should be replaced with placeholders
        assert '{{template-name}}' not in sanitized
        assert '[TEMPLATE:template-name]' in sanitized
        assert '[TEMPLATE:complex]' in sanitized

        # Dataview queries should be replaced
        assert 'LIST FROM #tag' not in sanitized
        assert '[DATAVIEW_QUERY]' in sanitized

    def test_find_backlinks(self):
        """Test finding potential backlinks."""
        file_path = Path('/vault/My Note.md')
        content = """
        ---
        aliases: [Alternative Name, Alt]
        ---

        Content here.
        """

        backlinks = self.parser.find_backlinks(content, file_path)

        expected = ['My Note', 'My Note.md', 'Alternative Name', 'Alt']
        assert sorted(backlinks) == sorted(expected)

    def test_build_graph_connections(self):
        """Test building graph connection data."""
        content = """
        Link to [[Page A]] and [[Page B]].
        Embed ![[Document C]].
        Another link to [[Page A]] for stronger connection.
        """

        graph_data = self.parser.build_graph_connections(content)

        # Should have outgoing links
        assert 'Page A' in graph_data['outgoing_links']
        assert 'Page B' in graph_data['outgoing_links']

        # Should have embeds
        assert 'Document C' in graph_data['embeds']

        # Page A should have higher connection strength (appears twice)
        assert graph_data['connection_strength']['Page A'] == 2
        assert graph_data['connection_strength']['Page B'] == 1
        assert graph_data['connection_strength']['Document C'] == 2  # Embeds are stronger

    def test_extract_enhanced_links(self):
        """Test extracting both standard and Obsidian links."""
        content = """
        Standard [markdown link](https://example.com).
        Wikilink [[Internal Page]].
        Another [link](./local-file.md).
        """

        links = self.parser.extract_enhanced_links(content)

        # Should have both markdown and wikilinks
        link_types = [link['link_type'] for link in links]
        assert 'markdown' in link_types
        assert 'wikilink' in link_types

        # Should have correct targets
        targets = [link['link_target'] for link in links]
        assert 'https://example.com' in targets
        assert 'Internal Page' in targets
        assert './local-file.md' in targets

    def test_get_obsidian_metadata(self):
        """Test getting comprehensive Obsidian metadata."""
        content = """
        ---
        tags: [project, ai]
        ---

        # My Note

        Link to [[Other Note]] and embed ![[Image]].

        > [!note] Important
        This is a callout.

        {{template-usage}}

        #additional-tag
        """

        file_path = Path('/vault/My Note.md')
        metadata = self.parser.get_obsidian_metadata(content, file_path)

        # Should have all feature types
        assert 'obsidian_features' in metadata
        assert 'enhanced_tags' in metadata
        assert 'enhanced_links' in metadata
        assert 'graph_data' in metadata

        # Should detect feature presence
        assert metadata['has_templates'] is True
        assert metadata['has_callouts'] is True
        assert metadata['has_dataview'] is False

    def test_normalize_obsidian_tag(self):
        """Test Obsidian tag normalization."""
        # Valid tags
        assert self.parser._normalize_obsidian_tag('simple') == 'simple'
        assert self.parser._normalize_obsidian_tag('nested/tag') == 'nested/tag'
        assert self.parser._normalize_obsidian_tag('Deep/Nested/Structure') == 'deep/nested/structure'
        assert self.parser._normalize_obsidian_tag('tag with spaces') == 'tag-with-spaces'

        # Invalid tags
        assert self.parser._normalize_obsidian_tag('123invalid') == ''
        assert self.parser._normalize_obsidian_tag('') == ''
        assert self.parser._normalize_obsidian_tag('tag/') == ''
        assert self.parser._normalize_obsidian_tag('/invalid') == ''
        assert self.parser._normalize_obsidian_tag('a') == ''  # Too short

    def test_complex_obsidian_document(self):
        """Test parsing a complex Obsidian document with multiple features."""
        content = """
        ---
        title: Complex Document
        tags: [project, ai, development]
        aliases: [Complex Doc, CD]
        ---

        # Complex Document

        This document demonstrates various Obsidian features.

        ## Links and References

        - Standard link: [[Basic Page]]
        - Link with alias: [[Long Page Name|Short Name]]
        - Section link: [[Other Doc#Important Section]]
        - Block reference: [[Notes#^key-insight]]

        ## Embeds

        ![[Important Image]]
        ![[Data Table|Table Caption]]

        ## Templates

        {{daily-template}}
        {{meeting:project-review}}

        ## Callouts

        > [!note] Key Point
        > This is important information.

        > [!warning]
        > Be careful here.

        ## Tags

        #status/in-progress #priority/high #team/ai-research

        ## Block References

        This is a key insight. ^key-insight

        Another important point. ^important-point

        ## Dataview Query

        ```dataview
        LIST FROM #project AND #ai
        WHERE status = "active"
        SORT file.mtime DESC
        ```

        End of document.
        """

        features = self.parser.parse_obsidian_features(content)

        # Verify all feature types are detected
        assert len(features['wikilinks']) >= 4
        assert len(features['embeds']) >= 2
        assert len(features['templates']) >= 2
        assert len(features['callouts']) >= 2
        assert len(features['block_references']) >= 2
        assert len(features['dataview_queries']) >= 1

        # Verify specific features
        wikilink_targets = [link['link_target'] for link in features['wikilinks']]
        assert 'Basic Page' in wikilink_targets
        assert 'Long Page Name' in wikilink_targets
        assert 'Other Doc' in wikilink_targets
        assert 'Notes' in wikilink_targets

        # Verify enhanced tags
        tags = self.parser.parse_obsidian_tags(content)
        assert 'status/in-progress' in tags
        assert 'priority/high' in tags
        assert 'team/ai-research' in tags