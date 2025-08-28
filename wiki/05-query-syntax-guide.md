# Query Syntax Guide

## Overview

mdquery uses SQL-like syntax to query indexed markdown content. This guide covers basic queries, advanced features, and specific use cases for different types of searches.

## Basic Queries

### Simple SELECT Statements

```sql
-- Get all files
SELECT * FROM files;

-- Get specific columns
SELECT filename, modified_date FROM files;

-- Order results
SELECT filename FROM files ORDER BY modified_date DESC;

-- Limit results
SELECT filename FROM files LIMIT 10;
```

### WHERE Clauses

```sql
-- Filter by filename
SELECT * FROM files WHERE filename LIKE '%.md';

-- Filter by date
SELECT * FROM files WHERE modified_date > '2024-01-01';

-- Filter by file size
SELECT * FROM files WHERE file_size > 1000;

-- Multiple conditions
SELECT * FROM files
WHERE modified_date > '2024-01-01'
AND file_size > 1000;
```

## Full-Text Search with FTS5

mdquery uses SQLite's FTS5 for powerful full-text search capabilities.

### Basic Content Search

```sql
-- Search content for specific terms
SELECT filename FROM files WHERE content MATCH 'knowledge management';

-- Search with multiple terms (AND)
SELECT filename FROM files WHERE content MATCH 'python AND machine learning';

-- Search with OR operator
SELECT filename FROM files WHERE content MATCH 'python OR javascript';

-- Phrase search
SELECT filename FROM files WHERE content MATCH '"machine learning"';
```

### Advanced FTS5 Features

```sql
-- Search in specific fields
SELECT filename FROM files WHERE content MATCH 'title:knowledge';
SELECT filename FROM files WHERE content MATCH 'headings:introduction';

-- Wildcard searches
SELECT filename FROM files WHERE content MATCH 'program*';

-- Proximity search (terms within 5 words)
SELECT filename FROM files WHERE content MATCH 'python NEAR/5 tutorial';

-- Boolean operators with grouping
SELECT filename FROM files WHERE content MATCH '(python OR javascript) AND tutorial';
```

### Ranking and Relevance

```sql
-- Get relevance ranking
SELECT filename, rank FROM files
WHERE content MATCH 'machine learning'
ORDER BY rank;

-- Combine with other criteria
SELECT filename, word_count, rank FROM files
WHERE content MATCH 'python' AND word_count > 500
ORDER BY rank;
```

## Metadata Querying

### Frontmatter Querying

Query YAML/TOML frontmatter data:

```sql
-- Find files with specific frontmatter key
SELECT f.filename, fm.value
FROM files f
JOIN frontmatter fm ON f.id = fm.file_id
WHERE fm.key = 'title';

-- Find files by frontmatter value
SELECT f.filename
FROM files f
JOIN frontmatter fm ON f.id = fm.file_id
WHERE fm.key = 'author' AND fm.value = 'John Doe';

-- Find files with specific tags in frontmatter
SELECT f.filename
FROM files f
JOIN frontmatter fm ON f.id = fm.file_id
WHERE fm.key = 'tags' AND fm.value LIKE '%research%';

-- Get all frontmatter for a file
SELECT fm.key, fm.value, fm.value_type
FROM files f
JOIN frontmatter fm ON f.id = fm.file_id
WHERE f.filename = 'my-note.md';
```

### Tag Querying

```sql
-- Find files with specific tag
SELECT f.filename
FROM files f
JOIN tags t ON f.id = t.file_id
WHERE t.tag = 'research';

-- Find files with tag patterns
SELECT f.filename
FROM files f
JOIN tags t ON f.id = t.file_id
WHERE t.tag LIKE 'research%';

-- Find files with multiple tags (AND)
SELECT f.filename
FROM files f
JOIN tags t ON f.id = t.file_id
WHERE t.tag IN ('research', 'python', 'machine-learning')
GROUP BY f.id
HAVING COUNT(DISTINCT t.tag) = 3;

-- Find files with any of multiple tags (OR)
SELECT DISTINCT f.filename
FROM files f
JOIN tags t ON f.id = t.file_id
WHERE t.tag IN ('research', 'python', 'machine-learning');

-- Get all tags for a file with their sources
SELECT t.tag, t.source
FROM files f
JOIN tags t ON f.id = t.file_id
WHERE f.filename = 'my-note.md';

-- Tag frequency analysis
SELECT t.tag, COUNT(*) as count
FROM tags t
GROUP BY t.tag
ORDER BY count DESC;
```

