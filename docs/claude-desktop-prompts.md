# Optimized Claude Desktop Prompts for mdquery MCP Integration

This document contains tested, optimized prompts for using mdquery with Claude Desktop to analyze tagged content in Obsidian vaults and generate comprehensive topic-based reports.

## Quick Start Prompts

### 1. Initial Comprehensive Analysis

```markdown
I need a comprehensive topic-based analysis of my research notes. Please analyze documents tagged with [YOUR_TAG] and create a detailed guidebook organized by topics.

**Requirements:**
- No summaries or fluff - I want actionable content only
- Complete tutorial steps - Include all steps for recreation if tutorials found
- Topic organization - Break content into logical topic groups
- Comprehensive coverage - This is for deep research, not quick overview

**Analysis Steps:**
1. First, use `comprehensive_tag_analysis` with:
   - Tag pattern: "[YOUR_TAG]"
   - Grouping strategy: "semantic"
   - Remove fluff: true
   - Include actionable: true
   - Include theoretical: true

2. Then extract and organize:
   - Actionable items, procedures, and methods
   - Complete tutorials with step-by-step instructions
   - Relevant examples and case studies
   - Important references and resources

3. Create structured guidebook with:
   - Topic-based sections
   - Actionable subsections
   - Complete tutorial reproductions
   - Reference materials and links

**My tag pattern**: [REPLACE_WITH_YOUR_TAG]

Please start by analyzing my tagged content and proceed with detailed extraction and organization.
```

### 2. Database Schema Discovery

```markdown
Please help me understand what data is available in my notes database. Use the `get_schema` tool to show me:

1. All available tables and their structure
2. Sample data from the main tables
3. Available search fields and capabilities

Then suggest 3-5 useful queries I can run to explore my content.
```

### 3. Tag Landscape Overview

```markdown
I want to understand the tag structure in my notes. Please:

1. Use `query_markdown` to show me the most popular tags:
   ```sql
   SELECT tag, COUNT(*) as usage_count 
   FROM tags 
   GROUP BY tag 
   ORDER BY usage_count DESC 
   LIMIT 20
   ```

2. Use `comprehensive_tag_analysis` with:
   - Tag patterns: "*" (all tags)
   - Grouping strategy: "tag-hierarchy"
   - Include relationships: true

3. Recommend which tags would be most valuable for comprehensive analysis based on their usage patterns and content quality.
```

## Deep Dive Analysis Prompts

### 4. Topic-Specific Deep Dive

```markdown
Based on my initial analysis, I want to dive deeper into [SPECIFIC_TOPIC]. Please:

1. Find all related content using `query_markdown`:
   ```sql
   SELECT path, title, tags, word_count 
   FROM files 
   WHERE tags LIKE '%[TOPIC_TAG]%' 
   ORDER BY word_count DESC
   ```

2. Use `fuzzy_search` to find semantically related content:
   - Search text: "[TOPIC_DESCRIPTION]"
   - Threshold: 0.7
   - Max results: 20
   - Fields: "content,title"

3. Extract and compile:
   - Step-by-step procedures and tutorials
   - Best practices and methodologies
   - Actionable resources and tools
   - Code examples or commands
   - Implementation guidelines

4. Create a focused sub-guidebook for this topic with practical implementation focus.

**Topic**: [REPLACE_WITH_TOPIC]
**Related tags**: [REPLACE_WITH_RELATED_TAGS]
```

### 5. Tutorial and How-To Extraction

```markdown
I want to extract all actionable tutorials and how-to guides from my notes. Please:

1. Use `comprehensive_tag_analysis` to find tutorial content:
   - Tag patterns: "tutorial,guide,howto,step-by-step"
   - Remove fluff: true
   - Include actionable: true

2. Use `fuzzy_search` for tutorial-style content:
   - Search terms: "tutorial step-by-step how to guide instructions"
   - Threshold: 0.6
   - Fields: "content,title"

3. For each tutorial found, extract:
   - Complete step-by-step procedures
   - Prerequisites and requirements
   - Code examples or commands
   - Expected outcomes and validation steps
   - Troubleshooting tips if available

4. Organize into actionable, standalone guides I can follow without referring to original sources.

Format each tutorial with clear headings, numbered steps, and all necessary details for successful implementation.
```

