# Blog Management Workflow

This example demonstrates how to use mdquery to manage a technical blog, track content performance, and optimize your editorial workflow.

## Scenario

You maintain a technical blog with multiple content types:
- Tutorial posts
- Opinion pieces
- Product reviews
- Technical deep-dives

You need to:
- Track content performance and SEO metrics
- Manage editorial calendar and deadlines
- Find content gaps and opportunities
- Optimize internal linking structure

## Blog Structure

```
blog/
├── posts/
│   ├── 2024-01-15-getting-started-with-python.md
│   ├── 2024-02-03-machine-learning-basics.md
│   └── 2024-03-10-advanced-sql-techniques.md
├── drafts/
│   ├── upcoming-ai-trends.md
│   └── database-optimization-guide.md
└── ideas/
    ├── content-ideas.md
    └── reader-requests.md
```

## Frontmatter Structure

Each blog post includes comprehensive metadata:

```yaml
---
title: "Getting Started with Python for Data Science"
slug: "python-data-science-beginners"
date: 2024-01-15
author: "Jane Doe"
category: "tutorial"
tags: [python, data-science, beginners, tutorial]
status: "published"
seo_title: "Python for Data Science: Complete Beginner's Guide 2024"
meta_description: "Learn Python for data science from scratch. Complete tutorial with examples, exercises, and real-world projects."
word_count: 2500
reading_time: 12
featured_image: "/images/python-data-science.jpg"
social_shares: 245
page_views: 1850
comments: 23
last_updated: 2024-01-20
---
```

## Key Queries

### 1. Content Performance Dashboard

```sql
SELECT
    f.title,
    fm_date.value as publish_date,
    fm_category.value as category,
    CAST(fm_views.value AS INTEGER) as page_views,
    CAST(fm_shares.value AS INTEGER) as social_shares,
    CAST(fm_comments.value AS INTEGER) as comments,
    CAST(fm_reading_time.value AS INTEGER) as reading_time
FROM files f
JOIN frontmatter fm_date ON f.id = fm_date.file_id AND fm_date.key = 'date'
LEFT JOIN frontmatter fm_category ON f.id = fm_category.file_id AND fm_category.key = 'category'
LEFT JOIN frontmatter fm_views ON f.id = fm_views.file_id AND fm_views.key = 'page_views'
LEFT JOIN frontmatter fm_shares ON f.id = fm_shares.file_id AND fm_shares.key = 'social_shares'
LEFT JOIN frontmatter fm_comments ON f.id = fm_comments.file_id AND fm_comments.key = 'comments'
LEFT JOIN frontmatter fm_reading_time ON f.id = fm_reading_time.file_id AND fm_reading_time.key = 'reading_time'
WHERE f.directory LIKE '%posts%'
  AND fm_date.value >= '2024-01-01'
ORDER BY CAST(fm_views.value AS INTEGER) DESC;
```

### 2. Editorial Calendar Overview

```sql
SELECT
    DATE(fm_date.value) as publish_date,
    f.title,
    fm_status.value as status,
    fm_category.value as category,
    CAST(fm_word_count.value AS INTEGER) as word_count,
    CASE
        WHEN fm_status.value = 'draft' THEN 'In Progress'
        WHEN fm_status.value = 'review' THEN 'Ready for Review'
        WHEN fm_status.value = 'scheduled' THEN 'Scheduled'
        WHEN fm_status.value = 'published' THEN 'Live'
        ELSE 'Unknown'
    END as workflow_status
FROM files f
JOIN frontmatter fm_date ON f.id = fm_date.file_id AND fm_date.key = 'date'
LEFT JOIN frontmatter fm_status ON f.id = fm_status.file_id AND fm_status.key = 'status'
LEFT JOIN frontmatter fm_category ON f.id = fm_category.file_id AND fm_category.key = 'category'
LEFT JOIN frontmatter fm_word_count ON f.id = fm_word_count.file_id AND fm_word_count.key = 'word_count'
WHERE DATE(fm_date.value) BETWEEN date('now') AND date('now', '+30 days')
ORDER BY DATE(fm_date.value);
```

