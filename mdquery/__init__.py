"""
mdquery - Universal markdown querying tool

A SQL-like interface for searching and analyzing markdown files across
different note-taking systems and static site generators.
"""

__version__ = "0.4.0"
__author__ = "mdquery"
__description__ = "Universal markdown querying tool with SQL-like syntax"

from .models import QueryResult, FileMetadata, ParsedContent

__all__ = [
    "QueryResult",
    "FileMetadata",
    "ParsedContent",
]