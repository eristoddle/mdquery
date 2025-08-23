"""
Unit tests for the TagParser class.
"""

import unittest
from mdquery.parsers.tags import TagParser


class TestTagParser(unittest.TestCase):
    """Test cases for TagParser functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.parser = TagParser()

    def test_parse_frontmatter_tags_simple_array(self):
        """Test parsing tags from simple frontmatter array."""
        frontmatter = {
            'tags': {
                'value': ['python', 'programming', 'tutorial'],
                'type': 'array'
            }
        }

        result = self.parser.parse_frontmatter_tags(frontmatter)
        expected = ['programming', 'python', 'tutorial']
        self.assertEqual(result, expected)

    def test_parse_frontmatter_tags_multiple_keys(self):
        """Test parsing tags from multiple frontmatter keys."""
        frontmatter = {
            'tags': {
                'value': ['python', 'programming'],
                'type': 'array'
            },
            'categories': {
                'value': ['tutorial', 'beginner'],
                'type': 'array'
            },
            'keywords': {
                'value': ['coding'],
                'type': 'array'
            }
        }

        result = self.parser.parse_frontmatter_tags(frontmatter)
        expected = ['beginner', 'coding', 'programming', 'python', 'tutorial']
        self.assertEqual(result, expected)

    def test_parse_frontmatter_tags_comma_separated_string(self):
        """Test parsing tags from comma-separated string."""
        frontmatter = {
            'tags': {
                'value': 'python, programming, web-development',
                'type': 'string'
            }
        }

        result = self.parser.parse_frontmatter_tags(frontmatter)
        expected = ['programming', 'python', 'web-development']
        self.assertEqual(result, expected)

    def test_parse_frontmatter_tags_single_string(self):
        """Test parsing single tag from string."""
        frontmatter = {
            'tag': {
                'value': 'python-programming',
                'type': 'string'
            }
        }

        result = self.parser.parse_frontmatter_tags(frontmatter)
        expected = ['python-programming']
        self.assertEqual(result, expected)

    def test_parse_frontmatter_tags_raw_values(self):
        """Test parsing tags from raw frontmatter values (not typed)."""
        frontmatter = {
            'tags': ['Python', 'Programming', 'Tutorial'],
            'category': 'Web Development'
        }

        result = self.parser.parse_frontmatter_tags(frontmatter)
        expected = ['programming', 'python', 'tutorial', 'web-development']
        self.assertEqual(result, expected)

    def test_parse_inline_tags_basic(self):
        """Test parsing basic inline hashtags."""
        content = """
        # My Article

        This is about #python and #programming. I also like #web-development.

        ## Section

        More content with #machine-learning and #ai.
        """

        result = self.parser.parse_inline_tags(content)
        expected = ['ai', 'machine-learning', 'programming', 'python', 'web-development']
        self.assertEqual(result, expected)

    def test_parse_inline_tags_nested_obsidian_style(self):
        """Test parsing Obsidian-style nested tags."""
        content = """
        # Notes

        This covers #programming/python and #programming/javascript.
        Also interested in #research/machine-learning/nlp.
        """

        result = self.parser.parse_inline_tags(content)
        expected = ['programming/javascript', 'programming/python', 'research/machine-learning/nlp']
        self.assertEqual(result, expected)

    def test_parse_inline_tags_with_underscores(self):
        """Test parsing tags with underscores."""
        content = """
        Working on #data_science and #machine_learning projects.
        Also #web_dev and #front_end development.
        """

        result = self.parser.parse_inline_tags(content)
        expected = ['data_science', 'front_end', 'machine_learning', 'web_dev']
        self.assertEqual(result, expected)

    def test_parse_inline_tags_ignore_invalid(self):
        """Test that invalid tags are ignored."""
        content = """
        # Test

        Valid: #python #web-development #data_science
        Invalid: #123 #-invalid #/invalid #invalid- #
        Edge cases: # #a #1a
        """

        result = self.parser.parse_inline_tags(content)
        expected = ['data_science', 'python', 'web-development']
        self.assertEqual(result, expected)

    def test_parse_inline_tags_in_code_blocks(self):
        """Test that tags in code blocks are still detected."""
        content = """
        # Example

        Here's some code:
        ```python
        # This is a comment with #python tag
        print("Hello #world")
        ```

        And regular text with #programming.
        """

        result = self.parser.parse_inline_tags(content)
        expected = ['programming', 'python', 'world']
        self.assertEqual(result, expected)

    def test_parse_all_tags(self):
        """Test parsing tags from both frontmatter and content."""
        frontmatter = {
            'tags': {
                'value': ['python', 'tutorial'],
                'type': 'array'
            }
        }

        content = """
        # Python Tutorial

        This covers #programming and #web-development.
        Also includes #python basics.
        """

        result = self.parser.parse_all_tags(frontmatter, content)

        expected = {
            'frontmatter': ['python', 'tutorial'],
            'content': ['programming', 'python', 'web-development']
        }
        self.assertEqual(result, expected)

    def test_get_all_unique_tags(self):
        """Test getting all unique tags from both sources."""
        frontmatter = {
            'tags': {
                'value': ['python', 'tutorial'],
                'type': 'array'
            }
        }

        content = """
        This covers #programming and #python basics.
        """

        result = self.parser.get_all_unique_tags(frontmatter, content)
        expected = ['programming', 'python', 'tutorial']
        self.assertEqual(result, expected)

    def test_normalize_tag(self):
        """Test tag normalization."""
        test_cases = [
            ('Python', 'python'),
            ('Web Development', 'web-development'),
            ('  #machine-learning  ', 'machine-learning'),
            ('Data_Science', 'data_science'),
            ('AI/ML', 'ai/ml'),
            ('123', ''),  # Pure numbers should be rejected
            ('', ''),
            ('   ', ''),
            ('#', ''),
            ('1abc', ''),  # Starting with number should be rejected
            ('a1b2c3', 'a1b2c3'),  # Numbers in middle are OK
            ('tag-with-special!@#chars', 'tag-with-specialchars'),
        ]

        for input_tag, expected in test_cases:
            with self.subTest(input_tag=input_tag):
                result = self.parser._normalize_tag(input_tag)
                self.assertEqual(result, expected)

    def test_expand_nested_tags(self):
        """Test expanding nested tags to include parents."""
        tags = ['programming/python', 'research/ml/nlp', 'web', 'data/analysis/pandas']

        result = self.parser.expand_nested_tags(tags)
        expected = [
            'data',
            'data/analysis',
            'data/analysis/pandas',
            'programming',
            'programming/python',
            'research',
            'research/ml',
            'research/ml/nlp',
            'web'
        ]
        self.assertEqual(result, expected)

    def test_get_tag_hierarchy(self):
        """Test building tag hierarchy."""
        tags = ['programming/python', 'programming/javascript', 'research/ml/nlp', 'web']

        result = self.parser.get_tag_hierarchy(tags)
        expected = {
            'programming': ['programming/python', 'programming/javascript'],
            'research': ['research/ml'],
            'research/ml': ['research/ml/nlp']
        }
        self.assertEqual(result, expected)

    def test_frontmatter_edge_cases(self):
        """Test edge cases in frontmatter parsing."""
        # Empty frontmatter
        result = self.parser.parse_frontmatter_tags({})
        self.assertEqual(result, [])

        # Non-tag keys
        frontmatter = {
            'title': {'value': 'My Article', 'type': 'string'},
            'date': {'value': '2023-01-01', 'type': 'date'}
        }
        result = self.parser.parse_frontmatter_tags(frontmatter)
        self.assertEqual(result, [])

        # Mixed valid and invalid tags
        frontmatter = {
            'tags': {
                'value': ['valid-tag', '123', '', 'another-valid'],
                'type': 'array'
            }
        }
        result = self.parser.parse_frontmatter_tags(frontmatter)
        expected = ['another-valid', 'valid-tag']
        self.assertEqual(result, expected)

    def test_content_edge_cases(self):
        """Test edge cases in content parsing."""
        # Empty content
        result = self.parser.parse_inline_tags("")
        self.assertEqual(result, [])

        # Content with no tags
        content = "This is just regular text with no hashtags."
        result = self.parser.parse_inline_tags(content)
        self.assertEqual(result, [])

        # Tags at different positions
        content = "#start middle #middle and #end"
        result = self.parser.parse_inline_tags(content)
        expected = ['end', 'middle', 'start']
        self.assertEqual(result, expected)

    def test_case_sensitivity(self):
        """Test that tag parsing is case-insensitive but normalized to lowercase."""
        frontmatter = {
            'tags': {
                'value': ['Python', 'JAVASCRIPT', 'Web-Development'],
                'type': 'array'
            }
        }

        content = "#PYTHON and #JavaScript and #web-DEVELOPMENT"

        fm_result = self.parser.parse_frontmatter_tags(frontmatter)
        content_result = self.parser.parse_inline_tags(content)

        expected_fm = ['javascript', 'python', 'web-development']
        expected_content = ['javascript', 'python', 'web-development']

        self.assertEqual(fm_result, expected_fm)
        self.assertEqual(content_result, expected_content)

    def test_special_characters_in_nested_tags(self):
        """Test handling of special characters in nested tags."""
        content = """
        Valid nested: #programming/python #data/science/ml
        Invalid nested: #/invalid #programming/ #/
        Mixed: #valid/tag #invalid//tag #another/valid_tag
        """

        result = self.parser.parse_inline_tags(content)
        expected = ['another/valid_tag', 'data/science/ml', 'programming/python', 'valid/tag']
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()