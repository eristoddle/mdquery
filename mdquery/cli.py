"""
Command-line interface for mdquery using click framework.
"""

import sys
import logging
import json
from pathlib import Path
from typing import Optional

import click

from .database import DatabaseManager, DatabaseError
from .indexer import Indexer, IndexingError
from .query import QueryEngine, QueryError, QueryValidationError, QueryExecutionError
from .cache import CacheManager


# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CLIError(Exception):
    """Custom exception for CLI-related errors."""
    pass


def get_database_path(directory: str) -> Path:
    """Get the database path for a given directory."""
    return Path(directory) / '.mdquery' / 'index.db'


def ensure_database_directory(db_path: Path) -> None:
    """Ensure the database directory exists."""
    db_path.parent.mkdir(parents=True, exist_ok=True)


def handle_error(error: Exception, context: str = "") -> None:
    """Handle errors with user-friendly messages."""
    if isinstance(error, (DatabaseError, IndexingError, QueryError)):
        click.echo(f"Error {context}: {error}", err=True)
    elif isinstance(error, FileNotFoundError):
        click.echo(f"Error {context}: File or directory not found: {error.filename}", err=True)
    elif isinstance(error, PermissionError):
        click.echo(f"Error {context}: Permission denied: {error.filename}", err=True)
    else:
        click.echo(f"Unexpected error {context}: {error}", err=True)
        if logger.isEnabledFor(logging.DEBUG):
            logger.exception("Unexpected error details")


@click.group()
@click.version_option(version='1.0.0')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--debug', is_flag=True, help='Enable debug logging')
def cli(verbose: bool, debug: bool):
    """mdquery - Universal markdown querying tool with SQL-like syntax.

    Query your markdown files using SQL syntax across different note-taking systems
    like Obsidian, Joplin, Jekyll, and more.

    Examples:
      mdquery query "SELECT * FROM files WHERE tags LIKE '%research%'"
      mdquery index ./notes --recursive
      mdquery schema --table files
    """
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif verbose:
        logging.getLogger().setLevel(logging.INFO)


@cli.command()
@click.argument('sql_query')
@click.option('--format', '-f', default='table',
              type=click.Choice(['json', 'csv', 'table', 'markdown'], case_sensitive=False),
              help='Output format')
@click.option('--directory', '-d', default='.',
              help='Directory containing indexed markdown files')
@click.option('--limit', '-l', type=int,
              help='Maximum number of results to return')
@click.option('--timeout', '-t', type=float, default=30.0,
              help='Query timeout in seconds')
def query(sql_query: str, format: str, directory: str, limit: Optional[int], timeout: float):
    """Execute a SQL query against indexed markdown files.

    The query will be executed against the database for the specified directory.
    If no index exists, you'll need to run 'mdquery index' first.

    Examples:
      mdquery query "SELECT path, title FROM files_with_metadata WHERE title IS NOT NULL"
      mdquery query "SELECT * FROM files WHERE modified_date > '2024-01-01'" --format json
      mdquery query "SELECT tag, COUNT(*) as count FROM tags GROUP BY tag ORDER BY count DESC" --limit 10
    """
    try:
        # Resolve directory path
        dir_path = Path(directory).resolve()
        if not dir_path.exists():
            raise CLIError(f"Directory does not exist: {directory}")

        # Get database path
        db_path = get_database_path(str(dir_path))
        if not db_path.exists():
            raise CLIError(f"No index found for directory {directory}. Run 'mdquery index {directory}' first.")

        # Initialize database and query engine
        db_manager = DatabaseManager(db_path)
        query_engine = QueryEngine(db_manager)

        # Set query parameters
        if limit:
            query_engine.set_max_results(limit)
        query_engine.set_query_timeout(timeout)

        # Execute query
        result = query_engine.execute_query(sql_query)

        # Format and output results
        formatted_output = query_engine.format_results(result, format.lower())
        click.echo(formatted_output)

        # Show execution stats in verbose mode (but not for JSON format to avoid breaking parsing)
        if logger.isEnabledFor(logging.INFO) and format.lower() != 'json':
            click.echo(f"\nQuery executed in {result.execution_time_ms:.2f}ms, returned {result.row_count} rows", err=True)

    except (QueryValidationError, QueryExecutionError) as e:
        handle_error(e, "executing query")
        sys.exit(1)
    except CLIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        handle_error(e, "executing query")
        sys.exit(1)


