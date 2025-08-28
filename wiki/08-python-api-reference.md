# Python API Reference

## Overview

mdquery provides a comprehensive Python API for programmatic access to indexing and querying functionality. The API is designed to be intuitive and follows Python best practices for object-oriented design.

## Core Classes

### Indexer

The `Indexer` class handles scanning directories and processing markdown files.

#### Class Definition

```python
from mdquery.indexer import Indexer
from mdquery.database import DatabaseManager
from mdquery.config import SimplifiedConfig

# Initialize with database manager
db_manager = DatabaseManager(db_path="path/to/database.db")
indexer = Indexer(db_manager)
```

#### Methods

##### `index_directory(directory_path, recursive=True, force=False)`

Index all markdown files in a directory.

**Parameters:**
- `directory_path` (str): Path to directory to index
- `recursive` (bool): Whether to include subdirectories (default: True)
- `force` (bool): Whether to reindex existing files (default: False)

**Returns:**
- `IndexResult`: Object containing indexing statistics

**Example:**
```python
result = indexer.index_directory("/path/to/notes", recursive=True)
print(f"Indexed {result.files_processed} files")
print(f"Found {result.new_files} new files")
print(f"Updated {result.updated_files} files")
```

##### `incremental_index_directory(directory_path, recursive=True)`

Perform incremental indexing (only process changed files).

**Parameters:**
- `directory_path` (str): Path to directory to index
- `recursive` (bool): Whether to include subdirectories (default: True)

**Returns:**
- `IndexResult`: Object containing indexing statistics

**Example:**
```python
result = indexer.incremental_index_directory("/path/to/notes")
print(f"Processed {result.files_processed} files")
print(f"Skipped {result.files_skipped} unchanged files")
```

##### `get_file_metadata(file_path)`

Extract metadata from a single file without indexing.

**Parameters:**
- `file_path` (str): Path to markdown file

**Returns:**
- `FileMetadata`: Object containing extracted metadata

**Example:**
```python
metadata = indexer.get_file_metadata("/path/to/note.md")
print(f"Word count: {metadata.word_count}")
print(f"Tags: {metadata.tags}")
print(f"Links: {metadata.links}")
```

### QueryEngine

The `QueryEngine` class provides SQL query execution capabilities.

#### Class Definition

```python
from mdquery.query import QueryEngine
from mdquery.database import DatabaseManager

# Initialize with database manager
db_manager = DatabaseManager(db_path="path/to/database.db")
query_engine = QueryEngine(db_manager)
```

#### Methods

##### `execute_query(sql, format="json", limit=None, timeout=30.0)`

Execute a SQL query against the indexed data.

**Parameters:**
- `sql` (str): SQL query to execute
- `format` (str): Output format ("json", "csv", "table", "markdown")
- `limit` (int, optional): Maximum number of results
- `timeout` (float): Query timeout in seconds

**Returns:**
- `QueryResult`: Object containing query results and metadata

**Example:**
```python
result = query_engine.execute_query(
    "SELECT filename, word_count FROM files WHERE tags LIKE '%research%'",
    format="json",
    limit=10
)

print(f"Found {result.row_count} results")
for row in result.data:
    print(f"{row['filename']}: {row['word_count']} words")
```

##### `validate_query(sql)`

Validate SQL query syntax and security.

**Parameters:**
- `sql` (str): SQL query to validate

**Returns:**
- `ValidationResult`: Object containing validation status and errors

**Example:**
```python
validation = query_engine.validate_query("SELECT * FROM files")
if validation.is_valid:
    print("Query is valid")
else:
    print(f"Validation errors: {validation.errors}")
```

##### `get_schema(table=None)`

Get database schema information.

**Parameters:**
- `table` (str, optional): Specific table to get schema for

**Returns:**
- `SchemaInfo`: Object containing schema details

**Example:**
```python
schema = query_engine.get_schema()
print("Available tables:")
for table in schema.tables:
    print(f"  {table.name}: {table.row_count} rows")

# Get specific table schema
files_schema = query_engine.get_schema("files")
print("Files table columns:")
for column in files_schema.columns:
    print(f"  {column.name}: {column.type}")
```

##### `format_results(result, format="json")`

