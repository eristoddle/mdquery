# Writing Analytics and Productivity

This example demonstrates how to use mdquery to analyze your writing patterns, track productivity, and identify trends in your content creation.

## Scenario

You're a content creator who writes across multiple formats:
- Blog posts and articles
- Technical documentation
- Personal journal entries
- Project notes and documentation

Goals:
- Track writing productivity and patterns
- Analyze content quality and engagement
- Identify peak writing times and conditions
- Optimize writing workflow and habits

## Writing Data Structure

```
writing/
├── blog/
│   ├── 2024-01-15-productivity-systems.md
│   ├── 2024-02-03-remote-work-tips.md
│   └── 2024-03-10-ai-writing-tools.md
├── documentation/
│   ├── api-reference-guide.md
│   ├── user-onboarding-flow.md
│   └── troubleshooting-common-issues.md
├── journal/
│   ├── 2024-01-daily-reflections.md
│   ├── 2024-02-learning-notes.md
│   └── 2024-03-project-insights.md
└── projects/
    ├── website-redesign-notes.md
    ├── mobile-app-requirements.md
    └── data-pipeline-documentation.md
```

## Frontmatter Structure

Each writing piece includes detailed metadata for analytics:

```yaml
---
title: "Building Better Productivity Systems"
date: 2024-01-15
time_started: "09:30"
time_finished: "11:45"
writing_session_duration: 135
word_count: 1850
character_count: 11250
writing_location: "home-office"
writing_tool: "obsidian"
content_type: "blog-post"
category: "productivity"
tags: [productivity, systems, habits, workflow]
difficulty_level: 3
energy_level: 8
focus_quality: 9
interruptions: 2
research_time: 45
editing_time: 30
satisfaction_rating: 8
target_audience: "professionals"
writing_goal: "educate"
publish_status: "published"
engagement_score: 7.5
social_shares: 23
comments: 8
page_views: 450
---
```

## Key Analytics Queries

### 1. Writing Productivity Dashboard

```sql
SELECT
    DATE(fm_date.value) as writing_date,
    COUNT(*) as pieces_written,
    SUM(CAST(fm_word_count.value AS INTEGER)) as total_words,
    AVG(CAST(fm_duration.value AS INTEGER)) as avg_session_duration,
    AVG(CAST(fm_satisfaction.value AS INTEGER)) as avg_satisfaction,
    SUM(CAST(fm_duration.value AS INTEGER)) as total_writing_time
FROM files f
JOIN frontmatter fm_date ON f.id = fm_date.file_id AND fm_date.key = 'date'
LEFT JOIN frontmatter fm_word_count ON f.id = fm_word_count.file_id AND fm_word_count.key = 'word_count'
LEFT JOIN frontmatter fm_duration ON f.id = fm_duration.file_id AND fm_duration.key = 'writing_session_duration'
LEFT JOIN frontmatter fm_satisfaction ON f.id = fm_satisfaction.file_id AND fm_satisfaction.key = 'satisfaction_rating'
WHERE f.directory LIKE '%writing%'
  AND fm_date.value >= '2024-01-01'
GROUP BY DATE(fm_date.value)
ORDER BY writing_date DESC;
```

### 2. Writing Patterns by Time of Day

```sql
SELECT
    CASE
        WHEN CAST(substr(fm_time_started.value, 1, 2) AS INTEGER) BETWEEN 6 AND 11 THEN 'Morning (6-11 AM)'
        WHEN CAST(substr(fm_time_started.value, 1, 2) AS INTEGER) BETWEEN 12 AND 17 THEN 'Afternoon (12-5 PM)'
        WHEN CAST(substr(fm_time_started.value, 1, 2) AS INTEGER) BETWEEN 18 AND 21 THEN 'Evening (6-9 PM)'
        ELSE 'Night (10 PM-5 AM)'
    END as time_period,
    COUNT(*) as writing_sessions,
    AVG(CAST(fm_word_count.value AS INTEGER)) as avg_words_per_session,
    AVG(CAST(fm_focus_quality.value AS INTEGER)) as avg_focus_quality,
    AVG(CAST(fm_satisfaction.value AS INTEGER)) as avg_satisfaction,
    AVG(CAST(fm_duration.value AS INTEGER)) as avg_duration_minutes
FROM files f
JOIN frontmatter fm_time_started ON f.id = fm_time_started.file_id AND fm_time_started.key = 'time_started'
LEFT JOIN frontmatter fm_word_count ON f.id = fm_word_count.file_id AND fm_word_count.key = 'word_count'
LEFT JOIN frontmatter fm_focus_quality ON f.id = fm_focus_quality.file_id AND fm_focus_quality.key = 'focus_quality'
LEFT JOIN frontmatter fm_satisfaction ON f.id = fm_satisfaction.file_id AND fm_satisfaction.key = 'satisfaction_rating'
LEFT JOIN frontmatter fm_duration ON f.id = fm_duration.file_id AND fm_duration.key = 'writing_session_duration'
WHERE f.directory LIKE '%writing%'
GROUP BY time_period
ORDER BY avg_satisfaction DESC;
```

