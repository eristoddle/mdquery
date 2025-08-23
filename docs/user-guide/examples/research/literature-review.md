# Literature Review with mdquery

This example demonstrates how to use mdquery for managing academic literature reviews, tracking sources, and analyzing research themes.

## Scenario

You're conducting a literature review on "machine learning in healthcare" and have collected notes from various sources including:
- Academic papers (PDFs with extracted notes)
- Web articles and blog posts
- Conference presentations
- Book chapters

Your notes are organized with frontmatter containing source information and tags for topics.

## Sample Note Structure

```markdown
---
title: "Deep Learning for Medical Image Analysis"
authors: ["Smith, J.", "Johnson, A."]
year: 2023
source: "Journal of Medical AI"
doi: "10.1000/journal.2023.001"
type: "journal-article"
tags: [machine-learning, healthcare, medical-imaging, deep-learning]
status: "reviewed"
rating: 4
---

# Deep Learning for Medical Image Analysis

## Summary
This paper presents a comprehensive survey of deep learning applications in medical image analysis...

## Key Findings
- CNN architectures show 95% accuracy in tumor detection
- Transfer learning reduces training time by 60%
- Regulatory challenges remain for clinical deployment

## Methodology
The authors reviewed 150 papers published between 2020-2023...

## Relevance to Research
This paper provides strong evidence for the effectiveness of deep learning in medical imaging, supporting our hypothesis that ML can improve diagnostic accuracy.

## Citations
- [Related Work on CNN Architectures](https://doi.org/10.1000/related.2022.001)
- [Transfer Learning in Medical AI](https://arxiv.org/abs/2022.12345)
```

## Common Literature Review Queries

### 1. Source Inventory and Statistics

```sql
-- Get overview of literature collection
SELECT
    fm_type.value as source_type,
    COUNT(*) as count,
    AVG(CAST(fm_rating.value AS REAL)) as avg_rating,
    MIN(CAST(fm_year.value AS INTEGER)) as earliest_year,
    MAX(CAST(fm_year.value AS INTEGER)) as latest_year
FROM files f
JOIN frontmatter fm_type ON f.id = fm_type.file_id AND fm_type.key = 'type'
LEFT JOIN frontmatter fm_rating ON f.id = fm_rating.file_id AND fm_rating.key = 'rating'
LEFT JOIN frontmatter fm_year ON f.id = fm_year.file_id AND fm_year.key = 'year'
WHERE f.directory LIKE '%literature%'
GROUP BY fm_type.value
ORDER BY count DESC;
```

**Expected Output:**
```
source_type      | count | avg_rating | earliest_year | latest_year
journal-article  | 45    | 3.8        | 2020          | 2024
conference-paper | 23    | 3.6        | 2021          | 2024
book-chapter     | 12    | 4.1        | 2019          | 2023
web-article      | 8     | 3.2        | 2022          | 2024
```

### 2. Research Theme Analysis

```sql
-- Analyze research themes and their evolution
SELECT
    t.tag as theme,
    COUNT(*) as paper_count,
    AVG(CAST(fm_year.value AS INTEGER)) as avg_year,
    AVG(CAST(fm_rating.value AS REAL)) as avg_rating,
    GROUP_CONCAT(DISTINCT fm_type.value) as source_types
FROM tags t
JOIN files f ON t.file_id = f.id
LEFT JOIN frontmatter fm_year ON f.id = fm_year.file_id AND fm_year.key = 'year'
LEFT JOIN frontmatter fm_rating ON f.id = fm_rating.file_id AND fm_rating.key = 'rating'
LEFT JOIN frontmatter fm_type ON f.id = fm_type.file_id AND fm_type.key = 'type'
WHERE f.directory LIKE '%literature%'
GROUP BY t.tag
HAVING paper_count >= 3
ORDER BY paper_count DESC, avg_rating DESC;
```

### 3. High-Impact Sources

