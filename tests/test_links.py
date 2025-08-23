"""
Tests for the link parser module.
"""

import pytest
from mdquery.parsers.links import LinkParser


class TestLinkParser:
    """Test cases for LinkParser class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = LinkParser()

    def test_markdown_links_basic(self):
        """Test basic markdown link parsing."""
        content = "Check out [Google](https://google.com) and [GitHub](https://github.com)."

        links = self.parser.parse(content)

        assert len(links) == 2

        # Check first link
        assert links[0]['link_text'] == 'Google'
        assert links[0]['link_target'] == 'https://google.com'
        assert links[0]['link_type'] == 'markdown'
        assert links[0]['is_internal'] == False

        # Check second link
        assert links[1]['link_text'] == 'GitHub'
        assert links[1]['link_target'] == 'https://github.com'
        assert links[1]['link_type'] == 'markdown'
        assert links[1]['is_internal'] == False

    def test_markdown_links_internal(self):
        """Test internal markdown links."""
        content = "See [about page](./about.md) and [home](/) for more info."

        links = self.parser.parse(content)

        assert len(links) == 2
        assert all(link['is_internal'] for link in links)
        assert links[0]['link_target'] == './about.md'
        assert links[1]['link_target'] == '/'

    def test_markdown_links_empty_text(self):
        """Test markdown links with empty text."""
        content = "Visit [](https://example.com) for details."

        links = self.parser.parse(content)

        assert len(links) == 1
        assert links[0]['link_text'] == ''
        assert links[0]['link_target'] == 'https://example.com'

    def test_wikilinks_basic(self):
        """Test basic wikilink parsing."""
        content = "See [[Home Page]] and [[About]] for more information."

        links = self.parser.parse(content)

        assert len(links) == 2

        # Check first wikilink
        assert links[0]['link_text'] == 'Home Page'
        assert links[0]['link_target'] == 'Home Page'
        assert links[0]['link_type'] == 'wikilink'
        assert links[0]['is_internal'] == True

        # Check second wikilink
        assert links[1]['link_text'] == 'About'
        assert links[1]['link_target'] == 'About'
        assert links[1]['link_type'] == 'wikilink'
        assert links[1]['is_internal'] == True

    def test_wikilinks_with_alias(self):
        """Test wikilinks with aliases."""
        content = "Check [[Home Page|homepage]] and [[About Us|about]] sections."

        links = self.parser.parse(content)

        assert len(links) == 2

        # Check first wikilink with alias
        assert links[0]['link_text'] == 'homepage'
        assert links[0]['link_target'] == 'Home Page'
        assert links[0]['link_type'] == 'wikilink'

        # Check second wikilink with alias
        assert links[1]['link_text'] == 'about'
        assert links[1]['link_target'] == 'About Us'
        assert links[1]['link_type'] == 'wikilink'

    def test_reference_links(self):
        """Test reference link parsing."""
        content = """
        Check out [Google][google] and [GitHub][gh].

        [google]: https://google.com
        [gh]: https://github.com
        """

        links = self.parser.parse(content)

        assert len(links) == 2

        # Check first reference link
        google_link = next(link for link in links if link['link_text'] == 'Google')
        assert google_link['link_target'] == 'https://google.com'
        assert google_link['link_type'] == 'reference'
        assert google_link['is_internal'] == False

        # Check second reference link
        github_link = next(link for link in links if link['link_text'] == 'GitHub')
        assert github_link['link_target'] == 'https://github.com'
        assert github_link['link_type'] == 'reference'
        assert github_link['is_internal'] == False

    def test_reference_links_implicit(self):
        """Test reference links with implicit reference."""
        content = """
        Check out [Google][] for search.

        [Google]: https://google.com
        """

        links = self.parser.parse(content)

        assert len(links) == 1
        assert links[0]['link_text'] == 'Google'
        assert links[0]['link_target'] == 'https://google.com'
        assert links[0]['link_type'] == 'reference'

    def test_autolinks(self):
        """Test autolink parsing."""
        content = "Visit <https://example.com> and <https://github.com> directly."

        links = self.parser.parse(content)

        assert len(links) == 2

        # Check first autolink
        assert links[0]['link_text'] is None
        assert links[0]['link_target'] == 'https://example.com'
        assert links[0]['link_type'] == 'autolink'
        assert links[0]['is_internal'] == False

        # Check second autolink
        assert links[1]['link_text'] is None
        assert links[1]['link_target'] == 'https://github.com'
        assert links[1]['link_type'] == 'autolink'
        assert links[1]['is_internal'] == False

    def test_mixed_link_types(self):
        """Test parsing content with multiple link types."""
        content = """
        # Mixed Links

        Regular link: [Google](https://google.com)
        Wikilink: [[Home Page]]
        Wikilink with alias: [[About|about page]]
        Reference link: [GitHub][gh]
        Autolink: <https://example.com>
        Internal link: [docs](./docs/readme.md)

        [gh]: https://github.com
        """

        links = self.parser.parse(content)

        assert len(links) == 6

        # Count by type
        link_types = [link['link_type'] for link in links]
        assert link_types.count('markdown') == 2
        assert link_types.count('wikilink') == 2
        assert link_types.count('reference') == 1
        assert link_types.count('autolink') == 1

        # Count internal vs external
        internal_count = sum(1 for link in links if link['is_internal'])
        external_count = sum(1 for link in links if not link['is_internal'])
        assert internal_count == 3  # wikilinks + internal markdown link
        assert external_count == 3  # external markdown + reference + autolink

    def test_internal_link_detection(self):
        """Test internal vs external link detection."""
        test_cases = [
            # External links
            ('https://example.com', False),
            ('http://example.com', False),
            ('ftp://files.example.com', False),
            ('//example.com', False),
            ('mailto:test@example.com', False),

            # Internal links
            ('./page.md', True),
            ('../parent.md', True),
            ('/absolute/path.md', True),
            ('relative/path.md', True),
            ('#anchor', True),
            ('page#section', True),
            ('', True),
        ]

        for target, expected_internal in test_cases:
            result = self.parser._is_internal_link(target)
            assert result == expected_internal, f"Failed for target: {target}"

    def test_get_internal_links(self):
        """Test filtering for internal links only."""
        content = """
        [External](https://example.com)
        [Internal](./page.md)
        [[Wikilink]]
        <https://external.com>
        """

        internal_links = self.parser.get_internal_links(content)

        assert len(internal_links) == 2
        assert all(link['is_internal'] for link in internal_links)

        targets = [link['link_target'] for link in internal_links]
        assert './page.md' in targets
        assert 'Wikilink' in targets

    def test_get_external_links(self):
        """Test filtering for external links only."""
        content = """
        [External](https://example.com)
        [Internal](./page.md)
        [[Wikilink]]
        <https://external.com>
        """

        external_links = self.parser.get_external_links(content)

        assert len(external_links) == 2
        assert all(not link['is_internal'] for link in external_links)

        targets = [link['link_target'] for link in external_links]
        assert 'https://example.com' in targets
        assert 'https://external.com' in targets

    def test_get_wikilinks(self):
        """Test filtering for wikilinks only."""
        content = """
        [Regular](https://example.com)
        [[Wikilink One]]
        [[Wikilink Two|alias]]
        <https://autolink.com>
        """

        wikilinks = self.parser.get_wikilinks(content)

        assert len(wikilinks) == 2
        assert all(link['link_type'] == 'wikilink' for link in wikilinks)

        targets = [link['link_target'] for link in wikilinks]
        assert 'Wikilink One' in targets
        assert 'Wikilink Two' in targets

    def test_get_link_targets(self):
        """Test getting unique link targets."""
        content = """
        [Link 1](https://example.com)
        [Link 2](https://example.com)  # Duplicate target
        [[Page]]
        [Different](https://other.com)
        """

        targets = self.parser.get_link_targets(content)

        assert len(targets) == 3  # Duplicates removed
        assert 'https://example.com' in targets
        assert 'Page' in targets
        assert 'https://other.com' in targets

    def test_count_links_by_type(self):
        """Test counting links by type."""
        content = """
        [Markdown 1](https://example.com)
        [Markdown 2](./internal.md)
        [[Wikilink 1]]
        [[Wikilink 2|alias]]
        [Reference][ref]
        <https://autolink.com>

        [ref]: https://reference.com
        """

        counts = self.parser.count_links_by_type(content)

        assert counts['markdown'] == 2
        assert counts['wikilink'] == 2
        assert counts['reference'] == 1
        assert counts['autolink'] == 1
        assert counts['internal'] == 3  # 1 markdown + 2 wikilinks
        assert counts['external'] == 3  # 1 markdown + 1 reference + 1 autolink

    def test_empty_content(self):
        """Test parsing empty content."""
        links = self.parser.parse("")
        assert links == []

    def test_no_links(self):
        """Test content with no links."""
        content = "This is just plain text with no links at all."
        links = self.parser.parse(content)
        assert links == []

    def test_malformed_links(self):
        """Test handling of malformed links."""
        content = """
        [Incomplete markdown link](
        [[Incomplete wikilink
        [Missing reference][nonexistent]
        <incomplete autolink
        """

        # Should not crash and should not extract malformed links
        links = self.parser.parse(content)
        assert len(links) == 0

    def test_links_in_code_blocks(self):
        """Test that links in code blocks are still extracted."""
        content = """
        Regular link: [Google](https://google.com)

        ```
        Code block link: [GitHub](https://github.com)
        ```

        `Inline code link: [Example](https://example.com)`
        """

        links = self.parser.parse(content)

        # All links should be extracted (parser doesn't distinguish code blocks)
        assert len(links) == 3
        targets = [link['link_target'] for link in links]
        assert 'https://google.com' in targets
        assert 'https://github.com' in targets
        assert 'https://example.com' in targets

    def test_multiline_links(self):
        """Test links that span multiple lines."""
        content = """
        [Multi-line
        link text](https://example.com)

        [[Multi-line
        wikilink]]
        """

        links = self.parser.parse(content)

        # Should handle multiline gracefully
        assert len(links) == 2

    def test_special_characters_in_links(self):
        """Test links with special characters."""
        content = """
        [Link with (parentheses)](https://example.com/path(with)parens)
        [Link with [brackets]](https://example.com/path[with]brackets)
        [[Page with spaces and-dashes]]
        [Unicode link 🔗](https://example.com/unicode)
        """

        links = self.parser.parse(content)

        # Should handle special characters in both text and URLs
        assert len(links) >= 2  # At least the basic ones should work

        # Check that URLs with special chars are preserved
        targets = [link['link_target'] for link in links]
        assert any('(with)parens' in target for target in targets)

    def test_case_insensitive_references(self):
        """Test that reference links are case insensitive."""
        content = """
        [Link][REF]
        [Another][ref]

        [ref]: https://example.com
        """

        links = self.parser.parse(content)

        # Both should resolve to the same reference
        assert len(links) == 2
        assert all(link['link_target'] == 'https://example.com' for link in links)