"""
Command-line interface for mdquery using click framework.
"""

import click


@click.group()
@click.version_option()
def cli():
    """mdquery - Universal markdown querying tool with SQL-like syntax."""
    pass


@cli.command()
@click.argument('query')
@click.option('--format', default='table', help='Output format: json, csv, table, markdown')
@click.option('--directory', default='.', help='Directory to search for markdown files')
def query(query: str, format: str, directory: str):
    """Execute a SQL query against markdown files."""
    # Implementation will be added in task 10
    click.echo(f"Query: {query}")
    click.echo(f"Format: {format}")
    click.echo(f"Directory: {directory}")


@cli.command()
@click.argument('directory')
@click.option('--recursive/--no-recursive', default=True, help='Recursively scan subdirectories')
def index(directory: str, recursive: bool):
    """Index markdown files in the specified directory."""
    # Implementation will be added in task 10
    click.echo(f"Indexing directory: {directory}")
    click.echo(f"Recursive: {recursive}")


@cli.command()
@click.option('--table', help='Show schema for specific table')
def schema(table: str):
    """Display database schema information."""
    # Implementation will be added in task 10
    click.echo(f"Schema for table: {table}")


if __name__ == '__main__':
    cli()