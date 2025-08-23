"""
Unit tests for the frontmatter parser component.
"""

import pytest
from datetime import datetime
from mdquery.parsers.frontmatter import FrontmatterParser


class TestFrontmatterParser:
    """Test cases for FrontmatterParser class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = FrontmatterParser()

    def test_yaml_frontmatter_basic(self):
        """Test basic YAML frontmatter parsing."""
        content = """---
title: Test Document
author: John Doe
published: true
tags:
  - python
  - testing
---

# Main Content
This is the main content.
"""
        result = self.parser.parse(content)

        assert result['title']['value'] == 'Test Document'
        assert result['title']['type'] == 'string'
        assert result['author']['value'] == 'John Doe'
        assert result['published']['value'] is True
        assert result['published']['type'] == 'boolean'
        assert result['tags']['type'] == 'array'
        assert result['tags']['value'] == ['python', 'testing']

    def test_json_frontmatter(self):
        """Test JSON frontmatter parsing."""
        content = """{
  "title": "JSON Document",
  "count": 42,
  "active": false,
  "categories": ["tech", "blog"]
}

# Content
JSON frontmatter content.
"""
        result = self.parser.parse(content)

        assert result['title']['value'] == 'JSON Document'
        assert result['count']['value'] == 42
        assert result['count']['type'] == 'number'
        assert result['active']['value'] is False
        assert result['categories']['type'] == 'array'

    def test_toml_frontmatter(self):
        """Test TOML frontmatter parsing."""
        content = """+++
title = "TOML Document"
date = "2023-12-01"
weight = 10
draft = false
tags = ["hugo", "toml"]
+++

# TOML Content
This uses TOML frontmatter.
"""
        result = self.parser.parse(content)

        assert result['title']['value'] == 'TOML Document'
        assert result['date']['type'] == 'date'
        assert result['weight']['value'] == 10
        assert result['draft']['value'] is False
        assert result['tags']['type'] == 'array'

    def test_type_inference_strings(self):
        """Test type inference for various string formats."""
        content = """---
regular_string: "Hello World"
date_string: "2023-12-01"
datetime_string: "2023-12-01T10:30:00"
boolean_string: "true"
number_string: "42"
float_string: "3.14"
---

Content here.
"""
        result = self.parser.parse(content)

        assert result['regular_string']['type'] == 'string'
        assert result['date_string']['type'] == 'date'
        assert result['datetime_string']['type'] == 'date'
        assert result['boolean_string']['type'] == 'boolean_string'
        assert result['boolean_string']['boolean_value'] is True
        assert result['number_string']['type'] == 'number_string'
        assert result['number_string']['numeric_value'] == 42
        assert result['float_string']['type'] == 'number_string'
        assert result['float_string']['numeric_value'] == 3.14

    def test_type_inference_numbers(self):
        """Test type inference for numeric values."""
        content = """---
integer: 42
float_val: 3.14159
negative: -10
zero: 0
---

Content.
"""
        result = self.parser.parse(content)

        assert result['integer']['type'] == 'number'
        assert result['integer']['value'] == 42
        assert result['float_val']['type'] == 'number'
        assert result['float_val']['value'] == 3.14159
        assert result['negative']['value'] == -10
        assert result['zero']['value'] == 0

    def test_type_inference_booleans(self):
        """Test type inference for boolean values."""
        content = """---
true_val: true
false_val: false
yes_string: "yes"
no_string: "no"
on_string: "on"
off_string: "off"
---

Content.
"""
        result = self.parser.parse(content)

        assert result['true_val']['type'] == 'boolean'
        assert result['true_val']['value'] is True
        assert result['false_val']['type'] == 'boolean'
        assert result['false_val']['value'] is False
        assert result['yes_string']['type'] == 'boolean_string'
        assert result['yes_string']['boolean_value'] is True
        assert result['no_string']['boolean_value'] is False

    def test_type_inference_arrays(self):
        """Test type inference for arrays with mixed types."""
        content = """---
