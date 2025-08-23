# Best Practices Guide

This guide covers best practices for using mdquery effectively with different markdown systems and workflows.

## Indexing Best Practices

### Directory Organization

**Organize by System Type**
```bash
# Good: Separate different markdown systems
mdquery index ~/Documents/Obsidian-Vault --cache-path obsidian.db
mdquery index ~/Documents/Jekyll-Site/_posts --cache-path blog.db
mdquery index ~/Documents/Research-Notes --cache-path research.db

# Also Good: Combined index for cross-system queries
mdquery index ~/Documents/Notes --cache-path unified.db
```

**Use Descriptive Cache Names**
```bash
# Good: Descriptive cache names
mdquery index ~/work-notes --cache-path work-knowledge-base.db
mdquery index ~/personal-notes --cache-path personal-journal.db

# Avoid: Generic names when you have multiple collections
# mdquery index ~/notes --cache-path cache.db
```

### Incremental Updates

**Set Up Regular Indexing**
```bash
# Create a script for regular updates
#!/bin/bash
# update-index.sh
mdquery index ~/Documents/Notes --cache-path ~/notes.db
echo "Index updated: $(date)"

# Run via cron for automatic updates
# 0 */6 * * * /path/to/update-index.sh
```

**Monitor Large Collections**
```bash
# Use verbose mode for large collections
mdquery index ~/large-collection --verbose --cache-path large.db

# Check index statistics
mdquery query "SELECT COUNT(*) as total_files,
                      SUM(word_count) as total_words,
                      AVG(word_count) as avg_words
               FROM files" --cache-path large.db
```

## Query Best Practices

### Start Simple, Then Refine

**Progressive Query Development**
```sql
-- 1. Start with basic exploration
SELECT COUNT(*) FROM files;

-- 2. Add basic filtering
SELECT filename FROM files WHERE modified_date > '2024-01-01';

-- 3. Add joins for richer data
SELECT f.filename, GROUP_CONCAT(t.tag) as tags
FROM files f
LEFT JOIN tags t ON f.id = t.file_id
WHERE f.modified_date > '2024-01-01'
GROUP BY f.id;

-- 4. Add complex analysis
SELECT f.filename, f.word_count, GROUP_CONCAT(t.tag) as tags,
       COUNT(l.link_target) as link_count
FROM files f
LEFT JOIN tags t ON f.id = t.file_id
LEFT JOIN links l ON f.id = l.file_id
WHERE f.modified_date > '2024-01-01'
GROUP BY f.id
ORDER BY f.word_count DESC;
```

### Use Appropriate Search Methods

**Full-Text Search for Content**
```sql
-- Good: Use FTS5 for text search
SELECT f.filename FROM files f
JOIN content_fts fts ON f.id = fts.file_id
WHERE content_fts MATCH 'machine learning';

-- Avoid: LIKE for content search (slow)
-- SELECT filename FROM files WHERE content LIKE '%machine learning%';
```

**Exact Matching for Metadata**
```sql
-- Good: Exact tag matching
SELECT f.filename FROM files f
JOIN tags t ON f.id = t.file_id
WHERE t.tag = 'research';

-- Good: Pattern matching for filenames
SELECT filename FROM files WHERE filename LIKE 'meeting-2024%';
```

### Optimize Query Performance

**Use LIMIT for Exploration**
```sql
-- Good: Limit results during exploration
SELECT * FROM files ORDER BY modified_date DESC LIMIT 20;

-- Good: Use LIMIT with complex queries
SELECT f.filename, COUNT(t.tag) as tag_count
FROM files f
LEFT JOIN tags t ON f.id = t.file_id
GROUP BY f.id
ORDER BY tag_count DESC
LIMIT 10;
```

**Filter Early and Specifically**
```sql
-- Good: Specific date filtering
SELECT f.filename FROM files f
JOIN tags t ON f.id = t.file_id
WHERE f.modified_date > '2024-01-01' AND t.tag = 'project';

-- Less efficient: Broad filtering
-- SELECT f.filename FROM files f
-- JOIN tags t ON f.id = t.file_id
-- WHERE t.tag LIKE '%proj%';
```