@cli.command()
@click.argument('directory', default='.')
@click.option('--recursive/--no-recursive', default=True,
              help='Recursively scan subdirectories')
@click.option('--incremental', '-i', is_flag=True,
              help='Only index modified files (faster)')
@click.option('--rebuild', '-r', is_flag=True,
              help='Rebuild the entire index from scratch')
@click.option('--sync', '-s', is_flag=True,
              help='Synchronize index with current directory state')
def index(directory: str, recursive: bool, incremental: bool, rebuild: bool, sync: bool):
    """Index markdown files in the specified directory.

    Creates a searchable index of all markdown files in the directory.
    The index is stored in a .mdquery subdirectory.

    Examples:
      mdquery index ./notes
      mdquery index ./blog --no-recursive
      mdquery index ./research --incremental
      mdquery index ./docs --rebuild
    """
    try:
        # Resolve directory path
        dir_path = Path(directory).resolve()
        if not dir_path.exists():
            raise CLIError(f"Directory does not exist: {directory}")

        if not dir_path.is_dir():
            raise CLIError(f"Path is not a directory: {directory}")

        # Get database path and ensure directory exists
        db_path = get_database_path(str(dir_path))
        ensure_database_directory(db_path)

        # Initialize components
        db_manager = DatabaseManager(db_path)
        cache_manager = CacheManager(db_path, db_manager)
        indexer = Indexer(db_manager, cache_manager)

        # Initialize database and cache
        db_manager.initialize_database()
        cache_manager.initialize_cache()

        # Choose indexing strategy
        if rebuild:
            click.echo(f"Rebuilding index for {directory}...")
            stats = indexer.rebuild_index(dir_path)
        elif sync:
            click.echo(f"Synchronizing index for {directory}...")
            stats = indexer.sync_directory_index(dir_path, recursive)
        elif incremental:
            click.echo(f"Incrementally indexing {directory}...")
            stats = indexer.incremental_index_directory(dir_path, recursive)
        else:
            click.echo(f"Indexing {directory}...")
            stats = indexer.index_directory(dir_path, recursive)

        # Display results
        if sync:
            click.echo(f"Sync complete:")
            click.echo(f"  Files added: {stats.get('files_added', 0)}")
            click.echo(f"  Files updated: {stats.get('files_updated', 0)}")
            click.echo(f"  Files removed: {stats.get('files_removed', 0)}")
            click.echo(f"  Files unchanged: {stats.get('files_unchanged', 0)}")
            if stats.get('errors', 0) > 0:
                click.echo(f"  Errors: {stats['errors']}")
        else:
            click.echo(f"Indexing complete:")
            click.echo(f"  Files processed: {stats.get('files_processed', 0)}")
            if 'files_updated' in stats:
                click.echo(f"  Files updated: {stats['files_updated']}")
            click.echo(f"  Files skipped: {stats.get('files_skipped', 0)}")
            if stats.get('errors', 0) > 0:
                click.echo(f"  Errors: {stats['errors']}")

        # Show total file count
        total_files = indexer.get_file_count()
        click.echo(f"  Total files in index: {total_files}")

    except IndexingError as e:
        handle_error(e, "indexing files")
        sys.exit(1)
    except CLIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        handle_error(e, "indexing files")
        sys.exit(1)


@cli.command()
@click.option('--table', '-t', help='Show schema for specific table or view')
@click.option('--directory', '-d', default='.',
              help='Directory containing the index')
@click.option('--format', '-f', default='table',
              type=click.Choice(['json', 'table'], case_sensitive=False),
              help='Output format')
