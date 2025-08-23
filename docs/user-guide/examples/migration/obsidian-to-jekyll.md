# Obsidian to Jekyll Migration

This example demonstrates how to use mdquery to migrate content from Obsidian to Jekyll, handling format differences and maintaining content integrity.

## Migration Overview

**Source**: Obsidian vault with wikilinks, tags, and custom formatting
**Target**: Jekyll static site with proper frontmatter and markdown links

**Key Challenges**:
- Convert wikilinks to Jekyll-compatible links
- Transform Obsidian tags to Jekyll categories/tags
- Adapt frontmatter formats
- Handle attachment references
- Maintain content relationships

## Pre-Migration Analysis

### 1. Assess Obsidian Vault Structure

```sql
-- Analyze vault content structure
SELECT
    f.directory,
    COUNT(*) as file_count,
    AVG(f.word_count) as avg_word_count,
    COUNT(DISTINCT t.tag) as unique_tags,
    SUM(CASE WHEN f.filename LIKE '%.png' OR f.filename LIKE '%.jpg' THEN 1 ELSE 0 END) as image_files
FROM files f
LEFT JOIN tags t ON f.id = t.file_id
WHERE f.directory LIKE '%obsidian-vault%'
GROUP BY f.directory
ORDER BY file_count DESC;
```

### 2. Identify Wikilink Patterns

```sql
-- Find all wikilink patterns that need conversion
SELECT
    l.link_text,
    l.target_path,
    COUNT(*) as usage_count,
    GROUP_CONCAT(DISTINCT f.filename) as source_files
FROM links l
JOIN files f ON l.source_file_id = f.id
WHERE f.directory LIKE '%obsidian-vault%'
  AND l.link_type = 'wikilink'
GROUP BY l.link_text, l.target_path
ORDER BY usage_count DESC;
```

### 3. Tag Usage Analysis

```sql
-- Analyze tag usage for Jekyll category mapping
SELECT
    t.tag,
    COUNT(*) as usage_count,
    COUNT(DISTINCT f.directory) as directories_used,
    GROUP_CONCAT(DISTINCT f.filename, '; ') as example_files
FROM tags t
JOIN files f ON t.file_id = f.id
WHERE f.directory LIKE '%obsidian-vault%'
GROUP BY t.tag
HAVING usage_count >= 3
ORDER BY usage_count DESC;
```

## Migration Queries

### 1. Generate Jekyll Frontmatter

```sql
-- Convert Obsidian notes to Jekyll format
SELECT
    f.filename,
    f.file_path,
    '---' as frontmatter_start,
    'title: "' || COALESCE(f.title, replace(f.filename, '.md', '')) || '"' as title_line,
    'date: ' || COALESCE(fm_date.value, date('now')) as date_line,
    'categories: [' || COALESCE(fm_category.value, 'uncategorized') || ']' as categories_line,
    'tags: [' || GROUP_CONCAT(DISTINCT t.tag, ', ') || ']' as tags_line,
    'layout: post' as layout_line,
    '---' as frontmatter_end
FROM files f
LEFT JOIN frontmatter fm_date ON f.id = fm_date.file_id AND fm_date.key = 'date'
LEFT JOIN frontmatter fm_category ON f.id = fm_category.file_id AND fm_category.key = 'category'
LEFT JOIN tags t ON f.id = t.file_id
WHERE f.directory LIKE '%obsidian-vault%'
  AND f.filename LIKE '%.md'
GROUP BY f.id
ORDER BY f.filename;
```

### 2. Wikilink Conversion Map

```sql
-- Create mapping for wikilink to Jekyll link conversion
SELECT
    l.link_text as obsidian_wikilink,
    CASE
        WHEN target_f.filename IS NOT NULL THEN
            '{% post_url ' || substr(target_f.filename, 1, length(target_f.filename) - 3) || ' %}'
        ELSE
            '[' || l.link_text || '](#broken-link)'
    END as jekyll_link,
    CASE
        WHEN target_f.filename IS NOT NULL THEN 'valid'
        ELSE 'broken'
    END as link_status,
    COUNT(*) as usage_count
FROM links l
JOIN files f ON l.source_file_id = f.id
LEFT JOIN files target_f ON l.target_file_id = target_f.id
WHERE f.directory LIKE '%obsidian-vault%'
  AND l.link_type = 'wikilink'
GROUP BY l.link_text, target_f.filename
ORDER BY usage_count DESC;
```

### 3. Image Reference Migration