```sql
-- Find highly-rated recent sources
SELECT
    fm_title.value as title,
    fm_authors.value as authors,
    fm_year.value as year,
    fm_rating.value as rating,
    fm_source.value as journal,
    GROUP_CONCAT(DISTINCT t.tag) as themes
FROM files f
JOIN frontmatter fm_title ON f.id = fm_title.file_id AND fm_title.key = 'title'
LEFT JOIN frontmatter fm_authors ON f.id = fm_authors.file_id AND fm_authors.key = 'authors'
LEFT JOIN frontmatter fm_year ON f.id = fm_year.file_id AND fm_year.key = 'year'
LEFT JOIN frontmatter fm_rating ON f.id = fm_rating.file_id AND fm_rating.key = 'rating'
LEFT JOIN frontmatter fm_source ON f.id = fm_source.file_id AND fm_source.key = 'source'
LEFT JOIN tags t ON f.id = t.file_id
WHERE f.directory LIKE '%literature%'
  AND CAST(fm_rating.value AS REAL) >= 4.0
  AND CAST(fm_year.value AS INTEGER) >= 2022
GROUP BY f.id
ORDER BY CAST(fm_rating.value AS REAL) DESC, CAST(fm_year.value AS INTEGER) DESC;
```

### 4. Research Gaps Analysis

```sql
-- Find underexplored topic combinations
WITH topic_pairs AS (
    SELECT
        t1.tag as topic1,
        t2.tag as topic2,
        COUNT(*) as co_occurrence
    FROM tags t1
    JOIN tags t2 ON t1.file_id = t2.file_id AND t1.tag < t2.tag
    JOIN files f ON t1.file_id = f.id
    WHERE f.directory LIKE '%literature%'
    GROUP BY t1.tag, t2.tag
),
single_topics AS (
    SELECT tag, COUNT(*) as single_count
    FROM tags t
    JOIN files f ON t.file_id = f.id
    WHERE f.directory LIKE '%literature%'
    GROUP BY tag
)
SELECT
    tp.topic1,
    tp.topic2,
    st1.single_count as topic1_count,
    st2.single_count as topic2_count,
    tp.co_occurrence,
    ROUND(CAST(tp.co_occurrence AS REAL) / MIN(st1.single_count, st2.single_count) * 100, 1) as overlap_percentage
FROM topic_pairs tp
JOIN single_topics st1 ON tp.topic1 = st1.tag
JOIN single_topics st2 ON tp.topic2 = st2.tag
WHERE st1.single_count >= 5 AND st2.single_count >= 5
  AND overlap_percentage < 30  -- Low overlap suggests research gap
ORDER BY overlap_percentage ASC, tp.co_occurrence DESC;
```

### 5. Citation Network Analysis

```sql
-- Analyze citation patterns and find key papers
SELECT
    l.link_target as cited_work,
    COUNT(*) as citation_count,
    GROUP_CONCAT(DISTINCT f.filename) as citing_papers,
    AVG(CAST(fm_rating.value AS REAL)) as avg_citing_paper_rating
FROM files f
JOIN links l ON f.id = l.file_id
LEFT JOIN frontmatter fm_rating ON f.id = fm_rating.file_id AND fm_rating.key = 'rating'
WHERE f.directory LIKE '%literature%'
  AND l.is_internal = 0
  AND (l.link_target LIKE '%doi.org%'
       OR l.link_target LIKE '%arxiv.org%'
       OR l.link_target LIKE '%.pdf')
GROUP BY l.link_target
HAVING citation_count >= 2
ORDER BY citation_count DESC, avg_citing_paper_rating DESC;
```

### 6. Review Progress Tracking

