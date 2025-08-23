"""
Command-line interface for mdquery using click framework.
"""

import sys
import logging
import json
from pathlib import Path
from typing import Optional
from datetime import datetime

import click

from .database import DatabaseManager
from .indexer import Indexer
from .query import QueryEngine
from .cache import CacheManager
from .research import ResearchEngine, ResearchFilter
from .exceptions import (
    MdqueryError, DatabaseError, IndexingError, QueryError,
    QueryValidationError, QueryExecutionError, QueryTimeoutError,
    FileAccessError, FileCorruptedError, DirectoryNotFoundError,
    PerformanceError, ResourceError, format_error_context
)
from .logging_config import setup_logging, log_error, get_logging_statistics

logger = logging.getLogger(__name__)


class CLIError(MdqueryError):
    """Custom exception for CLI-related errors."""
    pass


def get_database_path(directory: str) -> Path:
    """Get the database path for a given directory."""
    return Path(directory) / '.mdquery' / 'index.db'


def ensure_database_directory(db_path: Path) -> None:
    """Ensure the database directory exists."""
    try:
        db_path.parent.mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError) as e:
        raise CLIError(f"Cannot create database directory: {e}") from e


def handle_error(error: Exception, context: str = "", verbose: bool = False) -> None:
    """
    Handle errors with user-friendly messages and appropriate exit codes.

    Args:
        error: Exception that occurred
        context: Context description for the error
        verbose: Whether to show detailed error information
    """
    if isinstance(error, MdqueryError):
        # Handle known mdquery errors with context
        error_context = format_error_context(error)
        if verbose and error_context != "no context":
            click.echo(f"Error {context}: {error} | {error_context}", err=True)
        else:
            click.echo(f"Error {context}: {error}", err=True)

        # Set appropriate exit codes
        if isinstance(error, (FileAccessError, DirectoryNotFoundError)):
            sys.exit(2)  # File/directory not found
        elif isinstance(error, QueryValidationError):
            sys.exit(3)  # Invalid query
        elif isinstance(error, QueryTimeoutError):
            sys.exit(4)  # Timeout
        elif isinstance(error, (PerformanceError, ResourceError)):
            sys.exit(5)  # Resource/performance issues
        else:
            sys.exit(1)  # General error

    elif isinstance(error, FileNotFoundError):
        click.echo(f"Error {context}: File or directory not found: {error.filename}", err=True)
        sys.exit(2)
    elif isinstance(error, PermissionError):
        click.echo(f"Error {context}: Permission denied: {error.filename}", err=True)
        sys.exit(2)
    else:
        # Unexpected error
        click.echo(f"Unexpected error {context}: {error}", err=True)
        if verbose:
            import traceback
            click.echo(traceback.format_exc(), err=True)
        sys.exit(1)


@click.group()
@click.version_option(version='1.0.0')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.option('--log-file', type=click.Path(), help='Log file path')
@click.option('--structured-logs', is_flag=True, help='Enable structured JSON logging')
@click.pass_context
def cli(ctx: click.Context, verbose: bool, debug: bool, log_file: Optional[str], structured_logs: bool):
    """mdquery - Universal markdown querying tool with SQL-like syntax.

    Query your markdown files using SQL syntax across different note-taking systems
    like Obsidian, Joplin, Jekyll, and more.

    Examples:
      mdquery query "SELECT * FROM files WHERE tags LIKE '%research%'"
      mdquery index ./notes --recursive
      mdquery schema --table files
    """
    # Set up logging based on options
    level = "DEBUG" if debug else ("INFO" if verbose else "WARNING")
    log_file_path = Path(log_file) if log_file else None

    try:
        setup_logging(
            level=level,
            log_file=log_file_path,
            structured=structured_logs,
            enable_performance_monitoring=True
        )
    except Exception as e:
        click.echo(f"Failed to setup logging: {e}", err=True)
        sys.exit(1)

    # Store options in context for use by subcommands
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose or debug
    ctx.obj['debug'] = debug


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
@click.pass_context
def query(ctx: click.Context, sql_query: str, format: str, directory: str,
          limit: Optional[int], timeout: float):
    """Execute a SQL query against indexed markdown files.

    The query will be executed against the database for the specified directory.
    If no index exists, you'll need to run 'mdquery index' first.

    Examples:
      mdquery query "SELECT path, title FROM files_with_metadata WHERE title IS NOT NULL"
      mdquery query "SELECT * FROM files WHERE modified_date > '2024-01-01'" --format json
      mdquery query "SELECT tag, COUNT(*) as count FROM tags GROUP BY tag ORDER BY count DESC" --limit 10
    """
    verbose = ctx.obj.get('verbose', False)

    try:
        # Get database path and check if it exists
        db_path = get_database_path(directory)
        if not db_path.exists():
            raise CLIError(f"No index found for directory '{directory}'. Run 'mdquery index {directory}' first.")

        # Initialize database and query engine
        try:
            db_manager = DatabaseManager(db_path)
            query_engine = QueryEngine(db_manager)
        except Exception as e:
            raise CLIError(f"Failed to initialize database: {e}") from e

        # Configure query engine
        if limit:
            query_engine.set_max_results(limit)
        query_engine.set_query_timeout(timeout)

        # Execute query
        logger.info(f"Executing query: {sql_query}")
        result = query_engine.execute_query(sql_query)

        # Format and output results
        try:
            formatted_output = query_engine.format_results(result, format)
            click.echo(formatted_output)
        except Exception as e:
            raise CLIError(f"Failed to format results: {e}") from e

        # Log performance info in verbose mode
        if verbose:
            click.echo(f"\n# Query executed in {result.execution_time_ms:.2f}ms, returned {result.row_count} rows", err=True)

    except (MdqueryError, FileNotFoundError, PermissionError) as e:
        handle_error(e, "executing query", verbose)
    except KeyboardInterrupt:
        click.echo("\nQuery interrupted by user", err=True)
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        wrapped_error = CLIError(f"Unexpected error during query execution: {e}")
        log_error(wrapped_error, logger, {'query': sql_query, 'directory': directory})
        handle_error(wrapped_error, "executing query", verbose)
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


