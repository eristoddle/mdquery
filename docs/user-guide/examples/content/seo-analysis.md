# SEO Analysis and Optimization

This example demonstrates how to use mdquery to analyze and optimize your content for search engines, track SEO metrics, and identify improvement opportunities.

## SEO Data Structure

```yaml
---
title: "Complete Guide to Python Data Analysis"
seo_title: "Python Data Analysis Tutorial: Complete Guide 2024"
meta_description: "Learn Python data analysis from scratch. Complete tutorial with pandas, numpy, matplotlib examples and real-world projects."
slug: "python-data-analysis-guide"
canonical_url: "https://example.com/python-data-analysis-guide"
date: 2024-01-15
updated: 2024-03-10
word_count: 2850
reading_time: 14
target_keywords: ["python data analysis", "pandas tutorial", "data science python"]
secondary_keywords: ["numpy", "matplotlib", "data visualization", "python beginners"]
content_type: "tutorial"
category: "programming"
tags: [python, data-analysis, pandas, tutorial]
featured_image: "/images/python-data-analysis.jpg"
featured_image_alt: "Python data analysis code on laptop screen"
internal_links: 5
external_links: 8
headings_count: 12
h1_count: 1
h2_count: 6
h3_count: 5
images_count: 8
images_with_alt: 7
code_blocks: 15
seo_score: 85
page_views: 2450
organic_traffic: 1890
bounce_rate: 0.35
time_on_page: 420
social_shares: 67
backlinks: 12
---
```

## SEO Analysis Queries

### 1. Content SEO Health Dashboard

```sql
SELECT
    COUNT(*) as total_posts,
    AVG(CAST(fm_seo_score.value AS INTEGER)) as avg_seo_score,
    COUNT(CASE WHEN CAST(fm_seo_score.value AS INTEGER) >= 80 THEN 1 END) as high_seo_posts,
    COUNT(CASE WHEN fm_meta_desc.value IS NULL OR LENGTH(fm_meta_desc.value) = 0 THEN 1 END) as missing_meta_desc,
    COUNT(CASE WHEN CAST(fm_h1_count.value AS INTEGER) != 1 THEN 1 END) as h1_issues,
    COUNT(CASE WHEN CAST(fm_word_count.value AS INTEGER) < 300 THEN 1 END) as thin_content,
    AVG(CAST(fm_word_count.value AS INTEGER)) as avg_word_count
FROM files f
LEFT JOIN frontmatter fm_seo_score ON f.id = fm_seo_score.file_id AND fm_seo_score.key = 'seo_score'
LEFT JOIN frontmatter fm_meta_desc ON f.id = fm_meta_desc.file_id AND fm_meta_desc.key = 'meta_description'
LEFT JOIN frontmatter fm_h1_count ON f.id = fm_h1_count.file_id AND fm_h1_count.key = 'h1_count'
LEFT JOIN frontmatter fm_word_count ON f.id = fm_word_count.file_id AND fm_word_count.key = 'word_count'
WHERE f.directory LIKE '%blog%' OR f.directory LIKE '%content%';
```

### 2. Meta Description Analysis

```sql
SELECT
    f.title,
    fm_meta_desc.value as meta_description,
    LENGTH(fm_meta_desc.value) as meta_desc_length,
    CASE
        WHEN fm_meta_desc.value IS NULL THEN 'Missing'
        WHEN LENGTH(fm_meta_desc.value) < 120 THEN 'Too Short'
        WHEN LENGTH(fm_meta_desc.value) > 160 THEN 'Too Long'
        ELSE 'Optimal'
    END as meta_desc_status,
    CAST(fm_page_views.value AS INTEGER) as page_views,
    CAST(fm_organic_traffic.value AS INTEGER) as organic_traffic
FROM files f
LEFT JOIN frontmatter fm_meta_desc ON f.id = fm_meta_desc.file_id AND fm_meta_desc.key = 'meta_description'
LEFT JOIN frontmatter fm_page_views ON f.id = fm_page_views.file_id AND fm_page_views.key = 'page_views'
LEFT JOIN frontmatter fm_organic_traffic ON f.id = fm_organic_traffic.file_id AND fm_organic_traffic.key = 'organic_traffic'
WHERE f.directory LIKE '%blog%' OR f.directory LIKE '%content%'
ORDER BY
    CASE meta_desc_status
        WHEN 'Missing' THEN 1
        WHEN 'Too Short' THEN 2
        WHEN 'Too Long' THEN 3
        ELSE 4
    END,
    page_views DESC;
```