### 6. Research Trend Analysis

```markdown
I want to understand the evolution and trends in my research. Please:

1. Use `query_markdown` to analyze content by time periods:
   ```sql
   SELECT 
     strftime('%Y-%m', created_date) as month,
     COUNT(*) as files_created,
     AVG(word_count) as avg_words
   FROM files 
   WHERE tags LIKE '%[YOUR_TAG]%'
   GROUP BY month 
   ORDER BY month DESC
   ```

2. Use `comprehensive_tag_analysis` with temporal grouping:
   - Tag patterns: "[YOUR_TAG]"
   - Grouping strategy: "temporal"
   - Include relationships: true

3. Identify:
   - Knowledge gaps that need filling
   - Emerging themes and patterns
   - Most productive research periods
   - Topic evolution over time
   - Interconnections between different research areas

4. Provide recommendations for:
   - Areas needing more research
   - Connections to explore further
   - Consolidation opportunities

**Tag pattern**: [REPLACE_WITH_YOUR_TAG]
```

## Specialized Analysis Prompts

### 7. Cross-Reference and Connection Analysis

```markdown
I want to understand how different topics in my research connect to each other. Please:

1. Use `comprehensive_tag_analysis` with relationship analysis:
   - Tag patterns: "[PRIMARY_TAG],[SECONDARY_TAG],[TERTIARY_TAG]"
   - Grouping strategy: "semantic"
   - Include relationships: true

2. Use `query_markdown` to find files with multiple relevant tags:
   ```sql
   SELECT f.path, f.title, GROUP_CONCAT(t.tag) as all_tags
   FROM files f
   JOIN tags t ON f.id = t.file_id
   WHERE t.tag IN ('[TAG1]', '[TAG2]', '[TAG3]')
   GROUP BY f.id
   HAVING COUNT(DISTINCT t.tag) > 1
   ORDER BY COUNT(DISTINCT t.tag) DESC
   ```

3. Identify:
   - Bridge concepts that connect different topics
   - Potential synthesis opportunities
   - Knowledge integration points
   - Cross-disciplinary connections

4. Create a concept map showing how different research areas interconnect and suggest synthesis projects.

**Primary tags**: [REPLACE_WITH_YOUR_TAGS]
```

### 8. Quality and Gap Analysis

```markdown
I want to assess the quality and completeness of my research notes. Please:

1. Use `comprehensive_tag_analysis` with quality filtering:
   - Tag patterns: "[YOUR_TAG]"
   - Remove fluff: true
   - Min content quality: 0.5

2. Use `query_markdown` to identify different content types:
   ```sql
   SELECT 
     CASE 
       WHEN word_count < 100 THEN 'Brief Notes'
       WHEN word_count < 500 THEN 'Medium Articles'
       ELSE 'Comprehensive Documents'
     END as content_type,
     COUNT(*) as count,
     AVG(word_count) as avg_words
   FROM files 
   WHERE tags LIKE '%[YOUR_TAG]%'
   GROUP BY content_type
   ```

3. Analyze and report:
   - High-quality, actionable content vs. lower-quality notes
   - Content depth distribution
   - Topics with insufficient coverage
   - Areas with conflicting or incomplete information
   - Missing procedural details in tutorials

4. Provide recommendations for:
   - Notes that need expansion or revision
   - Research areas requiring more depth
   - Consolidation opportunities
   - Quality improvement strategies

**Tag pattern**: [REPLACE_WITH_YOUR_TAG]
```

## Workflow Optimization Prompts

### 9. Create Research Bibliography