@cli.command()
@click.option('--directory', '-d', default='.',
              help='Directory containing the index')
@click.option('--format', '-f', default='table',
              type=click.Choice(['json', 'table'], case_sensitive=False),
              help='Output format')
@click.option('--files', help='Comma-separated list of specific files to analyze')
def seo(directory: str, format: str, files: Optional[str]):
    """Analyze SEO aspects of markdown files.

    Performs SEO analysis including title, description, category validation,
    content length analysis, and identifies common SEO issues.

    Examples:
      mdquery seo
      mdquery seo --files "blog/post1.md,blog/post2.md"
      mdquery seo --format json
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

        # Initialize query engine and get advanced engine
        db_manager = DatabaseManager(db_path)
        query_engine = QueryEngine(db_manager)
        advanced_engine = query_engine.get_advanced_engine()

        # Parse file list if provided
        file_paths = None
        if files:
            file_paths = [f.strip() for f in files.split(',')]

        # Perform SEO analysis
        analyses = advanced_engine.analyze_seo(file_paths)

        if format.lower() == 'json':
            # Convert to JSON-serializable format
            json_data = []
            for analysis in analyses:
                json_data.append({
                    'file_path': analysis.file_path,
                    'title': analysis.title,
                    'description': analysis.description,
                    'category': analysis.category,
                    'word_count': analysis.word_count,
                    'heading_count': analysis.heading_count,
                    'tags': analysis.tags,
                    'issues': analysis.issues,
                    'score': analysis.score
                })
            click.echo(json.dumps(json_data, indent=2))
        else:
            # Format as table
            click.echo("SEO Analysis Results")
            click.echo("=" * 80)

            for analysis in analyses:
                click.echo(f"\nFile: {analysis.file_path}")
                click.echo(f"Score: {analysis.score:.1f}/100")
                click.echo(f"Title: {analysis.title or 'MISSING'}")
                click.echo(f"Description: {analysis.description or 'MISSING'}")
                click.echo(f"Category: {analysis.category or 'MISSING'}")
                click.echo(f"Word Count: {analysis.word_count}")
                click.echo(f"Headings: {analysis.heading_count}")
                click.echo(f"Tags: {', '.join(analysis.tags) if analysis.tags else 'NONE'}")

                if analysis.issues:
                    click.echo("Issues:")
                    for issue in analysis.issues:
                        click.echo(f"  - {issue}")

    except CLIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        handle_error(e, "performing SEO analysis")
        sys.exit(1)


@cli.command()
@click.option('--directory', '-d', default='.',
              help='Directory containing the index')
@click.option('--format', '-f', default='table',
              type=click.Choice(['json', 'table'], case_sensitive=False),
              help='Output format')
@click.option('--files', help='Comma-separated list of specific files to analyze')
def structure(directory: str, format: str, files: Optional[str]):
    """Analyze content structure and hierarchy.

    Examines heading hierarchy, content organization, readability,
    and identifies structural issues in markdown files.

    Examples:
      mdquery structure
      mdquery structure --files "docs/guide.md"
      mdquery structure --format json
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

        # Initialize query engine and get advanced engine
        db_manager = DatabaseManager(db_path)
        query_engine = QueryEngine(db_manager)
        advanced_engine = query_engine.get_advanced_engine()

        # Parse file list if provided
        file_paths = None
        if files:
            file_paths = [f.strip() for f in files.split(',')]

        # Perform structure analysis
        analyses = advanced_engine.analyze_content_structure(file_paths)

        if format.lower() == 'json':
            # Convert to JSON-serializable format
            json_data = []
            for analysis in analyses:
                json_data.append({
                    'file_path': analysis.file_path,
                    'heading_hierarchy': analysis.heading_hierarchy,
                    'word_count': analysis.word_count,
                    'paragraph_count': analysis.paragraph_count,
                    'readability_score': analysis.readability_score,
                    'structure_issues': analysis.structure_issues
                })
            click.echo(json.dumps(json_data, indent=2))
        else:
            # Format as table
            click.echo("Content Structure Analysis")
            click.echo("=" * 80)

            for analysis in analyses:
                click.echo(f"\nFile: {analysis.file_path}")
                click.echo(f"Word Count: {analysis.word_count}")
                click.echo(f"Paragraphs: {analysis.paragraph_count}")
                if analysis.readability_score:
                    click.echo(f"Readability Score: {analysis.readability_score:.1f}")

                if analysis.heading_hierarchy:
                    click.echo("Heading Hierarchy:")
                    for heading in analysis.heading_hierarchy:
                        indent = "  " * (heading['level'] - 1)
                        click.echo(f"  {indent}H{heading['level']}: {heading['text']}")

                if analysis.structure_issues:
                    click.echo("Structure Issues:")
                    for issue in analysis.structure_issues:
                        click.echo(f"  - {issue}")

    except CLIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        handle_error(e, "performing structure analysis")
        sys.exit(1)


