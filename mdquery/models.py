"""
Core data models and type hints for mdquery.

This module defines the primary data structures used throughout the mdquery system
for representing query results, file metadata, and parsed content.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


@dataclass
class FileMetadata:
    """
    Represents metadata for a markdown file.

    Contains file system information and computed properties like content hash
    and word count that are used for indexing and cache validation.
    """
    path: Path
    filename: str
    directory: str
    modified_date: datetime
    created_date: Optional[datetime]
    file_size: int
    content_hash: str
    word_count: int = 0
    heading_count: int = 0


@dataclass
class ParsedContent:
    """
    Represents the parsed content of a markdown file.

    Contains all extracted information including frontmatter, content,
    tags, and links that will be indexed for querying.
    """
    frontmatter: Dict[str, Any]
    content: str
    title: Optional[str]
    headings: List[str]
    tags: List[str]
    links: List[Dict[str, Union[str, bool]]]

    def __post_init__(self):
        """Ensure all fields have proper default values."""
        if self.frontmatter is None:
            self.frontmatter = {}
        if self.headings is None:
            self.headings = []
        if self.tags is None:
            self.tags = []
        if self.links is None:
            self.links = []


@dataclass
class QueryResult:
    """
    Represents the result of executing a query against the markdown database.

    Contains the query results along with metadata about the execution
    such as row count and execution time.
    """
    rows: List[Dict[str, Any]]
    columns: List[str]
    row_count: int
    execution_time_ms: float
    query: str

    def __post_init__(self):
        """Ensure row_count matches actual rows if not explicitly set."""
        if self.row_count is None:
            self.row_count = len(self.rows)

    def to_dict(self) -> Dict[str, Any]:
        """Convert QueryResult to dictionary for serialization."""
        return {
            "rows": self.rows,
            "columns": self.columns,
            "row_count": self.row_count,
            "execution_time_ms": self.execution_time_ms,
            "query": self.query
        }