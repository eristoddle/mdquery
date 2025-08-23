# Query Syntax Guide

This guide covers the complete SQL syntax supported by mdquery for searching and analyzing your markdown files.

## Database Schema Overview

mdquery organizes your markdown files into several interconnected tables:

- **`files`** - File metadata (path, dates, word count, etc.)
- **`frontmatter`** - YAML frontmatter key-value pairs
- **`tags`** - Extracted tags from frontmatter and content
- **`links`** - Markdown and wikilinks found in content
- **`content_fts`** - Full-text searchable content (FTS5)

## Basic Query Structure

All mdquery queries follow standard SQL SELECT syntax:

```sql
SELECT columns
FROM table
WHERE conditions
ORDER BY column
LIMIT number;
```

## Table Reference

### Files Table

The `files` table contains metadata about each markdown file:

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Unique file identifier |
| `path` | TEXT | Full file path |
| `filename` | TEXT | File name with extension |
| `directory` | TEXT | Directory path |
| `modified_date` | DATETIME | Last modification time |
| `created_date` | DATETIME | File creation time |
| `file_size` | INTEGER | File size in bytes |
| `content_hash` | TEXT | SHA-256 hash of content |
| `word_count` | INTEGER | Number of words in file |
| `heading_count` | INTEGER | Number of headings in file |

**Examples:**
```sql
-- Find all files
SELECT * FROM files;

-- Find large files
SELECT filename, word_count FROM files WHERE word_count > 1000;

-- Find recently modified files
SELECT filename, modified_date FROM files
WHERE modified_date > '2024-01-01'
ORDER BY modified_date DESC;

-- Find files in specific directory
SELECT filename FROM files WHERE directory LIKE '%research%';
```

### Frontmatter Table

The `frontmatter` table stores YAML frontmatter as key-value pairs:

| Column | Type | Description |
|--------|------|-------------|
| `file_id` | INTEGER | Reference to files.id |
| `key` | TEXT | Frontmatter key name |
| `value` | TEXT | Frontmatter value (as string) |
| `value_type` | TEXT | Data type: string, number, boolean, array, date |

**Examples:**
```sql
-- Find files with specific title
SELECT f.filename FROM files f
JOIN frontmatter fm ON f.id = fm.file_id
WHERE fm.key = 'title' AND fm.value LIKE '%Research%';

-- Find files by author
SELECT f.filename, fm.value as author FROM files f
JOIN frontmatter fm ON f.id = fm.file_id
WHERE fm.key = 'author';

-- Find published posts
SELECT f.filename FROM files f
JOIN frontmatter fm ON f.id = fm.file_id
WHERE fm.key = 'published' AND fm.value = 'true';

-- Find files with numeric ratings
SELECT f.filename, fm.value as rating FROM files f
JOIN frontmatter fm ON f.id = fm.file_id
WHERE fm.key = 'rating' AND fm.value_type = 'number'
ORDER BY CAST(fm.value AS REAL) DESC;
```

### Tags Table

The `tags` table contains extracted tags from both frontmatter and content:

| Column | Type | Description |
|--------|------|-------------|
| `file_id` | INTEGER | Reference to files.id |
| `tag` | TEXT | Tag name |
| `source` | TEXT | 'frontmatter' or 'content' |

**Examples:**
```sql
-- Find files with specific tag
SELECT f.filename FROM files f
JOIN tags t ON f.id = t.file_id
WHERE t.tag = 'research';

-- Find most popular tags
SELECT tag, COUNT(*) as count FROM tags
GROUP BY tag
ORDER BY count DESC
LIMIT 10;

-- Find files with multiple tags
SELECT f.filename FROM files f
WHERE f.id IN (SELECT file_id FROM tags WHERE tag = 'research')
  AND f.id IN (SELECT file_id FROM tags WHERE tag = 'project');

-- Find nested tags (Obsidian-style)
SELECT DISTINCT tag FROM tags WHERE tag LIKE '%/%';

-- Compare frontmatter vs content tags
SELECT source, COUNT(*) as count FROM tags
GROUP BY source;
```

### Links Table

The `links` table contains all links found in markdown content:

| Column | Type | Description |
|--------|------|-------------|
| `file_id` | INTEGER | Reference to files.id |
| `link_text` | TEXT | Display text of the link |
| `link_target` | TEXT | URL or target of the link |
| `link_type` | TEXT | 'markdown', 'wikilink', or 'reference' |
| `is_internal` | BOOLEAN | True for internal/relative links |

**Examples:**
```sql
-- Find files with external links
SELECT f.filename, l.link_target FROM files f
JOIN links l ON f.id = l.file_id
WHERE l.is_internal = 0;

-- Find wikilinks (Obsidian-style)
SELECT f.filename, l.link_target FROM files f
JOIN links l ON f.id = l.file_id
WHERE l.link_type = 'wikilink';

-- Find broken internal links
SELECT f.filename, l.link_target FROM files f
JOIN links l ON f.id = l.file_id
WHERE l.is_internal = 1
  AND l.link_target NOT IN (SELECT filename FROM files);

-- Count links per file
SELECT f.filename, COUNT(l.link_target) as link_count FROM files f
LEFT JOIN links l ON f.id = l.file_id
GROUP BY f.id
ORDER BY link_count DESC;
```

