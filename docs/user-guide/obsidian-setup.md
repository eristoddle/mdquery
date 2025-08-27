# Obsidian Setup Guide for mdquery

A complete guide to integrating mdquery with your Obsidian vault for AI-powered note analysis and querying.

## Overview

mdquery is perfectly designed for Obsidian users, providing powerful SQL-like querying capabilities for your markdown notes while preserving all Obsidian-specific features like wikilinks, tags, and frontmatter.

### Key Obsidian Features Supported

✅ **Wikilinks**: `[[Note Name]]` and `[[Note Name|Display Text]]`
✅ **Nested Tags**: `#projects/ai/research` and `#status/in-progress`
✅ **YAML Frontmatter**: All properties and metadata
✅ **Dataview Fields**: Inline fields like `field:: value`
✅ **Folder Structure**: Multi-level organization
✅ **Aliases**: Note aliases from frontmatter
✅ **Daily Notes**: Date-based note organization
✅ **Templates**: Template metadata preservation

## Quick Start (5 Minutes)

### Step 1: Install mdquery

```bash
# Install mdquery
pip install mdquery

# Verify installation
python -c "import mdquery; print('mdquery installed successfully!')"
```

### Step 2: Find Your Obsidian Vault Path

**Method 1: Through Obsidian**
1. Open Obsidian
2. Go to Settings → About
3. Copy the "Vault folder" path

**Method 2: Typical Locations**
```bash
# macOS
~/Documents/Obsidian Vault
~/Obsidian/VaultName

# Windows
C:\Users\YourName\Documents\Obsidian Vault
C:\Users\YourName\OneDrive\Obsidian\VaultName

# Linux
~/Documents/Obsidian
~/Obsidian/VaultName
```

### Step 3: Configure Claude Desktop

Create or edit `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "obsidian-notes": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/Users/YourName/Documents/Obsidian Vault"
      }
    }
  }
}
```

**🔧 Replace `/Users/YourName/Documents/Obsidian Vault` with your actual vault path**

### Step 4: Restart Claude Desktop

Close and reopen Claude Desktop completely.

### Step 5: Test the Integration

Start a conversation with Claude:

```
"I'd like to analyze my Obsidian vault. Can you show me what types of notes I have and find some interesting patterns?"
```

Claude will automatically:
1. Index your Obsidian vault
2. Analyze your note structure
3. Show you patterns in your knowledge base

**🎉 You're done!** Continue reading for advanced configurations and Obsidian-specific workflows.

## Configuration Options

### Minimal Configuration (Recommended)

Perfect for most Obsidian users:

```json
{
  "mcpServers": {
    "obsidian": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/path/to/your/obsidian/vault"
      }
    }
  }
}
```

### Optimized Configuration

For larger vaults (1000+ notes) or better performance:

```json
{
  "mcpServers": {
    "obsidian": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/path/to/your/obsidian/vault",
        "MDQUERY_PERFORMANCE_MODE": "high",
        "MDQUERY_AUTO_OPTIMIZE": "true",
        "MDQUERY_CACHE_TTL": "120"
      }
    }
  }
}
```

### Multiple Vaults Configuration

If you have multiple Obsidian vaults:

```json
{
  "mcpServers": {
    "obsidian-personal": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/Users/YourName/Obsidian/Personal",
        "MDQUERY_DB_PATH": "/Users/YourName/.mdquery/personal.db"
      }
    },
    "obsidian-work": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/Users/YourName/Obsidian/Work",
        "MDQUERY_DB_PATH": "/Users/YourName/.mdquery/work.db"
      }
    }
  }
}
```

### Obsidian + iCloud/OneDrive Configuration

For cloud-synced vaults:

```json
{
  "mcpServers": {
    "obsidian": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/Users/YourName/Library/Mobile Documents/iCloud~md~obsidian/Documents/VaultName",
        "MDQUERY_AUTO_OPTIMIZE": "true",
        "MDQUERY_LAZY_LOADING": "true"
      }
    }
  }
}
```

## Obsidian-Specific Workflows

### 1. Daily Notes Analysis

Perfect for reviewing your daily notes and finding patterns:

```
"Analyze my daily notes from the last month. What are the main themes and topics I've been working on?"
```

**What Claude will do:**
- Find all daily notes based on date patterns
- Extract key topics and themes
- Identify recurring meetings, projects, or concerns
- Suggest areas that might need more attention

### 2. Tag Hierarchy Analysis

Obsidian's nested tags are perfectly supported:

```
"Show me my tag hierarchy and find which nested tags I use most frequently. Are there any tags that should be reorganized?"
```

**Example tag analysis:**
- `#projects/ai/research` (15 notes)
- `#projects/ai/implementation` (8 notes)
- `#projects/web/frontend` (12 notes)
- `#status/in-progress` (25 notes)

### 3. Wikilink Network Analysis

Analyze your note connections:

```
"Analyze my wikilink network. Which notes are most connected? Are there any notes that should be linked but aren't?"
```

**Claude will:**
- Map your wikilink relationships
- Identify hub notes (most connected)
- Find orphaned notes (no connections)
- Suggest potential new connections

### 4. Research Project Organization

Perfect for academic or research vaults:

```
"I'm working on a research project about machine learning. Help me organize all related notes and find gaps in my research."
```

**Workflow includes:**
- Finding all ML-related notes by tags and content
- Analyzing research progression and themes
- Identifying missing connections between concepts
- Suggesting literature review organization

### 5. Content Quality Audit

Maintain your vault quality:

```
"Audit my Obsidian vault for content quality. Find notes that might need updating, have broken links, or are incomplete."
```

**Quality checks:**
- Notes with TODO items or incomplete sections
- Broken wikilinks to non-existent notes
- Notes that haven't been updated recently
- Orphaned notes that might need connecting

### 6. Template and Structure Analysis

Optimize your note-taking system:

```
"Analyze my note templates and structure. How consistent am I with frontmatter? What templates work best?"
```

**Analysis includes:**
- Frontmatter consistency across notes
- Most effective note structures
- Template usage patterns
- Suggestions for standardization

## Advanced Obsidian Features

### Dataview Field Support

mdquery automatically recognizes Dataview-style inline fields:

```markdown
# Meeting Notes

Date:: 2024-03-15
Attendees:: [[John Doe]], [[Jane Smith]]
Project:: [[AI Research Project]]
Status:: completed
Next Action:: [[Follow-up Email]]
```

Query these fields naturally:

```
"Find all meeting notes from last month where the status is 'completed' and John Doe was an attendee."
```

### Complex Frontmatter Queries

Obsidian's rich frontmatter is fully supported:

```yaml
---
title: "Research Paper Analysis"
authors: ["Smith, J.", "Doe, A."]
year: 2024
tags: [research, ai, nlp]
status: in-progress
rating: 4.5
project: "[[NLP Research]]"
related: ["[[Previous Study]]", "[[Similar Work]]"]
---
```

Query examples:
```
"Find all research papers from 2024 with a rating above 4.0 that are related to NLP."

"Show me all notes in the 'AI Research' project that are still in-progress."
```

### Folder-Based Organization

mdquery respects your Obsidian folder structure:

```
Vault/
├── Daily Notes/
├── Projects/
│   ├── AI Research/
│   └── Web Development/
├── Resources/
│   ├── Books/
│   ├── Articles/
│   └── Videos/
└── Templates/
```

Query by folder:
```
"Analyze all notes in my 'AI Research' folder and summarize the key findings."

"What resources (books, articles, videos) do I have about machine learning?"
```

## Common Obsidian Use Cases

### Academic Research Vault

**Typical Structure:**
```
Research Vault/
├── Literature Review/
├── Paper Notes/
├── Concepts/
├── Methodology/
├── Daily Progress/
└── References/
```

**Sample Queries:**
```
"Create a literature review summary from all my paper notes, organized by research theme."

"Find gaps in my research where I have concepts but no supporting literature."

"Analyze my daily progress notes to create a research timeline."
```

### Personal Knowledge Management

**Typical Structure:**
```
PKM Vault/
├── Areas/
│   ├── Career/
│   ├── Health/
│   └── Learning/
├── Resources/
├── Projects/
└── Daily/
```

**Sample Queries:**
```
"What are the main themes in my learning notes? What skills am I developing?"

"Analyze my career-related notes and suggest areas for professional development."

"Find connections between my health and productivity notes."
```

### Creative Writing Vault

**Typical Structure:**
```
Writing Vault/
├── Characters/
├── Plots/
├── World Building/
├── Scenes/
├── Research/
└── Daily Writing/
```

**Sample Queries:**
```
"Analyze my character development notes and find inconsistencies or gaps."

"Map the relationships between my characters and plot elements."

"Track my daily writing progress and identify productive patterns."
```

### Business/Consulting Vault

**Typical Structure:**
```
Business Vault/
├── Clients/
├── Projects/
├── Methods/
├── Meeting Notes/
├── Ideas/
└── Templates/
```

