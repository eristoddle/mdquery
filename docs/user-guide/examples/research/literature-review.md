# Literature Review Management

This example demonstrates how to use mdquery to manage academic literature reviews, track citations, and organize research themes.

## Scenario

You're conducting a literature review on "Transformer Architectures in Natural Language Processing" and need to:
- Track papers and citations
- Identify research themes and gaps
- Generate bibliographies
- Find connections between papers

## Setup

Your research notes are organized like this:
```
research/
├── papers/
│   ├── attention-is-all-you-need.md
│   ├── bert-pretraining.md
│   └── gpt-3-language-models.md
├── themes/
│   ├── attention-mechanisms.md
│   ├── pretraining-strategies.md
│   └── scaling-laws.md
└── reviews/
    ├── transformer-survey-2023.md
    └── nlp-progress-review.md
```

Each paper note includes structured frontmatter:
```yaml
---
title: "Attention Is All You Need"
authors: ["Vaswani, A.", "Shazeer, N.", "Parmar, N."]
year: 2017
venue: "NIPS"
doi: "10.5555/3295222.3295349"
tags: [transformers, attention, neural-networks, nlp]
status: read
rating: 5
key_contributions: ["self-attention", "transformer-architecture", "parallel-computation"]
---
```

## Key Queries

### 1. Find All Papers by Topic

```sql
SELECT f.filename, f.title, fm_year.value as year, fm_venue.value as venue
FROM files f
JOIN frontmatter fm_year ON f.id = fm_year.file_id AND fm_year.key = 'year'
LEFT JOIN frontmatter fm_venue ON f.id = fm_venue.file_id AND fm_venue.key = 'venue'
JOIN tags t ON f.id = t.file_id
WHERE t.tag = 'transformers'
  AND f.directory LIKE '%papers%'
ORDER BY CAST(fm_year.value AS INTEGER) DESC;
```

### 2. Generate Bibliography by Year

```sql
SELECT
    fm_authors.value as authors,
    f.title,
    fm_year.value as year,
    fm_venue.value as venue,
    fm_doi.value as doi
FROM files f
JOIN frontmatter fm_authors ON f.id = fm_authors.file_id AND fm_authors.key = 'authors'
JOIN frontmatter fm_year ON f.id = fm_year.file_id AND fm_year.key = 'year'
LEFT JOIN frontmatter fm_venue ON f.id = fm_venue.file_id AND fm_venue.key = 'venue'
LEFT JOIN frontmatter fm_doi ON f.id = fm_doi.file_id AND fm_doi.key = 'doi'
WHERE f.directory LIKE '%papers%'
ORDER BY CAST(fm_year.value AS INTEGER) DESC, f.title;
```

### 3. Identify Research Themes

```sql
SELECT
    t.tag as theme,
    COUNT(*) as paper_count,
    GROUP_CONCAT(f.title, '; ') as papers,
    AVG(CAST(fm_rating.value AS FLOAT)) as avg_rating
FROM tags t
JOIN files f ON t.file_id = f.id
LEFT JOIN frontmatter fm_rating ON f.id = fm_rating.file_id AND fm_rating.key = 'rating'
WHERE f.directory LIKE '%papers%'
GROUP BY t.tag
HAVING paper_count >= 3
ORDER BY paper_count DESC;
```

### 4. Find Highly Cited Papers

```sql
SELECT
    f.title,
    fm_authors.value as authors,
    fm_year.value as year,
    COUNT(l.id) as citation_count
FROM files f
JOIN frontmatter fm_authors ON f.id = fm_authors.file_id AND fm_authors.key = 'authors'
JOIN frontmatter fm_year ON f.id = fm_year.file_id AND fm_year.key = 'year'
LEFT JOIN links l ON f.id = l.target_file_id
WHERE f.directory LIKE '%papers%'
GROUP BY f.id
ORDER BY citation_count DESC, CAST(fm_year.value AS INTEGER) DESC;
```

### 5. Research Gap Analysis

```sql
-- Find themes with few recent papers
SELECT
    t.tag as theme,
    COUNT(*) as total_papers,
    COUNT(CASE WHEN CAST(fm_year.value AS INTEGER) >= 2020 THEN 1 END) as recent_papers,
    MAX(CAST(fm_year.value AS INTEGER)) as latest_year
FROM tags t
JOIN files f ON t.file_id = f.id
JOIN frontmatter fm_year ON f.id = fm_year.file_id AND fm_year.key = 'year'
WHERE f.directory LIKE '%papers%'
GROUP BY t.tag
HAVING total_papers >= 5 AND recent_papers <= 2
ORDER BY total_papers DESC;
```

