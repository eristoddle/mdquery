# Parsers

This section documents the parser components that extract structured data from markdown files.

## Parser Architecture

mdquery uses a modular parser system to extract different types of data from markdown files:

```
BaseParser (abstract)
├── FrontmatterParser - YAML frontmatter extraction
├── MarkdownParser - Markdown content processing
├── TagParser - Tag extraction from content and frontmatter
├── LinkParser - Link extraction (markdown and wiki-style)
└── Format-specific parsers
    ├── ObsidianParser - Obsidian-specific features
    ├── JoplinParser - Joplin export format
    ├── JekyllParser - Jekyll frontmatter and structure
    └── GenericParser - Standard markdown fallback
```

## Core Parsers

### FrontmatterParser

Extracts YAML frontmatter from the beginning of markdown files.

**Supported Formats:**
- YAML frontmatter (between `---` delimiters)
- TOML frontmatter (between `+++` delimiters)
- JSON frontmatter (between `{` and `}`)

**Features:**
- Type detection (string, number, boolean, array, object)
- Nested object support
- Date parsing and normalization
- Error handling for malformed frontmatter

**Example:**
```yaml
---
title: "My Blog Post"
date: 2024-03-15
tags: [blogging, markdown]
published: true
author:
  name: "John Doe"
  email: "john@example.com"
---
```

### MarkdownParser

Processes markdown content and extracts structural information.

**Extracted Data:**
- Headings (with levels and hierarchy)
- Paragraphs and word counts
- Code blocks (with language detection)
- Lists (ordered and unordered)
- Tables
- Images and media references

**Features:**
- CommonMark compliance
- GitHub Flavored Markdown extensions
- Heading hierarchy analysis
- Content statistics (word count, reading time)

### TagParser

Extracts tags from both frontmatter and content.

**Tag Sources:**
- Frontmatter `tags` field (array or comma-separated)
- Inline hashtags (`#tag`)
- Obsidian-style tags (`[[tag]]`)
- Custom tag patterns

**Features:**
- Tag normalization (lowercase, no spaces)
- Duplicate removal
- Context preservation (where tag was found)
- Hierarchical tag support (`parent/child`)

### LinkParser

Extracts various types of links from markdown content.

**Link Types:**
- Standard markdown links (`[text](url)`)
- Reference links (`[text][ref]`)
- Wikilinks (`[[page]]` or `[[page|display text]]`)
- Image links (`![alt](image.jpg)`)
- External URLs (auto-detected)

**Features:**
- Link validation (internal vs external)
- Broken link detection
- Link text extraction
- Context preservation

## Format-Specific Parsers

### ObsidianParser

Handles Obsidian-specific markdown features.

**Obsidian Features:**
- Wikilinks with aliases (`[[note|alias]]`)
- Block references (`[[note#^block-id]]`)
- Embedded files (`![[image.png]]`)
- Tags in content (`#tag` and `#nested/tag`)
- Callouts (`> [!note]`)
- Math expressions (`$$math$$`)

**Configuration:**
```python
obsidian_parser = ObsidianParser(
    vault_path="/path/to/vault",
    attachment_folder="attachments",
    enable_block_refs=True,
    enable_callouts=True
)
```

### JoplinParser

Processes Joplin export format.

**Joplin Features:**
- Resource references (`[](:/resource-id)`)
- Note links (`[](:/note-id)`)
- Joplin-specific frontmatter
- Notebook hierarchy
- Tag extraction from Joplin metadata

### JekyllParser

Handles Jekyll static site generator format.

**Jekyll Features:**
- Liquid template tags (`{% tag %}`)
- Jekyll frontmatter variables
- Post filename date extraction
- Category and tag processing
- Permalink generation

### GenericParser

Fallback parser for standard markdown files.

**Features:**
- CommonMark standard compliance
- Basic frontmatter support
- Standard link and image processing
- Simple tag extraction from frontmatter

## Parser Configuration

### Global Configuration

```python
from mdquery.parsers import ParserConfig

config = ParserConfig(
    # Frontmatter settings
    frontmatter_formats=['yaml', 'toml', 'json'],
    strict_frontmatter=False,

    # Tag settings
    tag_patterns=[r'#(\w+)', r'\[\[([^\]]+)\]\]'],
    normalize_tags=True,
    hierarchical_tags=True,

    # Link settings
    resolve_relative_links=True,
    validate_links=True,
    extract_link_context=True,

    # Content settings
    extract_headings=True,
    extract_code_blocks=True,
    calculate_reading_time=True,

    # Format detection
    auto_detect_format=True,
    default_format='generic'
)
```

### Parser-Specific Configuration

```python
# Obsidian parser configuration
obsidian_config = {
    'vault_path': '/path/to/vault',
    'attachment_folder': 'attachments',
    'enable_wikilinks': True,
    'enable_block_refs': True,
    'enable_callouts': True,
    'tag_prefix': '#'
}

# Jekyll parser configuration
jekyll_config = {
    'posts_dir': '_posts',
    'drafts_dir': '_drafts',
    'collections': ['projects', 'tutorials'],
    'permalink_style': 'date',
    'process_liquid': True
}
```

## Custom Parsers

### Creating a Custom Parser