## System-Specific Best Practices

### Obsidian Vaults

**Leverage Obsidian Features**
```sql
-- Find MOCs (Maps of Content)
SELECT f.filename FROM files f
JOIN frontmatter fm ON f.id = fm.file_id
WHERE fm.key = 'type' AND fm.value = 'moc';

-- Analyze wikilink networks
SELECT f.filename, COUNT(l.link_target) as outgoing_links
FROM files f
JOIN links l ON f.id = l.file_id
WHERE l.link_type = 'wikilink'
GROUP BY f.id
ORDER BY outgoing_links DESC;

-- Find nested tag hierarchies
SELECT tag, COUNT(*) as usage FROM tags
WHERE tag LIKE '%/%'
GROUP BY tag
ORDER BY usage DESC;
```

**Daily Notes Analysis**
```sql
-- Find daily notes pattern
SELECT filename FROM files
WHERE filename REGEXP '^[0-9]{4}-[0-9]{2}-[0-9]{2}\.md$'
ORDER BY filename DESC;

-- Analyze daily note consistency
SELECT
    strftime('%Y-%m', modified_date) as month,
    COUNT(*) as daily_notes
FROM files
WHERE filename REGEXP '^[0-9]{4}-[0-9]{2}-[0-9]{2}\.md$'
GROUP BY month
ORDER BY month DESC;
```

### Jekyll Sites

**Blog Post Analysis**
```sql
-- Find published posts
SELECT f.filename, fm_title.value as title, fm_date.value as date
FROM files f
JOIN frontmatter fm_pub ON f.id = fm_pub.file_id AND fm_pub.key = 'published' AND fm_pub.value = 'true'
JOIN frontmatter fm_title ON f.id = fm_title.file_id AND fm_title.key = 'title'
JOIN frontmatter fm_date ON f.id = fm_date.file_id AND fm_date.key = 'date'
WHERE f.directory LIKE '%_posts%'
ORDER BY fm_date.value DESC;

-- SEO analysis
SELECT
    f.filename,
    fm_title.value as title,
    fm_desc.value as description,
    CASE WHEN fm_desc.value IS NULL THEN 'Missing' ELSE 'Present' END as seo_status
FROM files f
LEFT JOIN frontmatter fm_title ON f.id = fm_title.file_id AND fm_title.key = 'title'
LEFT JOIN frontmatter fm_desc ON f.id = fm_desc.file_id AND fm_desc.key = 'description'
WHERE f.directory LIKE '%_posts%';
```

**Category and Tag Analysis**
```sql
-- Category distribution
SELECT fm.value as category, COUNT(*) as post_count
FROM frontmatter fm
JOIN files f ON fm.file_id = f.id
WHERE fm.key = 'categories' AND f.directory LIKE '%_posts%'
GROUP BY fm.value
ORDER BY post_count DESC;

-- Find posts without categories
SELECT f.filename FROM files f
LEFT JOIN frontmatter fm ON f.id = fm.file_id AND fm.key = 'categories'
WHERE f.directory LIKE '%_posts%' AND fm.value IS NULL;
```

### Joplin Exports

**Handle Joplin Metadata**
```sql
-- Extract Joplin IDs from content
SELECT f.filename,
       SUBSTR(fts.content,
              INSTR(fts.content, 'id: ') + 4,
              36) as joplin_id
FROM files f
JOIN content_fts fts ON f.id = fts.file_id
WHERE fts.content MATCH 'id:'
  AND f.directory LIKE '%joplin%';

-- Find Joplin notebooks (based on directory structure)
SELECT DISTINCT directory as notebook FROM files
WHERE directory LIKE '%joplin%'
ORDER BY notebook;
```

## Workflow-Specific Best Practices

### Research Workflows

