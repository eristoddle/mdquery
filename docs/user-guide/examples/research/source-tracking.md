# Source Tracking and Citation Management

This example demonstrates how to use mdquery to track sources, manage citations, and maintain research provenance across your notes.

## Overview

Effective source tracking helps you:
- Maintain citation accuracy and completeness
- Track source reliability and bias
- Generate bibliographies automatically
- Identify gaps in source diversity
- Verify claims with original sources

## Source Data Structure

```yaml
---
title: "The Impact of Remote Work on Productivity"
source_type: "journal_article"
authors: ["Smith, J.", "Johnson, M.", "Williams, K."]
publication: "Journal of Workplace Studies"
year: 2023
volume: 45
issue: 3
pages: "123-145"
doi: "10.1234/jws.2023.45.3.123"
url: "https://example.com/article"
access_date: "2024-01-15"
source_quality: 8
bias_rating: 2
methodology: "quantitative"
sample_size: 1250
key_findings: ["25% productivity increase", "improved work-life balance", "reduced commute stress"]
tags: [remote-work, productivity, workplace-studies]
cited_in: ["remote-work-analysis.md", "future-of-work-trends.md"]
---
```

## Key Tracking Queries

### 1. Source Quality Assessment

```sql
SELECT
    fm_source_type.value as source_type,
    COUNT(*) as source_count,
    AVG(CAST(fm_quality.value AS INTEGER)) as avg_quality_rating,
    AVG(CAST(fm_bias.value AS INTEGER)) as avg_bias_rating,
    COUNT(CASE WHEN CAST(fm_quality.value AS INTEGER) >= 8 THEN 1 END) as high_quality_sources,
    COUNT(CASE WHEN fm_doi.value IS NOT NULL THEN 1 END) as sources_with_doi
FROM files f
LEFT JOIN frontmatter fm_source_type ON f.id = fm_source_type.file_id AND fm_source_type.key = 'source_type'
LEFT JOIN frontmatter fm_quality ON f.id = fm_quality.file_id AND fm_quality.key = 'source_quality'
LEFT JOIN frontmatter fm_bias ON f.id = fm_bias.file_id AND fm_bias.key = 'bias_rating'
LEFT JOIN frontmatter fm_doi ON f.id = fm_doi.file_id AND fm_doi.key = 'doi'
WHERE f.directory LIKE '%sources%'
GROUP BY fm_source_type.value
ORDER BY avg_quality_rating DESC;
```

### 2. Citation Network Analysis

```sql
-- Find most frequently cited sources
SELECT
    f.title as source_title,
    fm_authors.value as authors,
    fm_year.value as publication_year,
    COUNT(citing_files.id) as citation_count,
    GROUP_CONCAT(citing_files.filename, '; ') as citing_documents
FROM files f
LEFT JOIN frontmatter fm_authors ON f.id = fm_authors.file_id AND fm_authors.key = 'authors'
LEFT JOIN frontmatter fm_year ON f.id = fm_year.file_id AND fm_year.key = 'year'
LEFT JOIN links l ON f.id = l.target_file_id
LEFT JOIN files citing_files ON l.source_file_id = citing_files.id
WHERE f.directory LIKE '%sources%'
GROUP BY f.id
HAVING citation_count > 0
ORDER BY citation_count DESC;
```

### 3. Source Diversity Analysis

```sql
-- Analyze source diversity by publication year and type
SELECT
    fm_year.value as publication_year,
    fm_source_type.value as source_type,
    COUNT(*) as source_count,
    COUNT(DISTINCT fm_authors.value) as unique_authors,
    COUNT(DISTINCT fm_publication.value) as unique_publications,
    AVG(CAST(fm_quality.value AS INTEGER)) as avg_quality
FROM files f
LEFT JOIN frontmatter fm_year ON f.id = fm_year.file_id AND fm_year.key = 'year'
LEFT JOIN frontmatter fm_source_type ON f.id = fm_source_type.file_id AND fm_source_type.key = 'source_type'
LEFT JOIN frontmatter fm_authors ON f.id = fm_authors.file_id AND fm_authors.key = 'authors'
LEFT JOIN frontmatter fm_publication ON f.id = fm_publication.file_id AND fm_publication.key = 'publication'
LEFT JOIN frontmatter fm_quality ON f.id = fm_quality.file_id AND fm_quality.key = 'source_quality'
WHERE f.directory LIKE '%sources%'
  AND fm_year.value >= '2020'
GROUP BY fm_year.value, fm_source_type.value
ORDER BY publication_year DESC, source_count DESC;
```

