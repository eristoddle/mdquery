# Personal Knowledge Base Management

This example demonstrates how to use mdquery to organize and maintain a personal knowledge base, track learning progress, and discover connections between ideas.

## Scenario

You maintain a personal knowledge base covering multiple domains:
- Technical learning (programming, tools, frameworks)
- Professional development (career, skills, industry trends)
- Personal interests (hobbies, books, ideas)
- Project documentation (side projects, experiments)

Goals:
- Track learning progress and knowledge gaps
- Discover connections between different domains
- Maintain and update outdated information
- Generate insights from accumulated knowledge

## Knowledge Base Structure

```
knowledge-base/
├── technical/
│   ├── programming/
│   │   ├── python-advanced-concepts.md
│   │   └── javascript-frameworks-comparison.md
│   ├── tools/
│   │   ├── git-advanced-workflows.md
│   │   └── docker-best-practices.md
│   └── architecture/
│       ├── microservices-patterns.md
│       └── database-design-principles.md
├── professional/
│   ├── career/
│   │   ├── leadership-principles.md
│   │   └── technical-interview-prep.md
│   ├── industry/
│   │   ├── ai-trends-2024.md
│   │   └── remote-work-best-practices.md
│   └── skills/
│       ├── communication-techniques.md
│       └── project-management-methods.md
├── personal/
│   ├── books/
│   │   ├── atomic-habits-notes.md
│   │   └── thinking-fast-and-slow-summary.md
│   ├── ideas/
│   │   ├── startup-idea-validation.md
│   │   └── productivity-system-design.md
│   └── reflections/
│       ├── 2024-q1-review.md
│       └── learning-from-failures.md
└── projects/
    ├── personal-website-rebuild.md
    ├── home-automation-system.md
    └── data-analysis-toolkit.md
```

## Note Structure

Each knowledge base entry includes structured metadata:

```yaml
---
title: "Advanced Python Concepts: Decorators and Metaclasses"
created: 2024-01-15
updated: 2024-03-10
category: technical
subcategory: programming
tags: [python, decorators, metaclasses, advanced, programming]
status: active
confidence: 8
source: ["Python Tricks book", "Real Python tutorials", "personal experimentation"]
related_projects: ["data-analysis-toolkit", "web-scraper-framework"]
learning_stage: intermediate
review_date: 2024-06-10
---
```

## Key Queries

### 1. Learning Progress Dashboard

```sql
SELECT
    fm_category.value as domain,
    COUNT(*) as total_notes,
    AVG(CAST(fm_confidence.value AS INTEGER)) as avg_confidence,
    COUNT(CASE WHEN fm_status.value = 'active' THEN 1 END) as active_notes,
    COUNT(CASE WHEN fm_status.value = 'archived' THEN 1 END) as archived_notes,
    MAX(DATE(fm_updated.value)) as last_updated
FROM files f
LEFT JOIN frontmatter fm_category ON f.id = fm_category.file_id AND fm_category.key = 'category'
LEFT JOIN frontmatter fm_confidence ON f.id = fm_confidence.file_id AND fm_confidence.key = 'confidence'
LEFT JOIN frontmatter fm_status ON f.id = fm_status.file_id AND fm_status.key = 'status'
LEFT JOIN frontmatter fm_updated ON f.id = fm_updated.file_id AND fm_updated.key = 'updated'
WHERE f.directory LIKE '%knowledge-base%'
GROUP BY fm_category.value
ORDER BY avg_confidence DESC;
```

### 2. Knowledge Gaps Analysis

```sql
-- Find areas with low confidence scores
SELECT
    f.title,
    fm_category.value as category,
    fm_subcategory.value as subcategory,
    CAST(fm_confidence.value AS INTEGER) as confidence,
    fm_learning_stage.value as learning_stage,
    DATE(fm_updated.value) as last_updated,
    julianday('now') - julianday(DATE(fm_updated.value)) as days_since_update
FROM files f
LEFT JOIN frontmatter fm_category ON f.id = fm_category.file_id AND fm_category.key = 'category'
LEFT JOIN frontmatter fm_subcategory ON f.id = fm_subcategory.file_id AND fm_subcategory.key = 'subcategory'
LEFT JOIN frontmatter fm_confidence ON f.id = fm_confidence.file_id AND fm_confidence.key = 'confidence'
LEFT JOIN frontmatter fm_learning_stage ON f.id = fm_learning_stage.file_id AND fm_learning_stage.key = 'learning_stage'
LEFT JOIN frontmatter fm_updated ON f.id = fm_updated.file_id AND fm_updated.key = 'updated'
WHERE f.directory LIKE '%knowledge-base%'
  AND CAST(fm_confidence.value AS INTEGER) <= 5
ORDER BY CAST(fm_confidence.value AS INTEGER), days_since_update DESC;
```

