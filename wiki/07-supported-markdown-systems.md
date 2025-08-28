# Supported Markdown Systems

## Overview

mdquery supports multiple markdown-based note-taking systems and static site generators, each with their specific features and conventions. The system automatically detects the type of markdown system based on directory structure and file patterns, then applies appropriate parsing rules.

## Obsidian

### Obsidian Support Features

The Obsidian parser provides comprehensive support for Obsidian-specific features, enabling rich metadata extraction and relationship mapping from Obsidian vaults.

#### Wikilink Parsing

Obsidian's wikilinks are parsed with detailed metadata extraction, supporting various link types:

- **Standard wikilinks**: `[[Page]]` or `[[Page|Alias]]`
- **Section references**: `[[Page#Section]]`
- **Block references**: `[[Page#^block-id]]`
- **Embedded content**: `![[Page]]`

The parser extracts link text, target, type, and additional metadata such as section references, block IDs, and alias information.

```python
# Example of wikilink parsing from ObsidianParser
wikilinks = [
    {
        'link_text': 'Zettelkasten Method',
        'link_target': 'Zettelkasten Method',
        'link_type': 'wikilink',
        'is_internal': True,
        'obsidian_type': 'page',
        'section': None,
        'block_id': None,
        'has_alias': False
    }
]
```

#### Nested Tag Support

Obsidian's hierarchical tag system is fully supported:

- **Nested tags**: `#research/methods/qualitative`
- **Tag hierarchy extraction**: Parent-child relationships
- **Tag path queries**: Search by tag hierarchy levels

```sql
-- Find all research-related tags
SELECT tag FROM tags WHERE tag LIKE 'research%';

-- Find specific nested tags
SELECT tag FROM tags WHERE tag LIKE 'research/methods%';
```

#### Obsidian-Specific Features

- **Callouts**: `> [!note]`, `> [!warning]`, etc.
- **Templates**: Template file detection and processing
- **Dataview queries**: Basic detection of Dataview syntax
- **Canvas files**: Support for `.canvas` files (as JSON)
- **Vault configuration**: Reading `.obsidian/app.json` for settings

#### Configuration for Obsidian

```json
{
  "note_system_type": "obsidian",
  "parsing": {
    "enable_wikilinks": true,
    "enable_nested_tags": true,
    "process_callouts": true,
    "extract_dataview": true,
    "follow_aliases": true
  },
  "obsidian": {
    "vault_path": "/path/to/vault",
    "config_dir": ".obsidian",
    "include_canvas": true,
    "extract_aliases": true,
    "process_templates": true
  }
}
```

### Sample Obsidian Queries

```sql
-- Find notes with wikilinks
SELECT f.filename, ol.link_target, ol.obsidian_type
FROM files f
JOIN obsidian_links ol ON f.id = ol.file_id
WHERE ol.obsidian_type = 'wikilink';

-- Find embedded content
SELECT f.filename, ol.link_target
FROM files f
JOIN obsidian_links ol ON f.id = ol.file_id
WHERE ol.obsidian_type = 'embed';

-- Nested tag analysis
SELECT
  SUBSTR(tag, 1, INSTR(tag || '/', '/') - 1) as root_tag,
  COUNT(*) as count
FROM tags
WHERE tag LIKE '%/%'
GROUP BY root_tag
ORDER BY count DESC;
```

## Joplin

### Joplin Support Features

mdquery provides comprehensive support for Joplin's markdown format and metadata structure.

#### Joplin Metadata Extraction

Joplin stores metadata as inline text at the beginning of files:

```markdown
Created: 2024-01-10T10:30:00Z
Updated: 2024-01-15T14:22:00Z
Tags: research, markdown, parsing
Source: web-clipper

# Meeting Notes

Content of the note...
```

This metadata is extracted and stored in the frontmatter table:

```sql
-- Example extracted metadata
INSERT INTO frontmatter (file_id, key, value, value_type) VALUES
(?, 'created', '2024-01-10T10:30:00Z', 'date'),
(?, 'updated', '2024-01-15T14:22:00Z', 'date'),
(?, 'tags', 'research,markdown,parsing', 'string'),
(?, 'source', 'web-clipper', 'string');
```

#### Tag Processing

Joplin tags are processed from the inline metadata and also extracted from content:

- **Inline tags**: From `Tags:` metadata line
- **Content tags**: Hashtags in the content body
- **Tag normalization**: Spaces converted to hyphens

#### Resource and Attachment Handling

Joplin's resource system is supported:

- **Resource links**: `[](:/resource-id)` format
- **Image attachments**: Embedded images and files
- **External links**: Standard markdown links

#### Configuration for Joplin

```json
{
  "note_system_type": "joplin",
  "parsing": {
    "extract_joplin_metadata": true,
    "process_resources": true,
    "normalize_tags": true,
    "extract_timestamps": true
  },
  "joplin": {
    "data_dir": "/path/to/joplin/data",
    "include_resources": true,
    "process_notebooks": true
  }
}
```

### Sample Joplin Queries

```sql
-- Find notes by creation date
SELECT filename, created_date
FROM files
WHERE created_date > '2024-01-01'
ORDER BY created_date DESC;

-- Find web-clipped content
SELECT f.filename, fm.value as source
FROM files f
JOIN frontmatter fm ON f.id = fm.file_id
WHERE fm.key = 'source' AND fm.value LIKE '%web%';

-- Resource usage analysis
SELECT f.filename, COUNT(l.id) as resource_count
FROM files f
JOIN links l ON f.id = l.file_id
WHERE l.link_target LIKE ':%'
GROUP BY f.id
ORDER BY resource_count DESC;
```

## Jekyll

### Jekyll Support Features