```sql
-- Track review progress by status
SELECT
    fm_status.value as status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM files WHERE directory LIKE '%literature%'), 1) as percentage,
    AVG(f.word_count) as avg_note_length
FROM files f
LEFT JOIN frontmatter fm_status ON f.id = fm_status.file_id AND fm_status.key = 'status'
WHERE f.directory LIKE '%literature%'
GROUP BY fm_status.value
ORDER BY
    CASE fm_status.value
        WHEN 'to-read' THEN 1
        WHEN 'reading' THEN 2
        WHEN 'reviewed' THEN 3
        WHEN 'synthesized' THEN 4
        ELSE 5
    END;
```

### 7. Temporal Analysis

```sql
-- Analyze research trends over time
SELECT
    fm_year.value as year,
    COUNT(*) as papers_published,
    COUNT(DISTINCT t.tag) as unique_themes,
    AVG(CAST(fm_rating.value AS REAL)) as avg_quality,
    GROUP_CONCAT(DISTINCT
        CASE WHEN paper_rank <= 3 THEN t.tag END
    ) as top_themes
FROM files f
JOIN frontmatter fm_year ON f.id = fm_year.file_id AND fm_year.key = 'year'
LEFT JOIN frontmatter fm_rating ON f.id = fm_rating.file_id AND fm_rating.key = 'rating'
LEFT JOIN (
    SELECT
        t.file_id,
        t.tag,
        ROW_NUMBER() OVER (PARTITION BY fm_year.value ORDER BY COUNT(*) DESC) as paper_rank
    FROM tags t
    JOIN files f ON t.file_id = f.id
    JOIN frontmatter fm_year ON f.id = fm_year.file_id AND fm_year.key = 'year'
    WHERE f.directory LIKE '%literature%'
    GROUP BY fm_year.value, t.tag
) t ON f.id = t.file_id
WHERE f.directory LIKE '%literature%'
  AND CAST(fm_year.value AS INTEGER) BETWEEN 2020 AND 2024
GROUP BY fm_year.value
ORDER BY CAST(fm_year.value AS INTEGER) DESC;
```

## Synthesis Queries

### Generate Literature Summary

```sql
-- Create a comprehensive literature summary
SELECT
    'LITERATURE REVIEW SUMMARY' as section,
    '' as content
UNION ALL
SELECT
    'Total Sources',
    CAST(COUNT(*) AS TEXT) || ' papers reviewed'
FROM files f WHERE f.directory LIKE '%literature%'
UNION ALL
SELECT
    'Date Range',
    MIN(fm_year.value) || ' - ' || MAX(fm_year.value)
FROM files f
JOIN frontmatter fm_year ON f.id = fm_year.file_id AND fm_year.key = 'year'
WHERE f.directory LIKE '%literature%'
UNION ALL
SELECT
    'Top Themes',
    GROUP_CONCAT(theme_summary, '; ')
FROM (
    SELECT t.tag || ' (' || COUNT(*) || ' papers)' as theme_summary
    FROM tags t
    JOIN files f ON t.file_id = f.id
    WHERE f.directory LIKE '%literature%'
    GROUP BY t.tag
    ORDER BY COUNT(*) DESC
    LIMIT 5
)
UNION ALL
SELECT
    'High-Impact Papers',
    GROUP_CONCAT(paper_summary, '; ')
FROM (
    SELECT fm_title.value || ' (' || fm_rating.value || '/5)' as paper_summary
    FROM files f
    JOIN frontmatter fm_title ON f.id = fm_title.file_id AND fm_title.key = 'title'
    JOIN frontmatter fm_rating ON f.id = fm_rating.file_id AND fm_rating.key = 'rating'
    WHERE f.directory LIKE '%literature%'
      AND CAST(fm_rating.value AS REAL) >= 4.0
    ORDER BY CAST(fm_rating.value AS REAL) DESC
    LIMIT 3
);
```

### Export Bibliography