### 3. Content Gap Analysis

```sql
-- Find underrepresented categories
SELECT
    fm_category.value as category,
    COUNT(*) as post_count,
    AVG(CAST(fm_views.value AS INTEGER)) as avg_views,
    MAX(DATE(fm_date.value)) as last_post_date,
    julianday('now') - julianday(MAX(DATE(fm_date.value))) as days_since_last_post
FROM files f
JOIN frontmatter fm_category ON f.id = fm_category.file_id AND fm_category.key = 'category'
LEFT JOIN frontmatter fm_views ON f.id = fm_views.file_id AND fm_views.key = 'page_views'
LEFT JOIN frontmatter fm_date ON f.id = fm_date.file_id AND fm_date.key = 'date'
WHERE f.directory LIKE '%posts%'
GROUP BY fm_category.value
ORDER BY days_since_last_post DESC;
```

### 4. SEO Performance Analysis

```sql
SELECT
    f.title,
    fm_seo_title.value as seo_title,
    LENGTH(fm_meta_desc.value) as meta_desc_length,
    CAST(fm_word_count.value AS INTEGER) as word_count,
    CAST(fm_views.value AS INTEGER) as page_views,
    CASE
        WHEN LENGTH(fm_meta_desc.value) BETWEEN 150 AND 160 THEN 'Optimal'
        WHEN LENGTH(fm_meta_desc.value) < 150 THEN 'Too Short'
        WHEN LENGTH(fm_meta_desc.value) > 160 THEN 'Too Long'
        ELSE 'Missing'
    END as meta_desc_status,
    CASE
        WHEN CAST(fm_word_count.value AS INTEGER) >= 1000 THEN 'Good Length'
        WHEN CAST(fm_word_count.value AS INTEGER) >= 500 THEN 'Moderate Length'
        ELSE 'Too Short'
    END as content_length_status
FROM files f
LEFT JOIN frontmatter fm_seo_title ON f.id = fm_seo_title.file_id AND fm_seo_title.key = 'seo_title'
LEFT JOIN frontmatter fm_meta_desc ON f.id = fm_meta_desc.file_id AND fm_meta_desc.key = 'meta_description'
LEFT JOIN frontmatter fm_word_count ON f.id = fm_word_count.file_id AND fm_word_count.key = 'word_count'
LEFT JOIN frontmatter fm_views ON f.id = fm_views.file_id AND fm_views.key = 'page_views'
WHERE f.directory LIKE '%posts%'
ORDER BY CAST(fm_views.value AS INTEGER) DESC;
```

### 5. Internal Linking Opportunities

```sql
-- Find posts with few internal links
SELECT
    f.title,
    fm_category.value as category,
    COUNT(l.id) as internal_links,
    CAST(fm_views.value AS INTEGER) as page_views
FROM files f
LEFT JOIN frontmatter fm_category ON f.id = fm_category.file_id AND fm_category.key = 'category'
LEFT JOIN frontmatter fm_views ON f.id = fm_views.file_id AND fm_views.key = 'page_views'
LEFT JOIN links l ON f.id = l.source_file_id AND l.is_external = 0
WHERE f.directory LIKE '%posts%'
GROUP BY f.id
HAVING internal_links < 3
ORDER BY CAST(fm_views.value AS INTEGER) DESC;
```

### 6. Content Performance by Category

```sql
SELECT
    fm_category.value as category,
    COUNT(*) as post_count,
    AVG(CAST(fm_views.value AS INTEGER)) as avg_page_views,
    AVG(CAST(fm_shares.value AS INTEGER)) as avg_social_shares,
    AVG(CAST(fm_comments.value AS INTEGER)) as avg_comments,
    AVG(CAST(fm_reading_time.value AS INTEGER)) as avg_reading_time,
    SUM(CAST(fm_views.value AS INTEGER)) as total_views
FROM files f
JOIN frontmatter fm_category ON f.id = fm_category.file_id AND fm_category.key = 'category'
LEFT JOIN frontmatter fm_views ON f.id = fm_views.file_id AND fm_views.key = 'page_views'
LEFT JOIN frontmatter fm_shares ON f.id = fm_shares.file_id AND fm_shares.key = 'social_shares'
LEFT JOIN frontmatter fm_comments ON f.id = fm_comments.file_id AND fm_comments.key = 'comments'
LEFT JOIN frontmatter fm_reading_time ON f.id = fm_reading_time.file_id AND fm_reading_time.key = 'reading_time'
WHERE f.directory LIKE '%posts%'
GROUP BY fm_category.value
ORDER BY avg_page_views DESC;
```