### 4. Bibliography Generation

```sql
-- Generate APA-style bibliography
SELECT
    fm_authors.value || ' (' || fm_year.value || '). ' ||
    f.title || '. ' ||
    CASE fm_source_type.value
        WHEN 'journal_article' THEN
            fm_publication.value || ', ' ||
            COALESCE(fm_volume.value, '') ||
            CASE WHEN fm_issue.value IS NOT NULL THEN '(' || fm_issue.value || ')' ELSE '' END ||
            CASE WHEN fm_pages.value IS NOT NULL THEN ', ' || fm_pages.value ELSE '' END || '.'
        WHEN 'book' THEN
            fm_publication.value || '.'
        WHEN 'website' THEN
            fm_publication.value || '. Retrieved from ' || fm_url.value
        ELSE fm_publication.value || '.'
    END ||
    CASE WHEN fm_doi.value IS NOT NULL THEN ' https://doi.org/' || fm_doi.value ELSE '' END
    as apa_citation
FROM files f
LEFT JOIN frontmatter fm_authors ON f.id = fm_authors.file_id AND fm_authors.key = 'authors'
LEFT JOIN frontmatter fm_year ON f.id = fm_year.file_id AND fm_year.key = 'year'
LEFT JOIN frontmatter fm_source_type ON f.id = fm_source_type.file_id AND fm_source_type.key = 'source_type'
LEFT JOIN frontmatter fm_publication ON f.id = fm_publication.file_id AND fm_publication.key = 'publication'
LEFT JOIN frontmatter fm_volume ON f.id = fm_volume.file_id AND fm_volume.key = 'volume'
LEFT JOIN frontmatter fm_issue ON f.id = fm_issue.file_id AND fm_issue.key = 'issue'
LEFT JOIN frontmatter fm_pages ON f.id = fm_pages.file_id AND fm_pages.key = 'pages'
LEFT JOIN frontmatter fm_url ON f.id = fm_url.file_id AND fm_url.key = 'url'
LEFT JOIN frontmatter fm_doi ON f.id = fm_doi.file_id AND fm_doi.key = 'doi'
WHERE f.directory LIKE '%sources%'
ORDER BY fm_authors.value, fm_year.value;
```

### 5. Source Gap Analysis

```sql
-- Identify potential gaps in source coverage
SELECT
    t.tag as research_topic,
    COUNT(DISTINCT f.id) as source_count,
    COUNT(DISTINCT fm_source_type.value) as source_type_diversity,
    MIN(CAST(fm_year.value AS INTEGER)) as earliest_source,
    MAX(CAST(fm_year.value AS INTEGER)) as latest_source,
    AVG(CAST(fm_quality.value AS INTEGER)) as avg_quality,
    CASE
        WHEN COUNT(DISTINCT f.id) < 5 THEN 'Insufficient Sources'
        WHEN COUNT(DISTINCT fm_source_type.value) < 3 THEN 'Limited Source Types'
        WHEN MAX(CAST(fm_year.value AS INTEGER)) < 2020 THEN 'Outdated Sources'
        ELSE 'Well Covered'
    END as coverage_status
FROM files f
JOIN tags t ON f.id = t.file_id
LEFT JOIN frontmatter fm_source_type ON f.id = fm_source_type.file_id AND fm_source_type.key = 'source_type'
LEFT JOIN frontmatter fm_year ON f.id = fm_year.file_id AND fm_year.key = 'year'
LEFT JOIN frontmatter fm_quality ON f.id = fm_quality.file_id AND fm_quality.key = 'source_quality'
WHERE f.directory LIKE '%sources%'
GROUP BY t.tag
HAVING source_count >= 2
ORDER BY coverage_status, source_count DESC;
```

## Advanced Source Analysis

### Author Collaboration Networks

```sql
-- Identify author collaboration patterns
SELECT
    a1.value as author1,
    a2.value as author2,
    COUNT(*) as collaborations,
    GROUP_CONCAT(f.title, '; ') as collaborative_works,
    AVG(CAST(fm_quality.value AS INTEGER)) as avg_quality_of_collaborations
FROM frontmatter a1
JOIN frontmatter a2 ON a1.file_id = a2.file_id
JOIN files f ON a1.file_id = f.id
LEFT JOIN frontmatter fm_quality ON f.id = fm_quality.file_id AND fm_quality.key = 'source_quality'
WHERE a1.key = 'authors' AND a2.key = 'authors'
  AND a1.value != a2.value
  AND a1.id < a2.id  -- Avoid duplicates
  AND f.directory LIKE '%sources%'
GROUP BY a1.value, a2.value
HAVING collaborations > 1
ORDER BY collaborations DESC;
```