### 3. Content Performance Analysis

```sql
SELECT
    fm_content_type.value as content_type,
    COUNT(*) as pieces_count,
    AVG(CAST(fm_word_count.value AS INTEGER)) as avg_word_count,
    AVG(CAST(fm_engagement.value AS FLOAT)) as avg_engagement_score,
    AVG(CAST(fm_page_views.value AS INTEGER)) as avg_page_views,
    AVG(CAST(fm_social_shares.value AS INTEGER)) as avg_social_shares,
    AVG(CAST(fm_satisfaction.value AS INTEGER)) as avg_writer_satisfaction
FROM files f
JOIN frontmatter fm_content_type ON f.id = fm_content_type.file_id AND fm_content_type.key = 'content_type'
LEFT JOIN frontmatter fm_word_count ON f.id = fm_word_count.file_id AND fm_word_count.key = 'word_count'
LEFT JOIN frontmatter fm_engagement ON f.id = fm_engagement.file_id AND fm_engagement.key = 'engagement_score'
LEFT JOIN frontmatter fm_page_views ON f.id = fm_page_views.file_id AND fm_page_views.key = 'page_views'
LEFT JOIN frontmatter fm_social_shares ON f.id = fm_social_shares.file_id AND fm_social_shares.key = 'social_shares'
LEFT JOIN frontmatter fm_satisfaction ON f.id = fm_satisfaction.file_id AND fm_satisfaction.key = 'satisfaction_rating'
WHERE f.directory LIKE '%writing%'
GROUP BY fm_content_type.value
ORDER BY avg_engagement_score DESC;
```

### 4. Writing Environment Impact

```sql
SELECT
    fm_location.value as writing_location,
    fm_tool.value as writing_tool,
    COUNT(*) as sessions,
    AVG(CAST(fm_word_count.value AS INTEGER)) as avg_words,
    AVG(CAST(fm_focus_quality.value AS INTEGER)) as avg_focus,
    AVG(CAST(fm_interruptions.value AS INTEGER)) as avg_interruptions,
    AVG(CAST(fm_satisfaction.value AS INTEGER)) as avg_satisfaction,
    AVG(CAST(fm_duration.value AS INTEGER)) as avg_duration
FROM files f
LEFT JOIN frontmatter fm_location ON f.id = fm_location.file_id AND fm_location.key = 'writing_location'
LEFT JOIN frontmatter fm_tool ON f.id = fm_tool.file_id AND fm_tool.key = 'writing_tool'
LEFT JOIN frontmatter fm_word_count ON f.id = fm_word_count.file_id AND fm_word_count.key = 'word_count'
LEFT JOIN frontmatter fm_focus_quality ON f.id = fm_focus_quality.file_id AND fm_focus_quality.key = 'focus_quality'
LEFT JOIN frontmatter fm_interruptions ON f.id = fm_interruptions.file_id AND fm_interruptions.key = 'interruptions'
LEFT JOIN frontmatter fm_satisfaction ON f.id = fm_satisfaction.file_id AND fm_satisfaction.key = 'satisfaction_rating'
LEFT JOIN frontmatter fm_duration ON f.id = fm_duration.file_id AND fm_duration.key = 'writing_session_duration'
WHERE f.directory LIKE '%writing%'
GROUP BY fm_location.value, fm_tool.value
HAVING sessions >= 5
ORDER BY avg_satisfaction DESC, avg_focus DESC;
```

### 5. Writing Velocity Trends