### 3. Keyword Performance Analysis

```sql
-- Analyze target keyword performance
SELECT
    fm_target_keywords.value as target_keyword,
    COUNT(*) as posts_targeting,
    AVG(CAST(fm_organic_traffic.value AS INTEGER)) as avg_organic_traffic,
    AVG(CAST(fm_seo_score.value AS INTEGER)) as avg_seo_score,
    SUM(CAST(fm_page_views.value AS INTEGER)) as total_page_views,
    GROUP_CONCAT(f.title, '; ') as targeting_posts
FROM files f
JOIN frontmatter fm_target_keywords ON f.id = fm_target_keywords.file_id AND fm_target_keywords.key = 'target_keywords'
LEFT JOIN frontmatter fm_organic_traffic ON f.id = fm_organic_traffic.file_id AND fm_organic_traffic.key = 'organic_traffic'
LEFT JOIN frontmatter fm_seo_score ON f.id = fm_seo_score.file_id AND fm_seo_score.key = 'seo_score'
LEFT JOIN frontmatter fm_page_views ON f.id = fm_page_views.file_id AND fm_page_views.key = 'page_views'
WHERE f.directory LIKE '%blog%' OR f.directory LIKE '%content%'
GROUP BY fm_target_keywords.value
HAVING posts_targeting >= 2
ORDER BY avg_organic_traffic DESC;
```

### 4. Content Structure Analysis

```sql
-- Analyze heading structure and content organization
SELECT
    f.title,
    CAST(fm_word_count.value AS INTEGER) as word_count,
    CAST(fm_h1_count.value AS INTEGER) as h1_count,
    CAST(fm_h2_count.value AS INTEGER) as h2_count,
    CAST(fm_h3_count.value AS INTEGER) as h3_count,
    CAST(fm_headings_count.value AS INTEGER) as total_headings,
    CAST(fm_internal_links.value AS INTEGER) as internal_links,
    CAST(fm_external_links.value AS INTEGER) as external_links,
    CASE
        WHEN CAST(fm_h1_count.value AS INTEGER) != 1 THEN 'H1 Issue'
        WHEN CAST(fm_headings_count.value AS INTEGER) < 3 THEN 'Few Headings'
        WHEN CAST(fm_internal_links.value AS INTEGER) < 3 THEN 'Few Internal Links'
        ELSE 'Good Structure'
    END as structure_status,
    CAST(fm_seo_score.value AS INTEGER) as seo_score
FROM files f
LEFT JOIN frontmatter fm_word_count ON f.id = fm_word_count.file_id AND fm_word_count.key = 'word_count'
LEFT JOIN frontmatter fm_h1_count ON f.id = fm_h1_count.file_id AND fm_h1_count.key = 'h1_count'
LEFT JOIN frontmatter fm_h2_count ON f.id = fm_h2_count.file_id AND fm_h2_count.key = 'h2_count'
LEFT JOIN frontmatter fm_h3_count ON f.id = fm_h3_count.file_id AND fm_h3_count.key = 'h3_count'
LEFT JOIN frontmatter fm_headings_count ON f.id = fm_headings_count.file_id AND fm_headings_count.key = 'headings_count'
LEFT JOIN frontmatter fm_internal_links ON f.id = fm_internal_links.file_id AND fm_internal_links.key = 'internal_links'
LEFT JOIN frontmatter fm_external_links ON f.id = fm_external_links.file_id AND fm_external_links.key = 'external_links'
LEFT JOIN frontmatter fm_seo_score ON f.id = fm_seo_score.file_id AND fm_seo_score.key = 'seo_score'
WHERE f.directory LIKE '%blog%' OR f.directory LIKE '%content%'
ORDER BY structure_status, seo_score DESC;
```

### 5. Image SEO Analysis