@cli.command()
@click.argument('file_path')
@click.option('--directory', '-d', default='.',
              help='Directory containing the index')
@click.option('--threshold', '-t', default=0.3, type=float,
              help='Similarity threshold (0.0 to 1.0)')
@click.option('--format', '-f', default='table',
              type=click.Choice(['json', 'table'], case_sensitive=False),
              help='Output format')
def similar(file_path: str, directory: str, threshold: float, format: str):
    """Find content similar to the specified file.

    Uses tag overlap to identify files with similar content based on
    shared tags and calculates similarity scores.

    Examples:
      mdquery similar "research/ai-paper.md"
      mdquery similar "blog/post.md" --threshold 0.5
      mdquery similar "notes/topic.md" --format json
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

        # Initialize query engine and get advanced engine
        db_manager = DatabaseManager(db_path)
        query_engine = QueryEngine(db_manager)
        advanced_engine = query_engine.get_advanced_engine()

        # Find similar content
        similarities = advanced_engine.find_similar_content(file_path, threshold)

        if format.lower() == 'json':
            # Convert to JSON-serializable format
            json_data = []
            for sim in similarities:
                json_data.append({
                    'file1_path': sim.file1_path,
                    'file2_path': sim.file2_path,
                    'common_tags': sim.common_tags,
                    'similarity_score': sim.similarity_score,
                    'total_tags_file1': sim.total_tags_file1,
                    'total_tags_file2': sim.total_tags_file2
                })
            click.echo(json.dumps(json_data, indent=2))
        else:
            # Format as table
            if not similarities:
                click.echo(f"No similar files found for {file_path} (threshold: {threshold})")
                return

            click.echo(f"Similar Files to {file_path}")
            click.echo("=" * 80)

            for sim in similarities:
                click.echo(f"\nFile: {sim.file2_path}")
                click.echo(f"Similarity: {sim.similarity_score:.3f}")
                click.echo(f"Common Tags ({len(sim.common_tags)}): {', '.join(sim.common_tags)}")
                click.echo(f"Tag Counts: {sim.total_tags_file1} vs {sim.total_tags_file2}")

    except CLIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        handle_error(e, "finding similar content")
        sys.exit(1)


@cli.command()
@click.option('--directory', '-d', default='.',
              help='Directory containing the index')
@click.option('--format', '-f', default='table',
              type=click.Choice(['json', 'table'], case_sensitive=False),
              help='Output format')
def links(directory: str, format: str):
    """Analyze link relationships between files.

    Identifies bidirectional links, link strength, and relationship patterns
    to understand content connectivity and navigation structure.

    Examples:
      mdquery links
      mdquery links --format json
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

        # Initialize query engine and get advanced engine
        db_manager = DatabaseManager(db_path)
        query_engine = QueryEngine(db_manager)
        advanced_engine = query_engine.get_advanced_engine()

        # Analyze link relationships
        analyses = advanced_engine.analyze_link_relationships()

        if format.lower() == 'json':
            # Convert to JSON-serializable format
            json_data = []
            for analysis in analyses:
                json_data.append({
                    'source_file': analysis.source_file,
                    'target_file': analysis.target_file,
                    'link_type': analysis.link_type,
                    'is_bidirectional': analysis.is_bidirectional,
                    'link_strength': analysis.link_strength
                })
            click.echo(json.dumps(json_data, indent=2))
        else:
            # Format as table
            if not analyses:
                click.echo("No link relationships found")
                return

            click.echo("Link Relationship Analysis")
            click.echo("=" * 80)

            for analysis in analyses[:20]:  # Show top 20
                bidirectional = " (bidirectional)" if analysis.is_bidirectional else ""
                click.echo(f"\n{analysis.source_file} -> {analysis.target_file}")
                click.echo(f"  Type: {analysis.link_type}{bidirectional}")
                click.echo(f"  Strength: {analysis.link_strength:.1f}")

    except CLIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        handle_error(e, "analyzing link relationships")
        sys.exit(1)


@cli.command()
@click.option('--directory', '-d', default='.',
              help='Directory containing the index')
@click.option('--format', '-f', default='table',
              type=click.Choice(['json', 'table'], case_sensitive=False),
              help='Output format')
