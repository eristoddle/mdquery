# mdquery Examples

This directory contains real-world examples of using mdquery for different workflows and use cases.

## Example Categories

### Research Workflows
- [Literature Review](research/literature-review.md) - Managing academic research and citations
- [Source Tracking](research/source-tracking.md) - Tracking sources and references across notes
- [Topic Analysis](research/topic-analysis.md) - Analyzing research themes and patterns

### Content Creation
- [Blog Management](content/blog-management.md) - Managing blog posts and editorial workflow
- [SEO Analysis](content/seo-analysis.md) - Optimizing content for search engines
- [Content Planning](content/content-planning.md) - Editorial calendar and content gaps

### Knowledge Management
- [Personal Knowledge Base](knowledge/personal-kb.md) - Organizing personal notes and insights
- [Team Documentation](knowledge/team-docs.md) - Managing team knowledge and documentation
- [Learning Notes](knowledge/learning-notes.md) - Organizing learning materials and progress

### System Migration
- [Obsidian to Jekyll](migration/obsidian-to-jekyll.md) - Migrating from Obsidian to Jekyll
- [Multi-System Analysis](migration/multi-system.md) - Analyzing content across different systems
- [Link Validation](migration/link-validation.md) - Finding and fixing broken links

### Analytics and Reporting
- [Writing Analytics](analytics/writing-analytics.md) - Analyzing writing patterns and productivity
- [Content Metrics](analytics/content-metrics.md) - Measuring content performance and engagement
- [Knowledge Graphs](analytics/knowledge-graphs.md) - Visualizing connections between notes

## Quick Examples

### Find Recent Research Notes
```sql
SELECT f.filename, f.modified_date, GROUP_CONCAT(t.tag) as tags
FROM files f
LEFT JOIN tags t ON f.id = t.file_id
WHERE f.modified_date > date('now', '-30 days')
  AND (t.tag LIKE '%research%' OR f.filename LIKE '%research%')
GROUP BY f.id
ORDER BY f.modified_date DESC;
```

### Analyze Tag Usage
```sql
SELECT tag, COUNT(*) as usage_count,
       COUNT(DISTINCT f.directory) as directories
FROM tags t
JOIN files f ON t.file_id = f.id
GROUP BY tag
HAVING usage_count > 5
ORDER BY usage_count DESC;
```

### Find Content Gaps
```sql
SELECT t.tag as topic,
       COUNT(*) as existing_content,
       MAX(f.modified_date) as last_updated,
       julianday('now') - julianday(MAX(f.modified_date)) as days_since_update
FROM tags t
JOIN files f ON t.file_id = f.id
GROUP BY t.tag
HAVING existing_content > 3 AND days_since_update > 90
ORDER BY existing_content DESC;
```

### Export Bibliography
```sql
SELECT DISTINCT
    l.link_target as source,
    COUNT(*) as citations,
    GROUP_CONCAT(DISTINCT f.filename) as citing_files
FROM files f
JOIN links l ON f.id = l.file_id
WHERE l.is_internal = 0
  AND (l.link_target LIKE '%.pdf'
       OR l.link_target LIKE '%doi.org%'
       OR l.link_target LIKE '%arxiv.org%')
GROUP BY l.link_target
ORDER BY citations DESC;
```

## Getting Started

1. Choose an example that matches your use case
2. Adapt the queries to your specific directory structure and tagging system
3. Start with simple queries and gradually add complexity
4. Save useful queries as scripts for repeated use

## Contributing Examples

Have a useful mdquery workflow? We'd love to include it! Examples should:

- Solve a real-world problem
- Include clear explanations and context
- Provide sample queries with expected output
- Work with common markdown formats and structures

See the individual example files for detailed walkthroughs and explanations.