```sql
-- Handle image and attachment references
SELECT
    f.filename as source_file,
    l.target_path as obsidian_image_path,
    CASE
        WHEN l.target_path LIKE '%attachments/%' THEN
            '/assets/images/' || substr(l.target_path, instr(l.target_path, '/') + 1)
        ELSE
            '/assets/images/' || l.target_path
    END as jekyll_image_path,
    l.link_text as alt_text
FROM files f
JOIN links l ON f.id = l.source_file_id
WHERE f.directory LIKE '%obsidian-vault%'
  AND l.link_type = 'image'
  AND (l.target_path LIKE '%.png' OR l.target_path LIKE '%.jpg' OR l.target_path LIKE '%.gif')
ORDER BY f.filename;
```

### 4. Content Structure Analysis

```sql
-- Analyze content that needs structural changes
SELECT
    f.filename,
    f.word_count,
    COUNT(CASE WHEN l.link_type = 'wikilink' THEN 1 END) as wikilinks_count,
    COUNT(CASE WHEN l.link_type = 'image' THEN 1 END) as images_count,
    COUNT(DISTINCT t.tag) as tags_count,
    CASE
        WHEN COUNT(CASE WHEN l.link_type = 'wikilink' THEN 1 END) > 10 THEN 'High'
        WHEN COUNT(CASE WHEN l.link_type = 'wikilink' THEN 1 END) > 5 THEN 'Medium'
        ELSE 'Low'
    END as migration_complexity
FROM files f
LEFT JOIN links l ON f.id = l.source_file_id
LEFT JOIN tags t ON f.id = t.file_id
WHERE f.directory LIKE '%obsidian-vault%'
  AND f.filename LIKE '%.md'
GROUP BY f.id
ORDER BY migration_complexity DESC, wikilinks_count DESC;
```

## Post-Migration Validation

### 1. Link Integrity Check

```sql
-- Verify all links work in Jekyll format
SELECT
    f.filename as source_file,
    l.target_path as original_target,
    CASE
        WHEN target_f.filename IS NOT NULL THEN 'Valid'
        ELSE 'Broken'
    END as link_status,
    l.link_text as link_context
FROM files f
JOIN links l ON f.id = l.source_file_id
LEFT JOIN files target_f ON l.target_file_id = target_f.id
WHERE f.directory LIKE '%jekyll-site%'
ORDER BY link_status, f.filename;
```

### 2. Content Completeness Verification

```sql
-- Compare content before and after migration
SELECT
    'Obsidian' as source,
    COUNT(*) as total_files,
    SUM(word_count) as total_words,
    COUNT(DISTINCT t.tag) as unique_tags,
    AVG(word_count) as avg_words_per_file
FROM files f
LEFT JOIN tags t ON f.id = t.file_id
WHERE f.directory LIKE '%obsidian-vault%'
  AND f.filename LIKE '%.md'

UNION ALL

SELECT
    'Jekyll' as source,
    COUNT(*) as total_files,
    SUM(word_count) as total_words,
    COUNT(DISTINCT t.tag) as unique_tags,
    AVG(word_count) as avg_words_per_file
FROM files f
LEFT JOIN tags t ON f.id = t.file_id
WHERE f.directory LIKE '%jekyll-site%'
  AND f.filename LIKE '%.md';
```

### 3. Tag Migration Verification

```sql
-- Verify tag migration accuracy
SELECT
    obsidian_tags.tag,
    obsidian_tags.obsidian_count,
    COALESCE(jekyll_tags.jekyll_count, 0) as jekyll_count,
    CASE
        WHEN obsidian_tags.obsidian_count = COALESCE(jekyll_tags.jekyll_count, 0) THEN 'Perfect'
        WHEN COALESCE(jekyll_tags.jekyll_count, 0) = 0 THEN 'Missing'
        ELSE 'Partial'
    END as migration_status
FROM (
    SELECT t.tag, COUNT(*) as obsidian_count
    FROM tags t
    JOIN files f ON t.file_id = f.id
    WHERE f.directory LIKE '%obsidian-vault%'
    GROUP BY t.tag
) obsidian_tags
LEFT JOIN (
    SELECT t.tag, COUNT(*) as jekyll_count
    FROM tags t
    JOIN files f ON t.file_id = f.id
    WHERE f.directory LIKE '%jekyll-site%'
    GROUP BY t.tag
) jekyll_tags ON obsidian_tags.tag = jekyll_tags.tag
ORDER BY migration_status, obsidian_tags.obsidian_count DESC;
```

## Migration Scripts Generation

### 1. Batch Rename Script

```sql
-- Generate bash script for file renaming (Jekyll date format)
SELECT
    'mv "' || f.file_path || '" "' ||
    f.directory || '/' ||
    COALESCE(fm_date.value, date('now')) || '-' ||
    lower(replace(replace(f.title, ' ', '-'), '''', '')) || '.md"' as rename_command
FROM files f
LEFT JOIN frontmatter fm_date ON f.id = fm_date.file_id AND fm_date.key = 'date'
WHERE f.directory LIKE '%obsidian-vault%'
  AND f.filename LIKE '%.md'
  AND f.title IS NOT NULL
ORDER BY f.filename;
```