### Methodology Distribution

```sql
-- Analyze research methodology distribution
SELECT
    fm_methodology.value as methodology,
    COUNT(*) as source_count,
    AVG(CAST(fm_sample_size.value AS INTEGER)) as avg_sample_size,
    AVG(CAST(fm_quality.value AS INTEGER)) as avg_quality_rating,
    GROUP_CONCAT(DISTINCT t.tag) as research_areas
FROM files f
LEFT JOIN frontmatter fm_methodology ON f.id = fm_methodology.file_id AND fm_methodology.key = 'methodology'
LEFT JOIN frontmatter fm_sample_size ON f.id = fm_sample_size.file_id AND fm_sample_size.key = 'sample_size'
LEFT JOIN frontmatter fm_quality ON f.id = fm_quality.file_id AND fm_quality.key = 'source_quality'
LEFT JOIN tags t ON f.id = t.file_id
WHERE f.directory LIKE '%sources%'
  AND fm_methodology.value IS NOT NULL
GROUP BY fm_methodology.value
ORDER BY source_count DESC;
```

### Citation Impact Analysis

```sql
-- Analyze which sources have the most impact on your work
SELECT
    f.title as source_title,
    fm_authors.value as authors,
    COUNT(DISTINCT citing_files.id) as direct_citations,
    COUNT(DISTINCT secondary_citations.id) as secondary_citations,
    (COUNT(DISTINCT citing_files.id) + COUNT(DISTINCT secondary_citations.id)) as total_impact,
    CAST(fm_quality.value AS INTEGER) as source_quality,
    fm_year.value as publication_year
FROM files f
LEFT JOIN frontmatter fm_authors ON f.id = fm_authors.file_id AND fm_authors.key = 'authors'
LEFT JOIN frontmatter fm_quality ON f.id = fm_quality.file_id AND fm_quality.key = 'source_quality'
LEFT JOIN frontmatter fm_year ON f.id = fm_year.file_id AND fm_year.key = 'year'
-- Direct citations
LEFT JOIN links direct_links ON f.id = direct_links.target_file_id
LEFT JOIN files citing_files ON direct_links.source_file_id = citing_files.id
-- Secondary citations (files that cite files that cite this source)
LEFT JOIN links secondary_links ON citing_files.id = secondary_links.target_file_id
LEFT JOIN files secondary_citations ON secondary_links.source_file_id = secondary_citations.id
WHERE f.directory LIKE '%sources%'
GROUP BY f.id
HAVING direct_citations > 0
ORDER BY total_impact DESC;
```

## Source Validation Workflows

### Link Integrity Check

```sql
-- Verify source URLs are still accessible
SELECT
    f.title,
    fm_url.value as source_url,
    fm_access_date.value as last_checked,
    julianday('now') - julianday(fm_access_date.value) as days_since_check,
    CASE
        WHEN julianday('now') - julianday(fm_access_date.value) > 90 THEN 'Needs Verification'
        WHEN julianday('now') - julianday(fm_access_date.value) > 30 THEN 'Check Soon'
        ELSE 'Recently Verified'
    END as verification_status
FROM files f
LEFT JOIN frontmatter fm_url ON f.id = fm_url.file_id AND fm_url.key = 'url'
LEFT JOIN frontmatter fm_access_date ON f.id = fm_access_date.file_id AND fm_access_date.key = 'access_date'
WHERE f.directory LIKE '%sources%'
  AND fm_url.value IS NOT NULL
ORDER BY days_since_check DESC;
```

### Duplicate Source Detection