Format query results in different output formats.

**Parameters:**
- `result`: Raw query result
- `format` (str): Output format ("json", "csv", "table", "markdown")

**Returns:**
- `str`: Formatted result string

**Example:**
```python
raw_result = query_engine.execute_query("SELECT * FROM files LIMIT 5")
table_output = query_engine.format_results(raw_result, "table")
print(table_output)
```

### DatabaseManager

The `DatabaseManager` class handles SQLite database operations.

#### Class Definition

```python
from mdquery.database import DatabaseManager

# Initialize with database path
db_manager = DatabaseManager(db_path="path/to/database.db")
```

#### Methods

##### `connect()`

Establish database connection.

**Example:**
```python
db_manager.connect()
```

##### `execute_query(sql, params=None)`

Execute raw SQL query.

**Parameters:**
- `sql` (str): SQL query
- `params` (tuple, optional): Query parameters

**Returns:**
- `sqlite3.Cursor`: Database cursor with results

**Example:**
```python
cursor = db_manager.execute_query(
    "SELECT * FROM files WHERE word_count > ?",
    (1000,)
)
for row in cursor.fetchall():
    print(row)
```

##### `get_tables()`

Get list of database tables.

**Returns:**
- `List[str]`: List of table names

**Example:**
```python
tables = db_manager.get_tables()
print("Available tables:", tables)
```

##### `get_table_info(table_name)`

Get detailed information about a table.

**Parameters:**
- `table_name` (str): Name of table

**Returns:**
- `TableInfo`: Object with table details

**Example:**
```python
info = db_manager.get_table_info("files")
print(f"Table: {info.name}")
print(f"Columns: {len(info.columns)}")
print(f"Row count: {info.row_count}")
```

##### `close()`

Close database connection.

**Example:**
```python
db_manager.close()
```

## Data Models

### FileMetadata

Represents metadata extracted from a markdown file.

```python
@dataclass
class FileMetadata:
    path: str
    filename: str
    directory: str
    modified_date: datetime
    created_date: datetime
    file_size: int
    content_hash: str
    word_count: int
    heading_count: int
    title: Optional[str]
    frontmatter: Dict[str, Any]
    tags: List[str]
    links: List[Link]
    content: str
    headings: List[str]
```

**Example:**
```python
metadata = indexer.get_file_metadata("note.md")
print(f"Title: {metadata.title}")
print(f"Tags: {', '.join(metadata.tags)}")
print(f"Word count: {metadata.word_count}")
```

### QueryResult

Contains the results of a query execution.

```python
@dataclass
class QueryResult:
    data: List[Dict[str, Any]]
    columns: List[str]
    row_count: int
    execution_time: float
    query: str
    format: str
```

**Example:**
```python
result = query_engine.execute_query("SELECT * FROM files LIMIT 5")
print(f"Query: {result.query}")
print(f"Columns: {result.columns}")
print(f"Rows: {result.row_count}")
print(f"Execution time: {result.execution_time:.3f}s")
```

### IndexResult

Contains the results of an indexing operation.

```python
@dataclass
class IndexResult:
    files_processed: int
    files_skipped: int
    new_files: int
    updated_files: int
    errors: List[str]
    execution_time: float
    directory: str
```

**Example:**
```python
result = indexer.index_directory("/path/to/notes")
print(f"Processed: {result.files_processed}")
print(f"New: {result.new_files}")
print(f"Updated: {result.updated_files}")
print(f"Time: {result.execution_time:.2f}s")
```

## Configuration API

### SimplifiedConfig

Easy-to-use configuration class.

```python
from mdquery.config import SimplifiedConfig

# Initialize with minimal configuration
config = SimplifiedConfig(notes_dir="/path/to/notes")

# Initialize with custom paths
config = SimplifiedConfig(
    notes_dir="/path/to/notes",
    db_path="/custom/database.db",
    cache_dir="/custom/cache",
    auto_index=True
)

# Save configuration
config.save_config()

# Load configuration
config = SimplifiedConfig.load_config("/path/to/config.json")
```

#### Properties

- `notes_dir`: Path to notes directory
- `db_path`: Path to database file
- `cache_dir`: Path to cache directory
- `auto_index`: Whether to auto-index on startup
- `note_system_type`: Detected note system type