def report(directory: str, format: str):
    """Generate comprehensive content analysis report.

    Provides aggregated statistics and insights about the entire
    markdown collection including SEO, structure, and relationship metrics.

    Examples:
      mdquery report
      mdquery report --format json
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

        # Initialize query engine and get advanced engine
        db_manager = DatabaseManager(db_path)
        query_engine = QueryEngine(db_manager)
        advanced_engine = query_engine.get_advanced_engine()

        # Generate comprehensive report
        report_data = advanced_engine.generate_content_report()

        if format.lower() == 'json':
            click.echo(json.dumps(report_data, indent=2, default=str))
        else:
            # Format as readable report
            click.echo("Content Analysis Report")
            click.echo("=" * 80)

            # Basic statistics
            stats = report_data.get('basic_stats', {})
            click.echo(f"\nBasic Statistics:")
            click.echo(f"  Total Files: {stats.get('total_files', 0)}")
            click.echo(f"  Total Words: {stats.get('total_words', 0):,}")
            click.echo(f"  Average Words per File: {stats.get('avg_word_count', 0):.1f}")
            click.echo(f"  Empty Files: {stats.get('empty_files', 0)}")

            # Tag statistics
            tag_stats = report_data.get('tag_stats', {})
            click.echo(f"\nTag Statistics:")
            click.echo(f"  Unique Tags: {tag_stats.get('unique_tags', 0)}")
            click.echo(f"  Average Tags per File: {tag_stats.get('avg_tags_per_file', 0):.1f}")

            # Popular tags
            popular_tags = report_data.get('popular_tags', [])[:10]
            if popular_tags:
                click.echo(f"\nMost Popular Tags:")
                for tag_info in popular_tags:
                    click.echo(f"  {tag_info['tag']}: {tag_info['usage_count']} files")

            # Frontmatter coverage
            frontmatter = report_data.get('frontmatter_coverage', [])[:10]
            if frontmatter:
                click.echo(f"\nFrontmatter Field Coverage:")
                for field_info in frontmatter:
                    click.echo(f"  {field_info['key']}: {field_info['coverage_percent']:.1f}% ({field_info['file_count']} files)")

            # Quality issues
            quality_issues = report_data.get('quality_issues', [])[:10]
            if quality_issues:
                click.echo(f"\nContent Quality Issues:")
                for issue in quality_issues:
                    click.echo(f"  {issue['path']}: {issue['issue_type']} ({issue['word_count']} words)")

    except CLIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        handle_error(e, "generating report")
        sys.exit(1)


@cli.command()
@click.argument('aggregation_name')
@click.option('--directory', '-d', default='.',
              help='Directory containing the index')
@click.option('--format', '-f', default='table',
              type=click.Choice(['json', 'csv', 'table', 'markdown'], case_sensitive=False),
              help='Output format')
def aggregate(aggregation_name: str, directory: str, format: str):
    """Execute predefined aggregation queries for reporting.

    Available aggregations:
      files_by_directory - File counts and word statistics by directory
      content_by_month - Content creation/modification trends by month
      tag_cooccurrence - Tags that frequently appear together
      link_popularity - Most linked-to content
      word_count_distribution - Distribution of content lengths

    Examples:
      mdquery aggregate files_by_directory
      mdquery aggregate tag_cooccurrence --format csv
      mdquery aggregate word_count_distribution
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

        # Initialize query engine and get advanced engine
        db_manager = DatabaseManager(db_path)
        query_engine = QueryEngine(db_manager)
        advanced_engine = query_engine.get_advanced_engine()

        # Execute aggregation query
        result = advanced_engine.execute_aggregation_query(aggregation_name)

        # Format and output results
        formatted_output = query_engine.format_results(result, format.lower())
        click.echo(formatted_output)

        # Show execution stats in verbose mode (but not for JSON format to avoid breaking parsing)
        if logger.isEnabledFor(logging.INFO) and format.lower() != 'json':
            click.echo(f"\nQuery executed in {result.execution_time_ms:.2f}ms, returned {result.row_count} rows", err=True)

    except CLIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        handle_error(e, "executing aggregation query")
        sys.exit(1)


@cli.command()
@click.argument('search_text')
@click.option('--directory', '-d', default='.',
              help='Directory containing the index')
@click.option('--threshold', '-t', default=0.6, type=float,
              help='Similarity threshold (0.0 to 1.0)')
@click.option('--max-results', '-m', default=50, type=int,
              help='Maximum number of results to return')
@click.option('--fields', default='content,title,headings',
              help='Fields to search in (comma-separated)')
@click.option('--format', '-f', default='table',
              type=click.Choice(['json', 'table'], case_sensitive=False),
              help='Output format')