```markdown
Help me create a comprehensive bibliography and resource list from my research notes. Please:

1. Use `query_markdown` to find all referenced sources:
   ```sql
   SELECT DISTINCT path, title 
   FROM files 
   WHERE (content LIKE '%http%' OR content LIKE '%doi:%' OR content LIKE '%ISBN%')
   AND tags LIKE '%[YOUR_TAG]%'
   ```

2. Use `fuzzy_search` to find citation and reference patterns:
   - Search text: "citation reference source author published"
   - Threshold: 0.5
   - Fields: "content"

3. Extract and organize:
   - Web URLs and online resources
   - Academic papers and DOIs
   - Books and ISBN references
   - Tools and software mentioned
   - Datasets and repositories

4. Create a structured bibliography with:
   - Categorized resource lists
   - Annotation for each resource
   - Relevance to specific topics
   - Quality assessment

**Tag pattern**: [REPLACE_WITH_YOUR_TAG]
```

### 10. Generate Action Items and Next Steps

```markdown
Based on my research notes, help me identify concrete next steps and action items. Please:

1. Use `comprehensive_tag_analysis` focusing on actionable content:
   - Tag patterns: "[YOUR_TAG]"
   - Include actionable: true
   - Include theoretical: false
   - Remove fluff: true

2. Use `fuzzy_search` to find action-oriented content:
   - Search text: "next steps action items todo implement try test experiment"
   - Threshold: 0.6
   - Fields: "content"

3. Extract and prioritize:
   - Specific actions to take
   - Experiments to conduct
   - Tools to try or learn
   - Connections to make
   - Skills to develop
   - Research gaps to fill

4. Organize into:
   - Immediate actions (can be done this week)
   - Short-term goals (1-4 weeks)
   - Medium-term projects (1-3 months)
   - Long-term objectives (3+ months)

5. For each action item, include:
   - Specific steps to take
   - Resources needed
   - Expected outcomes
   - Success criteria

**Tag pattern**: [REPLACE_WITH_YOUR_TAG]
```

## Testing and Validation Prompts

### 11. System Health Check

```markdown
Please help me verify that mdquery is working correctly with my notes:

1. Use `get_schema` to show database structure and row counts
2. Use `query_markdown` to test basic functionality:
   ```sql
   SELECT COUNT(*) as total_files, 
          COUNT(DISTINCT tag) as unique_tags,
          AVG(word_count) as avg_words
   FROM files f
   LEFT JOIN tags t ON f.id = t.file_id
   ```
3. Test `fuzzy_search` with a simple query related to your domain
4. Run a basic `comprehensive_tag_analysis` on a small tag subset

Report any errors or unexpected results, and confirm all tools are functioning properly.
```

### 12. Performance Benchmark

```markdown
Help me understand the performance characteristics of my notes database:

1. Use `query_markdown` to analyze database size and distribution:
   ```sql
   SELECT 
     COUNT(*) as total_files,
     SUM(word_count) as total_words,
     MIN(created_date) as oldest_note,
     MAX(created_date) as newest_note,
     COUNT(DISTINCT tag) as unique_tags
   FROM files f
   LEFT JOIN tags t ON f.id = t.file_id
   ```

2. Test response times for different operations:
   - Simple queries
   - Complex tag analysis
   - Fuzzy search with different thresholds

3. Recommend optimizations based on my usage patterns and database size.
```

## Customization Guidelines

### Adapting Prompts for Your Use Case

1. **Replace Placeholder Tags**: Change `[YOUR_TAG]` to your actual tags
2. **Adjust Quality Thresholds**: Modify `min_content_quality` based on your content
3. **Customize Search Terms**: Update fuzzy search terms for your domain
4. **Modify Grouping Strategies**: Choose between "semantic", "tag-hierarchy", or "temporal"
5. **Set Appropriate Limits**: Adjust result limits based on your collection size

### Tag Pattern Examples

- **Wildcards**: "ai/*" (matches ai/ml, ai/nlp, etc.)
- **Multiple tags**: "research,ai,machine-learning"  
- **Hierarchical**: "projects/current" (matches nested tags)
- **Broad matching**: "*learning*" (matches any tag containing "learning")

### Quality Threshold Guidelines

- **0.3**: Include most content, filter obvious fluff
- **0.5**: Medium quality threshold, good balance
- **0.7**: High quality only, very selective
- **0.9**: Exceptional content only

These prompts are optimized for comprehensive research analysis and actionable insight extraction. Adapt them to your specific domain and tagging structure for best results.