### Content FTS Table

The `content_fts` table provides full-text search capabilities using SQLite FTS5:

| Column | Type | Description |
|--------|------|-------------|
| `file_id` | INTEGER | Reference to files.id |
| `title` | TEXT | File title (from frontmatter or first heading) |
| `content` | TEXT | Full markdown content |
| `headings` | TEXT | All headings concatenated |

**Examples:**
```sql
-- Full-text search in content
SELECT f.filename FROM files f
JOIN content_fts fts ON f.id = fts.file_id
WHERE content_fts MATCH 'markdown AND parsing';

-- Search in titles only
SELECT f.filename FROM files f
JOIN content_fts fts ON f.id = fts.file_id
WHERE fts.title MATCH 'project';

-- Search in headings
SELECT f.filename FROM files f
JOIN content_fts fts ON f.id = fts.file_id
WHERE fts.headings MATCH 'introduction OR overview';

-- Phrase search
SELECT f.filename FROM files f
JOIN content_fts fts ON f.id = fts.file_id
WHERE content_fts MATCH '"knowledge management"';

-- Boolean search operators
SELECT f.filename FROM files f
JOIN content_fts fts ON f.id = fts.file_id
WHERE content_fts MATCH 'python NOT javascript';
```

## Advanced Query Patterns

### Unified File View

For convenience, you can create a unified view that combines file metadata with common frontmatter fields:

```sql
-- Create a comprehensive file view
SELECT
    f.filename,
    f.directory,
    f.modified_date,
    f.word_count,
    fm_title.value as title,
    fm_author.value as author,
    fm_status.value as status,
    GROUP_CONCAT(DISTINCT t.tag) as tags,
    COUNT(DISTINCT l.link_target) as link_count
FROM files f
LEFT JOIN frontmatter fm_title ON f.id = fm_title.file_id AND fm_title.key = 'title'
LEFT JOIN frontmatter fm_author ON f.id = fm_author.file_id AND fm_author.key = 'author'
LEFT JOIN frontmatter fm_status ON f.id = fm_status.file_id AND fm_status.key = 'status'
LEFT JOIN tags t ON f.id = t.file_id
LEFT JOIN links l ON f.id = l.file_id
GROUP BY f.id
ORDER BY f.modified_date DESC;
```

### Content Analysis Queries

```sql
-- Find files without titles
SELECT f.filename FROM files f
LEFT JOIN frontmatter fm ON f.id = fm.file_id AND fm.key = 'title'
WHERE fm.value IS NULL;

-- Average word count by directory
SELECT
    SUBSTR(directory, 1, INSTR(directory || '/', '/') - 1) as top_dir,
    AVG(word_count) as avg_words,
    COUNT(*) as file_count
FROM files
GROUP BY top_dir
ORDER BY avg_words DESC;

-- Tag co-occurrence analysis
SELECT
    t1.tag as tag1,
    t2.tag as tag2,
    COUNT(*) as co_occurrence
FROM tags t1
JOIN tags t2 ON t1.file_id = t2.file_id AND t1.tag < t2.tag
GROUP BY t1.tag, t2.tag
HAVING co_occurrence > 1
ORDER BY co_occurrence DESC;

-- Content freshness analysis
SELECT
    CASE
        WHEN modified_date > date('now', '-7 days') THEN 'This week'
        WHEN modified_date > date('now', '-30 days') THEN 'This month'
        WHEN modified_date > date('now', '-90 days') THEN 'Last 3 months'
        ELSE 'Older'
    END as age_group,
    COUNT(*) as file_count
FROM files
GROUP BY age_group
ORDER BY file_count DESC;
```

### Research and Analysis Queries

```sql
-- Find related content by tag similarity
WITH file_tags AS (
    SELECT f.id, f.filename, GROUP_CONCAT(t.tag) as tags
    FROM files f
    JOIN tags t ON f.id = t.file_id
    GROUP BY f.id
)
SELECT
    ft1.filename as file1,
    ft2.filename as file2,
    ft1.tags as tags1,
    ft2.tags as tags2
FROM file_tags ft1
JOIN file_tags ft2 ON ft1.id < ft2.id
WHERE ft1.tags LIKE '%research%' AND ft2.tags LIKE '%research%';

-- Source attribution tracking
SELECT
    f.filename,
    l.link_target as source,
    l.link_text as context
FROM files f
JOIN links l ON f.id = l.file_id
WHERE l.is_internal = 0
  AND (l.link_text LIKE '%source%' OR l.link_text LIKE '%reference%')
ORDER BY f.filename;

-- Content gap analysis
SELECT
    t.tag,
    COUNT(*) as current_count,
    date('now', '-30 days') as cutoff_date,
    COUNT(CASE WHEN f.modified_date > date('now', '-30 days') THEN 1 END) as recent_count
FROM tags t
JOIN files f ON t.file_id = f.id
GROUP BY t.tag
HAVING current_count > 5 AND recent_count = 0
ORDER BY current_count DESC;
```