**Sample Queries:**
```
"Analyze client feedback patterns across all projects."

"Find successful methods and approaches from past projects."

"Create a knowledge base of best practices from my consulting work."
```

## Obsidian Plugin Compatibility

### Recommended Compatible Plugins

mdquery works well alongside these popular Obsidian plugins:

**✅ Fully Compatible:**
- **Dataview**: mdquery can query Dataview fields and metadata
- **Templater**: Template metadata is preserved and queryable
- **Tag Wrangler**: Enhanced tag management works with mdquery analysis
- **Calendar**: Daily notes integration supported
- **Periodic Notes**: Weekly/monthly notes are properly indexed

**✅ Complementary:**
- **Graph Analysis**: Use mdquery for detailed analysis, Graph view for visualization
- **Outline**: mdquery provides content analysis, Outline shows structure
- **Search**: mdquery offers advanced querying beyond Obsidian's built-in search

**⚠️ Special Considerations:**
- **Excalidraw**: Drawing content not analyzed, but file metadata is indexed
- **Kanban**: Board structure not analyzed, but card content is indexed
- **Advanced Tables**: Table content is indexed as markdown text

### Plugin-Specific Workflows

#### With Dataview Plugin

If you use Dataview queries, mdquery can analyze the data patterns:

```
"Analyze all the task completion data from my Dataview queries. What patterns do you see in my productivity?"
```

#### With Calendar Plugin

Enhanced daily note analysis:

```
"Using my calendar daily notes, show me my most productive days and what factors contribute to good days."
```

#### With Tag Wrangler

Advanced tag analysis and cleanup suggestions:

```
"Analyze my tag usage and suggest a cleaner tag hierarchy. Which tags are redundant or could be merged?"
```

## Performance Optimization for Large Vaults

### For Vaults with 5,000+ Notes

```json
{
  "mcpServers": {
    "obsidian": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/path/to/large/vault",
        "MDQUERY_PERFORMANCE_MODE": "high",
        "MDQUERY_AUTO_OPTIMIZE": "true",
        "MDQUERY_CONCURRENT_QUERIES": "5",
        "MDQUERY_CACHE_TTL": "240",
        "MDQUERY_LAZY_LOADING": "true"
      }
    }
  }
}
```

### For Vaults with 10,000+ Notes

Consider incremental indexing:

```json
{
  "mcpServers": {
    "obsidian": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/path/to/huge/vault",
        "MDQUERY_PERFORMANCE_MODE": "high",
        "MDQUERY_AUTO_OPTIMIZE": "true",
        "MDQUERY_CONCURRENT_QUERIES": "3",
        "MDQUERY_CACHE_TTL": "480",
        "MDQUERY_LAZY_LOADING": "true",
        "MDQUERY_INCREMENTAL_INDEX": "true"
      }
    }
  }
}
```

**Performance Tips:**
- Initial indexing may take 5-10 minutes for very large vaults
- Subsequent updates are much faster (incremental)
- Consider excluding attachment folders if they're large

## Troubleshooting Obsidian-Specific Issues

### Common Problems and Solutions

#### "No notes found" after configuration

**Possible causes:**
1. **Incorrect vault path**: Verify the path points to your .obsidian folder's parent
2. **Permissions**: Ensure the vault directory is readable
3. **Hidden files**: Make sure the vault isn't in a hidden directory

**Solutions:**
```bash
# Check if path exists and is readable
ls -la "/path/to/your/vault"

# Look for .obsidian folder (confirms it's a vault)
ls -la "/path/to/your/vault/.obsidian"
```

#### Wikilinks not being recognized

**Symptoms**: `[[Note Name]]` appears as plain text in queries

**Solutions:**
1. Ensure notes are properly indexed: `"Re-index my vault completely"`
2. Check wikilink format (spaces vs dashes in filenames)
3. Verify note files have .md extension

#### Tags not appearing in analysis

**Symptoms**: Tag queries return empty results

