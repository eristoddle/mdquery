"""
Unit tests for the markdown content parser.
"""

import pytest
from mdquery.parsers.markdown import MarkdownParser, HeadingInfo, ParsedMarkdown


class TestMarkdownParser:
    """Test cases for MarkdownParser."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = MarkdownParser()

    def test_empty_content(self):
        """Test parsing empty content."""
        result = self.parser.parse("")
        assert result.sanitized_content == ""
        assert result.headings == []
        assert result.word_count == 0
        assert result.heading_hierarchy == {}
        assert result.plain_text == ""

    def test_whitespace_only_content(self):
        """Test parsing content with only whitespace."""
        result = self.parser.parse("   \n\n  \t  ")
        assert result.sanitized_content == ""
        assert result.headings == []
        assert result.word_count == 0
        assert result.heading_hierarchy == {}
        assert result.plain_text == ""

    def test_simple_text_content(self):
        """Test parsing simple text without markdown."""
        content = "This is a simple paragraph with some words."
        result = self.parser.parse(content)

        assert result.sanitized_content == content
        assert result.headings == []
        assert result.word_count == 8
        assert result.heading_hierarchy == {}
        assert result.plain_text == content

    def test_atx_headings(self):
        """Test parsing ATX-style headings (# ## ### etc.)."""
        content = """# Main Title
## Section One
### Subsection A
#### Deep Section
##### Deeper Section
###### Deepest Section
## Section Two"""

        result = self.parser.parse(content)

        expected_headings = [
            HeadingInfo(1, "Main Title", "main-title", 1),
            HeadingInfo(2, "Section One", "section-one", 2),
            HeadingInfo(3, "Subsection A", "subsection-a", 3),
            HeadingInfo(4, "Deep Section", "deep-section", 4),
            HeadingInfo(5, "Deeper Section", "deeper-section", 5),
            HeadingInfo(6, "Deepest Section", "deepest-section", 6),
            HeadingInfo(2, "Section Two", "section-two", 7),
        ]

        assert len(result.headings) == 7
        for i, heading in enumerate(expected_headings):
            assert result.headings[i].level == heading.level
            assert result.headings[i].text == heading.text
            assert result.headings[i].anchor == heading.anchor

    def test_setext_headings(self):
        """Test parsing Setext-style headings (underlined)."""
        content = """Main Title
==========

Section Title
-------------

Some content here."""

        result = self.parser.parse(content)

        assert len(result.headings) == 2
        assert result.headings[0].level == 1
        assert result.headings[0].text == "Main Title"
        assert result.headings[1].level == 2
        assert result.headings[1].text == "Section Title"

    def test_mixed_heading_styles(self):
        """Test parsing mixed ATX and Setext headings."""
        content = """# ATX Heading 1

Setext Heading 1
================

## ATX Heading 2

Setext Heading 2
----------------

### ATX Heading 3"""

        result = self.parser.parse(content)

        assert len(result.headings) == 5
        assert result.headings[0].text == "ATX Heading 1"
        assert result.headings[1].text == "Setext Heading 1"
        assert result.headings[2].text == "ATX Heading 2"
        assert result.headings[3].text == "Setext Heading 2"
        assert result.headings[4].text == "ATX Heading 3"

    def test_heading_hierarchy(self):
        """Test building heading hierarchy."""
        content = """# Chapter 1
## Section 1.1
### Subsection 1.1.1
### Subsection 1.1.2
## Section 1.2
# Chapter 2
## Section 2.1"""

        result = self.parser.parse(content)

        hierarchy = result.heading_hierarchy
        assert hierarchy["Chapter 1"] == []
        assert hierarchy["Section 1.1"] == ["Chapter 1"]
        assert hierarchy["Subsection 1.1.1"] == ["Chapter 1", "Section 1.1"]
        assert hierarchy["Subsection 1.1.2"] == ["Chapter 1", "Section 1.1"]
        assert hierarchy["Section 1.2"] == ["Chapter 1"]
        assert hierarchy["Chapter 2"] == []
        assert hierarchy["Section 2.1"] == ["Chapter 2"]

    def test_markdown_formatting_removal(self):
        """Test removal of markdown formatting from plain text."""
        content = """# Heading

This is **bold text** and *italic text* and ~~strikethrough~~.

Here's a [link](http://example.com) and an ![image](image.jpg).

Here's some `inline code` and a [[wikilink]].

> This is a blockquote

- List item 1
- List item 2

1. Numbered item 1
2. Numbered item 2"""

        result = self.parser.parse(content)

        # Check that markdown formatting is removed from plain text
        plain_text = result.plain_text
        assert "**" not in plain_text
        assert "*" not in plain_text
        assert "~~" not in plain_text
        assert "[" not in plain_text
        assert "]" not in plain_text
        assert "(" not in plain_text
        assert ")" not in plain_text
        assert "`" not in plain_text
        assert ">" not in plain_text
        assert "-" not in plain_text
        assert "1." not in plain_text
        assert "2." not in plain_text

        # Check that actual text content is preserved
        assert "bold text" in plain_text
        assert "italic text" in plain_text
        assert "strikethrough" in plain_text
        assert "link" in plain_text
        assert "image" in plain_text
        assert "inline code" in plain_text
        assert "wikilink" in plain_text
        assert "blockquote" in plain_text
        assert "List item 1" in plain_text
        assert "Numbered item 1" in plain_text

    def test_code_block_removal(self):
        """Test removal of code blocks from plain text."""
        content = """# Code Examples

Here's some text.

```python
def hello():
    print("Hello, world!")
```

More text here.

```
Some generic code block
with multiple lines
```

And `inline code` too."""

        result = self.parser.parse(content)

        plain_text = result.plain_text
        assert "def hello():" not in plain_text
        assert "print(" not in plain_text
        assert "Some generic code block" not in plain_text
        assert "with multiple lines" not in plain_text

        # Regular text should be preserved
        assert "Here's some text" in plain_text
        assert "More text here" in plain_text
        assert "inline code" in plain_text

    def test_word_counting(self):
        """Test word counting functionality."""
        test_cases = [
            ("", 0),
            ("word", 1),
            ("two words", 2),
            ("This is a sentence with seven words.", 7),
            ("Multiple\nlines\nwith\nwords", 4),
            ("  Spaces   around   words  ", 3),
            ("Punctuation, doesn't! affect? word: counting.", 5),
        ]

        for content, expected_count in test_cases:
            result = self.parser.parse(content)
            assert result.word_count == expected_count, f"Failed for: '{content}'"

    def test_complex_document_structure(self):
        """Test parsing a complex document with various elements."""
        content = """# Project Documentation

## Overview

This project provides **markdown querying** capabilities.

### Features

- SQL-like queries
- Multiple output formats
- Fast indexing

### Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application

## Usage Examples

Here's how to use it:

```bash
mdquery "SELECT * FROM files WHERE tags LIKE '%python%'"
```

### Advanced Queries

You can also use [complex queries](docs/queries.md) for better results.

> **Note**: Always backup your data before running queries.

## Configuration

The configuration file uses YAML format:

```yaml
database:
  path: "./cache.db"
  timeout: 30
```

## Conclusion

This tool is useful for [[knowledge management]] and research."""

        result = self.parser.parse(content)

        # Check headings
        assert len(result.headings) == 8
        assert result.headings[0].text == "Project Documentation"
        assert result.headings[1].text == "Overview"
        assert result.headings[2].text == "Features"
        assert result.headings[3].text == "Installation"
        assert result.headings[4].text == "Usage Examples"
        assert result.headings[5].text == "Advanced Queries"
        assert result.headings[6].text == "Configuration"
        assert result.headings[7].text == "Conclusion"

        # Check hierarchy
        hierarchy = result.heading_hierarchy
        assert hierarchy["Overview"] == ["Project Documentation"]
        assert hierarchy["Features"] == ["Project Documentation", "Overview"]
        assert hierarchy["Installation"] == ["Project Documentation", "Overview"]

        # Check word count (should be reasonable)
        assert result.word_count > 50

        # Check that code blocks are removed from plain text (but inline code content is preserved)
        assert "SELECT * FROM" not in result.plain_text  # This was in a code block
        assert "database:" not in result.plain_text  # This was in a YAML code block
        assert "pip install" in result.plain_text  # This was inline code, content should be preserved

        # Check that regular text is preserved
        assert "markdown querying" in result.plain_text
        assert "knowledge management" in result.plain_text

    def test_special_characters_sanitization(self):
        """Test sanitization of special characters for FTS5."""
        content = """# Smart Quotes Test

This has "smart quotes" and 'smart apostrophes'.

It also has em-dashes — and en-dashes – and ellipses…

Some unicode: café, naïve, résumé."""

        result = self.parser.parse(content)

        sanitized = result.sanitized_content
        # Regular quotes should be preserved (this content doesn't have smart quotes)
        assert '"' in sanitized
        assert "'" in sanitized

        # Dashes should be normalized
        assert '—' not in sanitized
        assert '–' not in sanitized

        # Ellipses should be normalized
        assert '…' not in sanitized
        assert '...' in sanitized

        # Test actual smart quotes replacement with unicode characters
        smart_quote_content = "This has \u201creal smart quotes\u201d and \u2018smart apostrophes\u2019."
        smart_result = self.parser.parse(smart_quote_content)
        smart_sanitized = smart_result.sanitized_content
        # Smart quotes should be converted to regular quotes
        assert '\u201c' not in smart_sanitized  # Left double quote should be gone
        assert '\u201d' not in smart_sanitized  # Right double quote should be gone
        assert '\u2018' not in smart_sanitized  # Left single quote should be gone
        assert '\u2019' not in smart_sanitized  # Right single quote should be gone
        # Regular quotes should be present instead
        assert '"' in smart_sanitized
        assert "'" in smart_sanitized

    def test_heading_anchor_generation(self):
        """Test anchor generation for headings."""
        content = """# Simple Heading
## Heading with Spaces
### Heading with Special Characters!@#
#### Heading with **Bold** and *Italic*
##### Multiple    Spaces    Between    Words"""

        result = self.parser.parse(content)

        expected_anchors = [
            "simple-heading",
            "heading-with-spaces",
            "heading-with-special-characters",
            "heading-with-bold-and-italic",
            "multiple-spaces-between-words"
        ]

        for i, expected_anchor in enumerate(expected_anchors):
            assert result.headings[i].anchor == expected_anchor

    def test_utility_methods(self):
        """Test utility methods for heading manipulation."""
        content = """# Main Title
## Section One
### Subsection
## Section Two
### Another Subsection
#### Deep Section"""

        result = self.parser.parse(content)

        # Test get_heading_text_only
        heading_texts = self.parser.get_heading_text_only(result.headings)
        expected_texts = ["Main Title", "Section One", "Subsection", "Section Two", "Another Subsection", "Deep Section"]
        assert heading_texts == expected_texts

        # Test get_headings_by_level
        h1_headings = self.parser.get_headings_by_level(result.headings, 1)
        assert len(h1_headings) == 1
        assert h1_headings[0].text == "Main Title"

        h2_headings = self.parser.get_headings_by_level(result.headings, 2)
        assert len(h2_headings) == 2
        assert h2_headings[0].text == "Section One"
        assert h2_headings[1].text == "Section Two"

        h3_headings = self.parser.get_headings_by_level(result.headings, 3)
        assert len(h3_headings) == 2

        h4_headings = self.parser.get_headings_by_level(result.headings, 4)
        assert len(h4_headings) == 1
        assert h4_headings[0].text == "Deep Section"

    def test_edge_cases(self):
        """Test various edge cases."""
        # Heading with only hashes
        result = self.parser.parse("# ")
        assert len(result.headings) == 0

        # Invalid setext heading (no text above)
        result = self.parser.parse("====")
        assert len(result.headings) == 0

        # Heading with trailing hashes
        result = self.parser.parse("# Heading #####")
        assert len(result.headings) == 1
        assert result.headings[0].text == "Heading"

        # Mixed content with no headings
        content = "Just some **bold** text with *italics* and a [link](url)."
        result = self.parser.parse(content)
        assert len(result.headings) == 0
        assert result.word_count > 0
        assert "bold" in result.plain_text
        assert "italics" in result.plain_text
        assert "link" in result.plain_text