## FTS5 Search Syntax

The `content_fts` table uses SQLite's FTS5 extension, which supports advanced search operators:

### Basic Operators

- **AND**: `term1 AND term2` - Both terms must be present
- **OR**: `term1 OR term2` - Either term can be present
- **NOT**: `term1 NOT term2` - First term present, second term absent
- **Phrase**: `"exact phrase"` - Exact phrase match
- **Prefix**: `term*` - Terms starting with "term"

### Examples

```sql
-- Boolean search
WHERE content_fts MATCH 'python AND (django OR flask)'

-- Phrase search
WHERE content_fts MATCH '"machine learning" OR "artificial intelligence"'

-- Prefix search
WHERE content_fts MATCH 'develop*'  -- matches develop, development, developer, etc.

-- Exclude terms
WHERE content_fts MATCH 'programming NOT javascript'

-- Column-specific search
WHERE fts.title MATCH 'project' AND fts.content MATCH 'python'
```

## Date and Time Queries

SQLite provides powerful date/time functions for temporal analysis:

```sql
-- Files modified today
SELECT * FROM files WHERE date(modified_date) = date('now');

-- Files from last week
SELECT * FROM files WHERE modified_date > date('now', '-7 days');

-- Files by month
SELECT
    strftime('%Y-%m', modified_date) as month,
    COUNT(*) as file_count
FROM files
GROUP BY month
ORDER BY month DESC;

-- Files modified on weekends
SELECT filename, modified_date FROM files
WHERE CAST(strftime('%w', modified_date) AS INTEGER) IN (0, 6);

-- Seasonal analysis
SELECT
    CASE CAST(strftime('%m', modified_date) AS INTEGER)
        WHEN 12 OR 1 OR 2 THEN 'Winter'
        WHEN 3 OR 4 OR 5 THEN 'Spring'
        WHEN 6 OR 7 OR 8 THEN 'Summer'
        ELSE 'Fall'
    END as season,
    COUNT(*) as file_count
FROM files
GROUP BY season;
```

## Performance Tips

1. **Use Indexes**: The database is pre-indexed on common query patterns
2. **Limit Results**: Use `LIMIT` for large result sets
3. **Specific Conditions**: More specific WHERE clauses run faster
4. **FTS5 for Text**: Use `content_fts` table for text searches, not LIKE on content
5. **Join Order**: Put most selective conditions first in JOINs

### Optimized Query Examples

```sql
-- Good: Use FTS5 for text search
SELECT f.filename FROM files f
JOIN content_fts fts ON f.id = fts.file_id
WHERE content_fts MATCH 'python';

-- Avoid: LIKE on large text fields
-- SELECT filename FROM files WHERE content LIKE '%python%';

-- Good: Specific tag lookup
SELECT f.filename FROM files f
JOIN tags t ON f.id = t.file_id
WHERE t.tag = 'research';

-- Good: Use LIMIT for exploration
SELECT * FROM files ORDER BY modified_date DESC LIMIT 10;
```

## Common Query Patterns

### Finding Files

```sql
-- By name pattern
SELECT * FROM files WHERE filename LIKE 'meeting-%.md';

-- By directory
SELECT * FROM files WHERE directory LIKE '%projects%';

-- By size
SELECT filename, word_count FROM files WHERE word_count BETWEEN 500 AND 2000;

-- By date range
SELECT * FROM files WHERE modified_date BETWEEN '2024-01-01' AND '2024-01-31';
```

### Content Analysis

```sql
-- Empty or short files
SELECT filename, word_count FROM files WHERE word_count < 50;

-- Files without frontmatter
SELECT f.filename FROM files f
LEFT JOIN frontmatter fm ON f.id = fm.file_id
WHERE fm.file_id IS NULL;

-- Duplicate titles
SELECT fm.value as title, COUNT(*) as count FROM frontmatter fm
WHERE fm.key = 'title'
GROUP BY fm.value
HAVING count > 1;
```

### Link Analysis

```sql
-- Most linked-to files
SELECT l.link_target, COUNT(*) as incoming_links FROM links l
WHERE l.is_internal = 1
GROUP BY l.link_target
ORDER BY incoming_links DESC;

-- Files with no outgoing links
SELECT f.filename FROM files f
LEFT JOIN links l ON f.id = l.file_id
WHERE l.file_id IS NULL;

-- External link domains
SELECT
    SUBSTR(l.link_target, 1, INSTR(l.link_target || '/', '/') - 1) as domain,
    COUNT(*) as link_count
FROM links l
WHERE l.is_internal = 0 AND l.link_target LIKE 'http%'
GROUP BY domain
ORDER BY link_count DESC;
```

This comprehensive syntax guide should help you write powerful queries to analyze and search your markdown collections. For more examples, see the [Examples](examples/) section.