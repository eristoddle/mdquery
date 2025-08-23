# Indexer API

The Indexer is responsible for scanning directories, parsing markdown files, and populating the SQLite database with extracted metadata and content.

## Class: `mdquery.indexer.Indexer`

### Constructor

```python
def __init__(self, cache_manager: CacheManager = None)
```

**Parameters:**
- `cache_manager` (CacheManager, optional): Cache manager instance. If None, creates a default instance.

**Example:**
```python
from mdquery import Indexer, CacheManager

cache_manager = CacheManager("my_notes.db")
indexer = Indexer(cache_manager=cache_manager)
```

### Methods

#### `index_directory(path: Path, recursive: bool = True) -> None`

Indexes all markdown files in a directory.

**Parameters:**
- `path` (Path): Directory path to index
- `recursive` (bool): Whether to scan subdirectories recursively

**Example:**
```python
from pathlib import Path

indexer.index_directory(Path("/path/to/notes"), recursive=True)
```

**Behavior:**
- Scans for `.md` files
- Skips files that haven't changed (based on modification time and content hash)
- Processes files through all parsers (frontmatter, markdown, tags, links)
- Updates database with extracted data

#### `index_file(file_path: Path) -> None`

Indexes a single markdown file.

**Parameters:**
- `file_path` (Path): Path to the markdown file

**Example:**
```python
indexer.index_file(Path("/path/to/notes/important.md"))
```

**Behavior:**
- Extracts file metadata (size, dates, hash)
- Parses frontmatter, content, tags, and links
- Inserts or updates database records

#### `update_index(file_path: Path) -> None`

Updates the index for a specific file (alias for `index_file`).

**Parameters:**
- `file_path` (Path): Path to the markdown file

#### `rebuild_index() -> None`

Rebuilds the entire index from scratch.

**Example:**
```python
indexer.rebuild_index()
```

**Behavior:**
- Clears all existing index data
- Re-indexes all files in previously indexed directories
- Useful for schema updates or corruption recovery

### Properties

#### `cache_manager: CacheManager`

The associated cache manager instance.

#### `parsers: Dict[str, Parser]`

Dictionary of parser instances used by the indexer:
- `'frontmatter'`: FrontmatterParser
- `'markdown'`: MarkdownParser
- `'tags'`: TagParser
- `'links'`: LinkParser

### Error Handling

The indexer handles various error conditions gracefully:

- **Permission Errors**: Logs warning and skips inaccessible files
- **Corrupted Files**: Logs error with file path and continues processing
- **Encoding Issues**: Attempts UTF-8 with fallback to latin-1
- **Parser Errors**: Logs warnings and processes what's parseable

### Performance Considerations

- **Incremental Updates**: Only processes files that have changed
- **Content Hashing**: Uses SHA-256 to detect content changes
- **Batch Processing**: Processes files in batches for better performance
- **Memory Usage**: Processes files one at a time to minimize memory usage

### Example: Complete Indexing Workflow

```python
from pathlib import Path
from mdquery import Indexer, CacheManager

# Initialize components
cache_path = Path("my_knowledge_base.db")
cache_manager = CacheManager(cache_path)
cache_manager.initialize_cache()

indexer = Indexer(cache_manager=cache_manager)

# Index multiple directories
directories = [
    Path("~/Documents/Obsidian Vault"),
    Path("~/Documents/Jekyll Site/_posts"),
    Path("~/Documents/Research Notes")
]

for directory in directories:
    if directory.exists():
        print(f"Indexing {directory}...")
        indexer.index_directory(directory)
        print(f"Completed indexing {directory}")

print("Indexing complete!")
```

### Example: Monitoring Index Progress

```python
import logging
from mdquery import Indexer, CacheManager

# Set up logging to monitor progress
logging.basicConfig(level=logging.INFO)

cache_manager = CacheManager("notes.db")
cache_manager.initialize_cache()

indexer = Indexer(cache_manager=cache_manager)

# Index with progress monitoring
indexer.index_directory(Path("/large/notes/directory"))
```

### Integration with Other Components

The Indexer works closely with:

- **CacheManager**: For database operations and cache validation
- **Parsers**: For extracting different types of data from markdown files
- **QueryEngine**: Provides the data that queries operate on

See also:
- [QueryEngine API](query_engine.md)
- [CacheManager API](cache_manager.md)
- [Parser APIs](../parsers/)