```sql
-- Generate formatted bibliography
SELECT
    fm_authors.value || ' (' || fm_year.value || '). ' ||
    fm_title.value || '. ' ||
    COALESCE(fm_source.value, 'Unpublished') ||
    CASE
        WHEN fm_doi.value IS NOT NULL THEN '. DOI: ' || fm_doi.value
        ELSE ''
    END as citation
FROM files f
JOIN frontmatter fm_title ON f.id = fm_title.file_id AND fm_title.key = 'title'
LEFT JOIN frontmatter fm_authors ON f.id = fm_authors.file_id AND fm_authors.key = 'authors'
LEFT JOIN frontmatter fm_year ON f.id = fm_year.file_id AND fm_year.key = 'year'
LEFT JOIN frontmatter fm_source ON f.id = fm_source.file_id AND fm_source.key = 'source'
LEFT JOIN frontmatter fm_doi ON f.id = fm_doi.file_id AND fm_doi.key = 'doi'
WHERE f.directory LIKE '%literature%'
ORDER BY fm_authors.value, fm_year.value;
```

## Workflow Integration

### Daily Review Script

```bash
#!/bin/bash
# daily-literature-review.sh

echo "=== Daily Literature Review Report ==="
echo "Date: $(date)"
echo

echo "## Papers to Review Today"
mdquery query "
SELECT f.filename, fm_title.value as title
FROM files f
JOIN frontmatter fm_status ON f.id = fm_status.file_id AND fm_status.key = 'status'
LEFT JOIN frontmatter fm_title ON f.id = fm_title.file_id AND fm_title.key = 'title'
WHERE f.directory LIKE '%literature%' AND fm_status.value = 'to-read'
ORDER BY f.modified_date ASC
LIMIT 5
" --format table

echo
echo "## Recent High-Impact Additions"
mdquery query "
SELECT fm_title.value as title, fm_rating.value as rating
FROM files f
JOIN frontmatter fm_title ON f.id = fm_title.file_id AND fm_title.key = 'title'
JOIN frontmatter fm_rating ON f.id = fm_rating.file_id AND fm_rating.key = 'rating'
WHERE f.directory LIKE '%literature%'
  AND f.modified_date > date('now', '-7 days')
  AND CAST(fm_rating.value AS REAL) >= 4.0
ORDER BY f.modified_date DESC
" --format table

echo
echo "## Theme Progress"
mdquery query "
SELECT t.tag as theme, COUNT(*) as papers
FROM tags t
JOIN files f ON t.file_id = f.id
WHERE f.directory LIKE '%literature%'
GROUP BY t.tag
ORDER BY papers DESC
LIMIT 10
" --format table
```

### Research Question Tracking

```sql
-- Track how well research questions are being addressed
WITH research_questions AS (
    SELECT 'effectiveness' as question, 'machine-learning,healthcare,effectiveness' as required_tags
    UNION ALL
    SELECT 'implementation', 'machine-learning,healthcare,implementation,clinical'
    UNION ALL
    SELECT 'challenges', 'machine-learning,healthcare,challenges,barriers'
)
SELECT
    rq.question,
    COUNT(DISTINCT f.id) as relevant_papers,
    AVG(CAST(fm_rating.value AS REAL)) as avg_quality,
    GROUP_CONCAT(DISTINCT fm_title.value) as example_papers
FROM research_questions rq
LEFT JOIN files f ON f.directory LIKE '%literature%'
LEFT JOIN tags t ON f.id = t.file_id
LEFT JOIN frontmatter fm_rating ON f.id = fm_rating.file_id AND fm_rating.key = 'rating'
LEFT JOIN frontmatter fm_title ON f.id = fm_title.file_id AND fm_title.key = 'title'
WHERE t.tag IN (
    SELECT TRIM(value) FROM (
        SELECT rq.required_tags as tags
        UNION ALL
        SELECT REPLACE(rq.required_tags, ',', ' ') as tags
    ), json_each('["' || REPLACE(tags, ',', '","') || '"]')
)
GROUP BY rq.question
ORDER BY relevant_papers DESC;
```

This literature review workflow helps you maintain a systematic approach to academic research, track your progress, and identify patterns and gaps in the literature you're reviewing.