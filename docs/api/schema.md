# Database Schema Reference

This document provides a complete reference for mdquery's SQLite database schema, including tables, indexes, views, and relationships.

## Schema Overview

mdquery organizes markdown file data into a relational structure optimized for querying and analysis:

```
files (core file metadata)
├── frontmatter (YAML frontmatter key-value pairs)
├── tags (extracted tags with relationships)
├── links (markdown and wiki-style links)
└── content_fts (full-text searchable content)
```

## Core Tables

### `files` Table

Stores core metadata for each indexed markdown file.

```sql
CREATE TABLE files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL UNIQUE,
    directory TEXT NOT NULL,
    title TEXT,
    created_date DATETIME,
    modified_date DATETIME,
    file_size INTEGER,
    word_count INTEGER,
    character_count INTEGER,
    line_count INTEGER,
    paragraph_count INTEGER,
    heading_count INTEGER,
    content_hash TEXT,
    format_type TEXT DEFAULT 'markdown',
    encoding TEXT DEFAULT 'utf-8',
    indexed_date DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### Columns

| Column | Type | Description | Nullable |
|--------|------|-------------|----------|
| `id` | INTEGER | Primary key, auto-increment | No |
| `filename` | TEXT | File name without path | No |
| `file_path` | TEXT | Full file path (unique) | No |
| `directory` | TEXT | Directory containing the file | No |
| `title` | TEXT | Document title (from frontmatter or first heading) | Yes |
| `created_date` | DATETIME | File creation timestamp | Yes |
| `modified_date` | DATETIME | File modification timestamp | Yes |
| `file_size` | INTEGER | File size in bytes | Yes |
| `word_count` | INTEGER | Number of words in content | Yes |
| `character_count` | INTEGER | Number of characters in content | Yes |
| `line_count` | INTEGER | Number of lines in file | Yes |
| `paragraph_count` | INTEGER | Number of paragraphs | Yes |
| `heading_count` | INTEGER | Number of headings | Yes |
| `content_hash` | TEXT | SHA-256 hash of content for change detection | Yes |
| `format_type` | TEXT | File format (markdown, obsidian, joplin, etc.) | Yes |
| `encoding` | TEXT | File encoding | Yes |
| `indexed_date` | DATETIME | When file was indexed | Yes |

#### Indexes

```sql
CREATE INDEX idx_files_path ON files(file_path);
CREATE INDEX idx_files_filename ON files(filename);
CREATE INDEX idx_files_directory ON files(directory);
CREATE INDEX idx_files_modified ON files(modified_date);
CREATE INDEX idx_files_title ON files(title);
CREATE INDEX idx_files_word_count ON files(word_count);
```

### `frontmatter` Table

Stores YAML frontmatter key-value pairs from markdown files.

```sql
CREATE TABLE frontmatter (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    key TEXT NOT NULL,
    value TEXT,
    value_type TEXT DEFAULT 'string',
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);
```

#### Columns

| Column | Type | Description | Nullable |
|--------|------|-------------|----------|
| `id` | INTEGER | Primary key, auto-increment | No |
| `file_id` | INTEGER | Reference to files table | No |
| `key` | TEXT | Frontmatter key name | No |
| `value` | TEXT | Frontmatter value (serialized) | Yes |
| `value_type` | TEXT | Data type (string, number, boolean, array, object) | Yes |

#### Indexes

```sql
CREATE INDEX idx_frontmatter_file_id ON frontmatter(file_id);
CREATE INDEX idx_frontmatter_key ON frontmatter(key);
CREATE INDEX idx_frontmatter_key_value ON frontmatter(key, value);
```

### `tags` Table

Stores tags extracted from frontmatter and content.

```sql
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    tag TEXT NOT NULL,
    source TEXT DEFAULT 'content',
    position INTEGER,
    context TEXT,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);