string_array:
  - "one"
  - "two"
  - "three"
mixed_array:
  - "text"
  - 42
  - true
  - "2023-12-01"
nested_array:
  - ["a", "b"]
  - ["c", "d"]
---

Content.
"""
        result = self.parser.parse(content)

        assert result['string_array']['type'] == 'array'
        assert all(item == 'string' for item in result['string_array']['item_types'])

        assert result['mixed_array']['type'] == 'array'
        expected_types = ['string', 'number', 'boolean', 'date']
        assert result['mixed_array']['item_types'] == expected_types

        assert result['nested_array']['type'] == 'array'
        assert all(item == 'array' for item in result['nested_array']['item_types'])

    def test_type_inference_objects(self):
        """Test type inference for nested objects."""
        content = """---
author:
  name: "John Doe"
  age: 30
  active: true
config:
  debug: false
  timeout: 5000
  features:
    - "feature1"
    - "feature2"
---

Content.
"""
        result = self.parser.parse(content)

        assert result['author']['type'] == 'object'
        author_obj = result['author']['value']
        assert author_obj['name']['type'] == 'string'
        assert author_obj['age']['type'] == 'number'
        assert author_obj['active']['type'] == 'boolean'

        assert result['config']['type'] == 'object'
        config_obj = result['config']['value']
        assert config_obj['features']['type'] == 'array'

    def test_date_parsing(self):
        """Test various date format parsing."""
        content = """---
date1: "2023-12-01"
date2: "2023-12-01T10:30:00"
date3: "2023-12-01 15:45:30"
date4: "2023-12-01T10:30:00Z"
---

Content.
"""
        result = self.parser.parse(content)

        for key in ['date1', 'date2', 'date3']:
            assert result[key]['type'] == 'date'
            assert 'parsed_date' in result[key]

    def test_no_frontmatter(self):
        """Test parsing content with no frontmatter."""
        content = """# Just a regular markdown file

This has no frontmatter at all.
"""
        result = self.parser.parse(content)
        assert result == {}

    def test_empty_frontmatter(self):
        """Test parsing with empty frontmatter."""
        content = """---
---

# Content with empty frontmatter
"""
        result = self.parser.parse(content)
        assert result == {}

    def test_malformed_yaml(self):
        """Test handling of malformed YAML frontmatter."""
        content = """---