def fuzzy(search_text: str, directory: str, threshold: float, max_results: int, fields: str, format: str):
    """Perform fuzzy text matching for related content discovery.

    Uses multiple algorithms including sequence matching and n-gram analysis
    to find content similar to the search text across all indexed files.

    Examples:
      mdquery fuzzy "machine learning algorithms"
      mdquery fuzzy "data visualization" --threshold 0.7
      mdquery fuzzy "research methodology" --fields content --format json
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

        # Initialize research engine
        db_manager = DatabaseManager(db_path)
        query_engine = QueryEngine(db_manager)
        research_engine = ResearchEngine(query_engine)

        # Parse search fields
        search_fields = [field.strip() for field in fields.split(',')]

        # Perform fuzzy search
        matches = research_engine.fuzzy_search(
            search_text, threshold, max_results, search_fields
        )

        if format.lower() == 'json':
            # Convert to JSON-serializable format
            json_data = []
            for match in matches:
                json_data.append({
                    'file_path': match.file_path,
                    'matched_text': match.matched_text,
                    'similarity_score': match.similarity_score,
                    'context_before': match.context_before,
                    'context_after': match.context_after,
                    'match_type': match.match_type,
                    'line_number': match.line_number
                })
            click.echo(json.dumps(json_data, indent=2))
        else:
            # Format as table
            if not matches:
                click.echo(f"No fuzzy matches found for '{search_text}' (threshold: {threshold})")
                return

            click.echo(f"Fuzzy Search Results for '{search_text}'")
            click.echo("=" * 80)

            for match in matches:
                click.echo(f"\nFile: {match.file_path}")
                click.echo(f"Type: {match.match_type}")
                click.echo(f"Similarity: {match.similarity_score:.3f}")
                if match.line_number:
                    click.echo(f"Line: {match.line_number}")
                click.echo(f"Match: {match.matched_text}")
                if match.context_before or match.context_after:
                    click.echo(f"Context: ...{match.context_before} [{match.matched_text}] {match.context_after}...")

    except CLIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        handle_error(e, "performing fuzzy search")
        sys.exit(1)


@cli.command()
@click.argument('query_text')
@click.argument('collections', nargs=-1, required=True)
@click.option('--directory', '-d', default='.',
              help='Directory containing the index')
@click.option('--max-per-collection', '-m', default=20, type=int,
              help='Maximum results per collection')
@click.option('--format', '-f', default='table',
              type=click.Choice(['json', 'table'], case_sensitive=False),
              help='Output format')
def cross_search(query_text: str, collections: tuple, directory: str, max_per_collection: int, format: str):
    """Perform cross-collection querying for multiple note sources.

    Searches across different collections (directories or source types)
    and returns unified results with relevance scoring.

    Examples:
      mdquery cross-search "artificial intelligence" notes research papers
      mdquery cross-search "data analysis" blog docs --max-per-collection 10
      mdquery cross-search "machine learning" projects/ml research/ai --format json
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

        # Initialize research engine
        db_manager = DatabaseManager(db_path)
        query_engine = QueryEngine(db_manager)
        research_engine = ResearchEngine(query_engine)

        # Perform cross-collection search
        results = research_engine.cross_collection_search(
            query_text, list(collections), max_per_collection
        )

        if format.lower() == 'json':
            # Convert to JSON-serializable format
            json_data = []
            for result in results:
                json_data.append({
                    'collection_name': result.collection_name,
                    'file_path': result.file_path,
                    'relevance_score': result.relevance_score,
                    'matched_fields': result.matched_fields,
                    'metadata': result.metadata
                })
            click.echo(json.dumps(json_data, indent=2, default=str))
        else:
            # Format as table
            if not results:
                click.echo(f"No results found for '{query_text}' in collections: {', '.join(collections)}")
                return

            click.echo(f"Cross-Collection Search Results for '{query_text}'")
            click.echo("=" * 80)

            current_collection = None
            for result in results:
                if result.collection_name != current_collection:
                    current_collection = result.collection_name
                    click.echo(f"\n--- Collection: {current_collection} ---")

                click.echo(f"\nFile: {result.file_path}")
                click.echo(f"Relevance: {result.relevance_score:.3f}")
                click.echo(f"Matched Fields: {', '.join(result.matched_fields)}")

                metadata = result.metadata
                if metadata.get('author'):
                    click.echo(f"Author: {metadata['author']}")
                if metadata.get('category'):
                    click.echo(f"Category: {metadata['category']}")
                if metadata.get('tags'):
                    click.echo(f"Tags: {', '.join(metadata['tags'])}")

    except CLIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        handle_error(e, "performing cross-collection search")
        sys.exit(1)


@cli.command()
@click.option('--directory', '-d', default='.',
              help='Directory containing the index')
@click.option('--files', help='Comma-separated list of specific files to process')
@click.option('--patterns', help='Custom regex patterns for quote detection (comma-separated)')
@click.option('--format', '-f', default='table',
              type=click.Choice(['json', 'table'], case_sensitive=False),
              help='Output format')
