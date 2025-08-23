# MCP Workflow Examples

This guide provides practical examples of using mdquery with AI assistants through the Model Context Protocol (MCP) integration.

## Setup

Before running these examples, ensure you have:

1. mdquery installed with MCP support: `pip install mdquery[mcp]`
2. Claude Desktop or another MCP-compatible AI assistant configured
3. Your notes indexed in mdquery

### Configuration Examples

#### Single Research Directory
Perfect for focused research projects:

```json
{
  "mcpServers": {
    "mdquery": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/Users/username/Research/ML-Papers",
        "MDQUERY_DB_PATH": "/Users/username/.mdquery/research.db"
      }
    }
  }
}
```

#### Multiple Knowledge Areas
For researchers working across multiple domains:

```json
{
  "mcpServers": {
    "mdquery": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_DB_PATH": "/Users/username/.mdquery/all-research.db"
      }
    }
  }
}
```

*Then use: "Index my research from ~/Research/ML-Papers, ~/Research/NLP-Notes, and ~/Research/Computer-Vision"*

#### Project-Specific Setup
For temporary or project-specific analysis:

```json
{
  "mcpServers": {
    "mdquery": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_DB_PATH": "/Users/username/Projects/thesis/.mdquery/thesis.db"
      }
    }
  }
}
```

## Research Workflows

### Literature Review Management

**Scenario**: You're conducting a literature review on machine learning and need to organize your research notes, track citations, and identify gaps.

**Conversation with AI Assistant**:

```
User: "I'm working on a literature review about transformer architectures in NLP. I have about 50 research papers and notes scattered across my notes directory. Can you help me organize this research?"

AI Assistant: I'll help you organize your literature review on transformer architectures. Let me start by indexing your notes and then analyzing your research content.

[Uses index_directory tool]
[Uses query_markdown tool to find transformer-related content]
[Uses generate_research_summary tool]

Based on my analysis of your notes, here's what I found:

**Research Summary:**
- 47 files related to transformer architectures
- 23 unique papers referenced
- Key themes: attention mechanisms, BERT, GPT, T5, scaling laws
- Most recent additions: 3 papers from last week
- Research gap identified: Limited coverage of efficiency improvements

**Top Referenced Papers:**
1. "Attention Is All You Need" (Vaswani et al.) - cited in 12 notes
2. "BERT: Pre-training of Deep Bidirectional Transformers" - cited in 8 notes
3. "Language Models are Few-Shot Learners" (GPT-3) - cited in 7 notes

**Suggested Organization:**
- Create separate sections for: Architecture, Training, Applications, Efficiency
- 5 papers need better integration into your notes
- 3 broken citation links need fixing

Would you like me to generate a detailed bibliography or help you identify specific research gaps?
```

### Cross-Reference Analysis

**Conversation**:

```
User: "Find connections between my notes on attention mechanisms and my notes on computer vision. Are there any overlaps or related concepts I should explore?"

AI Assistant: I'll analyze the connections between your attention mechanism and computer vision notes.

[Uses fuzzy_search tool for attention mechanisms]
[Uses fuzzy_search tool for computer vision]
[Uses find_similar_content tool]
[Uses analyze_link_relationships tool]

**Cross-Reference Analysis:**

**Direct Connections Found:**
- 8 notes mention both attention and vision
- 3 papers specifically on visual attention mechanisms
- 2 notes on Vision Transformers (ViTs)

**Key Overlapping Concepts:**
1. **Self-Attention in Vision**: 4 notes discuss applying transformer attention to images
2. **Spatial Attention**: 6 notes cover attention mechanisms for spatial data
3. **Multi-Modal Models**: 3 notes on CLIP and similar models

**Suggested Exploration Areas:**
- Vision Transformers (ViT) - you have limited coverage
- Attention mechanisms in object detection (DETR)
- Cross-modal attention (vision-language models)

**Missing Connections:**
Your notes on "Convolutional Attention" and "Visual Question Answering" aren't linked but share common themes. I can help you create these connections.

Would you like me to generate a concept map showing these relationships?
```

## Content Management Workflows

### Blog Content Audit

**Scenario**: You manage a technical blog and need to audit content quality, find optimization opportunities, and plan future content.

**Conversation**:

