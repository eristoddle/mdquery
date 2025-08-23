#!/usr/bin/env python3
"""
Demonstration script for the mdquery file indexing engine.

This script shows how to use the indexing engine to process markdown files
and query the resulting database.
"""

import tempfile
from pathlib import Path

from mdquery.database import DatabaseManager
from mdquery.indexer import Indexer


def create_sample_files(base_dir: Path):
    """Create sample markdown files for demonstration."""

    # Create a blog post
    blog_post = base_dir / "blog" / "my-first-post.md"
    blog_post.parent.mkdir(parents=True, exist_ok=True)
    blog_post.write_text("""---
title: "My First Blog Post"
date: 2024-01-15
tags: [blogging, markdown, web]
category: tutorial
author: Jane Doe
---

# My First Blog Post

Welcome to my blog! This is my first post about #blogging and #web-development.

## What I'll Cover

- How to write in markdown
- Setting up a blog
- Best practices for content creation

## Links and References

Check out the [Markdown Guide](https://www.markdownguide.org/) for more information.

Also see my [[setup-guide]] for technical details.

### Tags and Organization

I use tags like #tutorial and #beginner to organize my content.
""")

    # Create a research note
    research_note = base_dir / "research" / "ai-trends.md"
    research_note.parent.mkdir(parents=True, exist_ok=True)
    research_note.write_text("""---
title: "AI Trends 2024"
tags: [ai, machine-learning, research]
status: draft
priority: high
---

# AI Trends 2024

Research notes on current #artificial-intelligence trends.

## Key Areas

### Large Language Models
- GPT-4 and beyond
- Multimodal capabilities
- Efficiency improvements

### Computer Vision
- Real-time processing
- Edge deployment
- Privacy-preserving techniques

## References

1. [OpenAI Research](https://openai.com/research/)
2. [Google AI Blog](https://ai.googleblog.com/)

See also: [[llm-comparison]] and [[cv-benchmarks]]

#research #2024 #trends
""")

    # Create a simple note
    simple_note = base_dir / "notes" / "quick-thoughts.md"
    simple_note.parent.mkdir(parents=True, exist_ok=True)
    simple_note.write_text("""# Quick Thoughts

Just some random ideas and #thoughts I wanted to capture.

## Ideas
- Build a markdown query tool
- Learn more about #databases
- Write better documentation

## Links
- [SQLite FTS5](https://www.sqlite.org/fts5.html)
- [Python Markdown](https://python-markdown.github.io/)

#ideas #productivity
""")

    return [blog_post, research_note, simple_note]


def main():
    """Demonstrate the indexing engine."""

    print("🚀 mdquery Indexing Engine Demo")
    print("=" * 40)

    # Create temporary directory and sample files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        print(f"📁 Creating sample files in: {temp_path}")

        files = create_sample_files(temp_path)
        print(f"✅ Created {len(files)} sample markdown files")

        # Initialize database and indexer
        print("\n🗄️  Initializing database...")
        db_manager = DatabaseManager(":memory:")  # Use in-memory database for demo
        db_manager.initialize_database()

        indexer = Indexer(db_manager)
        print("✅ Database and indexer initialized")

        # Index the files
        print(f"\n📊 Indexing directory: {temp_path}")
        stats = indexer.index_directory(temp_path, recursive=True)

        print(f"✅ Indexing complete!")
        print(f"   Files processed: {stats['files_processed']}")
        print(f"   Files skipped: {stats['files_skipped']}")
        print(f"   Errors: {stats['errors']}")

        # Query the database to show results
        print(f"\n📈 Database Statistics:")
        print(f"   Total files: {indexer.get_file_count()}")

        with db_manager.get_connection() as conn:
            # Show file information
            cursor = conn.execute("""
                SELECT filename, word_count, heading_count
                FROM files
                ORDER BY filename
            """)
            files_info = cursor.fetchall()

            print(f"\n📄 Indexed Files:")
            for file_info in files_info:
                print(f"   {file_info['filename']}: {file_info['word_count']} words, {file_info['heading_count']} headings")

            # Show tags
            cursor = conn.execute("""
                SELECT tag, COUNT(*) as count
                FROM tags
                GROUP BY tag
                ORDER BY count DESC, tag
            """)
            tags_info = cursor.fetchall()

            print(f"\n🏷️  Extracted Tags:")
            for tag_info in tags_info:
                print(f"   #{tag_info['tag']}: {tag_info['count']} files")

            # Show links
            cursor = conn.execute("""
                SELECT link_target, link_type, is_internal
                FROM links
                ORDER BY link_type, link_target
            """)
            links_info = cursor.fetchall()

            print(f"\n🔗 Extracted Links:")
            for link_info in links_info:
                link_type = "internal" if link_info['is_internal'] else "external"
                print(f"   {link_info['link_target']} ({link_info['link_type']}, {link_type})")

            # Demonstrate FTS5 search
            print(f"\n🔍 Full-Text Search Examples:")

            # Search for "markdown"
            cursor = conn.execute("""
                SELECT f.filename, fts.title
                FROM files f
                JOIN content_fts fts ON f.id = fts.file_id
                WHERE content_fts MATCH 'markdown'
            """)
            markdown_results = cursor.fetchall()

            print(f"   Files containing 'markdown': {len(markdown_results)}")
            for result in markdown_results:
                title = result['title'] or result['filename']
                print(f"     - {title}")

            # Search for AI-related content
            cursor = conn.execute("""
                SELECT f.filename, fts.title
                FROM files f
                JOIN content_fts fts ON f.id = fts.file_id
                WHERE content_fts MATCH 'AI OR "artificial intelligence"'
            """)
            ai_results = cursor.fetchall()

            print(f"   Files about AI: {len(ai_results)}")
            for result in ai_results:
                title = result['title'] or result['filename']
                print(f"     - {title}")

        print(f"\n✨ Demo complete! The indexing engine successfully:")
        print(f"   • Scanned directories recursively")
        print(f"   • Extracted file metadata (size, dates, hashes)")
        print(f"   • Parsed frontmatter with type inference")
        print(f"   • Extracted headings and content structure")
        print(f"   • Identified tags from frontmatter and content")
        print(f"   • Parsed various link types (markdown, wikilinks, etc.)")
        print(f"   • Enabled full-text search with SQLite FTS5")
        print(f"   • Provided incremental indexing capabilities")


if __name__ == "__main__":
    main()