### 3. Review Schedule

```sql
-- Notes that need review based on review_date
SELECT
    f.title,
    fm_category.value as category,
    DATE(fm_review_date.value) as review_date,
    CAST(fm_confidence.value AS INTEGER) as confidence,
    fm_status.value as status,
    CASE
        WHEN DATE(fm_review_date.value) < date('now') THEN 'Overdue'
        WHEN DATE(fm_review_date.value) <= date('now', '+7 days') THEN 'Due Soon'
        ELSE 'Future'
    END as review_status
FROM files f
LEFT JOIN frontmatter fm_category ON f.id = fm_category.file_id AND fm_category.key = 'category'
LEFT JOIN frontmatter fm_review_date ON f.id = fm_review_date.file_id AND fm_review_date.key = 'review_date'
LEFT JOIN frontmatter fm_confidence ON f.id = fm_confidence.file_id AND fm_confidence.key = 'confidence'
LEFT JOIN frontmatter fm_status ON f.id = fm_status.file_id AND fm_status.key = 'status'
WHERE f.directory LIKE '%knowledge-base%'
  AND fm_review_date.value IS NOT NULL
  AND fm_status.value = 'active'
ORDER BY DATE(fm_review_date.value);
```

### 4. Cross-Domain Connections

```sql
-- Find notes that span multiple categories through tags
SELECT
    t1.tag as shared_tag,
    COUNT(DISTINCT fm_category.value) as categories_spanned,
    GROUP_CONCAT(DISTINCT fm_category.value) as categories,
    COUNT(*) as note_count,
    GROUP_CONCAT(f.title, '; ') as related_notes
FROM files f
JOIN tags t1 ON f.id = t1.file_id
LEFT JOIN frontmatter fm_category ON f.id = fm_category.file_id AND fm_category.key = 'category'
WHERE f.directory LIKE '%knowledge-base%'
GROUP BY t1.tag
HAVING categories_spanned > 1 AND note_count >= 3
ORDER BY categories_spanned DESC, note_count DESC;
```

### 5. Learning Trajectory Analysis

```sql
-- Track learning progression over time
SELECT
    strftime('%Y-%m', fm_created.value) as month,
    fm_category.value as category,
    COUNT(*) as notes_created,
    AVG(CAST(fm_confidence.value AS INTEGER)) as avg_initial_confidence,
    COUNT(CASE WHEN fm_learning_stage.value = 'beginner' THEN 1 END) as beginner_topics,
    COUNT(CASE WHEN fm_learning_stage.value = 'intermediate' THEN 1 END) as intermediate_topics,
    COUNT(CASE WHEN fm_learning_stage.value = 'advanced' THEN 1 END) as advanced_topics
FROM files f
LEFT JOIN frontmatter fm_created ON f.id = fm_created.file_id AND fm_created.key = 'created'
LEFT JOIN frontmatter fm_category ON f.id = fm_category.file_id AND fm_category.key = 'category'
LEFT JOIN frontmatter fm_confidence ON f.id = fm_confidence.file_id AND fm_confidence.key = 'confidence'
LEFT JOIN frontmatter fm_learning_stage ON f.id = fm_learning_stage.file_id AND fm_learning_stage.key = 'learning_stage'
WHERE f.directory LIKE '%knowledge-base%'
  AND fm_created.value >= '2023-01-01'
GROUP BY strftime('%Y-%m', fm_created.value), fm_category.value
ORDER BY month, fm_category.value;
```

### 6. Project-Knowledge Connections