### 2. Content Replacement Script

```sql
-- Generate sed commands for wikilink replacement
SELECT
    'sed -i "s/\[\[' || l.link_text || '\]\]/' ||
    CASE
        WHEN target_f.filename IS NOT NULL THEN
            '[' || l.link_text || ']({% post_url ' ||
            substr(target_f.filename, 1, length(target_f.filename) - 3) || ' %})'
        ELSE
            '[' || l.link_text || '](#broken-link)'
    END || '/g" "' || f.file_path || '"' as sed_command
FROM links l
JOIN files f ON l.source_file_id = f.id
LEFT JOIN files target_f ON l.target_file_id = target_f.id
WHERE f.directory LIKE '%obsidian-vault%'
  AND l.link_type = 'wikilink'
GROUP BY l.link_text, f.file_path, target_f.filename
ORDER BY f.filename;
```

### 3. Frontmatter Addition Script

```sql
-- Generate script to add Jekyll frontmatter
SELECT
    f.file_path,
    '---
title: "' || COALESCE(f.title, replace(f.filename, '.md', '')) || '"
date: ' || COALESCE(fm_date.value, date('now')) || '
categories: [' || COALESCE(fm_category.value, 'blog') || ']
tags: [' || COALESCE(GROUP_CONCAT(DISTINCT t.tag, ', '), '') || ']
layout: post
---

' as frontmatter_content
FROM files f
LEFT JOIN frontmatter fm_date ON f.id = fm_date.file_id AND fm_date.key = 'date'
LEFT JOIN frontmatter fm_category ON f.id = fm_category.file_id AND fm_category.key = 'category'
LEFT JOIN tags t ON f.id = t.file_id
WHERE f.directory LIKE '%obsidian-vault%'
  AND f.filename LIKE '%.md'
GROUP BY f.id
ORDER BY f.filename;
```

## Quality Assurance

### 1. Migration Report

```sql
-- Generate comprehensive migration report
SELECT
    'Migration Summary' as section,
    'Files Migrated: ' || COUNT(*) as details
FROM files f
WHERE f.directory LIKE '%jekyll-site%'
  AND f.filename LIKE '%.md'

UNION ALL

SELECT
    'Link Conversion',
    'Wikilinks Converted: ' || COUNT(*)
FROM links l
JOIN files f ON l.source_file_id = f.id
WHERE f.directory LIKE '%jekyll-site%'
  AND l.link_type = 'markdown'

UNION ALL

SELECT
    'Broken Links',
    'Broken Links Found: ' || COUNT(*)
FROM links l
JOIN files f ON l.source_file_id = f.id
WHERE f.directory LIKE '%jekyll-site%'
  AND l.is_broken = 1

UNION ALL

SELECT
    'Tag Migration',
    'Tags Preserved: ' || COUNT(DISTINCT t.tag)
FROM tags t
JOIN files f ON t.file_id = f.id
WHERE f.directory LIKE '%jekyll-site%';
```

### 2. Content Diff Analysis

```sql
-- Identify content changes during migration
SELECT
    obsidian_f.filename as original_file,
    jekyll_f.filename as migrated_file,
    obsidian_f.word_count as original_word_count,
    jekyll_f.word_count as migrated_word_count,
    ABS(obsidian_f.word_count - jekyll_f.word_count) as word_count_diff,
    CASE
        WHEN ABS(obsidian_f.word_count - jekyll_f.word_count) = 0 THEN 'Identical'
        WHEN ABS(obsidian_f.word_count - jekyll_f.word_count) <= 10 THEN 'Minor Changes'
        ELSE 'Significant Changes'
    END as change_level
FROM files obsidian_f
JOIN files jekyll_f ON replace(obsidian_f.filename, '.md', '') =
                       substr(jekyll_f.filename, 12)  -- Skip date prefix
WHERE obsidian_f.directory LIKE '%obsidian-vault%'
  AND jekyll_f.directory LIKE '%jekyll-site%'
  AND obsidian_f.filename LIKE '%.md'
  AND jekyll_f.filename LIKE '%.md'
ORDER BY word_count_diff DESC;
```

## Best Practices

### Pre-Migration
- Backup original Obsidian vault
- Analyze content structure and complexity
- Plan tag/category mapping strategy
- Identify custom formatting that needs attention

### During Migration
- Process files in batches
- Validate each step before proceeding
- Keep detailed logs of changes made
- Test converted links and references

### Post-Migration
- Verify content integrity
- Check all internal links work
- Validate image references
- Test Jekyll site builds successfully

### Maintenance
- Set up monitoring for broken links
- Regular content audits
- Update migration scripts for future use
- Document lessons learned

This migration workflow ensures a systematic, verifiable transition from Obsidian to Jekyll while preserving content relationships and maintaining data integrity.