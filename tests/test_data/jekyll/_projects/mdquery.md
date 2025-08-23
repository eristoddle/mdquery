---
title: mdquery
description: Universal markdown querying tool
status: active
technologies: [python, sqlite, markdown]
github: https://github.com/example/mdquery
demo: https://example.com/mdquery-demo
featured: true
---

# mdquery Project

## Overview

mdquery is a universal markdown querying tool that provides SQL-like functionality for searching and analyzing markdown files across different note-taking systems.

## Features

- **SQL-like Queries**: Familiar syntax for powerful searches
- **Multi-Format Support**: Works with Obsidian, Joplin, Jekyll, and more
- **High Performance**: SQLite backend with FTS5 for fast searches
- **Multiple Interfaces**: CLI and MCP server support

## Technology Stack

- Python 3.8+
- SQLite with FTS5
- Click for CLI
- MCP for AI integration

## Usage

```bash
mdquery query "SELECT title, tags FROM files WHERE tags LIKE '%productivity%'"
```

## Status

Currently in active development. See the [GitHub repository]({{ page.github }}) for latest updates.