def quotes(directory: str, files: Optional[str], patterns: Optional[str], format: str):
    """Extract quotes and references with source attribution preservation.

    Identifies quoted text, citations, and references while preserving
    source attribution information for proper citation.

    Examples:
      mdquery quotes
      mdquery quotes --files "research/paper1.md,notes/quotes.md"
      mdquery quotes --patterns '"([^"]{20,})"' --format json
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

        # Initialize research engine
        db_manager = DatabaseManager(db_path)
        query_engine = QueryEngine(db_manager)
        research_engine = ResearchEngine(query_engine)

        # Parse file list if provided
        file_paths = None
        if files:
            file_paths = [f.strip() for f in files.split(',')]

        # Parse custom patterns if provided
        quote_patterns = None
        if patterns:
            quote_patterns = [p.strip() for p in patterns.split(',')]

        # Extract quotes with attribution
        attributions = research_engine.extract_quotes_with_attribution(file_paths, quote_patterns)

        if format.lower() == 'json':
            # Convert to JSON-serializable format
            json_data = []
            for attr in attributions:
                json_data.append({
                    'source_file': attr.source_file,
                    'quote_text': attr.quote_text,
                    'context': attr.context,
                    'author': attr.author,
                    'title': attr.title,
                    'date': attr.date,
                    'page_number': attr.page_number,
                    'url': attr.url,
                    'citation_format': attr.citation_format
                })
            click.echo(json.dumps(json_data, indent=2))
        else:
            # Format as table
            if not attributions:
                click.echo("No quotes found with the specified criteria")
                return

            click.echo("Extracted Quotes with Source Attribution")
            click.echo("=" * 80)

            for attr in attributions:
                click.echo(f"\nSource: {attr.source_file}")
                click.echo(f"Quote: \"{attr.quote_text}\"")
                if attr.author:
                    click.echo(f"Author: {attr.author}")
                if attr.title:
                    click.echo(f"Title: {attr.title}")
                if attr.date:
                    click.echo(f"Date: {attr.date}")
                if attr.url:
                    click.echo(f"URL: {attr.url}")
                click.echo(f"Citation: {attr.citation_format}")
                if len(attr.context) > 100:
                    click.echo(f"Context: {attr.context[:100]}...")
                else:
                    click.echo(f"Context: {attr.context}")

    except CLIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        handle_error(e, "extracting quotes")
        sys.exit(1)


@cli.command()
@click.option('--directory', '-d', default='.',
              help='Directory containing the index')
@click.option('--date-from', type=click.DateTime(formats=['%Y-%m-%d']),
              help='Filter from date (YYYY-MM-DD)')
@click.option('--date-to', type=click.DateTime(formats=['%Y-%m-%d']),
              help='Filter to date (YYYY-MM-DD)')
@click.option('--topics', help='Filter by topics/tags (comma-separated)')
@click.option('--sources', help='Filter by source paths (comma-separated)')
@click.option('--authors', help='Filter by authors (comma-separated)')
@click.option('--collections', help='Filter by collections/directories (comma-separated)')
@click.option('--format', '-f', default='table',
              type=click.Choice(['json', 'csv', 'table', 'markdown'], case_sensitive=False),
              help='Output format')
def research_filter(directory: str, date_from: Optional[datetime], date_to: Optional[datetime],
                   topics: Optional[str], sources: Optional[str], authors: Optional[str],
                   collections: Optional[str], format: str):
    """Filter content by research criteria including date ranges and topics.

    Provides advanced filtering for research organization based on
    multiple criteria including dates, topics, sources, and authors.

    Examples:
      mdquery research-filter --date-from 2024-01-01 --topics "machine learning,AI"
      mdquery research-filter --authors "Smith,Johnson" --format json
      mdquery research-filter --collections "research,papers" --date-to 2024-06-01
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

        # Initialize research engine
        db_manager = DatabaseManager(db_path)
        query_engine = QueryEngine(db_manager)
        research_engine = ResearchEngine(query_engine)

        # Build research filter
        research_filter = ResearchFilter(
            date_from=date_from,
            date_to=date_to,
            topics=[t.strip() for t in topics.split(',')] if topics else None,
            sources=[s.strip() for s in sources.split(',')] if sources else None,
            authors=[a.strip() for a in authors.split(',')] if authors else None,
            collections=[c.strip() for c in collections.split(',')] if collections else None
        )

        # Apply filter
        result = research_engine.filter_by_research_criteria(research_filter)

        # Format and output results
        formatted_output = query_engine.format_results(result, format.lower())
        click.echo(formatted_output)

        # Show execution stats in verbose mode (but not for JSON format to avoid breaking parsing)
        if logger.isEnabledFor(logging.INFO) and format.lower() != 'json':
            click.echo(f"\nQuery executed in {result.execution_time_ms:.2f}ms, returned {result.row_count} rows", err=True)

    except CLIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        handle_error(e, "filtering research content")
        sys.exit(1)


@cli.command()
@click.option('--directory', '-d', default='.',
              help='Directory containing the index')
@click.option('--date-from', type=click.DateTime(formats=['%Y-%m-%d']),
              help='Filter from date (YYYY-MM-DD)')
@click.option('--date-to', type=click.DateTime(formats=['%Y-%m-%d']),
              help='Filter to date (YYYY-MM-DD)')
@click.option('--topics', help='Filter by topics/tags (comma-separated)')
@click.option('--sources', help='Filter by source paths (comma-separated)')
@click.option('--authors', help='Filter by authors (comma-separated)')
@click.option('--collections', help='Filter by collections/directories (comma-separated)')
@click.option('--format', '-f', default='table',
              type=click.Choice(['json', 'table'], case_sensitive=False),
              help='Output format')