```python
from mdquery.parsers.base import BaseParser
from typing import Dict, Any
from pathlib import Path

class CustomParser(BaseParser):
    """Custom parser for specialized markdown format."""

    def __init__(self, **config):
        super().__init__(**config)
        self.custom_setting = config.get('custom_setting', 'default')

    def parse(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Parse markdown content and return structured data."""
        result = {
            'frontmatter': {},
            'tags': [],
            'links': [],
            'headings': [],
            'content_stats': {},
            'custom_data': {}
        }

        # Extract frontmatter
        result['frontmatter'] = self._parse_frontmatter(content)

        # Extract custom data
        result['custom_data'] = self._parse_custom_features(content)

        # Extract standard markdown elements
        result.update(self._parse_standard_elements(content))

        return result

    def _parse_custom_features(self, content: str) -> Dict[str, Any]:
        """Extract custom features specific to this format."""
        # Custom parsing logic here
        return {}

    def can_parse(self, file_path: Path, content: str) -> bool:
        """Determine if this parser can handle the given file."""
        # Detection logic (e.g., check for specific markers)
        return 'custom-marker' in content
```

### Registering Custom Parsers

```python
from mdquery import Indexer, CacheManager
from my_parsers import CustomParser

# Initialize components
cache_manager = CacheManager("notes.db")
indexer = Indexer(cache_manager=cache_manager)

# Register custom parser
custom_parser = CustomParser(custom_setting="value")
indexer.register_parser('custom', custom_parser)

# The indexer will now use the custom parser for compatible files
stats = indexer.index_directory("/path/to/notes")
```

## Parser Pipeline

### Processing Flow

1. **Format Detection**: Determine which parser to use
2. **Content Preprocessing**: Clean and normalize content
3. **Frontmatter Extraction**: Parse YAML/TOML/JSON frontmatter
4. **Content Parsing**: Extract markdown elements
5. **Data Normalization**: Standardize extracted data
6. **Validation**: Verify data integrity
7. **Storage**: Store structured data in database

### Error Handling

Parsers implement robust error handling:

```python
class ParserError(Exception):
    """Base exception for parser errors."""
    pass

class FrontmatterError(ParserError):
    """Error parsing frontmatter."""
    pass

class ContentError(ParserError):
    """Error parsing content."""
    pass

# Example error handling in parser
def parse_frontmatter(self, content: str) -> Dict[str, Any]:
    try:
        # Parse frontmatter
        return yaml.safe_load(frontmatter_content)
    except yaml.YAMLError as e:
        logger.warning(f"Invalid frontmatter: {e}")
        return {}  # Return empty dict instead of failing
    except Exception as e:
        logger.error(f"Unexpected error parsing frontmatter: {e}")
        raise FrontmatterError(f"Failed to parse frontmatter: {e}")
```

## Performance Optimization

### Caching

Parsers implement caching for expensive operations:

```python
from functools import lru_cache

class OptimizedParser(BaseParser):
    @lru_cache(maxsize=1000)
    def _parse_expensive_operation(self, content_hash: str, content: str):
        """Cache expensive parsing operations."""
        # Expensive parsing logic
        return result
```

### Streaming

For large files, parsers support streaming:

```python
def parse_large_file(self, file_path: Path) -> Dict[str, Any]:
    """Parse large files in chunks."""
    result = {'headings': [], 'links': []}

    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            # Process line by line
            if line.startswith('#'):
                result['headings'].append({
                    'text': line.strip('#').strip(),
                    'level': len(line) - len(line.lstrip('#')),
                    'line_number': line_num
                })

    return result
```

### Parallel Processing

Multiple files can be parsed in parallel:

```python
from concurrent.futures import ThreadPoolExecutor
from typing import List

def parse_files_parallel(self, file_paths: List[Path], max_workers: int = 4):
    """Parse multiple files in parallel."""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(self.parse_file, path): path
            for path in file_paths
        }

        results = {}
        for future in futures:
            path = futures[future]
            try:
                results[path] = future.result()
            except Exception as e:
                logger.error(f"Error parsing {path}: {e}")
                results[path] = None

        return results
```

## Testing Parsers

### Unit Tests

```python
import pytest
from mdquery.parsers import FrontmatterParser

def test_frontmatter_parser():
    parser = FrontmatterParser()
    content = """---
title: Test Post
tags: [test, example]
published: true
---

# Test Content
"""

    result = parser.parse_frontmatter(content)

    assert result['title'] == 'Test Post'
    assert result['tags'] == ['test', 'example']
    assert result['published'] is True

def test_parser_error_handling():
    parser = FrontmatterParser()
    invalid_content = """---
title: Test Post
invalid: yaml: content
---"""

    # Should not raise exception, should return empty dict
    result = parser.parse_frontmatter(invalid_content)
    assert result == {}
```

### Integration Tests

```python
def test_parser_integration():
    """Test parser integration with indexer."""
    cache_manager = CacheManager(":memory:")
    cache_manager.initialize_cache()

    indexer = Indexer(cache_manager=cache_manager)

    # Create test file
    test_content = """---
title: Integration Test
tags: [test]
---

# Test Heading

This is test content with a [link](example.com).
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(test_content)
        f.flush()

        # Index the file
        success = indexer.index_file(Path(f.name))
        assert success

        # Verify data was extracted correctly
        query_engine = QueryEngine(cache_manager=cache_manager)
        result = query_engine.execute_query("SELECT * FROM files")

        assert result.success
        assert len(result.data) == 1
        assert result.data[0]['title'] == 'Integration Test'
```

This parser system provides a flexible and extensible way to extract structured data from various markdown formats, enabling powerful querying and analysis capabilities.