```sql
-- Analyze image optimization
SELECT
    f.title,
    CAST(fm_images_count.value AS INTEGER) as total_images,
    CAST(fm_images_with_alt.value AS INTEGER) as images_with_alt,
    CASE
        WHEN CAST(fm_images_count.value AS INTEGER) = 0 THEN 'No Images'
        WHEN CAST(fm_images_with_alt.value AS INTEGER) = CAST(fm_images_count.value AS INTEGER) THEN 'All Alt Text'
        WHEN CAST(fm_images_with_alt.value AS INTEGER) = 0 THEN 'No Alt Text'
        ELSE 'Partial Alt Text'
    END as image_seo_status,
    fm_featured_image.value as featured_image,
    fm_featured_image_alt.value as featured_image_alt,
    CAST(fm_page_views.value AS INTEGER) as page_views
FROM files f
LEFT JOIN frontmatter fm_images_count ON f.id = fm_images_count.file_id AND fm_images_count.key = 'images_count'
LEFT JOIN frontmatter fm_images_with_alt ON f.id = fm_images_with_alt.file_id AND fm_images_with_alt.key = 'images_with_alt'
LEFT JOIN frontmatter fm_featured_image ON f.id = fm_featured_image.file_id AND fm_featured_image.key = 'featured_image'
LEFT JOIN frontmatter fm_featured_image_alt ON f.id = fm_featured_image_alt.file_id AND fm_featured_image_alt.key = 'featured_image_alt'
LEFT JOIN frontmatter fm_page_views ON f.id = fm_page_views.file_id AND fm_page_views.key = 'page_views'
WHERE f.directory LIKE '%blog%' OR f.directory LIKE '%content%'
ORDER BY
    CASE image_seo_status
        WHEN 'No Alt Text' THEN 1
        WHEN 'Partial Alt Text' THEN 2
        WHEN 'No Images' THEN 3
        ELSE 4
    END,
    page_views DESC;
```

### 6. Content Performance Correlation

```sql
-- Correlate SEO factors with performance
SELECT
    CASE
        WHEN CAST(fm_word_count.value AS INTEGER) < 500 THEN '< 500 words'
        WHEN CAST(fm_word_count.value AS INTEGER) < 1000 THEN '500-999 words'
        WHEN CAST(fm_word_count.value AS INTEGER) < 2000 THEN '1000-1999 words'
        ELSE '2000+ words'
    END as word_count_range,
    COUNT(*) as post_count,
    AVG(CAST(fm_organic_traffic.value AS INTEGER)) as avg_organic_traffic,
    AVG(CAST(fm_bounce_rate.value AS FLOAT)) as avg_bounce_rate,
    AVG(CAST(fm_time_on_page.value AS INTEGER)) as avg_time_on_page,
    AVG(CAST(fm_seo_score.value AS INTEGER)) as avg_seo_score
FROM files f
LEFT JOIN frontmatter fm_word_count ON f.id = fm_word_count.file_id AND fm_word_count.key = 'word_count'
LEFT JOIN frontmatter fm_organic_traffic ON f.id = fm_organic_traffic.file_id AND fm_organic_traffic.key = 'organic_traffic'
LEFT JOIN frontmatter fm_bounce_rate ON f.id = fm_bounce_rate.file_id AND fm_bounce_rate.key = 'bounce_rate'
LEFT JOIN frontmatter fm_time_on_page ON f.id = fm_time_on_page.file_id AND fm_time_on_page.key = 'time_on_page'
LEFT JOIN frontmatter fm_seo_score ON f.id = fm_seo_score.file_id AND fm_seo_score.key = 'seo_score'
WHERE f.directory LIKE '%blog%' OR f.directory LIKE '%content%'
  AND fm_word_count.value IS NOT NULL
GROUP BY word_count_range
ORDER BY avg_organic_traffic DESC;
```

## SEO Optimization Workflows

### 1. Priority Optimization List