**Source Tracking**
```sql
-- Create a research sources view
CREATE VIEW research_sources AS
SELECT
    f.filename,
    f.modified_date,
    fm_source.value as source_url,
    fm_author.value as author,
    GROUP_CONCAT(DISTINCT t.tag) as topics
FROM files f
LEFT JOIN frontmatter fm_source ON f.id = fm_source.file_id AND fm_source.key = 'source'
LEFT JOIN frontmatter fm_author ON f.id = fm_author.file_id AND fm_author.key = 'author'
LEFT JOIN tags t ON f.id = t.file_id
WHERE t.tag LIKE '%research%' OR f.filename LIKE '%research%'
GROUP BY f.id;

-- Query the view
SELECT * FROM research_sources WHERE author IS NOT NULL;
```

**Literature Review Queries**
```sql
-- Find citation patterns
SELECT
    l.link_target as cited_work,
    COUNT(*) as citation_count,
    GROUP_CONCAT(DISTINCT f.filename) as citing_files
FROM files f
JOIN links l ON f.id = l.file_id
WHERE l.is_internal = 0
  AND (l.link_target LIKE '%.pdf' OR l.link_target LIKE '%doi.org%')
GROUP BY l.link_target
ORDER BY citation_count DESC;

-- Research topic evolution
SELECT
    strftime('%Y-%m', f.modified_date) as month,
    t.tag as topic,
    COUNT(*) as mentions
FROM files f
JOIN tags t ON f.id = t.file_id
WHERE t.tag IN ('ai', 'machine-learning', 'nlp', 'deep-learning')
GROUP BY month, topic
ORDER BY month DESC, mentions DESC;
```

### Content Creation Workflows

**Editorial Calendar**
```sql
-- Content pipeline status
SELECT
    fm_status.value as status,
    COUNT(*) as count,
    GROUP_CONCAT(f.filename) as files
FROM files f
JOIN frontmatter fm_status ON f.id = fm_status.file_id AND fm_status.key = 'status'
WHERE f.directory LIKE '%drafts%' OR f.directory LIKE '%posts%'
GROUP BY fm_status.value;

-- Content gaps analysis
SELECT
    t.tag as topic,
    COUNT(*) as existing_content,
    MAX(f.modified_date) as last_updated
FROM tags t
JOIN files f ON t.file_id = f.id
WHERE f.directory LIKE '%posts%'
GROUP BY t.tag
HAVING last_updated < date('now', '-90 days')
ORDER BY existing_content DESC;
```

**SEO Optimization**
```sql
-- Missing meta descriptions
SELECT f.filename, f.word_count
FROM files f
LEFT JOIN frontmatter fm ON f.id = fm.file_id AND fm.key = 'description'
WHERE f.directory LIKE '%_posts%' AND fm.value IS NULL
ORDER BY f.word_count DESC;

-- Tag consistency check
SELECT
    t.tag,
    COUNT(*) as usage,
    COUNT(DISTINCT f.directory) as directories
FROM tags t
JOIN files f ON t.file_id = f.id
GROUP BY t.tag
HAVING usage > 1 AND directories > 1
ORDER BY usage DESC;
```

### Knowledge Management Workflows

**Knowledge Graph Analysis**
```sql
-- Find hub notes (highly connected)
SELECT
    f.filename,
    COUNT(DISTINCT l_out.link_target) as outgoing_links,
    COUNT(DISTINCT l_in.file_id) as incoming_links,
    (COUNT(DISTINCT l_out.link_target) + COUNT(DISTINCT l_in.file_id)) as total_connections
FROM files f
LEFT JOIN links l_out ON f.id = l_out.file_id AND l_out.is_internal = 1
LEFT JOIN links l_in ON f.filename = l_in.link_target AND l_in.is_internal = 1
GROUP BY f.id
ORDER BY total_connections DESC
LIMIT 20;

-- Find orphaned notes
SELECT f.filename FROM files f
LEFT JOIN links l_out ON f.id = l_out.file_id
LEFT JOIN links l_in ON f.filename = l_in.link_target
WHERE l_out.file_id IS NULL AND l_in.link_target IS NULL;
```