**Common causes:**
- Tags in code blocks or comments (excluded by design)
- Malformed tags (missing # or containing invalid characters)
- Tags in YAML frontmatter but not content

**Solutions:**
```
"Show me all the tags found in my vault and their usage counts."
```

#### Performance issues with large vaults

**Symptoms**: Slow responses or timeouts

**Solutions:**
1. Enable high-performance mode in configuration
2. Use incremental indexing for initial setup
3. Exclude large attachment folders

#### Daily notes not being recognized

**Symptoms**: Daily note queries don't find date-based notes

**Solutions:**
1. Check daily note naming format in Obsidian settings
2. Ensure daily notes are in expected location
3. Verify date format consistency

### Getting Vault Information

Use these queries to understand your vault structure:

```
"Show me the structure of my Obsidian vault - folders, file counts, and organization."

"What file naming conventions do I use? Are there any inconsistencies?"

"Analyze my vault metadata - what frontmatter fields do I use most?"
```

## Migration from Other Tools

### From Roam Research

If migrating from Roam:
- Block references become wikilinks
- Daily notes maintain date structure
- Tags transfer directly
- Graph relationships are preserved through wikilinks

### From Notion

Key differences when migrating from Notion:
- Database properties become frontmatter
- Pages become individual markdown files
- Relations become wikilinks
- Tags remain as tags

### From Logseq

Logseq similarities:
- Block structure flattens to markdown
- Daily notes work similarly
- Tags and wikilinks transfer directly

## Advanced Workflows

### Research Paper Management

```
"Help me organize my research papers. Create a bibliography, find citation networks, and identify key papers I should read next."
```

### Meeting Notes Analysis

```
"Analyze all my meeting notes from Q1 2024. What are the recurring themes, action items that were never completed, and decisions that need follow-up?"
```

### Learning Progress Tracking

```
"Track my learning progress across all my study notes. What topics have I mastered? Where do I need more practice?"
```

### Content Creation Pipeline

```
"Analyze my content ideas and draft notes. Which ideas are ready to be turned into full articles? What's my content pipeline looking like?"
```

### Project Management

```
"Review all my project notes and extract: current status, blockers, next actions, and resource needs across all active projects."
```

## Best Practices for Obsidian + mdquery

### 1. Consistent Frontmatter

Use consistent frontmatter structure:

```yaml
---
title: "Note Title"
date: 2024-03-15
tags: [category, specific-topic]
status: in-progress
project: "[[Project Name]]"
type: meeting-notes
---
```

### 2. Meaningful File Names

Use descriptive, consistent file naming:
```
YYYY-MM-DD Daily Note
Project - Meeting with Client
Research - Paper Title Summary
Concept - Machine Learning Overview
```

### 3. Strategic Tagging

Create a tag hierarchy that supports analysis:
```
#areas/career/skills
#areas/health/fitness
#projects/research/ai
#projects/personal/blog
#status/active
#status/completed
#type/meeting
#type/idea
```

### 4. Link Liberally

Create rich wikilink networks:
- Link to people: `[[John Smith]]`
- Link to concepts: `[[Machine Learning]]`
- Link to projects: `[[AI Research Project]]`
- Link to resources: `[[Important Paper]]`

### 5. Regular Analysis

Use mdquery regularly for vault maintenance:
- Weekly: Review new connections and orphaned notes
- Monthly: Analyze tag usage and reorganize
- Quarterly: Comprehensive vault analysis and cleanup

## Support and Community

### Getting Help

1. **Documentation**: [mdquery docs](../README.md)
2. **Issues**: GitHub issues for bugs and feature requests
3. **Community**: Discord/Reddit for Obsidian + mdquery discussions

### Contributing Obsidian-Specific Features

If you have ideas for Obsidian-specific improvements:
1. Test with your vault setup
2. Document the use case
3. Submit feature requests with examples

### Sharing Workflows

Share your successful Obsidian + mdquery workflows:
- Document your configuration
- Provide example queries
- Explain your vault organization

---

## Quick Reference

### Essential Queries for Obsidian Users

```sql
-- Find recent daily notes
SELECT * FROM files WHERE filename LIKE '%2024-03%' AND directory LIKE '%Daily%';

-- Analyze tag hierarchy
SELECT tag, COUNT(*) FROM tags WHERE tag LIKE '#projects/%' GROUP BY tag;

-- Find orphaned notes (no wikilinks)
SELECT f.filename FROM files f LEFT JOIN links l ON f.id = l.file_id WHERE l.file_id IS NULL;

-- Most connected notes
SELECT f.filename, COUNT(l.link_target) as connections
FROM files f JOIN links l ON f.id = l.file_id
GROUP BY f.id ORDER BY connections DESC;

-- Recent modifications by folder
SELECT directory, COUNT(*) as files, MAX(modified_date) as last_modified
FROM files GROUP BY directory ORDER BY last_modified DESC;
```

This guide should get you started with mdquery in your Obsidian vault. The combination of Obsidian's powerful note-taking features with mdquery's analytical capabilities creates a uniquely powerful knowledge management system.