```sql
-- Identify high-impact optimization opportunities
SELECT
    f.title,
    CAST(fm_page_views.value AS INTEGER) as page_views,
    CAST(fm_seo_score.value AS INTEGER) as current_seo_score,
    100 - CAST(fm_seo_score.value AS INTEGER) as improvement_potential,
    CASE
        WHEN fm_meta_desc.value IS NULL THEN 'Add Meta Description'
        WHEN CAST(fm_h1_count.value AS INTEGER) != 1 THEN 'Fix H1 Structure'
        WHEN CAST(fm_word_count.value AS INTEGER) < 500 THEN 'Expand Content'
        WHEN CAST(fm_internal_links.value AS INTEGER) < 3 THEN 'Add Internal Links'
        WHEN CAST(fm_images_with_alt.value AS INTEGER) < CAST(fm_images_count.value AS INTEGER) THEN 'Add Alt Text'
        ELSE 'Minor Optimizations'
    END as primary_action,
    CAST(fm_page_views.value AS INTEGER) * (100 - CAST(fm_seo_score.value AS INTEGER)) as optimization_priority_score
FROM files f
LEFT JOIN frontmatter fm_page_views ON f.id = fm_page_views.file_id AND fm_page_views.key = 'page_views'
LEFT JOIN frontmatter fm_seo_score ON f.id = fm_seo_score.file_id AND fm_seo_score.key = 'seo_score'
LEFT JOIN frontmatter fm_meta_desc ON f.id = fm_meta_desc.file_id AND fm_meta_desc.key = 'meta_description'
LEFT JOIN frontmatter fm_h1_count ON f.id = fm_h1_count.file_id AND fm_h1_count.key = 'h1_count'
LEFT JOIN frontmatter fm_word_count ON f.id = fm_word_count.file_id AND fm_word_count.key = 'word_count'
LEFT JOIN frontmatter fm_internal_links ON f.id = fm_internal_links.file_id AND fm_internal_links.key = 'internal_links'
LEFT JOIN frontmatter fm_images_count ON f.id = fm_images_count.file_id AND fm_images_count.key = 'images_count'
LEFT JOIN frontmatter fm_images_with_alt ON f.id = fm_images_with_alt.file_id AND fm_images_with_alt.key = 'images_with_alt'
WHERE f.directory LIKE '%blog%' OR f.directory LIKE '%content%'
  AND CAST(fm_seo_score.value AS INTEGER) < 90
ORDER BY optimization_priority_score DESC;
```

### 2. Internal Linking Opportunities

```sql
-- Find internal linking opportunities based on related content
SELECT
    source.title as source_post,
    target.title as target_post,
    COUNT(shared_tags.tag) as shared_topics,
    GROUP_CONCAT(DISTINCT shared_tags.tag) as common_tags,
    CAST(source_traffic.value AS INTEGER) as source_traffic,
    CAST(target_traffic.value AS INTEGER) as target_traffic,
    'Link Opportunity' as recommendation
FROM files source
JOIN tags source_tags ON source.id = source_tags.file_id
JOIN tags shared_tags ON source_tags.tag = shared_tags.tag
JOIN files target ON shared_tags.file_id = target.id
LEFT JOIN frontmatter source_traffic ON source.id = source_traffic.file_id AND source_traffic.key = 'organic_traffic'
LEFT JOIN frontmatter target_traffic ON target.id = target_traffic.file_id AND target_traffic.key = 'organic_traffic'
WHERE source.directory LIKE '%blog%'
  AND target.directory LIKE '%blog%'
  AND source.id != target.id
  AND NOT EXISTS (
    SELECT 1 FROM links l
    WHERE l.source_file_id = source.id
    AND l.target_file_id = target.id
  )
GROUP BY source.id, target.id
HAVING shared_topics >= 2
ORDER BY shared_topics DESC, source_traffic DESC;
```

### 3. Content Freshness Analysis

```sql
-- Identify content that needs updating for SEO
SELECT
    f.title,
    DATE(fm_date.value) as publish_date,
    DATE(fm_updated.value) as last_updated,
    julianday('now') - julianday(COALESCE(fm_updated.value, fm_date.value)) as days_since_update,
    CAST(fm_organic_traffic.value AS INTEGER) as organic_traffic,
    CAST(fm_page_views.value AS INTEGER) as page_views,
    CASE
        WHEN julianday('now') - julianday(COALESCE(fm_updated.value, fm_date.value)) > 365 THEN 'Urgent Update'
        WHEN julianday('now') - julianday(COALESCE(fm_updated.value, fm_date.value)) > 180 THEN 'Needs Update'
        ELSE 'Fresh'
    END as freshness_status,
    fm_target_keywords.value as target_keywords
FROM files f
LEFT JOIN frontmatter fm_date ON f.id = fm_date.file_id AND fm_date.key = 'date'
LEFT JOIN frontmatter fm_updated ON f.id = fm_updated.file_id AND fm_updated.key = 'updated'
LEFT JOIN frontmatter fm_organic_traffic ON f.id = fm_organic_traffic.file_id AND fm_organic_traffic.key = 'organic_traffic'
LEFT JOIN frontmatter fm_page_views ON f.id = fm_page_views.file_id AND fm_page_views.key = 'page_views'
LEFT JOIN frontmatter fm_target_keywords ON f.id = fm_target_keywords.file_id AND fm_target_keywords.key = 'target_keywords'
WHERE f.directory LIKE '%blog%' OR f.directory LIKE '%content%'
  AND CAST(fm_organic_traffic.value AS INTEGER) > 100  -- Focus on traffic-generating content
ORDER BY
    CASE freshness_status
        WHEN 'Urgent Update' THEN 1
        WHEN 'Needs Update' THEN 2
        ELSE 3
    END,
    organic_traffic DESC;
```