#### Methods

##### `save_config(path=None)`

Save configuration to file.

##### `load_config(path)`

Load configuration from file (class method).

##### `validate()`

Validate configuration settings.

## Complete Example

### Basic Usage

```python
from mdquery.config import SimplifiedConfig
from mdquery.indexer import Indexer
from mdquery.query import QueryEngine
from mdquery.database import DatabaseManager

# 1. Setup configuration
config = SimplifiedConfig(notes_dir="/path/to/notes")

# 2. Initialize components
db_manager = DatabaseManager(config.db_path)
indexer = Indexer(db_manager)
query_engine = QueryEngine(db_manager)

# 3. Index notes
print("Indexing notes...")
index_result = indexer.index_directory(config.notes_dir)
print(f"Indexed {index_result.files_processed} files")

# 4. Query notes
print("\nQuerying notes...")
result = query_engine.execute_query(
    "SELECT filename, word_count FROM files WHERE tags LIKE '%research%'",
    limit=10
)

print(f"Found {result.row_count} research notes:")
for row in result.data:
    print(f"  {row['filename']}: {row['word_count']} words")

# 5. Get schema information
schema = query_engine.get_schema()
print(f"\nDatabase contains {len(schema.tables)} tables")

# 6. Clean up
db_manager.close()
```

### Advanced Usage with Error Handling

```python
import logging
from mdquery.config import SimplifiedConfig
from mdquery.indexer import Indexer
from mdquery.query import QueryEngine
from mdquery.database import DatabaseManager
from mdquery.exceptions import MDQueryError, QueryValidationError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    try:
        # Configuration
        config = SimplifiedConfig(notes_dir="/path/to/notes")
        config.validate()

        # Initialize components
        db_manager = DatabaseManager(config.db_path)
        db_manager.connect()

        indexer = Indexer(db_manager)
        query_engine = QueryEngine(db_manager)

        # Index with error handling
        try:
            logger.info("Starting indexing...")
            result = indexer.incremental_index_directory(config.notes_dir)
            logger.info(f"Indexing complete: {result.files_processed} files")

            if result.errors:
                logger.warning(f"Indexing errors: {len(result.errors)}")
                for error in result.errors:
                    logger.error(f"  {error}")

        except Exception as e:
            logger.error(f"Indexing failed: {e}")
            return

        # Query with validation
        queries = [
            "SELECT COUNT(*) as total_files FROM files",
            "SELECT tag, COUNT(*) as count FROM tags GROUP BY tag ORDER BY count DESC LIMIT 10",
            "SELECT filename FROM files WHERE content MATCH 'python' LIMIT 5"
        ]

        for sql in queries:
            try:
                # Validate query first
                validation = query_engine.validate_query(sql)
                if not validation.is_valid:
                    logger.error(f"Invalid query: {validation.errors}")
                    continue

                # Execute query
                result = query_engine.execute_query(sql, format="json")
                logger.info(f"Query executed: {result.row_count} results in {result.execution_time:.3f}s")

                # Process results
                if result.data:
                    logger.info(f"Sample result: {result.data[0]}")

            except QueryValidationError as e:
                logger.error(f"Query validation error: {e}")
            except Exception as e:
                logger.error(f"Query execution error: {e}")

    except MDQueryError as e:
        logger.error(f"MDQuery error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        # Cleanup
        try:
            db_manager.close()
        except:
            pass

if __name__ == "__main__":
    main()
```

## Error Handling

### Exception Classes

mdquery provides specific exception classes for different error types:

- `MDQueryError`: Base exception class
- `ConfigurationError`: Configuration-related errors
- `IndexingError`: Errors during indexing
- `QueryValidationError`: Query validation failures
- `DatabaseError`: Database operation errors
- `ParsingError`: File parsing errors

### Example Error Handling

```python
from mdquery.exceptions import *

try:
    result = query_engine.execute_query(sql)
except QueryValidationError as e:
    print(f"Query validation failed: {e}")
except DatabaseError as e:
    print(f"Database error: {e}")
except MDQueryError as e:
    print(f"General mdquery error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```