```sql
-- Find knowledge notes related to specific projects
SELECT
    fm_projects.value as project,
    COUNT(*) as related_knowledge_notes,
    GROUP_CONCAT(DISTINCT fm_category.value) as knowledge_domains,
    AVG(CAST(fm_confidence.value AS INTEGER)) as avg_confidence,
    GROUP_CONCAT(f.title, '; ') as related_notes
FROM files f
JOIN frontmatter fm_projects ON f.id = fm_projects.file_id AND fm_projects.key = 'related_projects'
LEFT JOIN frontmatter fm_category ON f.id = fm_category.file_id AND fm_category.key = 'category'
LEFT JOIN frontmatter fm_confidence ON f.id = fm_confidence.file_id AND fm_confidence.key = 'confidence'
WHERE f.directory LIKE '%knowledge-base%'
GROUP BY fm_projects.value
ORDER BY related_knowledge_notes DESC;
```

## Advanced Analysis

### Knowledge Network Visualization

```sql
-- Create network data for knowledge connections
SELECT
    f1.title as source_note,
    f2.title as target_note,
    l.link_text as connection_context,
    fm1_category.value as source_category,
    fm2_category.value as target_category,
    CASE
        WHEN fm1_category.value = fm2_category.value THEN 'intra-domain'
        ELSE 'cross-domain'
    END as connection_type
FROM links l
JOIN files f1 ON l.source_file_id = f1.id
JOIN files f2 ON l.target_file_id = f2.id
LEFT JOIN frontmatter fm1_category ON f1.id = fm1_category.file_id AND fm1_category.key = 'category'
LEFT JOIN frontmatter fm2_category ON f2.id = fm2_category.file_id AND fm2_category.key = 'category'
WHERE f1.directory LIKE '%knowledge-base%'
  AND f2.directory LIKE '%knowledge-base%'
ORDER BY connection_type, fm1_category.value;
```

### Learning Efficiency Analysis

```sql
-- Analyze learning efficiency by source type
SELECT
    fm_source.value as learning_source,
    COUNT(*) as notes_count,
    AVG(CAST(fm_confidence.value AS INTEGER)) as avg_confidence,
    AVG(f.word_count) as avg_note_length,
    COUNT(CASE WHEN fm_learning_stage.value = 'advanced' THEN 1 END) as advanced_topics,
    AVG(julianday(fm_updated.value) - julianday(fm_created.value)) as avg_development_days
FROM files f
JOIN frontmatter fm_source ON f.id = fm_source.file_id AND fm_source.key = 'source'
LEFT JOIN frontmatter fm_confidence ON f.id = fm_confidence.file_id AND fm_confidence.key = 'confidence'
LEFT JOIN frontmatter fm_learning_stage ON f.id = fm_learning_stage.file_id AND fm_learning_stage.key = 'learning_stage'
LEFT JOIN frontmatter fm_created ON f.id = fm_created.file_id AND fm_created.key = 'created'
LEFT JOIN frontmatter fm_updated ON f.id = fm_updated.file_id AND fm_updated.key = 'updated'
WHERE f.directory LIKE '%knowledge-base%'
GROUP BY fm_source.value
HAVING notes_count >= 5
ORDER BY avg_confidence DESC;
```

### Knowledge Decay Detection

```sql
-- Identify knowledge that might be getting stale
SELECT
    f.title,
    fm_category.value as category,
    CAST(fm_confidence.value AS INTEGER) as confidence,
    DATE(fm_created.value) as created_date,
    DATE(fm_updated.value) as last_updated,
    julianday('now') - julianday(DATE(fm_updated.value)) as days_stale,
    CASE
        WHEN julianday('now') - julianday(DATE(fm_updated.value)) > 365 THEN 'Very Stale'
        WHEN julianday('now') - julianday(DATE(fm_updated.value)) > 180 THEN 'Stale'
        WHEN julianday('now') - julianday(DATE(fm_updated.value)) > 90 THEN 'Getting Old'
        ELSE 'Fresh'
    END as staleness_level
FROM files f
LEFT JOIN frontmatter fm_category ON f.id = fm_category.file_id AND fm_category.key = 'category'
LEFT JOIN frontmatter fm_confidence ON f.id = fm_confidence.file_id AND fm_confidence.key = 'confidence'
LEFT JOIN frontmatter fm_created ON f.id = fm_created.file_id AND fm_created.key = 'created'
LEFT JOIN frontmatter fm_updated ON f.id = fm_updated.file_id AND fm_updated.key = 'updated'
WHERE f.directory LIKE '%knowledge-base%'
  AND CAST(fm_confidence.value AS INTEGER) >= 7  -- Focus on high-confidence knowledge
ORDER BY days_stale DESC;
```