```sql
-- Track writing speed over time
SELECT
    strftime('%Y-%m', fm_date.value) as month,
    COUNT(*) as pieces_written,
    SUM(CAST(fm_word_count.value AS INTEGER)) as total_words,
    AVG(CAST(fm_word_count.value AS INTEGER)) as avg_words_per_piece,
    SUM(CAST(fm_duration.value AS INTEGER)) as total_minutes,
    ROUND(SUM(CAST(fm_word_count.value AS INTEGER)) * 1.0 / SUM(CAST(fm_duration.value AS INTEGER)), 2) as words_per_minute,
    AVG(CAST(fm_satisfaction.value AS INTEGER)) as avg_satisfaction
FROM files f
JOIN frontmatter fm_date ON f.id = fm_date.file_id AND fm_date.key = 'date'
LEFT JOIN frontmatter fm_word_count ON f.id = fm_word_count.file_id AND fm_word_count.key = 'word_count'
LEFT JOIN frontmatter fm_duration ON f.id = fm_duration.file_id AND fm_duration.key = 'writing_session_duration'
LEFT JOIN frontmatter fm_satisfaction ON f.id = fm_satisfaction.file_id AND fm_satisfaction.key = 'satisfaction_rating'
WHERE f.directory LIKE '%writing%'
  AND fm_date.value >= '2023-01-01'
GROUP BY strftime('%Y-%m', fm_date.value)
ORDER BY month;
```

### 6. Energy and Focus Correlation

```sql
-- Analyze relationship between energy, focus, and output
SELECT
    CAST(fm_energy.value AS INTEGER) as energy_level,
    CAST(fm_focus.value AS INTEGER) as focus_quality,
    COUNT(*) as sessions,
    AVG(CAST(fm_word_count.value AS INTEGER)) as avg_words,
    AVG(CAST(fm_satisfaction.value AS INTEGER)) as avg_satisfaction,
    AVG(CAST(fm_duration.value AS INTEGER)) as avg_duration
FROM files f
JOIN frontmatter fm_energy ON f.id = fm_energy.file_id AND fm_energy.key = 'energy_level'
JOIN frontmatter fm_focus ON f.id = fm_focus.file_id AND fm_focus.key = 'focus_quality'
LEFT JOIN frontmatter fm_word_count ON f.id = fm_word_count.file_id AND fm_word_count.key = 'word_count'
LEFT JOIN frontmatter fm_satisfaction ON f.id = fm_satisfaction.file_id AND fm_satisfaction.key = 'satisfaction_rating'
LEFT JOIN frontmatter fm_duration ON f.id = fm_duration.file_id AND fm_duration.key = 'writing_session_duration'
WHERE f.directory LIKE '%writing%'
GROUP BY CAST(fm_energy.value AS INTEGER), CAST(fm_focus.value AS INTEGER)
HAVING sessions >= 3
ORDER BY energy_level DESC, focus_quality DESC;
```

## Advanced Analytics

### Writing Streak Analysis

```sql
-- Calculate writing streaks
WITH daily_writing AS (
    SELECT
        DATE(fm_date.value) as writing_date,
        COUNT(*) as pieces_written,
        SUM(CAST(fm_word_count.value AS INTEGER)) as daily_words
    FROM files f
    JOIN frontmatter fm_date ON f.id = fm_date.file_id AND fm_date.key = 'date'
    LEFT JOIN frontmatter fm_word_count ON f.id = fm_word_count.file_id AND fm_word_count.key = 'word_count'
    WHERE f.directory LIKE '%writing%'
      AND fm_date.value >= '2024-01-01'
    GROUP BY DATE(fm_date.value)
),
streak_data AS (
    SELECT
        writing_date,
        pieces_written,
        daily_words,
        ROW_NUMBER() OVER (ORDER BY writing_date) -
        ROW_NUMBER() OVER (PARTITION BY pieces_written > 0 ORDER BY writing_date) as streak_group
    FROM daily_writing
)
SELECT
    MIN(writing_date) as streak_start,
    MAX(writing_date) as streak_end,
    COUNT(*) as streak_length,
    SUM(daily_words) as total_words_in_streak,
    AVG(daily_words) as avg_daily_words
FROM streak_data
WHERE pieces_written > 0
GROUP BY streak_group
HAVING streak_length >= 3
ORDER BY streak_length DESC;
```

