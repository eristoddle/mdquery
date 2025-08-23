#!/usr/bin/env python3
"""
Generate large test data collection for performance testing.
Creates 1000+ markdown files with varied content and metadata.

NOTE: The generated files are excluded from git via .gitignore
(tests/test_data/performance/) as they are large generated test data.
Run this script to regenerate performance test data as needed.
"""

import os
import random
from pathlib import Path
from datetime import datetime, timedelta

# Sample data for generating varied content
TITLES = [
    "Research Notes", "Meeting Summary", "Project Update", "Daily Reflection",
    "Technical Documentation", "Ideas and Thoughts", "Book Review", "Tutorial",
    "Analysis Report", "Planning Document", "Status Update", "Design Notes"
]

TAGS = [
    "research", "meeting", "project", "daily", "technical", "ideas", "books",
    "tutorial", "analysis", "planning", "status", "design", "productivity",
    "development", "management", "learning", "review", "documentation"
]

CATEGORIES = [
    "work", "personal", "learning", "projects", "research", "meetings",
    "documentation", "ideas", "reviews", "planning", "development"
]

AUTHORS = ["John Doe", "Jane Smith", "Bob Wilson", "Alice Johnson", "Charlie Brown"]

def generate_frontmatter(file_num):
    """Generate varied frontmatter for a file."""
    base_date = datetime(2023, 1, 1)
    file_date = base_date + timedelta(days=random.randint(0, 365))

    frontmatter = {
        "title": f"{random.choice(TITLES)} {file_num}",
        "date": file_date.strftime("%Y-%m-%d"),
        "author": random.choice(AUTHORS),
        "tags": random.sample(TAGS, random.randint(1, 5)),
        "category": random.choice(CATEGORIES),
        "published": random.choice([True, False]),
        "rating": round(random.uniform(1.0, 5.0), 1)
    }

    # Add some optional fields randomly
    if random.random() < 0.3:
        frontmatter["description"] = f"Description for file {file_num}"
    if random.random() < 0.2:
        frontmatter["priority"] = random.choice(["low", "medium", "high"])

    return frontmatter

def generate_content(file_num):
    """Generate varied markdown content."""
    paragraphs = []

    # Add heading
    paragraphs.append(f"# Content for File {file_num}")

    # Add introduction
    paragraphs.append(f"This is file number {file_num} in our performance test collection.")

    # Add random sections
    num_sections = random.randint(2, 6)
    for i in range(num_sections):
        paragraphs.append(f"\n## Section {i + 1}")

        # Add some content
        num_paragraphs = random.randint(1, 3)
        for j in range(num_paragraphs):
            content = f"This is paragraph {j + 1} of section {i + 1}. "
            content += "It contains some sample text to make the file more realistic. "
            content += f"Random number: {random.randint(1, 1000)}."
            paragraphs.append(content)

        # Maybe add a list
        if random.random() < 0.4:
            paragraphs.append("\nSome key points:")
            for k in range(random.randint(2, 5)):
                paragraphs.append(f"- Point {k + 1}")

        # Maybe add a code block
        if random.random() < 0.3:
            paragraphs.append("\n```python")
            paragraphs.append(f"def function_{i}():")
            paragraphs.append(f'    return "Result from section {i}"')
            paragraphs.append("```")

    # Add some tags in content
    if random.random() < 0.5:
        tags_in_content = random.sample(TAGS, random.randint(1, 3))
        tag_text = " ".join(f"#{tag}" for tag in tags_in_content)
        paragraphs.append(f"\nTags: {tag_text}")

    # Add some links
    if random.random() < 0.4:
        paragraphs.append(f"\nSee also: [Related File {random.randint(1, 100)}](file-{random.randint(1, 100)}.md)")

    return "\n\n".join(paragraphs)

def create_performance_files(output_dir, num_files=1000):
    """Create performance test files."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Generating {num_files} performance test files...")

    for i in range(1, num_files + 1):
        if i % 100 == 0:
            print(f"Generated {i}/{num_files} files...")

        # Generate frontmatter
        fm = generate_frontmatter(i)

        # Create frontmatter YAML
        frontmatter_lines = ["---"]
        for key, value in fm.items():
            if isinstance(value, list):
                frontmatter_lines.append(f"{key}: {value}")
            elif isinstance(value, str):
                frontmatter_lines.append(f'{key}: "{value}"')
            else:
                frontmatter_lines.append(f"{key}: {value}")
        frontmatter_lines.append("---")

        # Generate content
        content = generate_content(i)

        # Combine and write file
        full_content = "\n".join(frontmatter_lines) + "\n\n" + content

        # Create subdirectories for some files
        if i % 50 == 0:
            subdir = output_path / f"category_{fm['category']}"
            subdir.mkdir(exist_ok=True)
            file_path = subdir / f"file-{i:04d}.md"
        else:
            file_path = output_path / f"file-{i:04d}.md"

        file_path.write_text(full_content, encoding='utf-8')

    print(f"Generated {num_files} performance test files in {output_path}")

if __name__ == "__main__":
    # Generate performance test data
    perf_dir = Path(__file__).parent / "test_data" / "performance"
    create_performance_files(perf_dir, 1000)

    print("Performance test data generation complete!")