```
User: "I have a tech blog with about 100 posts. Can you audit my content for SEO issues, find internal linking opportunities, and suggest topics for new posts?"

AI Assistant: I'll perform a comprehensive audit of your blog content. Let me analyze SEO quality, content structure, and identify opportunities.

[Uses index_directory tool for blog posts]
[Uses analyze_seo tool]
[Uses analyze_content_structure tool]
[Uses analyze_link_relationships tool]
[Uses generate_content_report tool]

**Blog Content Audit Results:**

**SEO Analysis (100 posts analyzed):**
- Average SEO score: 72/100
- 23 posts missing meta descriptions
- 15 posts with suboptimal title tags
- 8 posts with poor heading structure
- 12 posts under 300 words (too short)

**Top SEO Issues:**
1. Missing H1 tags: 15 posts
2. No internal links: 28 posts
3. Images without alt text: 45 posts
4. Duplicate meta descriptions: 6 posts

**Internal Linking Opportunities:**
- "Machine Learning Basics" could link to 12 related posts
- "Python Tutorial Series" has poor internal connectivity
- 34 posts have no incoming internal links (orphaned content)

**Content Gap Analysis:**
Based on your existing topics, suggested new content:
1. "Advanced Python for Data Science" (high demand, low coverage)
2. "MLOps Best Practices" (trending topic, no current coverage)
3. "Transformer Architecture Deep Dive" (popular topic, basic coverage only)

**Content Performance Insights:**
- Most linked post: "Introduction to Neural Networks" (23 internal links)
- Longest posts perform better (avg 1,200+ words)
- Posts with code examples get more engagement

Would you like me to generate a detailed improvement plan for your top 10 posts?
```

### Content Calendar Planning

**Conversation**:

```
User: "Based on my existing blog content and current trends, help me plan a content calendar for the next quarter. Focus on topics that build on what I've already written."

AI Assistant: I'll analyze your existing content and create a strategic content calendar that builds on your strengths.

[Uses query_markdown tool to analyze content themes]
[Uses generate_research_summary tool for topic analysis]
[Uses fuzzy_search tool to find content gaps]

**Q2 2024 Content Calendar:**

**April - Foundation Building:**
Week 1: "Advanced Python Decorators" (builds on your Python basics series)
Week 2: "Database Optimization for ML" (connects ML and backend content)
Week 3: "Testing Machine Learning Models" (fills identified gap)
Week 4: "Docker for Data Scientists" (trending topic, builds on your DevOps content)

**May - Deep Dives:**
Week 1: "Transformer Architecture Explained" (high-demand topic)
Week 2: "Building Production ML Pipelines" (connects multiple existing topics)
Week 3: "Advanced Git for Data Teams" (builds on your Git basics post)
Week 4: "Monitoring ML Models in Production" (trending MLOps topic)

**June - Practical Applications:**
Week 1: "Real-world NLP Project Walkthrough" (combines NLP + project management)
Week 2: "Scaling Python Applications" (builds on performance optimization content)
Week 3: "ML Model Deployment Strategies" (completes your MLOps coverage)
Week 4: "Career Advice for ML Engineers" (personal branding content)

**Content Connections:**
Each post is designed to link to 3-5 existing posts, improving your internal link structure and SEO.

**Resource Requirements:**
- 8 posts need code examples (prepare GitHub repos)
- 4 posts need diagrams/visualizations
- 6 posts could benefit from guest expert quotes

Would you like me to create detailed outlines for any of these posts?
```

## Knowledge Management Workflows

### Personal Knowledge Base Maintenance

**Scenario**: You maintain a large personal knowledge base and need to identify outdated content, broken links, and consolidation opportunities.

**Conversation**:

```
User: "My personal knowledge base has grown to over 500 notes. Help me identify maintenance tasks: outdated content, broken links, duplicate information, and notes that should be connected but aren't."

AI Assistant: I'll perform a comprehensive maintenance analysis of your knowledge base to identify improvement opportunities.

[Uses index_directory tool]
[Uses analyze_link_relationships tool]
[Uses find_similar_content tool with various thresholds]
[Uses query_markdown tool for various maintenance queries]

**Knowledge Base Maintenance Report:**

**Outdated Content (47 notes need attention):**
- 23 notes not updated in over 2 years
- 12 notes with outdated technology references
- 8 notes marked as "draft" for over 6 months
- 4 notes with broken external links to deprecated resources

**Broken Links Analysis:**
- 34 internal broken links (target files moved/deleted)
- 18 external broken links (404 errors)
- 12 ambiguous wikilinks (multiple possible targets)

**Duplicate/Similar Content:**
High similarity pairs (>80% similar):
1. "Machine Learning Overview" & "ML Fundamentals" (87% similar)
2. "Python Best Practices" & "Clean Python Code" (82% similar)
3. "Git Workflow" & "Version Control Guide" (85% similar)

**Orphaned Notes (no incoming links):**
- 67 notes have no incoming links
- 23 of these are substantial content (>500 words)
- Suggested: Create index pages or add to existing note clusters

**Missing Connections:**
Notes that should be linked but aren't:
- "Deep Learning" notes don't link to "Neural Network Basics"
- "Project Management" cluster isolated from "Software Development" notes
- "Research Methods" notes could connect to specific project notes

**Consolidation Opportunities:**
1. **Python Learning Path**: 12 scattered Python notes could become a structured learning sequence
2. **ML Project Notes**: 8 project notes could be organized into a "Projects" section
3. **Tool Reviews**: 15 tool review notes could be consolidated into comparison guides

**Maintenance Priority:**
1. Fix broken internal links (high impact, easy fix)
2. Consolidate duplicate content (medium impact, medium effort)
3. Connect orphaned high-value notes (high impact, low effort)
4. Update outdated technology references (low impact, high effort)

Would you like me to generate specific action items for any of these maintenance tasks?
```

### Learning Progress Tracking

**Conversation**:

```
User: "I'm learning data science and have been taking notes for 6 months. Can you analyze my learning progress, identify knowledge gaps, and suggest what to focus on next?"

AI Assistant: I'll analyze your data science learning journey and provide insights on your progress and next steps.

[Uses generate_research_summary tool with date filters]
[Uses query_markdown tool for topic analysis]
[Uses fuzzy_search tool for skill assessment]

**Data Science Learning Progress Analysis:**

**Learning Timeline (6 months):**
- Month 1-2: Python fundamentals (23 notes, solid foundation)
- Month 3-4: Statistics and math (18 notes, good coverage)
- Month 5-6: Machine learning (31 notes, strong focus)

**Knowledge Areas Covered:**
✅ **Strong Areas:**
- Python programming (pandas, numpy, matplotlib)
- Supervised learning (regression, classification)
- Data visualization
- Basic statistics

⚠️ **Developing Areas:**
- Unsupervised learning (only 4 notes)
- Deep learning (basic coverage)
- Model evaluation (limited depth)

❌ **Gap Areas:**
- Feature engineering (minimal coverage)
- MLOps/deployment (not covered)
- Big data tools (Spark, etc.)
- Advanced statistics (hypothesis testing)

**Learning Velocity:**
- Average: 12 notes per month
- Peak learning: Month 5 (18 notes)
- Most active topics: scikit-learn, data cleaning

**Practical Application:**
- 3 completed projects documented
- 7 code examples in notes
- 2 real datasets analyzed

**Recommended Next Steps:**

**Immediate Focus (Next 2-4 weeks):**
1. **Feature Engineering**: Critical gap for practical ML
2. **Model Evaluation**: Deepen understanding of metrics and validation
3. **Unsupervised Learning**: Clustering and dimensionality reduction

**Medium-term Goals (1-2 months):**
1. **Deep Learning Fundamentals**: Neural networks, TensorFlow/PyTorch
2. **Advanced Statistics**: Hypothesis testing, A/B testing
3. **Time Series Analysis**: Important practical skill

**Long-term Development (3-6 months):**
1. **MLOps**: Model deployment and monitoring
2. **Big Data Tools**: Spark, distributed computing
3. **Specialized Domains**: NLP, computer vision, or recommendation systems

**Learning Resources Based on Your Style:**
Your notes show you prefer:
- Hands-on coding examples (include more in future notes)
- Visual explanations (your matplotlib notes are excellent)
- Real-world applications (continue with practical projects)

**Suggested Project:**
Build an end-to-end ML project incorporating feature engineering, proper evaluation, and basic deployment - this would address multiple gap areas.

Would you like me to create a detailed study plan for any of these focus areas?
```