```

#### Columns

| Column | Type | Description | Nullable |
|--------|------|-------------|----------|
| `id` | INTEGER | Primary key, auto-increment | No |
| `file_id` | INTEGER | Reference to files table | No |
| `tag` | TEXT | Tag name (normalized) | No |
| `source` | TEXT | Where tag was found (frontmatter, content, heading) | Yes |
| `position` | INTEGER | Position in file (for content tags) | Yes |
| `context` | TEXT | Surrounding context for content tags | Yes |

#### Indexes

```sql
CREATE INDEX idx_tags_file_id ON tags(file_id);
CREATE INDEX idx_tags_tag ON tags(tag);
CREATE INDEX idx_tags_source ON tags(source);
CREATE INDEX idx_tags_tag_file ON tags(tag, file_id);
```

### `links` Table

Stores markdown and wiki-style links between files.

```sql
CREATE TABLE links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file_id INTEGER NOT NULL,
    target_file_id INTEGER,
    link_text TEXT,
    target_path TEXT,
    link_type TEXT DEFAULT 'markdown',
    is_external BOOLEAN DEFAULT FALSE,
    is_broken BOOLEAN DEFAULT FALSE,
    position INTEGER,
    context TEXT,
    FOREIGN KEY (source_file_id) REFERENCES files(id) ON DELETE CASCADE,
    FOREIGN KEY (target_file_id) REFERENCES files(id) ON DELETE SET NULL
);
```

#### Columns

| Column | Type | Description | Nullable |
|--------|------|-------------|----------|
| `id` | INTEGER | Primary key, auto-increment | No |
| `source_file_id` | INTEGER | File containing the link | No |
| `target_file_id` | INTEGER | Target file (if internal and found) | Yes |
| `link_text` | TEXT | Display text of the link | Yes |
| `target_path` | TEXT | Target path or URL | Yes |
| `link_type` | TEXT | Link type (markdown, wikilink, image, etc.) | Yes |
| `is_external` | BOOLEAN | Whether link points outside the collection | Yes |
| `is_broken` | BOOLEAN | Whether target file exists | Yes |
| `position` | INTEGER | Position in source file | Yes |
| `context` | TEXT | Surrounding context | Yes |

#### Indexes

```sql
CREATE INDEX idx_links_source_file_id ON links(source_file_id);
CREATE INDEX idx_links_target_file_id ON links(target_file_id);
CREATE INDEX idx_links_target_path ON links(target_path);
CREATE INDEX idx_links_type ON links(link_type);
CREATE INDEX idx_links_broken ON links(is_broken);
```

### `content_fts` Table (Virtual)

Full-text search index for file content using SQLite FTS5.

```sql
CREATE VIRTUAL TABLE content_fts USING fts5(
    file_id UNINDEXED,
    filename,
    title,
    content,
    headings,
    tags,
    content='',
    contentless_delete=1
);
```

#### Columns

| Column | Type | Description |
|--------|------|-------------|
| `file_id` | INTEGER | Reference to files table (not indexed) |
| `filename` | TEXT | File name for search |
| `title` | TEXT | Document title for search |
| `content` | TEXT | Full file content for search |
| `headings` | TEXT | All headings concatenated |
| `tags` | TEXT | All tags concatenated |

## Views

### `file_summary` View

Provides a comprehensive summary of each file with aggregated data.

```sql
CREATE VIEW file_summary AS
SELECT
    f.id,
    f.filename,
    f.file_path,
    f.title,
    f.modified_date,
    f.word_count,
    COUNT(DISTINCT t.tag) as tag_count,
    COUNT(DISTINCT l.id) as link_count,
    COUNT(DISTINCT fm.key) as frontmatter_count,
    GROUP_CONCAT(DISTINCT t.tag) as tags,
    f.format_type,
    f.indexed_date