**Knowledge Maintenance**
```sql
-- Find stale content
SELECT
    f.filename,
    f.modified_date,
    julianday('now') - julianday(f.modified_date) as days_old
FROM files f
WHERE days_old > 180
ORDER BY days_old DESC;

-- Content quality metrics
SELECT
    f.filename,
    f.word_count,
    f.heading_count,
    COUNT(DISTINCT t.tag) as tag_count,
    COUNT(DISTINCT l.link_target) as link_count,
    CASE
        WHEN f.word_count > 500 AND COUNT(DISTINCT t.tag) > 2 THEN 'High'
        WHEN f.word_count > 200 AND COUNT(DISTINCT t.tag) > 1 THEN 'Medium'
        ELSE 'Low'
    END as quality_score
FROM files f
LEFT JOIN tags t ON f.id = t.file_id
LEFT JOIN links l ON f.id = l.file_id
GROUP BY f.id
ORDER BY quality_score DESC, f.word_count DESC;
```

## Performance and Maintenance

### Regular Maintenance Tasks

**Database Optimization**
```bash
# Vacuum database periodically
sqlite3 notes.db "VACUUM;"

# Analyze query performance
sqlite3 notes.db "ANALYZE;"

# Check database integrity
sqlite3 notes.db "PRAGMA integrity_check;"
```

**Index Validation**
```sql
-- Check for missing files
SELECT f.filename, f.path FROM files f
WHERE NOT EXISTS (
    SELECT 1 FROM pragma_table_info('files')
    WHERE name = 'path' AND f.path IS NOT NULL
);

-- Validate tag consistency
SELECT COUNT(*) as orphaned_tags FROM tags t
WHERE NOT EXISTS (SELECT 1 FROM files f WHERE f.id = t.file_id);
```

### Backup Strategies

**Database Backups**
```bash
# Regular backup script
#!/bin/bash
DATE=$(date +%Y%m%d)
cp notes.db "backups/notes-$DATE.db"

# Keep only last 30 days
find backups/ -name "notes-*.db" -mtime +30 -delete
```

**Export Important Queries**
```bash
# Save important queries as scripts
cat > research-summary.sql << 'EOF'
SELECT
    f.filename,
    f.word_count,
    GROUP_CONCAT(DISTINCT t.tag) as tags,
    f.modified_date
FROM files f
LEFT JOIN tags t ON f.id = t.file_id
WHERE t.tag LIKE '%research%'
GROUP BY f.id
ORDER BY f.modified_date DESC;
EOF

# Run saved queries
mdquery query --file research-summary.sql --format csv > research-report.csv
```

## Common Pitfalls to Avoid

### Query Pitfalls

**Avoid Cartesian Products**
```sql
-- Bad: Missing JOIN condition
-- SELECT f.filename, t.tag FROM files f, tags t;

-- Good: Proper JOIN
SELECT f.filename, t.tag FROM files f
JOIN tags t ON f.id = t.file_id;
```

**Avoid Inefficient LIKE Patterns**
```sql
-- Slow: Leading wildcard
-- SELECT filename FROM files WHERE filename LIKE '%report%';

-- Better: Use FTS5 for content search
SELECT f.filename FROM files f
JOIN content_fts fts ON f.id = fts.file_id
WHERE content_fts MATCH 'report';

-- Good: Trailing wildcard for filenames
SELECT filename FROM files WHERE filename LIKE 'report%';
```

### Indexing Pitfalls

**Don't Over-Index**
```bash
# Avoid: Indexing the same directory multiple times
# mdquery index ~/notes
# mdquery index ~/notes/subfolder  # Already included above

# Good: Index at appropriate level
mdquery index ~/notes --cache-path notes.db
```

**Handle Symbolic Links Carefully**
```bash
# Be aware of symbolic links that might cause duplicates
# Use --follow-symlinks flag consciously
mdquery index ~/notes --follow-symlinks --cache-path notes.db
```

By following these best practices, you'll get the most value from mdquery while maintaining good performance and data quality.