## Advanced Analysis

### Content Freshness Audit

```sql
-- Identify content that needs updating
SELECT
    f.title,
    fm_date.value as publish_date,
    fm_updated.value as last_updated,
    fm_category.value as category,
    CAST(fm_views.value AS INTEGER) as page_views,
    julianday('now') - julianday(COALESCE(fm_updated.value, fm_date.value)) as days_since_update,
    CASE
        WHEN julianday('now') - julianday(COALESCE(fm_updated.value, fm_date.value)) > 365 THEN 'Needs Update'
        WHEN julianday('now') - julianday(COALESCE(fm_updated.value, fm_date.value)) > 180 THEN 'Consider Update'
        ELSE 'Fresh'
    END as freshness_status
FROM files f
JOIN frontmatter fm_date ON f.id = fm_date.file_id AND fm_date.key = 'date'
LEFT JOIN frontmatter fm_updated ON f.id = fm_updated.file_id AND fm_updated.key = 'last_updated'
LEFT JOIN frontmatter fm_category ON f.id = fm_category.file_id AND fm_category.key = 'category'
LEFT JOIN frontmatter fm_views ON f.id = fm_views.file_id AND fm_views.key = 'page_views'
WHERE f.directory LIKE '%posts%'
  AND CAST(fm_views.value AS INTEGER) > 500  -- Focus on popular content
ORDER BY days_since_update DESC;
```

### Seasonal Content Planning

```sql
-- Analyze posting patterns by month
SELECT
    strftime('%m', fm_date.value) as month,
    strftime('%Y', fm_date.value) as year,
    COUNT(*) as posts_published,
    AVG(CAST(fm_views.value AS INTEGER)) as avg_views,
    GROUP_CONCAT(DISTINCT fm_category.value) as categories_covered
FROM files f
JOIN frontmatter fm_date ON f.id = fm_date.file_id AND fm_date.key = 'date'
LEFT JOIN frontmatter fm_views ON f.id = fm_views.file_id AND fm_views.key = 'page_views'
LEFT JOIN frontmatter fm_category ON f.id = fm_category.file_id AND fm_category.key = 'category'
WHERE f.directory LIKE '%posts%'
  AND fm_date.value >= '2023-01-01'
GROUP BY strftime('%Y-%m', fm_date.value)
ORDER BY year, month;
```

### Reader Engagement Analysis

```sql
-- Identify high-engagement content patterns
SELECT
    fm_category.value as category,
    CAST(fm_reading_time.value AS INTEGER) as reading_time_bucket,
    COUNT(*) as post_count,
    AVG(CAST(fm_comments.value AS INTEGER)) as avg_comments,
    AVG(CAST(fm_shares.value AS INTEGER)) as avg_shares,
    AVG(CAST(fm_views.value AS INTEGER)) as avg_views
FROM files f
JOIN frontmatter fm_category ON f.id = fm_category.file_id AND fm_category.key = 'category'
LEFT JOIN frontmatter fm_reading_time ON f.id = fm_reading_time.file_id AND fm_reading_time.key = 'reading_time'
LEFT JOIN frontmatter fm_comments ON f.id = fm_comments.file_id AND fm_comments.key = 'comments'
LEFT JOIN frontmatter fm_shares ON f.id = fm_shares.file_id AND fm_shares.key = 'social_shares'
LEFT JOIN frontmatter fm_views ON f.id = fm_views.file_id AND fm_views.key = 'page_views'
WHERE f.directory LIKE '%posts%'
GROUP BY fm_category.value,
         CASE
             WHEN CAST(fm_reading_time.value AS INTEGER) <= 5 THEN '0-5 min'
             WHEN CAST(fm_reading_time.value AS INTEGER) <= 10 THEN '6-10 min'
             WHEN CAST(fm_reading_time.value AS INTEGER) <= 15 THEN '11-15 min'
             ELSE '15+ min'
         END
ORDER BY avg_comments DESC;
```