def research_summary(directory: str, date_from: Optional[datetime], date_to: Optional[datetime],
                    topics: Optional[str], sources: Optional[str], authors: Optional[str],
                    collections: Optional[str], format: str):
    """Generate comprehensive research summary and statistics.

    Provides overview of research content including source distribution,
    temporal patterns, topic analysis, and content metrics.

    Examples:
      mdquery research-summary
      mdquery research-summary --topics "AI,ML" --format json
      mdquery research-summary --date-from 2024-01-01 --authors "Smith"
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

        # Initialize research engine
        db_manager = DatabaseManager(db_path)
        query_engine = QueryEngine(db_manager)
        research_engine = ResearchEngine(query_engine)

        # Build research filter if any criteria provided
        research_filter = None
        if any([date_from, date_to, topics, sources, authors, collections]):
            research_filter = ResearchFilter(
                date_from=date_from,
                date_to=date_to,
                topics=[t.strip() for t in topics.split(',')] if topics else None,
                sources=[s.strip() for s in sources.split(',')] if sources else None,
                authors=[a.strip() for a in authors.split(',')] if authors else None,
                collections=[c.strip() for c in collections.split(',')] if collections else None
            )

        # Generate research summary
        summary = research_engine.generate_research_summary(research_filter)

        if format.lower() == 'json':
            click.echo(json.dumps(summary, indent=2, default=str))
        else:
            # Format as readable report
            click.echo("Research Summary Report")
            click.echo("=" * 80)

            # Basic statistics
            stats = summary.get('basic_stats', {})
            click.echo(f"\nBasic Statistics:")
            click.echo(f"  Total Files: {stats.get('total_files', 0)}")
            click.echo(f"  Total Collections: {stats.get('total_collections', 0)}")
            click.echo(f"  Total Authors: {stats.get('total_authors', 0)}")
            click.echo(f"  Total Words: {stats.get('total_words', 0):,}")
            click.echo(f"  Average Words per File: {stats.get('avg_word_count', 0):.1f}")
            if stats.get('earliest_date'):
                click.echo(f"  Date Range: {stats['earliest_date']} to {stats['latest_date']}")

            # Source distribution
            sources = summary.get('source_distribution', [])
            if sources:
                click.echo(f"\nSource Distribution:")
                for source in sources[:10]:  # Top 10
                    click.echo(f"  {source['collection']}: {source['file_count']} files, {source['avg_words']:.0f} avg words")

            # Topic analysis
            topics = summary.get('topic_analysis', [])
            if topics:
                click.echo(f"\nTop Topics:")
                for topic in topics[:15]:  # Top 15
                    click.echo(f"  {topic['topic']} ({topic['type']}): {topic['frequency']} files")

            # Temporal patterns
            temporal = summary.get('temporal_patterns', [])
            if temporal:
                click.echo(f"\nRecent Activity (by month):")
                for period in temporal[:6]:  # Last 6 months
                    click.echo(f"  {period['month']}: {period['files_count']} files, {period['words_count']:,} words")

            # Author productivity
            authors = summary.get('author_productivity', [])
            if authors:
                click.echo(f"\nTop Authors:")
                for author in authors[:10]:  # Top 10
                    click.echo(f"  {author['author']}: {author['file_count']} files, {author['total_words']:,} words")

    except CLIError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        handle_error(e, "generating research summary")
        sys.exit(1)


if __name__ == '__main__':
    cli()
@cli.c
ommand()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path))
@click.option('--recursive/--no-recursive', default=True,
              help='Recursively scan subdirectories')
@click.option('--incremental/--full', default=True,
              help='Perform incremental indexing (only modified files)')
@click.option('--force', is_flag=True,
              help='Force full reindex even if cache exists')
@click.pass_context
def index(ctx: click.Context, directory: Path, recursive: bool, incremental: bool, force: bool):
    """Index markdown files in a directory.

    Scans the specified directory for markdown files and creates a searchable index.
    By default, performs incremental indexing to only process modified files.

    Examples:
      mdquery index ./notes
      mdquery index ./docs --no-recursive
      mdquery index ./blog --full --force
    """
    verbose = ctx.obj.get('verbose', False)

    try:
        # Get database path and ensure directory exists
        db_path = get_database_path(str(directory))
        ensure_database_directory(db_path)

        # Initialize database and indexer
        try:
            db_manager = DatabaseManager(db_path)
            db_manager.initialize_database()

            cache_manager = CacheManager(db_path.parent / 'cache.json')
            indexer = Indexer(db_manager, cache_manager)
        except Exception as e:
            raise CLIError(f"Failed to initialize indexer: {e}") from e

        # Determine indexing strategy
        if force:
            click.echo(f"Force rebuilding index for: {directory}")
            stats = indexer.rebuild_index(directory)
        elif incremental:
            click.echo(f"Incrementally indexing: {directory} (recursive={recursive})")
            stats = indexer.incremental_index_directory(directory, recursive)
        else:
            click.echo(f"Full indexing: {directory} (recursive={recursive})")
            stats = indexer.index_directory(directory, recursive)

        # Display results
        click.echo(f"\nIndexing complete:")
        click.echo(f"  Files processed: {stats['files_processed']}")
        if 'files_updated' in stats:
            click.echo(f"  Files updated: {stats['files_updated']}")
        if 'files_skipped' in stats:
            click.echo(f"  Files skipped: {stats['files_skipped']}")
        if stats.get('errors', 0) > 0:
            click.echo(f"  Errors encountered: {stats['errors']}", err=True)
            if verbose:
                click.echo("  Use --debug for detailed error information", err=True)

        # Show performance stats in verbose mode
        if verbose:
            from .logging_config import get_performance_monitor
            monitor = get_performance_monitor()
            perf_stats = monitor.get_statistics()
            if perf_stats:
                click.echo(f"\nPerformance statistics:", err=True)
                for operation, stats_data in perf_stats.items():
                    if stats_data and stats_data.get('count', 0) > 0:
                        click.echo(f"  {operation}: {stats_data['avg_duration']:.3f}s avg "
                                 f"({stats_data['count']} operations)", err=True)

    except (MdqueryError, FileNotFoundError, PermissionError) as e:
        handle_error(e, "indexing directory", verbose)
    except KeyboardInterrupt:
        click.echo("\nIndexing interrupted by user", err=True)
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        wrapped_error = CLIError(f"Unexpected error during indexing: {e}")
        log_error(wrapped_error, logger, {'directory': str(directory), 'recursive': recursive})
        handle_error(wrapped_error, "indexing directory", verbose)


@cli.command()
@click.option('--directory', '-d', default='.',
              help='Directory containing indexed markdown files')
@click.option('--table', '-t', help='Show schema for specific table')
@click.option('--stats', is_flag=True, help='Show database statistics')
@click.pass_context
def schema(ctx: click.Context, directory: str, table: Optional[str], stats: bool):
    """Show database schema information.

    Displays the database schema, table structures, and optionally statistics
    about the indexed data.

    Examples:
      mdquery schema
      mdquery schema --table files
      mdquery schema --stats
    """
    verbose = ctx.obj.get('verbose', False)

    try:
        # Get database path and check if it exists
        db_path = get_database_path(directory)
        if not db_path.exists():
            raise CLIError(f"No index found for directory '{directory}'. Run 'mdquery index {directory}' first.")

        # Initialize database manager
        try:
            db_manager = DatabaseManager(db_path)
        except Exception as e:
            raise CLIError(f"Failed to access database: {e}") from e

        # Get schema information
        schema_info = db_manager.get_schema_info()

        if table:
            # Show specific table schema
            if table in schema_info['tables']:
                table_info = schema_info['tables'][table]
                click.echo(f"Table: {table}")
                click.echo(f"Rows: {table_info['row_count']}")
                click.echo("\nColumns:")
                for col in table_info['columns']:
                    pk_marker = " (PRIMARY KEY)" if col['primary_key'] else ""
                    null_marker = " NOT NULL" if col['not_null'] else ""
                    click.echo(f"  {col['name']}: {col['type']}{null_marker}{pk_marker}")
            else:
                available_tables = ', '.join(schema_info['tables'].keys())
                raise CLIError(f"Table '{table}' not found. Available tables: {available_tables}")

        elif stats:
            # Show database statistics
            click.echo("Database Statistics:")
            click.echo(f"Schema version: {schema_info['version']}")
            click.echo(f"Tables: {len(schema_info['tables'])}")
            click.echo(f"Views: {len(schema_info['views'])}")
            click.echo(f"Indexes: {len(schema_info['indexes'])}")

            click.echo("\nTable Statistics:")
            for table_name, table_info in schema_info['tables'].items():
                click.echo(f"  {table_name}: {table_info['row_count']} rows")

        else:
            # Show full schema overview
            click.echo("Database Schema Overview:")
            click.echo(f"Version: {schema_info['version']}")

            click.echo("\nTables:")
            for table_name, table_info in schema_info['tables'].items():
                click.echo(f"  {table_name} ({table_info['row_count']} rows)")

            click.echo("\nViews:")
            for view_name in schema_info['views'].keys():
                click.echo(f"  {view_name}")

            if verbose:
                click.echo(f"\nIndexes: {len(schema_info['indexes'])}")
                for index_info in schema_info['indexes']:
                    click.echo(f"  {index_info['name']}")

    except (MdqueryError, FileNotFoundError, PermissionError) as e:
        handle_error(e, "showing schema", verbose)
    except Exception as e:
        wrapped_error = CLIError(f"Unexpected error showing schema: {e}")
        log_error(wrapped_error, logger, {'directory': directory})
        handle_error(wrapped_error, "showing schema", verbose)


@cli.command()
@click.option('--directory', '-d', default='.',
              help='Directory containing indexed markdown files')
@click.option('--hours', type=int, default=24,
              help='Number of hours to look back for statistics')
@click.pass_context
def stats(ctx: click.Context, directory: str, hours: int):
    """Show performance and error statistics.

    Displays comprehensive statistics about indexing performance,
    query execution times, and any errors encountered.

    Examples:
      mdquery stats
      mdquery stats --hours 48
    """
    verbose = ctx.obj.get('verbose', False)

    try:
        # Get logging statistics
        logging_stats = get_logging_statistics()

        click.echo("Performance Statistics:")
        perf_stats = logging_stats.get('performance_stats', {})
        if perf_stats:
            for operation, stats_data in perf_stats.items():
                if stats_data and stats_data.get('count', 0) > 0:
                    click.echo(f"  {operation}:")
                    click.echo(f"    Operations: {stats_data['count']}")
                    click.echo(f"    Average time: {stats_data['avg_duration']:.3f}s")
                    click.echo(f"    Min time: {stats_data['min_duration']:.3f}s")
                    click.echo(f"    Max time: {stats_data['max_duration']:.3f}s")
                    if stats_data.get('threshold_violations', 0) > 0:
                        click.echo(f"    Threshold violations: {stats_data['threshold_violations']}")
        else:
            click.echo("  No performance data available")

        click.echo(f"\nError Statistics (last {hours} hours):")
        error_stats = logging_stats.get('error_stats', {})
        if error_stats.get('total_errors', 0) > 0:
            click.echo(f"  Total errors: {error_stats['total_errors']}")
            click.echo("  Error types:")
            for error_type, count in error_stats.get('error_types', {}).items():
                click.echo(f"    {error_type}: {count}")

            if verbose and error_stats.get('recent_errors'):
                click.echo("\n  Recent errors:")
                for error in error_stats['recent_errors'][-5:]:  # Show last 5
                    click.echo(f"    {error['timestamp']}: {error['error_type']} - {error['error_message']}")
        else:
            click.echo("  No errors recorded")

        # Show database statistics if available
        db_path = get_database_path(directory)
        if db_path.exists():
            try:
                db_manager = DatabaseManager(db_path)
                schema_info = db_manager.get_schema_info()

                click.echo(f"\nDatabase Statistics:")
                total_files = schema_info['tables'].get('files', {}).get('row_count', 0)
                total_tags = schema_info['tables'].get('tags', {}).get('row_count', 0)
                total_links = schema_info['tables'].get('links', {}).get('row_count', 0)

                click.echo(f"  Indexed files: {total_files}")
                click.echo(f"  Total tags: {total_tags}")
                click.echo(f"  Total links: {total_links}")

            except Exception as e:
                if verbose:
                    click.echo(f"\nCould not access database statistics: {e}", err=True)

    except Exception as e:
        wrapped_error = CLIError(f"Unexpected error showing statistics: {e}")
        log_error(wrapped_error, logger, {'directory': directory})
        handle_error(wrapped_error, "showing statistics", verbose)


if __name__ == '__main__':
    cli()