FROM files f
LEFT JOIN tags t ON f.id = t.file_id
LEFT JOIN links l ON f.id = l.source_file_id
LEFT JOIN frontmatter fm ON f.id = fm.file_id
GROUP BY f.id;
```

### `tag_statistics` View

Provides statistics about tag usage across the collection.

```sql
CREATE VIEW tag_statistics AS
SELECT
    t.tag,
    COUNT(*) as file_count,
    COUNT(DISTINCT t.file_id) as unique_files,
    AVG(f.word_count) as avg_word_count,
    MIN(f.modified_date) as first_used,
    MAX(f.modified_date) as last_used,
    GROUP_CONCAT(DISTINCT t.source) as sources
FROM tags t
JOIN files f ON t.file_id = f.id
GROUP BY t.tag
ORDER BY file_count DESC;
```

### `link_network` View

Shows the link network between files for relationship analysis.

```sql
CREATE VIEW link_network AS
SELECT
    sf.filename as source_file,
    sf.file_path as source_path,
    tf.filename as target_file,
    tf.file_path as target_path,
    l.link_text,
    l.link_type,
    l.is_broken,
    COUNT(*) as link_count
FROM links l
JOIN files sf ON l.source_file_id = sf.id
LEFT JOIN files tf ON l.target_file_id = tf.id
GROUP BY l.source_file_id, l.target_file_id, l.link_type;
```

### `content_statistics` View

Provides content analysis statistics.

```sql
CREATE VIEW content_statistics AS
SELECT
    COUNT(*) as total_files,
    SUM(word_count) as total_words,
    AVG(word_count) as avg_words_per_file,
    MAX(word_count) as max_words,
    MIN(word_count) as min_words,
    SUM(character_count) as total_characters,
    COUNT(DISTINCT directory) as unique_directories,
    COUNT(DISTINCT format_type) as format_types,
    MIN(created_date) as oldest_file,
    MAX(modified_date) as newest_file
FROM files
WHERE word_count IS NOT NULL;
```

## Triggers

### Update Content Hash

Automatically update content hash when file content changes.

```sql
CREATE TRIGGER update_content_hash
AFTER UPDATE OF modified_date ON files
WHEN NEW.modified_date != OLD.modified_date
BEGIN
    UPDATE files
    SET content_hash = NULL
    WHERE id = NEW.id;
END;
```

### Maintain FTS Index

Keep full-text search index synchronized with file changes.

```sql
CREATE TRIGGER fts_insert
AFTER INSERT ON files
BEGIN
    INSERT INTO content_fts(file_id, filename, title, content, headings, tags)
    VALUES (NEW.id, NEW.filename, NEW.title, '', '', '');
END;

CREATE TRIGGER fts_delete
AFTER DELETE ON files
BEGIN
    DELETE FROM content_fts WHERE file_id = OLD.id;
END;

CREATE TRIGGER fts_update
AFTER UPDATE ON files
BEGIN
    DELETE FROM content_fts WHERE file_id = OLD.id;
    INSERT INTO content_fts(file_id, filename, title, content, headings, tags)
    VALUES (NEW.id, NEW.filename, NEW.title, '', '', '');
END;
```

## Common Query Patterns

### File Queries

```sql
-- Find files by name pattern
SELECT * FROM files WHERE filename LIKE '%.md';

-- Recent files
SELECT filename, modified_date
FROM files
WHERE modified_date > date('now', '-7 days')
ORDER BY modified_date DESC;

-- Large files
SELECT filename, word_count
FROM files
WHERE word_count > 1000
ORDER BY word_count DESC;

-- Files by directory
SELECT directory, COUNT(*) as file_count
FROM files
GROUP BY directory
ORDER BY file_count DESC;
```

### Tag Queries

```sql
-- Files with specific tag
SELECT f.filename
FROM files f
JOIN tags t ON f.id = t.file_id
WHERE t.tag = 'research';

-- Most common tags
SELECT tag, COUNT(*) as usage
FROM tags
GROUP BY tag
ORDER BY usage DESC
LIMIT 10;

-- Files with multiple tags
SELECT f.filename, GROUP_CONCAT(t.tag) as tags
FROM files f
JOIN tags t ON f.id = t.file_id
WHERE t.tag IN ('ai', 'machine-learning', 'research')
GROUP BY f.id
HAVING COUNT(DISTINCT t.tag) > 1;