### Content Quality Prediction

```sql
-- Identify factors that correlate with high-performing content
SELECT
    CASE
        WHEN CAST(fm_engagement.value AS FLOAT) >= 8 THEN 'High Engagement'
        WHEN CAST(fm_engagement.value AS FLOAT) >= 6 THEN 'Medium Engagement'
        ELSE 'Low Engagement'
    END as engagement_tier,
    COUNT(*) as pieces_count,
    AVG(CAST(fm_word_count.value AS INTEGER)) as avg_word_count,
    AVG(CAST(fm_research_time.value AS INTEGER)) as avg_research_time,
    AVG(CAST(fm_editing_time.value AS INTEGER)) as avg_editing_time,
    AVG(CAST(fm_difficulty.value AS INTEGER)) as avg_difficulty,
    AVG(CAST(fm_focus_quality.value AS INTEGER)) as avg_focus_quality,
    AVG(CAST(fm_satisfaction.value AS INTEGER)) as avg_writer_satisfaction
FROM files f
JOIN frontmatter fm_engagement ON f.id = fm_engagement.file_id AND fm_engagement.key = 'engagement_score'
LEFT JOIN frontmatter fm_word_count ON f.id = fm_word_count.file_id AND fm_word_count.key = 'word_count'
LEFT JOIN frontmatter fm_research_time ON f.id = fm_research_time.file_id AND fm_research_time.key = 'research_time'
LEFT JOIN frontmatter fm_editing_time ON f.id = fm_editing_time.file_id AND fm_editing_time.key = 'editing_time'
LEFT JOIN frontmatter fm_difficulty ON f.id = fm_difficulty.file_id AND fm_difficulty.key = 'difficulty_level'
LEFT JOIN frontmatter fm_focus_quality ON f.id = fm_focus_quality.file_id AND fm_focus_quality.key = 'focus_quality'
LEFT JOIN frontmatter fm_satisfaction ON f.id = fm_satisfaction.file_id AND fm_satisfaction.key = 'satisfaction_rating'
WHERE f.directory LIKE '%writing%'
GROUP BY engagement_tier
ORDER BY AVG(CAST(fm_engagement.value AS FLOAT)) DESC;
```

### Seasonal Writing Patterns

```sql
-- Analyze writing patterns by season and day of week
SELECT
    CASE
        WHEN CAST(strftime('%m', fm_date.value) AS INTEGER) IN (12, 1, 2) THEN 'Winter'
        WHEN CAST(strftime('%m', fm_date.value) AS INTEGER) IN (3, 4, 5) THEN 'Spring'
        WHEN CAST(strftime('%m', fm_date.value) AS INTEGER) IN (6, 7, 8) THEN 'Summer'
        ELSE 'Fall'
    END as season,
    CASE strftime('%w', fm_date.value)
        WHEN '0' THEN 'Sunday'
        WHEN '1' THEN 'Monday'
        WHEN '2' THEN 'Tuesday'
        WHEN '3' THEN 'Wednesday'
        WHEN '4' THEN 'Thursday'
        WHEN '5' THEN 'Friday'
        WHEN '6' THEN 'Saturday'
    END as day_of_week,
    COUNT(*) as writing_sessions,
    AVG(CAST(fm_word_count.value AS INTEGER)) as avg_words,
    AVG(CAST(fm_satisfaction.value AS INTEGER)) as avg_satisfaction,
    AVG(CAST(fm_focus_quality.value AS INTEGER)) as avg_focus
FROM files f
JOIN frontmatter fm_date ON f.id = fm_date.file_id AND fm_date.key = 'date'
LEFT JOIN frontmatter fm_word_count ON f.id = fm_word_count.file_id AND fm_word_count.key = 'word_count'
LEFT JOIN frontmatter fm_satisfaction ON f.id = fm_satisfaction.file_id AND fm_satisfaction.key = 'satisfaction_rating'
LEFT JOIN frontmatter fm_focus_quality ON f.id = fm_focus_quality.file_id AND fm_focus_quality.key = 'focus_quality'
WHERE f.directory LIKE '%writing%'
GROUP BY season, day_of_week
ORDER BY season,
         CASE day_of_week
             WHEN 'Monday' THEN 1
             WHEN 'Tuesday' THEN 2
             WHEN 'Wednesday' THEN 3
             WHEN 'Thursday' THEN 4
             WHEN 'Friday' THEN 5
             WHEN 'Saturday' THEN 6
             WHEN 'Sunday' THEN 7
         END;
```