### Link Querying

```sql
-- Find files that link to external sites
SELECT f.filename, l.link_target
FROM files f
JOIN links l ON f.id = l.file_id
WHERE l.is_internal = 0;

-- Find internal links (between notes)
SELECT f.filename, l.link_target
FROM files f
JOIN links l ON f.id = l.file_id
WHERE l.is_internal = 1;

-- Find broken internal links
SELECT f.filename, l.link_target
FROM files f
JOIN links l ON f.id = l.file_id
WHERE l.is_internal = 1
AND l.link_target NOT IN (SELECT filename FROM files);

-- Find most linked-to files
SELECT l.link_target, COUNT(*) as link_count
FROM links l
WHERE l.is_internal = 1
GROUP BY l.link_target
ORDER BY link_count DESC;

-- Find files with no outgoing links
SELECT f.filename
FROM files f
LEFT JOIN links l ON f.id = l.file_id
WHERE l.id IS NULL;
```

## Advanced Query Features

### Aggregation and Grouping

```sql
-- Count files by directory
SELECT directory, COUNT(*) as file_count
FROM files
GROUP BY directory
ORDER BY file_count DESC;

-- Average word count by tag
SELECT t.tag, AVG(f.word_count) as avg_words
FROM files f
JOIN tags t ON f.id = t.file_id
GROUP BY t.tag
HAVING COUNT(*) > 5;

-- Files created by month
SELECT strftime('%Y-%m', created_date) as month, COUNT(*) as count
FROM files
GROUP BY month
ORDER BY month;
```

### Subqueries and Complex Joins

```sql
-- Find files similar to a specific file (same tags)
SELECT f2.filename
FROM files f1
JOIN tags t1 ON f1.id = t1.file_id
JOIN tags t2 ON t1.tag = t2.tag
JOIN files f2 ON t2.file_id = f2.id
WHERE f1.filename = 'reference-note.md' AND f2.id != f1.id
GROUP BY f2.id
ORDER BY COUNT(*) DESC;

-- Find orphaned files (no tags, no links)
SELECT f.filename
FROM files f
WHERE f.id NOT IN (SELECT DISTINCT file_id FROM tags)
AND f.id NOT IN (SELECT DISTINCT file_id FROM links);

-- Most active directories (most recent modifications)
SELECT directory, MAX(modified_date) as last_modified, COUNT(*) as file_count
FROM files
GROUP BY directory
ORDER BY last_modified DESC;
```

### Window Functions

```sql
-- Rank files by word count within each directory
SELECT filename, directory, word_count,
       RANK() OVER (PARTITION BY directory ORDER BY word_count DESC) as rank
FROM files;

-- Running total of files created over time
SELECT created_date, filename,
       COUNT(*) OVER (ORDER BY created_date) as running_total
FROM files
ORDER BY created_date;
```

## Query Validation and Security

### Allowed Operations
mdquery only allows safe read operations:
- `SELECT` statements
- `WITH` clauses (CTEs)
- All standard SQL functions and operators

### Blocked Operations
The following operations are blocked for security:
- `INSERT`, `UPDATE`, `DELETE`
- `DROP`, `CREATE`, `ALTER`
- `PRAGMA` statements
- Multiple statements (semicolon-separated)

### Query Limits
- Single statement only (no semicolons)
- 30-second default timeout
- Configurable result limits
- Memory usage monitoring

### Best Practices

1. **Use LIMIT**: Always use LIMIT for large result sets
2. **Index-friendly queries**: Use indexed columns in WHERE clauses
3. **FTS5 for text search**: Use MATCH for content searches instead of LIKE
4. **Avoid SELECT ***: Select only needed columns for better performance
5. **Use EXISTS**: Use EXISTS instead of IN for subqueries when possible

### Example Optimized Queries

```sql
-- Good: Uses index and LIMIT
SELECT filename, modified_date
FROM files
WHERE modified_date > '2024-01-01'
ORDER BY modified_date DESC
LIMIT 10;

-- Good: Uses FTS5 for text search
SELECT filename
FROM files
WHERE content MATCH 'python tutorial'
LIMIT 20;

-- Good: Uses EXISTS for checking relationships
SELECT f.filename
FROM files f
WHERE EXISTS (
    SELECT 1 FROM tags t
    WHERE t.file_id = f.id AND t.tag = 'research'
)
LIMIT 50;
```