## SEO Reporting

### Monthly SEO Report

```sql
-- Generate comprehensive monthly SEO report
SELECT
    'Total Content Pieces' as metric,
    COUNT(*) as current_month,
    (SELECT COUNT(*) FROM files f2
     WHERE (f2.directory LIKE '%blog%' OR f2.directory LIKE '%content%')
     AND DATE(f2.created_date) < date('now', 'start of month')) as previous_total
FROM files f
WHERE f.directory LIKE '%blog%' OR f.directory LIKE '%content%'

UNION ALL

SELECT
    'Average SEO Score',
    ROUND(AVG(CAST(fm_seo_score.value AS INTEGER)), 1),
    (SELECT ROUND(AVG(CAST(fm2_seo_score.value AS INTEGER)), 1)
     FROM files f2
     LEFT JOIN frontmatter fm2_seo_score ON f2.id = fm2_seo_score.file_id AND fm2_seo_score.key = 'seo_score'
     WHERE (f2.directory LIKE '%blog%' OR f2.directory LIKE '%content%')
     AND DATE(f2.modified_date) < date('now', 'start of month'))
FROM files f
LEFT JOIN frontmatter fm_seo_score ON f.id = fm_seo_score.file_id AND fm_seo_score.key = 'seo_score'
WHERE f.directory LIKE '%blog%' OR f.directory LIKE '%content%'

UNION ALL

SELECT
    'High SEO Score Posts (80+)',
    COUNT(CASE WHEN CAST(fm_seo_score.value AS INTEGER) >= 80 THEN 1 END),
    NULL
FROM files f
LEFT JOIN frontmatter fm_seo_score ON f.id = fm_seo_score.file_id AND fm_seo_score.key = 'seo_score'
WHERE f.directory LIKE '%blog%' OR f.directory LIKE '%content%'

UNION ALL

SELECT
    'Posts Missing Meta Descriptions',
    COUNT(CASE WHEN fm_meta_desc.value IS NULL OR LENGTH(fm_meta_desc.value) = 0 THEN 1 END),
    NULL
FROM files f
LEFT JOIN frontmatter fm_meta_desc ON f.id = fm_meta_desc.file_id AND fm_meta_desc.key = 'meta_description'
WHERE f.directory LIKE '%blog%' OR f.directory LIKE '%content%';
```

### Keyword Cannibalization Detection

```sql
-- Detect potential keyword cannibalization
SELECT
    fm_target_keywords.value as target_keyword,
    COUNT(*) as competing_posts,
    GROUP_CONCAT(f.title, '; ') as competing_titles,
    AVG(CAST(fm_organic_traffic.value AS INTEGER)) as avg_organic_traffic,
    MAX(CAST(fm_organic_traffic.value AS INTEGER)) as best_performer_traffic,
    'Potential Cannibalization' as issue_type
FROM files f
JOIN frontmatter fm_target_keywords ON f.id = fm_target_keywords.file_id AND fm_target_keywords.key = 'target_keywords'
LEFT JOIN frontmatter fm_organic_traffic ON f.id = fm_organic_traffic.file_id AND fm_organic_traffic.key = 'organic_traffic'
WHERE f.directory LIKE '%blog%' OR f.directory LIKE '%content%'
GROUP BY fm_target_keywords.value
HAVING competing_posts > 1
ORDER BY competing_posts DESC, avg_organic_traffic DESC;
```

## Best Practices

### SEO Data Collection
- Track comprehensive SEO metrics consistently
- Monitor both technical and content factors
- Include user engagement metrics
- Regular SEO score updates

### Optimization Workflow
- Prioritize high-traffic, low-score content
- Focus on quick wins first
- Monitor impact of changes
- Regular content freshness audits

### Performance Monitoring
- Monthly SEO health reports
- Keyword performance tracking
- Internal linking analysis
- Image optimization audits

### Content Strategy
- Target keyword research and mapping
- Content gap identification
- Competitor analysis integration
- User intent optimization

This SEO analysis system provides data-driven insights to improve search engine visibility, optimize content performance, and maintain competitive search rankings.