## Productivity Insights

### Weekly Writing Report

```sql
-- Generate weekly productivity report
SELECT
    strftime('%Y-W%W', fm_date.value) as week,
    COUNT(*) as pieces_written,
    SUM(CAST(fm_word_count.value AS INTEGER)) as total_words,
    AVG(CAST(fm_word_count.value AS INTEGER)) as avg_words_per_piece,
    SUM(CAST(fm_duration.value AS INTEGER)) as total_writing_minutes,
    AVG(CAST(fm_satisfaction.value AS INTEGER)) as avg_satisfaction,
    COUNT(DISTINCT DATE(fm_date.value)) as writing_days,
    ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT DATE(fm_date.value)), 2) as pieces_per_writing_day
FROM files f
JOIN frontmatter fm_date ON f.id = fm_date.file_id AND fm_date.key = 'date'
LEFT JOIN frontmatter fm_word_count ON f.id = fm_word_count.file_id AND fm_word_count.key = 'word_count'
LEFT JOIN frontmatter fm_duration ON f.id = fm_duration.file_id AND fm_duration.key = 'writing_session_duration'
LEFT JOIN frontmatter fm_satisfaction ON f.id = fm_satisfaction.file_id AND fm_satisfaction.key = 'satisfaction_rating'
WHERE f.directory LIKE '%writing%'
  AND fm_date.value >= date('now', '-8 weeks')
GROUP BY strftime('%Y-W%W', fm_date.value)
ORDER BY week DESC;
```

### Goal Tracking

```sql
-- Track progress toward writing goals
SELECT
    'Daily Word Goal (500 words)' as goal_type,
    COUNT(CASE WHEN CAST(fm_word_count.value AS INTEGER) >= 500 THEN 1 END) as days_achieved,
    COUNT(*) as total_writing_days,
    ROUND(COUNT(CASE WHEN CAST(fm_word_count.value AS INTEGER) >= 500 THEN 1 END) * 100.0 / COUNT(*), 1) as achievement_percentage
FROM files f
JOIN frontmatter fm_date ON f.id = fm_date.file_id AND fm_date.key = 'date'
LEFT JOIN frontmatter fm_word_count ON f.id = fm_word_count.file_id AND fm_word_count.key = 'word_count'
WHERE f.directory LIKE '%writing%'
  AND fm_date.value >= date('now', '-30 days')

UNION ALL

SELECT
    'Weekly Piece Goal (3 pieces)' as goal_type,
    COUNT(CASE WHEN weekly_pieces >= 3 THEN 1 END) as weeks_achieved,
    COUNT(*) as total_weeks,
    ROUND(COUNT(CASE WHEN weekly_pieces >= 3 THEN 1 END) * 100.0 / COUNT(*), 1) as achievement_percentage
FROM (
    SELECT
        strftime('%Y-W%W', fm_date.value) as week,
        COUNT(*) as weekly_pieces
    FROM files f
    JOIN frontmatter fm_date ON f.id = fm_date.file_id AND fm_date.key = 'date'
    WHERE f.directory LIKE '%writing%'
      AND fm_date.value >= date('now', '-12 weeks')
    GROUP BY strftime('%Y-W%W', fm_date.value)
);
```

## Best Practices

### Data Collection
- Track writing sessions consistently
- Include subjective metrics (satisfaction, focus)
- Record environmental factors
- Monitor both process and outcome metrics

### Analysis Frequency
- Daily: Quick productivity check
- Weekly: Detailed performance review
- Monthly: Pattern identification and goal adjustment
- Quarterly: Long-term trend analysis

### Optimization Actions
- Identify peak performance conditions
- Eliminate or minimize negative factors
- Set realistic, data-driven goals
- Experiment with different approaches

### Metric Selection
- Focus on metrics that drive behavior change
- Balance quantity and quality measures
- Include both leading and lagging indicators
- Track what you can control

This writing analytics system provides data-driven insights to optimize your writing productivity, improve content quality, and maintain consistent creative output.