## Workflow Automation

### Weekly Content Review

```sql
-- Weekly performance summary
SELECT
    'This Week' as period,
    COUNT(*) as posts_published,
    SUM(CAST(fm_views.value AS INTEGER)) as total_views,
    AVG(CAST(fm_shares.value AS INTEGER)) as avg_shares,
    AVG(CAST(fm_comments.value AS INTEGER)) as avg_comments
FROM files f
JOIN frontmatter fm_date ON f.id = fm_date.file_id AND fm_date.key = 'date'
LEFT JOIN frontmatter fm_views ON f.id = fm_views.file_id AND fm_views.key = 'page_views'
LEFT JOIN frontmatter fm_shares ON f.id = fm_shares.file_id AND fm_shares.key = 'social_shares'
LEFT JOIN frontmatter fm_comments ON f.id = fm_comments.file_id AND fm_comments.key = 'comments'
WHERE f.directory LIKE '%posts%'
  AND DATE(fm_date.value) >= date('now', '-7 days')

UNION ALL

SELECT
    'Last Week' as period,
    COUNT(*) as posts_published,
    SUM(CAST(fm_views.value AS INTEGER)) as total_views,
    AVG(CAST(fm_shares.value AS INTEGER)) as avg_shares,
    AVG(CAST(fm_comments.value AS INTEGER)) as avg_comments
FROM files f
JOIN frontmatter fm_date ON f.id = fm_date.file_id AND fm_date.key = 'date'
LEFT JOIN frontmatter fm_views ON f.id = fm_views.file_id AND fm_views.key = 'page_views'
LEFT JOIN frontmatter fm_shares ON f.id = fm_shares.file_id AND fm_shares.key = 'social_shares'
LEFT JOIN frontmatter fm_comments ON f.id = fm_comments.file_id AND fm_comments.key = 'comments'
WHERE f.directory LIKE '%posts%'
  AND DATE(fm_date.value) BETWEEN date('now', '-14 days') AND date('now', '-7 days');
```

### Content Ideas Generation

```sql
-- Find successful content patterns for replication
SELECT
    t.tag as topic,
    COUNT(*) as post_count,
    AVG(CAST(fm_views.value AS INTEGER)) as avg_views,
    AVG(CAST(fm_shares.value AS INTEGER)) as avg_shares,
    MAX(DATE(fm_date.value)) as last_post_date,
    julianday('now') - julianday(MAX(DATE(fm_date.value))) as days_since_last_post
FROM files f
JOIN tags t ON f.id = t.file_id
JOIN frontmatter fm_date ON f.id = fm_date.file_id AND fm_date.key = 'date'
LEFT JOIN frontmatter fm_views ON f.id = fm_views.file_id AND fm_views.key = 'page_views'
LEFT JOIN frontmatter fm_shares ON f.id = fm_shares.file_id AND fm_shares.key = 'social_shares'
WHERE f.directory LIKE '%posts%'
GROUP BY t.tag
HAVING post_count >= 2
   AND avg_views > 1000
   AND days_since_last_post > 90
ORDER BY avg_views DESC, days_since_last_post DESC;
```

## Best Practices

### Content Organization
- Use consistent frontmatter across all posts
- Include comprehensive SEO metadata
- Track performance metrics regularly
- Maintain clear category taxonomy

### Editorial Workflow
- Regular content audits (monthly)
- Performance reviews (weekly)
- Content freshness checks (quarterly)
- SEO optimization reviews (bi-weekly)

### Analytics Integration
- Update performance metrics monthly
- Track social media engagement
- Monitor comment activity
- Analyze search traffic patterns

This blog management workflow helps maintain a data-driven approach to content creation, ensuring consistent quality and performance optimization across your technical blog.