-- Untagged files
SELECT filename
FROM files f
WHERE NOT EXISTS (
    SELECT 1 FROM tags t WHERE t.file_id = f.id
);
```

### Link Queries

```sql
-- Most linked files
SELECT tf.filename, COUNT(*) as incoming_links
FROM links l
JOIN files tf ON l.target_file_id = tf.id
GROUP BY tf.id
ORDER BY incoming_links DESC;

-- Broken links
SELECT sf.filename, l.target_path
FROM links l
JOIN files sf ON l.source_file_id = sf.id
WHERE l.is_broken = TRUE;

-- Bidirectional links
SELECT
    f1.filename as file1,
    f2.filename as file2
FROM links l1
JOIN links l2 ON l1.source_file_id = l2.target_file_id
    AND l1.target_file_id = l2.source_file_id
JOIN files f1 ON l1.source_file_id = f1.id
JOIN files f2 ON l1.target_file_id = f2.id;
```

### Full-Text Search

```sql
-- Content search
SELECT f.filename, snippet(content_fts, 2, '<mark>', '</mark>', '...', 32) as snippet
FROM files f
JOIN content_fts fts ON f.id = fts.file_id
WHERE content_fts MATCH 'machine learning'
ORDER BY rank;

-- Title search
SELECT filename, title
FROM files f
JOIN content_fts fts ON f.id = fts.file_id
WHERE content_fts MATCH 'title: "neural networks"';

-- Combined search
SELECT f.filename, f.title
FROM files f
JOIN content_fts fts ON f.id = fts.file_id
WHERE content_fts MATCH 'artificial intelligence OR "machine learning"'
ORDER BY rank;
```

### Frontmatter Queries

```sql
-- Files with specific frontmatter
SELECT f.filename, fm.value
FROM files f
JOIN frontmatter fm ON f.id = fm.file_id
WHERE fm.key = 'author' AND fm.value = 'John Doe';

-- Files by date range (from frontmatter)
SELECT f.filename, fm.value as date
FROM files f
JOIN frontmatter fm ON f.id = fm.file_id
WHERE fm.key = 'date'
    AND date(fm.value) BETWEEN '2024-01-01' AND '2024-12-31';

-- Frontmatter statistics
SELECT fm.key, COUNT(*) as usage, COUNT(DISTINCT fm.value) as unique_values
FROM frontmatter fm
GROUP BY fm.key
ORDER BY usage DESC;
```

## Performance Optimization

### Index Usage

The schema includes strategic indexes for common query patterns:

- **File path lookups**: `idx_files_path`
- **Tag searches**: `idx_tags_tag`, `idx_tags_tag_file`
- **Link analysis**: `idx_links_source_file_id`, `idx_links_target_file_id`
- **Date filtering**: `idx_files_modified`
- **Full-text search**: `content_fts` virtual table

### Query Optimization Tips

1. **Use EXPLAIN QUERY PLAN** to analyze query performance
2. **Filter early** with WHERE clauses on indexed columns
3. **Use FTS** for content searches instead of LIKE
4. **Limit results** with LIMIT clause for large datasets
5. **Use EXISTS** instead of IN for subqueries when possible

### Database Configuration

Recommended SQLite settings for optimal performance:

```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = 10000;
PRAGMA temp_store = MEMORY;
PRAGMA mmap_size = 268435456; -- 256MB
```

## Schema Evolution

### Version Management

The schema includes version tracking for migrations:

```sql
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    applied_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT INTO schema_version (version, description)
VALUES (1, 'Initial schema');
```

### Migration Strategy

Schema changes are handled through versioned migrations:

1. **Backward Compatible**: Add new columns with defaults
2. **Data Preservation**: Migrate existing data before schema changes
3. **Index Updates**: Rebuild indexes after structural changes
4. **Validation**: Verify data integrity after migrations

This schema provides a robust foundation for storing and querying markdown file data, with optimizations for common access patterns and full-text search capabilities.