```sql
-- Find potential duplicate sources
SELECT
    f1.title as source1,
    f2.title as source2,
    fm1_authors.value as authors1,
    fm2_authors.value as authors2,
    fm1_year.value as year1,
    fm2_year.value as year2,
    'Potential Duplicate' as status
FROM files f1
JOIN files f2 ON f1.id < f2.id
LEFT JOIN frontmatter fm1_authors ON f1.id = fm1_authors.file_id AND fm1_authors.key = 'authors'
LEFT JOIN frontmatter fm2_authors ON f2.id = fm2_authors.file_id AND fm2_authors.key = 'authors'
LEFT JOIN frontmatter fm1_year ON f1.id = fm1_year.file_id AND fm1_year.key = 'year'
LEFT JOIN frontmatter fm2_year ON f2.id = fm2_year.file_id AND fm2_year.key = 'year'
WHERE f1.directory LIKE '%sources%'
  AND f2.directory LIKE '%sources%'
  AND (
    -- Same authors and year
    (fm1_authors.value = fm2_authors.value AND fm1_year.value = fm2_year.value)
    OR
    -- Very similar titles
    (LENGTH(f1.title) > 10 AND LENGTH(f2.title) > 10 AND
     LENGTH(f1.title || f2.title) - LENGTH(REPLACE(LOWER(f1.title || f2.title), LOWER(f1.title), '')) > LENGTH(f1.title) * 0.8)
  )
ORDER BY fm1_authors.value, fm1_year.value;
```

## Reporting and Maintenance

### Monthly Source Review

```sql
-- Generate monthly source management report
SELECT
    'Total Sources' as metric,
    COUNT(*) as value,
    '' as details
FROM files f
WHERE f.directory LIKE '%sources%'

UNION ALL

SELECT
    'New Sources This Month',
    COUNT(*),
    GROUP_CONCAT(f.title, '; ')
FROM files f
WHERE f.directory LIKE '%sources%'
  AND f.created_date >= date('now', 'start of month')

UNION ALL

SELECT
    'High Quality Sources (8+)',
    COUNT(*),
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM files WHERE directory LIKE '%sources%'), 1) || '%'
FROM files f
JOIN frontmatter fm_quality ON f.id = fm_quality.file_id AND fm_quality.key = 'source_quality'
WHERE f.directory LIKE '%sources%'
  AND CAST(fm_quality.value AS INTEGER) >= 8

UNION ALL

SELECT
    'Sources Needing URL Verification',
    COUNT(*),
    ''
FROM files f
JOIN frontmatter fm_url ON f.id = fm_url.file_id AND fm_url.key = 'url'
LEFT JOIN frontmatter fm_access_date ON f.id = fm_access_date.file_id AND fm_access_date.key = 'access_date'
WHERE f.directory LIKE '%sources%'
  AND (fm_access_date.value IS NULL OR julianday('now') - julianday(fm_access_date.value) > 90);
```

### Source Quality Improvement

```sql
-- Identify sources that need quality improvement
SELECT
    f.title,
    CAST(fm_quality.value AS INTEGER) as current_quality,
    CASE
        WHEN fm_doi.value IS NULL THEN 'Add DOI'
        WHEN fm_authors.value IS NULL THEN 'Add Authors'
        WHEN fm_year.value IS NULL THEN 'Add Publication Year'
        WHEN fm_methodology.value IS NULL THEN 'Add Methodology'
        ELSE 'Complete'
    END as improvement_needed,
    COUNT(citing_files.id) as citation_importance
FROM files f
LEFT JOIN frontmatter fm_quality ON f.id = fm_quality.file_id AND fm_quality.key = 'source_quality'
LEFT JOIN frontmatter fm_doi ON f.id = fm_doi.file_id AND fm_doi.key = 'doi'
LEFT JOIN frontmatter fm_authors ON f.id = fm_authors.file_id AND fm_authors.key = 'authors'
LEFT JOIN frontmatter fm_year ON f.id = fm_year.file_id AND fm_year.key = 'year'
LEFT JOIN frontmatter fm_methodology ON f.id = fm_methodology.file_id AND fm_methodology.key = 'methodology'
LEFT JOIN links l ON f.id = l.target_file_id
LEFT JOIN files citing_files ON l.source_file_id = citing_files.id
WHERE f.directory LIKE '%sources%'
  AND (CAST(fm_quality.value AS INTEGER) < 7 OR improvement_needed != 'Complete')
GROUP BY f.id
ORDER BY citation_importance DESC, current_quality ASC;
```

## Best Practices

### Source Documentation
- Include complete bibliographic information
- Rate source quality and potential bias
- Document access dates for web sources
- Track methodology and sample sizes

### Citation Management
- Link sources to citing documents
- Maintain consistent citation formats
- Regular link validation and updates
- Track source usage patterns

### Quality Control
- Regular source quality audits
- Duplicate detection and removal
- URL accessibility verification
- Metadata completeness checks

### Research Integrity
- Diverse source types and perspectives
- Current and historical source balance
- Transparent bias assessment
- Proper attribution and context

This source tracking system ensures research integrity, maintains citation accuracy, and provides comprehensive source management for academic and professional research projects.