## Maintenance Workflows

### Weekly Review Process

```sql
-- Weekly knowledge base health check
SELECT
    'Total Active Notes' as metric,
    COUNT(*) as value
FROM files f
JOIN frontmatter fm_status ON f.id = fm_status.file_id AND fm_status.key = 'status'
WHERE f.directory LIKE '%knowledge-base%' AND fm_status.value = 'active'

UNION ALL

SELECT
    'Notes Needing Review' as metric,
    COUNT(*) as value
FROM files f
JOIN frontmatter fm_review_date ON f.id = fm_review_date.file_id AND fm_review_date.key = 'review_date'
WHERE f.directory LIKE '%knowledge-base%'
  AND DATE(fm_review_date.value) <= date('now', '+7 days')

UNION ALL

SELECT
    'Low Confidence Notes' as metric,
    COUNT(*) as value
FROM files f
JOIN frontmatter fm_confidence ON f.id = fm_confidence.file_id AND fm_confidence.key = 'confidence'
WHERE f.directory LIKE '%knowledge-base%'
  AND CAST(fm_confidence.value AS INTEGER) <= 4

UNION ALL

SELECT
    'Stale Notes (>6 months)' as metric,
    COUNT(*) as value
FROM files f
JOIN frontmatter fm_updated ON f.id = fm_updated.file_id AND fm_updated.key = 'updated'
WHERE f.directory LIKE '%knowledge-base%'
  AND julianday('now') - julianday(DATE(fm_updated.value)) > 180;
```

### Monthly Learning Report

```sql
-- Generate monthly learning progress report
SELECT
    fm_category.value as domain,
    COUNT(*) as total_notes,
    COUNT(CASE WHEN DATE(fm_updated.value) >= date('now', 'start of month') THEN 1 END) as updated_this_month,
    COUNT(CASE WHEN DATE(fm_created.value) >= date('now', 'start of month') THEN 1 END) as created_this_month,
    AVG(CAST(fm_confidence.value AS INTEGER)) as avg_confidence,
    COUNT(CASE WHEN CAST(fm_confidence.value AS INTEGER) >= 8 THEN 1 END) as high_confidence_notes,
    COUNT(CASE WHEN fm_learning_stage.value = 'advanced' THEN 1 END) as advanced_level_notes
FROM files f
LEFT JOIN frontmatter fm_category ON f.id = fm_category.file_id AND fm_category.key = 'category'
LEFT JOIN frontmatter fm_confidence ON f.id = fm_confidence.file_id AND fm_confidence.key = 'confidence'
LEFT JOIN frontmatter fm_learning_stage ON f.id = fm_learning_stage.file_id AND fm_learning_stage.key = 'learning_stage'
LEFT JOIN frontmatter fm_created ON f.id = fm_created.file_id AND fm_created.key = 'created'
LEFT JOIN frontmatter fm_updated ON f.id = fm_updated.file_id AND fm_updated.key = 'updated'
WHERE f.directory LIKE '%knowledge-base%'
GROUP BY fm_category.value
ORDER BY avg_confidence DESC;
```

## Best Practices

### Note Organization
- Use consistent metadata across all knowledge notes
- Include confidence levels to track understanding
- Set review dates for spaced repetition
- Link related concepts across domains

### Learning Tracking
- Regular confidence level updates
- Document learning sources for reference
- Track practical applications in projects
- Review and update stale knowledge

### Knowledge Maintenance
- Weekly review of due items
- Monthly progress assessment
- Quarterly knowledge audit
- Annual archive of outdated information

### Connection Building
- Actively link related concepts
- Create index notes for major topics
- Use tags to enable cross-domain discovery
- Document insights and connections

This personal knowledge base management system helps maintain organized, up-to-date, and interconnected knowledge that supports continuous learning and professional development.