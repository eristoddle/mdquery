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
    obsidian_features: Optional[Dict[str, Any]] = None

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
        if self.obsidian_features is None:
            self.obsidian_features = {}


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


@dataclass
class ObsidianLink:
    """Represents an Obsidian wikilink with enhanced metadata."""
    link_text: str
    link_target: str
    obsidian_type: str  # 'page', 'section', 'block'
    section: Optional[str] = None
    block_id: Optional[str] = None
    has_alias: bool = False


@dataclass
class ObsidianEmbed:
    """Represents an Obsidian embed."""
    embed_target: str
    embed_alias: Optional[str] = None
    embed_type: str = 'page'


@dataclass
class ObsidianTemplate:
    """Represents an Obsidian template usage."""
    template_name: str
    template_arg: Optional[str] = None
    start_pos: int = 0
    end_pos: int = 0


@dataclass
class ObsidianCallout:
    """Represents an Obsidian callout."""
    callout_type: str
    callout_title: Optional[str] = None
    line_number: int = 0


@dataclass
class ObsidianBlockReference:
    """Represents an Obsidian block reference."""
    block_id: str
    line_number: int = 0


@dataclass
class ObsidianDataviewQuery:
    """Represents an Obsidian Dataview query."""
    query_content: str
    line_number: int = 0
    start_pos: int = 0
    end_pos: int = 0


@dataclass
class ObsidianGraphConnection:
    """Represents a connection in the Obsidian graph."""
    source_file: str
    target_file: Optional[str]
    target_name: str
    connection_type: str  # 'wikilink', 'embed', 'backlink'
    connection_strength: int = 1


@dataclass
class ObsidianFeatures:
    """Container for all Obsidian-specific features in a file."""
    wikilinks: List[ObsidianLink]
    embeds: List[ObsidianEmbed]
    templates: List[ObsidianTemplate]
    callouts: List[ObsidianCallout]
    block_references: List[ObsidianBlockReference]
    dataview_queries: List[ObsidianDataviewQuery]
    graph_connections: List[ObsidianGraphConnection]

    def __post_init__(self):
        """Ensure all fields have proper default values."""
        if self.wikilinks is None:
            self.wikilinks = []
        if self.embeds is None:
            self.embeds = []
        if self.templates is None:
            self.templates = []
        if self.callouts is None:
            self.callouts = []
        if self.block_references is None:
            self.block_references = []
        if self.dataview_queries is None:
            self.dataview_queries = []
        if self.graph_connections is None:
            self.graph_connections = []