title: "Unclosed quote
author: John Doe
invalid: [unclosed array
---

Content.
"""
        # Should not raise exception, might return empty dict or partial parsing
        result = self.parser.parse(content)
        # The exact behavior depends on implementation, but it shouldn't crash
        assert isinstance(result, dict)

    def test_content_extraction_yaml(self):
        """Test extracting content without YAML frontmatter."""
        content = """---
title: Test
---

# Main Content
This is the actual content.
"""
        extracted = self.parser.get_content_without_frontmatter(content)
        expected = "# Main Content\nThis is the actual content."
        assert extracted.strip() == expected

    def test_content_extraction_json(self):
        """Test extracting content without JSON frontmatter."""
        content = """{
  "title": "Test"
}

# JSON Content
This follows JSON frontmatter.
"""
        extracted = self.parser.get_content_without_frontmatter(content)
        assert "# JSON Content" in extracted
        assert "title" not in extracted

    def test_content_extraction_toml(self):
        """Test extracting content without TOML frontmatter."""
        content = """+++
title = "Test"
+++

# TOML Content
This follows TOML frontmatter.
"""
        extracted = self.parser.get_content_without_frontmatter(content)
        assert "# TOML Content" in extracted
        assert "title" not in extracted

    def test_content_extraction_no_frontmatter(self):
        """Test content extraction when there's no frontmatter."""
        content = """# Regular Markdown

This has no frontmatter.
"""
        extracted = self.parser.get_content_without_frontmatter(content)
        assert extracted.strip() == content.strip()

    def test_obsidian_style_frontmatter(self):
        """Test Obsidian-style frontmatter with special fields."""
        content = """---
aliases:
  - "Alternative Title"
  - "Another Name"
tags:
  - "#research"
  - "#notes/personal"
created: 2023-12-01
modified: 2023-12-02T10:30:00
cssclass: custom-note
---

# Obsidian Note
Content here.
"""
        result = self.parser.parse(content)

        assert result['aliases']['type'] == 'array'
        assert result['tags']['type'] == 'array'
        assert result['created']['type'] == 'date'
        assert result['modified']['type'] == 'date'
        assert result['cssclass']['type'] == 'string'

    def test_jekyll_style_frontmatter(self):
        """Test Jekyll-style frontmatter."""
        content = """---
layout: post
title: "My Blog Post"
date: 2023-12-01 10:30:00 +0000
categories: [blog, tech]
permalink: /blog/my-post/
published: true
---

# Jekyll Post
Content here.
"""
        result = self.parser.parse(content)

        assert result['layout']['value'] == 'post'
        assert result['title']['value'] == 'My Blog Post'
        assert result['categories']['type'] == 'array'
        assert result['permalink']['type'] == 'string'
        assert result['published']['type'] == 'boolean'

    def test_joplin_style_frontmatter(self):
        """Test Joplin-style frontmatter."""
        content = """---
id: abc123def456
title: Joplin Note
created_time: 2023-12-01T10:30:00.000Z
updated_time: 2023-12-02T15:45:00.000Z
is_conflict: 0
latitude: 0.0
longitude: 0.0
altitude: 0.0
author:
source_url:
is_todo: 0
todo_due: 0
todo_completed: 0
source: joplin-desktop
source_application: net.cozic.joplin-desktop
application_data:
order: 0
user_created_time: 2023-12-01T10:30:00.000Z
user_updated_time: 2023-12-02T15:45:00.000Z
encryption_cipher_text:
encryption_applied: 0
markup_language: 1
is_shared: 0
---

# Joplin Note Content
"""
        result = self.parser.parse(content)

        assert result['id']['type'] == 'string'
        assert result['title']['type'] == 'string'
        assert result['created_time']['type'] == 'date'
        assert result['is_conflict']['type'] == 'number'
        assert result['latitude']['type'] == 'number'

    def test_null_and_empty_values(self):
        """Test handling of null and empty values."""
        content = """---
null_value: null
empty_string: ""
empty_array: []
zero_number: 0
false_boolean: false
---

Content.
"""
        result = self.parser.parse(content)

        assert result['null_value']['type'] == 'null'
        assert result['null_value']['value'] is None
        assert result['empty_string']['type'] == 'string'
        assert result['empty_string']['value'] == ''
        assert result['empty_array']['type'] == 'array'
        assert result['empty_array']['value'] == []
        assert result['zero_number']['type'] == 'number'
        assert result['false_boolean']['type'] == 'boolean'

    def test_special_characters_and_unicode(self):
        """Test handling of special characters and Unicode."""
        content = """---
unicode_title: "测试文档 🚀"
special_chars: 'Hello "World" & <tags>'
emoji_tags:
  - "🐍 python"
  - "🧪 testing"
accented: "café naïve résumé"
---

Content with émojis 🎉
"""
        result = self.parser.parse(content)

        assert result['unicode_title']['value'] == '测试文档 🚀'
        assert result['special_chars']['type'] == 'string'
        assert result['emoji_tags']['type'] == 'array'
        assert result['accented']['value'] == 'café naïve résumé'

    def test_large_frontmatter(self):
        """Test handling of large frontmatter blocks."""
        # Create a large frontmatter block
        large_tags = [f"tag_{i}" for i in range(100)]
        content = f"""---
title: "Large Document"
tags: {large_tags}
description: "{'A' * 1000}"
---

Content.
"""
        result = self.parser.parse(content)

        assert result['title']['value'] == 'Large Document'
        assert len(result['tags']['value']) == 100
        assert len(result['description']['value']) == 1000


if __name__ == '__main__':
    pytest.main([__file__])