## Advanced Analysis Workflows

### Multi-Collection Research

**Scenario**: You have notes across multiple systems (Obsidian vault, blog drafts, research papers) and need to analyze them together.

**Conversation**:

```
User: "I have notes in three different places: my Obsidian vault for daily notes, a separate folder for blog drafts, and another folder for research papers. Can you analyze all of them together to find connections and themes I might have missed?"

AI Assistant: I'll analyze your multi-collection note system to find cross-collection connections and themes.

[Uses index_directory tool for each collection]
[Uses cross_collection_search tool]
[Uses generate_research_summary tool for each collection]
[Uses find_similar_content tool across collections]

**Multi-Collection Analysis Results:**

**Collection Overview:**
1. **Obsidian Vault**: 234 daily notes, personal insights, quick thoughts
2. **Blog Drafts**: 23 draft posts, structured content, public-facing
3. **Research Papers**: 67 academic notes, formal research, citations

**Cross-Collection Themes:**
1. **Artificial Intelligence** (appears in all 3 collections)
   - Obsidian: 45 casual observations and ideas
   - Blog Drafts: 8 structured articles in progress
   - Research: 23 formal paper analyses

2. **Productivity Systems** (Obsidian + Blog Drafts)
   - Strong overlap between personal experiments and blog content
   - 12 blog ideas could be developed from Obsidian insights

3. **Learning Methodologies** (All collections)
   - Research papers inform your learning approach
   - Daily notes track practical application
   - Blog drafts synthesize insights for others

**Hidden Connections Discovered:**
- Your Obsidian note "Why I switched to Zettelkasten" connects to 3 research papers on knowledge management
- Blog draft "The Future of Remote Work" has supporting evidence in 8 daily notes
- Research insights on "Attention Mechanisms" appear as practical applications in daily notes

**Content Development Opportunities:**
1. **"AI in Daily Life" Blog Series**: Combine research insights with daily observations
2. **"Learning in Public" Content**: Your research → daily notes → blog pipeline is a story worth sharing
3. **"Productivity Research Review"**: Academic backing for your personal productivity experiments

**Synthesis Suggestions:**
- 15 Obsidian insights could become blog posts with research backing
- 8 research papers have practical applications documented in daily notes
- 5 blog drafts could be enhanced with research citations

**Knowledge Flow Analysis:**
Research → Daily Notes → Blog Drafts (healthy knowledge processing pipeline)
But also: Daily Notes → Research Questions (you're identifying research gaps through practice)

**Recommended Actions:**
1. Create cross-collection index notes linking related themes
2. Develop 3 high-potential blog posts using multi-collection insights
3. Identify research questions emerging from daily practice
4. Build a "knowledge synthesis" workflow for future content

Would you like me to help develop any of these cross-collection content opportunities?
```

### Trend Analysis Over Time

**Conversation**:

```
User: "I've been taking notes for 3 years. Can you analyze how my interests and focus areas have evolved over time? What trends do you see in my learning and thinking?"

AI Assistant: I'll analyze the evolution of your interests and thinking patterns over the past 3 years.

[Uses generate_research_summary tool with different date ranges]
[Uses query_markdown tool for temporal analysis]
[Uses fuzzy_search tool for interest tracking]

**3-Year Interest Evolution Analysis:**

**Year 1 (2021): Foundation Building**
- **Top Topics**: Programming basics (Python, JavaScript), web development
- **Note Characteristics**: Tutorial-focused, step-by-step learning
- **Average Note Length**: 450 words
- **Learning Style**: Structured, following courses and tutorials

**Year 2 (2022): Specialization Phase**
- **Top Topics**: Machine learning, data science, AI ethics
- **Note Characteristics**: More analytical, questioning assumptions
- **Average Note Length**: 680 words (increased depth)
- **Learning Style**: Project-based, experimental

**Year 3 (2023): Integration & Leadership**
- **Top Topics**: MLOps, team leadership, system design, AI strategy
- **Note Characteristics**: Strategic thinking, connecting concepts
- **Average Note Length**: 820 words (mature analysis)
- **Learning Style**: Problem-solving, teaching others

**Interest Evolution Patterns:**

**Technical Progression:**
2021: Basic Programming → 2022: Data Science → 2023: ML Engineering
- Clear progression from fundamentals to advanced applications
- Increasing focus on production and scalability

**Thinking Evolution:**
2021: "How does this work?" → 2022: "Why does this work?" → 2023: "How can we make this work better?"
- Shift from learning to understanding to optimizing

**Emerging Themes (2023):**
1. **AI Ethics & Responsibility**: 23 notes (new focus area)
2. **Team Dynamics**: 18 notes (leadership development)
3. **System Thinking**: 31 notes (holistic approach)

**Consistent Interests (All 3 Years):**
- **Learning Methodologies**: Continuous interest in how to learn effectively
- **Open Source**: Steady engagement with open source projects
- **Knowledge Sharing**: Growing from personal notes to teaching others

**Prediction for Year 4 (2024):**
Based on recent trends:
- **Strategic AI Implementation**: Moving from technical to business impact
- **Mentoring & Teaching**: Increasing focus on developing others
- **Cross-Disciplinary Integration**: Connecting AI with other domains

**Learning Velocity Changes:**
- Year 1: 8 notes/month (steady learning)
- Year 2: 12 notes/month (peak exploration)
- Year 3: 10 notes/month (quality over quantity)

**Knowledge Depth Indicators:**
- Cross-references between notes: 2021: 2.3/note → 2023: 5.7/note
- External citations: 2021: 0.8/note → 2023: 3.2/note
- Original insights vs. summaries: 2021: 20% → 2023: 65%

**Recommendations for Continued Growth:**
1. **Document Your Teaching**: You're naturally moving toward teaching - capture these insights
2. **Strategic Thinking**: Your systems thinking is developing - consider formal strategy study
3. **Cross-Domain Applications**: Explore AI applications in new domains
4. **Leadership Development**: Your team dynamics interest suggests leadership potential

Your learning journey shows excellent progression from consumer to creator to leader. The next phase likely involves scaling your impact through others.

Would you like me to suggest specific areas to focus on for your continued development?
```

## Integration with Other Tools

### Export for External Analysis

**Conversation**:

```
User: "I want to create a visualization of my note network using Gephi. Can you export my note connections in a format suitable for network analysis?"

AI Assistant: I'll export your note network data in formats suitable for Gephi and other network analysis tools.

[Uses analyze_link_relationships tool]
[Uses query_markdown tool for network data]

I've analyzed your note network and can provide several export formats:

**Network Statistics:**
- 342 nodes (notes)
- 1,247 edges (connections)
- Average degree: 7.3 connections per note
- Network density: 0.021
- Largest connected component: 298 notes (87%)

**Export Options:**

1. **Gephi Format (GEXF)**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<gexf xmlns="http://www.gexf.net/1.2draft" version="1.2">
  <graph mode="static" defaultedgetype="directed">
    <nodes>
      <node id="1" label="Machine Learning Basics"/>
      <node id="2" label="Neural Networks Introduction"/>
      <!-- ... more nodes ... -->
    </nodes>
    <edges>
      <edge id="1" source="1" target="2" weight="3"/>
      <!-- ... more edges ... -->
    </edges>
  </graph>
</gexf>
```

2. **CSV Format for Custom Analysis**:
```csv
# nodes.csv
id,label,word_count,tag_count,creation_date,category
1,"Machine Learning Basics",1250,5,2023-01-15,"technical"

# edges.csv
source,target,weight,link_type
1,2,3,"wikilink"
```

**Recommended Gephi Analysis:**
1. **Community Detection**: Use modularity to find topic clusters
2. **Centrality Analysis**: Identify your most important "hub" notes
3. **Temporal Analysis**: Color nodes by creation date to see evolution
4. **Topic Clustering**: Use tags as node attributes for colored visualization

**Key Insights for Visualization:**
- Your "Introduction to AI" note has the highest betweenness centrality (major connector)
- 5 distinct communities detected (likely corresponding to your main interest areas)
- 23 "bridge" notes connect different topic areas
- Temporal analysis shows your interests branching over time

Would you like me to generate the actual export files, or help you set up specific analysis parameters for Gephi?
```

These MCP workflow examples demonstrate the power of combining mdquery's analytical capabilities with AI assistance, enabling sophisticated analysis and insights that would be difficult to achieve manually.