def schema(table: Optional[str], directory: str, format: str):
    """Display database schema information.

    Shows the structure of the indexed database including tables, columns,
    and row counts. Useful for understanding what data is available for querying.

    Examples:
      mdquery schema
      mdquery schema --table files
      mdquery schema --format json
    """
    try:
        # Resolve directory path
        dir_path = Path(directory).resolve()
        if not dir_path.exists():
            raise CLIError(f"Directory does not exist: {directory}")

        # Get database path
        db_path = get_database_path(str(dir_path))
        if not db_path.exists():
            raise CLIError(f"No index found for directory {directory}. Run 'mdquery index {directory}' first.")

        # Initialize database manager
        db_manager = DatabaseManager(db_path)
        schema_info = db_manager.get_schema_info()

        if format.lower() == 'json':
            # Output as JSON
            click.echo(json.dumps(schema_info, indent=2, default=str))
        else:
            # Output as formatted table
            if table:
                # Show specific table
                if table in schema_info['tables']:
                    table_info = schema_info['tables'][table]
                    click.echo(f"Table: {table}")
                    click.echo(f"Rows: {table_info['row_count']}")
                    click.echo("\nColumns:")
                    for col in table_info['columns']:
                        pk_marker = " (PK)" if col['primary_key'] else ""
                        null_marker = " NOT NULL" if col['not_null'] else ""
                        click.echo(f"  {col['name']}: {col['type']}{pk_marker}{null_marker}")
                elif table in schema_info['views']:
                    view_info = schema_info['views'][table]
                    click.echo(f"View: {table}")
                    click.echo(f"Definition: {view_info['sql']}")
                else:
                    raise CLIError(f"Table or view '{table}' not found")
            else:
                # Show all tables and views
                click.echo(f"Database Schema (Version {schema_info['version']})")
                click.echo("=" * 50)

                click.echo("\nTables:")
                for table_name, table_info in schema_info['tables'].items():
                    click.echo(f"  {table_name}: {table_info['row_count']} rows")

                if schema_info['views']:
                    click.echo("\nViews:")
                    for view_name in schema_info['views'].keys():
                        click.echo(f"  {view_name}")

                if schema_info['indexes']:
                    click.echo(f"\nIndexes: {len(schema_info['indexes'])}")

                click.echo(f"\nUse --table <name> to see detailed information about a specific table or view.")

    except CLIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        handle_error(e, "retrieving schema")
        sys.exit(1)


@cli.command()
@click.option('--directory', '-d', default='.',
              help='Directory containing the index')
def examples(directory: str):
    """Show example queries for the indexed data.

    Displays a collection of useful example queries that demonstrate
    the capabilities of mdquery and help users get started.
    """
    try:
        # Resolve directory path
        dir_path = Path(directory).resolve()
        if not dir_path.exists():
            raise CLIError(f"Directory does not exist: {directory}")

        # Get database path
        db_path = get_database_path(str(dir_path))
        if not db_path.exists():
            raise CLIError(f"No index found for directory {directory}. Run 'mdquery index {directory}' first.")

        # Initialize query engine to get sample queries
        db_manager = DatabaseManager(db_path)
        query_engine = QueryEngine(db_manager)
        sample_queries = query_engine.get_sample_queries()

        click.echo("Example Queries")
        click.echo("=" * 50)

        for i, query_info in enumerate(sample_queries, 1):
            click.echo(f"\n{i}. {query_info['name']}")
            click.echo(f"   {query_info['description']}")
            click.echo(f"   mdquery query \"{query_info['query']}\"")

        click.echo(f"\nTip: Use --format json or --format csv to get machine-readable output")
        click.echo(f"Tip: Use --limit N to restrict the number of results")

    except CLIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        handle_error(e, "retrieving examples")
        sys.exit(1)


@cli.command()
@click.argument('file_path')
@click.option('--directory', '-d', default='.',
              help='Directory containing the index')
def remove(file_path: str, directory: str):
    """Remove a specific file from the index.

    Removes the specified file from the search index. Useful when files
    have been deleted or moved outside of mdquery.

    Examples:
      mdquery remove ./notes/old-file.md
      mdquery remove /path/to/deleted/file.md
    """
    try:
        # Resolve paths
        dir_path = Path(directory).resolve()
        target_file = Path(file_path).resolve()

        if not dir_path.exists():
            raise CLIError(f"Directory does not exist: {directory}")

        # Get database path
        db_path = get_database_path(str(dir_path))
        if not db_path.exists():
            raise CLIError(f"No index found for directory {directory}. Run 'mdquery index {directory}' first.")

        # Initialize components
        db_manager = DatabaseManager(db_path)
        cache_manager = CacheManager(db_path, db_manager)
        indexer = Indexer(db_manager, cache_manager)

        # Remove file from index
        if indexer.remove_file_from_index(target_file):
            click.echo(f"Removed {file_path} from index")
        else:
            click.echo(f"File {file_path} was not found in index")

    except CLIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        handle_error(e, "removing file from index")
        sys.exit(1)


if __name__ == '__main__':
    cli()