mdquery supports Jekyll static site generators with their specific frontmatter and structure conventions.

#### Jekyll Frontmatter

Jekyll uses YAML frontmatter extensively:

```yaml
---
layout: post
title: "Understanding Markdown Querying"
date: 2024-01-15 10:30:00
categories: [development, tools]
tags: [markdown, sql, querying]
author: "John Doe"
excerpt: "A comprehensive guide to querying markdown files"
published: true
---
```

This frontmatter is fully extracted and queryable:

```sql
-- Find published posts
SELECT f.filename, fm1.value as title, fm2.value as date
FROM files f
JOIN frontmatter fm1 ON f.id = fm1.file_id AND fm1.key = 'title'
JOIN frontmatter fm2 ON f.id = fm2.file_id AND fm2.key = 'date'
JOIN frontmatter fm3 ON f.id = fm3.file_id AND fm3.key = 'published'
WHERE fm3.value = 'true'
ORDER BY fm2.value DESC;
```

#### Jekyll Directory Structure

Jekyll's conventional directory structure is recognized:

- **_posts/**: Blog posts with date-based naming
- **_pages/**: Static pages
- **_drafts/**: Draft content
- **_data/**: Data files (YAML, JSON, CSV)
- **_includes/**: Reusable content snippets
- **_layouts/**: Page templates

#### Configuration for Jekyll

```json
{
  "note_system_type": "jekyll",
  "parsing": {
    "process_frontmatter": true,
    "extract_categories": true,
    "process_includes": true,
    "parse_liquid": false
  },
  "jekyll": {
    "site_dir": "/path/to/jekyll/site",
    "posts_dir": "_posts",
    "pages_dir": "_pages",
    "data_dir": "_data",
    "include_drafts": false,
    "process_liquid_tags": false
  }
}
```

### Sample Jekyll Queries

```sql
-- Find posts by category
SELECT f.filename, fm.value as categories
FROM files f
JOIN frontmatter fm ON f.id = fm.file_id
WHERE fm.key = 'categories' AND fm.value LIKE '%development%';

-- Posts by author
SELECT fm1.value as author, COUNT(*) as post_count
FROM frontmatter fm1
JOIN frontmatter fm2 ON fm1.file_id = fm2.file_id
WHERE fm1.key = 'author' AND fm2.key = 'layout' AND fm2.value = 'post'
GROUP BY fm1.value
ORDER BY post_count DESC;

-- Recently published posts
SELECT f.filename, fm.value as date
FROM files f
JOIN frontmatter fm ON f.id = fm.file_id
WHERE fm.key = 'date' AND f.directory LIKE '%_posts%'
ORDER BY fm.value DESC
LIMIT 10;
```

## Generic Markdown

### Generic Markdown Support

mdquery provides baseline functionality for any markdown files that don't fit specific system patterns.

#### Baseline Functionality

For generic markdown files, the parser extracts:

- **Headings**: Creates a heading hierarchy for navigation
- **Links**: Extracts external links and any wikilinks
- **Inline tags**: Processes hashtags in content
- **Content statistics**: Word count, line count, and other metrics
- **Basic frontmatter**: If present, processes YAML/TOML frontmatter

#### Simple Markdown Processing

```markdown
# Simple Note

This is a basic markdown file without frontmatter.

## Content

Just regular markdown content with:
- Lists
- **Bold text**
- *Italic text*
- [External links](https://example.com)

## Code Example

```python
def hello_world():
    print("Hello, World!")
```

That's it - simple and clean.
```

Even without frontmatter, valuable information is extracted:

```python
# Example extraction results
{
    'headings': ['Simple Note', 'Content', 'Code Example'],
    'word_count': 42,
    'link_count': 1,
    'external_links': ['https://example.com'],
    'code_blocks': ['python']
}
```

#### Configuration for Generic Markdown

```json
{
  "note_system_type": "generic",
  "parsing": {
    "process_frontmatter": true,
    "extract_headings": true,
    "extract_links": true,
    "process_code_blocks": true,
    "extract_inline_tags": true
  },
  "generic": {
    "include_patterns": ["*.md", "*.markdown", "*.txt"],
    "extract_metadata": true,
    "process_tables": true
  }
}
```

### Sample Generic Markdown Queries

```sql
-- Find files with code blocks
SELECT filename, word_count
FROM files
WHERE content MATCH 'code'
AND heading_count > 2;

-- External link analysis
SELECT f.filename, COUNT(l.id) as external_links
FROM files f
JOIN links l ON f.id = l.file_id
WHERE l.is_internal = 0
GROUP BY f.id
HAVING external_links > 0
ORDER BY external_links DESC;

-- Simple content search
SELECT filename, word_count
FROM files
WHERE content MATCH 'tutorial OR guide'
AND word_count > 500
ORDER BY word_count DESC;
```

## Auto-Detection

### System Detection Logic

mdquery automatically detects the markdown system type based on:

1. **Directory indicators**: Presence of `.obsidian/`, `_config.yml`, etc.
2. **File patterns**: Naming conventions and structures
3. **Content analysis**: Specific syntax patterns in files
4. **Configuration files**: System-specific configuration files

### Detection Priority

1. **Obsidian**: `.obsidian/` directory present
2. **Jekyll**: `_config.yml` file and `_posts/` directory
3. **Joplin**: Joplin metadata patterns in files
4. **Generic**: Default fallback for other markdown files

### Manual Override

You can override auto-detection:

```json
{
  "note_system_type": "obsidian",  // Force Obsidian parsing
  "auto_detect": false
}
```

Or via environment variable:

```bash
export MDQUERY_NOTE_SYSTEM_TYPE=obsidian
```