### 6. Author Collaboration Network

```sql
SELECT
    fm1.value as author1,
    fm2.value as author2,
    COUNT(*) as collaborations
FROM frontmatter fm1
JOIN frontmatter fm2 ON fm1.file_id = fm2.file_id
WHERE fm1.key = 'authors' AND fm2.key = 'authors'
  AND fm1.value != fm2.value
  AND fm1.id < fm2.id  -- Avoid duplicates
GROUP BY fm1.value, fm2.value
HAVING collaborations > 1
ORDER BY collaborations DESC;
```

## Advanced Analysis

### Citation Network Analysis

```sql
-- Papers that cite each other (create citation network)
SELECT
    source.title as citing_paper,
    target.title as cited_paper,
    l.link_text as context
FROM links l
JOIN files source ON l.source_file_id = source.id
JOIN files target ON l.target_file_id = target.id
WHERE source.directory LIKE '%papers%'
  AND target.directory LIKE '%papers%'
  AND l.link_type = 'wikilink';
```

### Research Timeline

```sql
-- Show research evolution over time
SELECT
    fm_year.value as year,
    COUNT(*) as papers_published,
    GROUP_CONCAT(DISTINCT t.tag) as themes_explored,
    AVG(CAST(fm_rating.value AS FLOAT)) as avg_quality_rating
FROM files f
JOIN frontmatter fm_year ON f.id = fm_year.file_id AND fm_year.key = 'year'
LEFT JOIN frontmatter fm_rating ON f.id = fm_rating.file_id AND fm_rating.key = 'rating'
LEFT JOIN tags t ON f.id = t.file_id
WHERE f.directory LIKE '%papers%'
GROUP BY fm_year.value
ORDER BY CAST(fm_year.value AS INTEGER);
```

### Key Contributions Analysis

```sql
-- Extract and analyze key contributions
SELECT
    fm_contrib.value as contribution,
    COUNT(*) as frequency,
    GROUP_CONCAT(f.title, '; ') as papers
FROM files f
JOIN frontmatter fm_contrib ON f.id = fm_contrib.file_id
WHERE fm_contrib.key = 'key_contributions'
  AND f.directory LIKE '%papers%'
GROUP BY fm_contrib.value
ORDER BY frequency DESC;
```

## Workflow Integration

### Daily Research Routine

1. **Morning Review**: Check recent additions
```sql
SELECT f.filename, f.modified_date, f.title
FROM files f
WHERE f.directory LIKE '%research%'
  AND f.modified_date > date('now', '-7 days')
ORDER BY f.modified_date DESC;
```

2. **Weekly Theme Analysis**: Identify emerging patterns
```sql
SELECT t.tag, COUNT(*) as recent_mentions
FROM tags t
JOIN files f ON t.file_id = f.id
WHERE f.modified_date > date('now', '-7 days')
  AND f.directory LIKE '%research%'
GROUP BY t.tag
ORDER BY recent_mentions DESC;
```

### Literature Review Report Generation

```sql
-- Comprehensive literature review summary
SELECT
    'Total Papers' as metric,
    COUNT(*) as value
FROM files f
WHERE f.directory LIKE '%papers%'

UNION ALL

SELECT
    'Date Range' as metric,
    MIN(fm_year.value) || ' - ' || MAX(fm_year.value) as value
FROM files f
JOIN frontmatter fm_year ON f.id = fm_year.file_id AND fm_year.key = 'year'
WHERE f.directory LIKE '%papers%'

UNION ALL

SELECT
    'Unique Authors' as metric,
    COUNT(DISTINCT fm_authors.value) as value
FROM files f
JOIN frontmatter fm_authors ON f.id = fm_authors.file_id AND fm_authors.key = 'authors'
WHERE f.directory LIKE '%papers%'

UNION ALL

SELECT
    'Research Themes' as metric,
    COUNT(DISTINCT t.tag) as value
FROM files f
JOIN tags t ON f.id = t.file_id
WHERE f.directory LIKE '%papers%';
```

## Best Practices

### Note Organization
- Use consistent frontmatter fields across all papers
- Include DOI and venue information for proper citations
- Rate papers (1-5) to track quality and importance
- Tag papers with multiple relevant themes

### Citation Management
- Link related papers using wikilinks
- Include context when citing (quote or summary)
- Track citation relationships for network analysis
- Regular link validation to catch broken references

### Research Tracking
- Weekly reviews to identify patterns and gaps
- Monthly theme analysis to guide future reading
- Quarterly comprehensive reports for progress tracking
- Annual literature review updates

This systematic approach to literature review management helps maintain organized, searchable, and analyzable research collections that support high-quality academic work.