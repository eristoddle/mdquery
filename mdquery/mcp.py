"""
MCP (Model Context Protocol) server interface for mdquery.

This module provides an MCP server that exposes mdquery functionality
to AI assistants through the Model Context Protocol.
"""

import asyncio
import json
import logging
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from concurrent.futures import ThreadPoolExecutor
import threading
from datetime import datetime

from mcp.server.fastmcp import FastMCP

from .database import DatabaseManager, create_database
from .indexer import Indexer
from .query import QueryEngine
from .cache import CacheManager
from .research import ResearchEngine, ResearchFilter
from .config import SimplifiedConfig, create_helpful_error_message
from .exceptions import ConfigurationError, MdqueryError
from .tag_analysis import TagAnalysisEngine
from .query_guidance import QueryGuidanceEngine

logger = logging.getLogger(__name__)


class MCPServerError(Exception):
    """Custom exception for MCP server errors."""
    pass


class MDQueryMCPServer:
    """
    MCP server for exposing mdquery functionality to AI assistants.

    Provides tools for querying markdown files, managing indexes,
    and retrieving schema information through the Model Context Protocol.
    """

    def __init__(self, config: Optional[SimplifiedConfig] = None,
                 db_path: Optional[Path] = None, cache_dir: Optional[Path] = None,
                 notes_dirs: Optional[List[Path]] = None):
        """
        Initialize MCP server with simplified configuration or legacy parameters.

        Args:
            config: SimplifiedConfig instance (preferred)
            db_path: Path to SQLite database file (legacy)
            cache_dir: Directory for cache files (legacy)
            notes_dirs: List of directories containing markdown files to auto-index (legacy)
        """
        if config:
            # Use new simplified configuration
            self.config = config
            self.db_path = config.config.db_path
            self.cache_dir = config.config.cache_dir
            self.notes_dirs = [config.config.notes_dir]
            self.auto_index = config.config.auto_index
        else:
            # Legacy initialization for backward compatibility
            self.config = None
            self.db_path = db_path or Path.home() / ".mdquery" / "mdquery.db"
            self.cache_dir = cache_dir or Path.home() / ".mdquery" / "cache"
            self.notes_dirs = notes_dirs or []
            self.auto_index = True

            # Ensure directories exist (legacy behavior)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.db_manager: Optional[DatabaseManager] = None
        self.query_engine: Optional[QueryEngine] = None
        self.indexer: Optional[Indexer] = None
        self.cache_manager: Optional[CacheManager] = None
        self.query_guidance_engine: Optional[QueryGuidanceEngine] = None

        # Thread pool for blocking operations
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="mdquery-mcp")

        # Thread safety lock
        self._lock = threading.RLock()

        # Initialization state tracking
        self._initialization_attempted = False
        self._initialization_successful = False
        self._initialization_error: Optional[Exception] = None

        # Initialize MCP server
        self.server = FastMCP("mdquery")
        self._setup_tools()

    def _setup_tools(self) -> None:
        """Set up MCP server tools."""

        @self.server.tool()
        async def query_markdown(sql: str, format: str = "json") -> str:
            """
            Execute SQL query against markdown database.

            Args:
                sql: SQL query to execute
                format: Output format (json, csv, table, markdown)

            Returns:
                Query results in specified format
            """
            try:
                await self._ensure_initialized()

                # Execute query in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    self.executor,
                    self.query_engine.execute_query,
                    sql
                )

                # Format results
                if format == "json":
                    return json.dumps(result.to_dict(), indent=2, default=str)
                else:
                    return self.query_engine.format_results(result, format)

            except Exception as e:
                logger.error(f"Query execution failed: {e}")
                raise MCPServerError(f"Query execution failed: {e}")

        @self.server.tool()
        async def get_schema(table: Optional[str] = None) -> str:
            """
            Get database schema information.

            Args:
                table: Specific table to get schema for (optional)

            Returns:
                Schema information as JSON
            """
            try:
                await self._ensure_initialized()

                # Get schema in thread pool
                loop = asyncio.get_event_loop()
                schema_info = await loop.run_in_executor(
                    self.executor,
                    self.query_engine.get_schema
                )

                # Filter by table if specified
                if table:
                    if table in schema_info.get("tables", {}):
                        filtered_schema = {
                            "table": table,
                            "schema": schema_info["tables"][table]
                        }
                    elif table in schema_info.get("views", {}):
                        filtered_schema = {
                            "view": table,
                            "schema": schema_info["views"][table]
                        }
                    else:
                        raise MCPServerError(f"Table or view '{table}' not found")

                    return json.dumps(filtered_schema, indent=2, default=str)
                else:
                    return json.dumps(schema_info, indent=2, default=str)

            except Exception as e:
                logger.error(f"Schema retrieval failed: {e}")
                raise MCPServerError(f"Schema retrieval failed: {e}")

        @self.server.tool()
        async def index_multiple_directories(paths: str, recursive: bool = True, incremental: bool = True) -> str:
            """
            Index markdown files in multiple directories.

            Args:
                paths: Comma-separated list of directory paths to index
                recursive: Whether to scan subdirectories
                incremental: Whether to use incremental indexing

            Returns:
                Combined indexing statistics as JSON
            """
            try:
                await self._ensure_initialized()

                # Parse paths
                path_list = [Path(p.strip()).expanduser().resolve() for p in paths.split(',')]

                # Validate all paths exist
                for path_obj in path_list:
                    if not path_obj.exists():
                        raise MCPServerError(f"Directory does not exist: {path_obj}")
                    if not path_obj.is_dir():
                        raise MCPServerError(f"Path is not a directory: {path_obj}")

                # Index all directories
                loop = asyncio.get_event_loop()
                all_stats = {}

                for path_obj in path_list:
                    if incremental:
                        stats = await loop.run_in_executor(
                            self.executor,
                            self.indexer.incremental_index_directory,
                            path_obj,
                            recursive
                        )
                    else:
                        stats = await loop.run_in_executor(
                            self.executor,
                            self.indexer.index_directory,
                            path_obj,
                            recursive
                        )
                    all_stats[str(path_obj)] = stats

                result = {
                    "paths": [str(p) for p in path_list],
                    "recursive": recursive,
                    "incremental": incremental,
                    "statistics": all_stats
                }

                return json.dumps(result, indent=2, default=str)

            except Exception as e:
                logger.error(f"Multiple directory indexing failed: {e}")
                raise MCPServerError(f"Multiple directory indexing failed: {e}")

        @self.server.tool()
        async def index_directory(path: str, recursive: bool = True, incremental: bool = True) -> str:
            """
            Index markdown files in a directory.

            Args:
                path: Directory path to index
                recursive: Whether to scan subdirectories
                incremental: Whether to use incremental indexing

            Returns:
                Indexing statistics as JSON
            """
            try:
                await self._ensure_initialized()

                path_obj = Path(path).expanduser().resolve()

                if not path_obj.exists():
                    raise MCPServerError(f"Directory does not exist: {path_obj}")

                if not path_obj.is_dir():
                    raise MCPServerError(f"Path is not a directory: {path_obj}")

                # Index directory in thread pool
                loop = asyncio.get_event_loop()

                if incremental:
                    stats = await loop.run_in_executor(
                        self.executor,
                        self.indexer.incremental_index_directory,
                        path_obj,
                        recursive
                    )
                else:
                    stats = await loop.run_in_executor(
                        self.executor,
                        self.indexer.index_directory,
                        path_obj,
                        recursive
                    )

                result = {
                    "path": str(path_obj),
                    "recursive": recursive,
                    "incremental": incremental,
                    "statistics": stats
                }

                return json.dumps(result, indent=2, default=str)

            except Exception as e:
                logger.error(f"Directory indexing failed: {e}")
                raise MCPServerError(f"Directory indexing failed: {e}")

        @self.server.tool()
        async def analyze_seo(files: Optional[str] = None) -> str:
            """
            Perform SEO analysis on markdown files.

            Args:
                files: Comma-separated list of specific files to analyze (optional)

            Returns:
                SEO analysis results as JSON
            """
            try:
                await self._ensure_initialized()

                # Parse file list if provided
                file_paths = None
                if files:
                    file_paths = [f.strip() for f in files.split(',')]

                # Perform SEO analysis in thread pool
                loop = asyncio.get_event_loop()

                def run_seo_analysis():
                    advanced_engine = self.query_engine.get_advanced_engine()
                    return advanced_engine.analyze_seo(file_paths)

                analyses = await loop.run_in_executor(self.executor, run_seo_analysis)

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

                return json.dumps(json_data, indent=2)

            except Exception as e:
                logger.error(f"SEO analysis failed: {e}")
                raise MCPServerError(f"SEO analysis failed: {e}")

        @self.server.tool()
        async def analyze_content_structure(files: Optional[str] = None) -> str:
            """
            Analyze content structure and hierarchy.

            Args:
                files: Comma-separated list of specific files to analyze (optional)

            Returns:
                Content structure analysis results as JSON
            """
            try:
                await self._ensure_initialized()

                # Parse file list if provided
                file_paths = None
                if files:
                    file_paths = [f.strip() for f in files.split(',')]

                # Perform structure analysis in thread pool
                loop = asyncio.get_event_loop()

                def run_structure_analysis():
                    advanced_engine = self.query_engine.get_advanced_engine()
                    return advanced_engine.analyze_content_structure(file_paths)

                analyses = await loop.run_in_executor(self.executor, run_structure_analysis)

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

                return json.dumps(json_data, indent=2)

            except Exception as e:
                logger.error(f"Structure analysis failed: {e}")
                raise MCPServerError(f"Structure analysis failed: {e}")

        @self.server.tool()
        async def find_similar_content(file_path: str, threshold: float = 0.3) -> str:
            """
            Find content similar to the specified file.

            Args:
                file_path: Path of the file to find similar content for
                threshold: Minimum similarity score (0.0 to 1.0)

            Returns:
                Similar content results as JSON
            """
            try:
                await self._ensure_initialized()

                # Find similar content in thread pool
                loop = asyncio.get_event_loop()

                def run_similarity_analysis():
                    advanced_engine = self.query_engine.get_advanced_engine()
                    return advanced_engine.find_similar_content(file_path, threshold)

                similarities = await loop.run_in_executor(self.executor, run_similarity_analysis)

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

                return json.dumps(json_data, indent=2)

            except Exception as e:
                logger.error(f"Similarity analysis failed: {e}")
                raise MCPServerError(f"Similarity analysis failed: {e}")

        @self.server.tool()
        async def analyze_link_relationships() -> str:
            """
            Analyze link relationships between files.

            Returns:
                Link relationship analysis results as JSON
            """
            try:
                await self._ensure_initialized()

                # Analyze link relationships in thread pool
                loop = asyncio.get_event_loop()

                def run_link_analysis():
                    advanced_engine = self.query_engine.get_advanced_engine()
                    return advanced_engine.analyze_link_relationships()

                analyses = await loop.run_in_executor(self.executor, run_link_analysis)

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

                return json.dumps(json_data, indent=2)

            except Exception as e:
                logger.error(f"Link analysis failed: {e}")
                raise MCPServerError(f"Link analysis failed: {e}")

        @self.server.tool()
        async def generate_content_report() -> str:
            """
            Generate comprehensive content analysis report.

            Returns:
                Comprehensive report data as JSON
            """
            try:
                await self._ensure_initialized()

                # Generate report in thread pool
                loop = asyncio.get_event_loop()

                def run_report_generation():
                    advanced_engine = self.query_engine.get_advanced_engine()
                    return advanced_engine.generate_content_report()

                report_data = await loop.run_in_executor(self.executor, run_report_generation)

                return json.dumps(report_data, indent=2, default=str)

            except Exception as e:
                logger.error(f"Report generation failed: {e}")
                raise MCPServerError(f"Report generation failed: {e}")

        @self.server.tool()
        async def execute_aggregation_query(aggregation_name: str, format: str = "json") -> str:
            """
            Execute predefined aggregation queries for reporting.

            Args:
                aggregation_name: Name of the aggregation query to execute
                format: Output format (json, csv, table, markdown)

            Returns:
                Aggregation query results in specified format
            """
            try:
                await self._ensure_initialized()

                # Execute aggregation query in thread pool
                loop = asyncio.get_event_loop()

                def run_aggregation():
                    advanced_engine = self.query_engine.get_advanced_engine()
                    return advanced_engine.execute_aggregation_query(aggregation_name)

                result = await loop.run_in_executor(self.executor, run_aggregation)

                # Format results
                if format == "json":
                    return json.dumps(result.to_dict(), indent=2, default=str)
                else:
                    return self.query_engine.format_results(result, format)

            except Exception as e:
                logger.error(f"Aggregation query execution failed: {e}")
                raise MCPServerError(f"Aggregation query execution failed: {e}")

        @self.server.tool()
        async def fuzzy_search(search_text: str, threshold: float = 0.6, max_results: int = 50,
                              search_fields: str = "content,title,headings") -> str:
            """
            Perform fuzzy text matching for related content discovery.

            Args:
                search_text: Text to search for similar content
                threshold: Minimum similarity score (0.0 to 1.0)
                max_results: Maximum number of results to return
                search_fields: Fields to search in (comma-separated)

            Returns:
                Fuzzy search results as JSON
            """
            try:
                await self._ensure_initialized()

                # Parse search fields
                fields_list = [field.strip() for field in search_fields.split(',')]

                # Perform fuzzy search in thread pool
                loop = asyncio.get_event_loop()

                def run_fuzzy_search():
                    research_engine = ResearchEngine(self.query_engine)
                    return research_engine.fuzzy_search(search_text, threshold, max_results, fields_list)

                matches = await loop.run_in_executor(self.executor, run_fuzzy_search)

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

                return json.dumps(json_data, indent=2)

            except Exception as e:
                logger.error(f"Fuzzy search failed: {e}")
                raise MCPServerError(f"Fuzzy search failed: {e}")

        @self.server.tool()
        async def cross_collection_search(query_text: str, collections: str, max_per_collection: int = 20) -> str:
            """
            Perform cross-collection querying for multiple note sources.

            Args:
                query_text: Text to search for across collections
                collections: Comma-separated list of collection identifiers
                max_per_collection: Maximum results per collection

            Returns:
                Cross-collection search results as JSON
            """
            try:
                await self._ensure_initialized()

                # Parse collections
                collections_list = [c.strip() for c in collections.split(',')]

                # Perform cross-collection search in thread pool
                loop = asyncio.get_event_loop()

                def run_cross_search():
                    research_engine = ResearchEngine(self.query_engine)
                    return research_engine.cross_collection_search(query_text, collections_list, max_per_collection)

                results = await loop.run_in_executor(self.executor, run_cross_search)

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

                return json.dumps(json_data, indent=2, default=str)

            except Exception as e:
                logger.error(f"Cross-collection search failed: {e}")
                raise MCPServerError(f"Cross-collection search failed: {e}")

        @self.server.tool()
        async def extract_quotes_with_attribution(files: Optional[str] = None, patterns: Optional[str] = None) -> str:
            """
            Extract quotes and references with source attribution preservation.

            Args:
                files: Comma-separated list of specific files to process (optional)
                patterns: Custom regex patterns for quote detection (comma-separated, optional)

            Returns:
                Source attributions with quote and citation information as JSON
            """
            try:
                await self._ensure_initialized()

                # Parse file list if provided
                file_paths = None
                if files:
                    file_paths = [f.strip() for f in files.split(',')]

                # Parse custom patterns if provided
                quote_patterns = None
                if patterns:
                    quote_patterns = [p.strip() for p in patterns.split(',')]

                # Extract quotes in thread pool
                loop = asyncio.get_event_loop()

                def run_quote_extraction():
                    research_engine = ResearchEngine(self.query_engine)
                    return research_engine.extract_quotes_with_attribution(file_paths, quote_patterns)

                attributions = await loop.run_in_executor(self.executor, run_quote_extraction)

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

                return json.dumps(json_data, indent=2)

            except Exception as e:
                logger.error(f"Quote extraction failed: {e}")
                raise MCPServerError(f"Quote extraction failed: {e}")

        @self.server.tool()
        async def filter_by_research_criteria(date_from: Optional[str] = None, date_to: Optional[str] = None,
                                            topics: Optional[str] = None, sources: Optional[str] = None,
                                            authors: Optional[str] = None, collections: Optional[str] = None,
                                            format: str = "json") -> str:
            """
            Filter content by research criteria including date ranges and topics.

            Args:
                date_from: Filter from date (YYYY-MM-DD format, optional)
                date_to: Filter to date (YYYY-MM-DD format, optional)
                topics: Filter by topics/tags (comma-separated, optional)
                sources: Filter by source paths (comma-separated, optional)
                authors: Filter by authors (comma-separated, optional)
                collections: Filter by collections/directories (comma-separated, optional)
                format: Output format (json, csv, table, markdown)

            Returns:
                Filtered research content as JSON or specified format
            """
            try:
                await self._ensure_initialized()

                # Parse date parameters
                date_from_obj = None
                date_to_obj = None
                if date_from:
                    date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                if date_to:
                    date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')

                # Build research filter
                research_filter = ResearchFilter(
                    date_from=date_from_obj,
                    date_to=date_to_obj,
                    topics=[t.strip() for t in topics.split(',')] if topics else None,
                    sources=[s.strip() for s in sources.split(',')] if sources else None,
                    authors=[a.strip() for a in authors.split(',')] if authors else None,
                    collections=[c.strip() for c in collections.split(',')] if collections else None
                )

                # Apply filter in thread pool
                loop = asyncio.get_event_loop()

                def run_research_filter():
                    research_engine = ResearchEngine(self.query_engine)
                    return research_engine.filter_by_research_criteria(research_filter)

                result = await loop.run_in_executor(self.executor, run_research_filter)

                # Format results
                if format == "json":
                    return json.dumps(result.to_dict(), indent=2, default=str)
                else:
                    return self.query_engine.format_results(result, format)

            except Exception as e:
                logger.error(f"Research filtering failed: {e}")
                raise MCPServerError(f"Research filtering failed: {e}")

        @self.server.tool()
        async def generate_research_summary(date_from: Optional[str] = None, date_to: Optional[str] = None,
                                          topics: Optional[str] = None, sources: Optional[str] = None,
                                          authors: Optional[str] = None, collections: Optional[str] = None) -> str:
            """
            Generate comprehensive research summary and statistics.

            Args:
                date_from: Filter from date (YYYY-MM-DD format, optional)
                date_to: Filter to date (YYYY-MM-DD format, optional)
                topics: Filter by topics/tags (comma-separated, optional)
                sources: Filter by source paths (comma-separated, optional)
                authors: Filter by authors (comma-separated, optional)
                collections: Filter by collections/directories (comma-separated, optional)

            Returns:
                Research summary statistics as JSON
            """
            try:
                await self._ensure_initialized()

                # Parse date parameters
                date_from_obj = None
                date_to_obj = None
                if date_from:
                    date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                if date_to:
                    date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')

                # Build research filter if any criteria provided
                research_filter = None
                if any([date_from, date_to, topics, sources, authors, collections]):
                    research_filter = ResearchFilter(
                        date_from=date_from_obj,
                        date_to=date_to_obj,
                        topics=[t.strip() for t in topics.split(',')] if topics else None,
                        sources=[s.strip() for s in sources.split(',')] if sources else None,
                        authors=[a.strip() for a in authors.split(',')] if authors else None,
                        collections=[c.strip() for c in collections.split(',')] if collections else None
                    )

                # Generate research summary in thread pool
                loop = asyncio.get_event_loop()

                def run_research_summary():
                    research_engine = ResearchEngine(self.query_engine)
                    return research_engine.generate_research_summary(research_filter)

                summary = await loop.run_in_executor(self.executor, run_research_summary)

                return json.dumps(summary, indent=2, default=str)

            except Exception as e:
                logger.error(f"Research summary generation failed: {e}")
                raise MCPServerError(f"Research summary generation failed: {e}")

        @self.server.tool()
        async def get_file_content(file_path: str, include_parsed: bool = False) -> str:
            """
            Retrieve content and metadata of a specific file.

            Args:
                file_path: Path to the file
                include_parsed: Whether to include parsed content (frontmatter, tags, links)

            Returns:
                File content and metadata as JSON
            """
            try:
                await self._ensure_initialized()

                file_path_obj = Path(file_path).expanduser().resolve()

                if not file_path_obj.exists():
                    raise MCPServerError(f"File does not exist: {file_path_obj}")

                if not file_path_obj.is_file():
                    raise MCPServerError(f"Path is not a file: {file_path_obj}")

                # Get file content in thread pool
                loop = asyncio.get_event_loop()

                # Read raw content
                def read_file():
                    try:
                        with open(file_path_obj, 'r', encoding='utf-8') as f:
                            content = f.read()
                    except UnicodeDecodeError:
                        with open(file_path_obj, 'r', encoding='latin-1') as f:
                            content = f.read()
                    return content

                content = await loop.run_in_executor(self.executor, read_file)

                # Get file metadata
                stat = file_path_obj.stat()
                metadata = {
                    "path": str(file_path_obj),
                    "filename": file_path_obj.name,
                    "directory": str(file_path_obj.parent),
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "created": getattr(stat, 'st_birthtime', stat.st_ctime)
                }

                result = {
                    "content": content,
                    "metadata": metadata
                }

                # Include parsed content if requested
                if include_parsed:
                    def get_parsed_data():
                        # Query database for parsed content
                        with self.db_manager.get_connection() as conn:
                            # Get file record
                            cursor = conn.execute(
                                "SELECT * FROM files WHERE path = ?",
                                (str(file_path_obj),)
                            )
                            file_record = cursor.fetchone()

                            if file_record:
                                file_id = file_record['id']

                                # Get frontmatter
                                cursor = conn.execute(
                                    "SELECT key, value, value_type FROM frontmatter WHERE file_id = ?",
                                    (file_id,)
                                )
                                frontmatter = {
                                    row['key']: row['value'] for row in cursor.fetchall()
                                }

                                # Get tags
                                cursor = conn.execute(
                                    "SELECT tag, source FROM tags WHERE file_id = ?",
                                    (file_id,)
                                )
                                tags = [
                                    {"tag": row['tag'], "source": row['source']}
                                    for row in cursor.fetchall()
                                ]

                                # Get links
                                cursor = conn.execute(
                                    "SELECT link_text, link_target, link_type, is_internal FROM links WHERE file_id = ?",
                                    (file_id,)
                                )
                                links = [
                                    {
                                        "text": row['link_text'],
                                        "target": row['link_target'],
                                        "type": row['link_type'],
                                        "internal": bool(row['is_internal'])
                                    }
                                    for row in cursor.fetchall()
                                ]

                                return {
                                    "frontmatter": frontmatter,
                                    "tags": tags,
                                    "links": links,
                                    "word_count": file_record['word_count'],
                                    "heading_count": file_record['heading_count']
                                }

                        return None

                    parsed_data = await loop.run_in_executor(self.executor, get_parsed_data)
                    if parsed_data:
                        result["parsed"] = parsed_data

                return json.dumps(result, indent=2, default=str)

            except Exception as e:
                logger.error(f"File content retrieval failed: {e}")
                raise MCPServerError(f"File content retrieval failed: {e}")

        @self.server.tool()
        async def comprehensive_tag_analysis(
            tag_patterns: str,
            grouping_strategy: str = "semantic",
            include_actionable: bool = True,
            include_theoretical: bool = True,
            remove_fluff: bool = True,
            min_content_quality: float = 0.3
        ) -> str:
            """
            Generate comprehensive analysis of tagged content with intelligent grouping.

            This tool provides advanced tag analysis with hierarchical tag support,
            semantic content grouping, and classification of actionable vs theoretical insights.
            It implements "fluff removal" to focus on substantive content.

            Args:
                tag_patterns: Comma-separated tag patterns to analyze (supports wildcards like "ai/*", "llm/coding")
                grouping_strategy: How to group content ("semantic", "tag-hierarchy", "temporal")
                include_actionable: Include practical recommendations and implementation guidance
                include_theoretical: Include conceptual insights and research directions
                remove_fluff: Filter out low-quality content to focus on substantive information
                min_content_quality: Minimum content quality score (0.0 to 1.0, default 0.3)

            Returns:
                Comprehensive tag analysis results as JSON including topic groups, insights, and statistics
            """
            try:
                await self._ensure_initialized()

                # Parse tag patterns
                patterns_list = [pattern.strip() for pattern in tag_patterns.split(',') if pattern.strip()]

                if not patterns_list:
                    raise MCPServerError("At least one tag pattern must be provided")

                # Perform comprehensive tag analysis in thread pool
                loop = asyncio.get_event_loop()

                def run_tag_analysis():
                    tag_engine = TagAnalysisEngine(self.query_engine)
                    return tag_engine.comprehensive_tag_analysis(
                        tag_patterns=patterns_list,
                        grouping_strategy=grouping_strategy,
                        include_actionable=include_actionable,
                        include_theoretical=include_theoretical,
                        remove_fluff=remove_fluff,
                        min_content_quality=min_content_quality
                    )

                analysis_result = await loop.run_in_executor(self.executor, run_tag_analysis)

                # Convert to JSON-serializable format
                result_data = {
                    'topic_groups': [],
                    'actionable_insights': [],
                    'theoretical_insights': [],
                    'tag_hierarchy': analysis_result.tag_hierarchy,
                    'content_statistics': analysis_result.content_statistics,
                    'quality_metrics': analysis_result.quality_metrics
                }

                # Convert topic groups
                for group in analysis_result.topic_groups:
                    group_data = {
                        'name': group.name,
                        'document_count': len(group.documents),
                        'documents': [
                            {
                                'path': doc['path'],
                                'title': doc.get('title'),
                                'word_count': doc.get('word_count', 0),
                                'tags': doc.get('tags', []),
                                'quality_score': doc.get('quality_score', 0.5)
                            }
                            for doc in group.documents
                        ],
                        'key_themes': group.key_themes,
                        'related_groups': group.related_groups,
                        'tag_patterns': group.tag_patterns,
                        'content_quality_score': group.content_quality_score
                    }
                    result_data['topic_groups'].append(group_data)

                # Convert actionable insights
                for insight in analysis_result.actionable_insights:
                    insight_data = {
                        'title': insight.title,
                        'description': insight.description,
                        'implementation_difficulty': insight.implementation_difficulty,
                        'expected_impact': insight.expected_impact,
                        'category': insight.category,
                        'source_files': insight.source_files,
                        'confidence_score': insight.confidence_score
                    }
                    result_data['actionable_insights'].append(insight_data)

                # Convert theoretical insights
                for insight in analysis_result.theoretical_insights:
                    insight_data = {
                        'title': insight.title,
                        'description': insight.description,
                        'related_concepts': insight.related_concepts,
                        'research_directions': insight.research_directions,
                        'source_files': insight.source_files,
                        'confidence_score': insight.confidence_score
                    }
                    result_data['theoretical_insights'].append(insight_data)

                return json.dumps(result_data, indent=2, default=str)

            except Exception as e:
                logger.error(f"Comprehensive tag analysis failed: {e}")
                raise MCPServerError(f"Comprehensive tag analysis failed: {e}")

        @self.server.tool()
        async def analyze_development_workflow(
            focus_areas: Optional[str] = None,
            time_range: Optional[str] = None,
            improvement_categories: str = "process,tools,automation,quality"
        ) -> str:
            """
            Analyze AI development workflow patterns and suggest improvements.

            This tool provides specialized analysis for AI development workflows,
            identifying patterns, improvement opportunities, and actionable recommendations
            for process optimization. It builds on comprehensive tag analysis to provide
            development-specific insights.

            Args:
                focus_areas: Comma-separated specific areas to focus on (e.g., "mcp,agents,automation")
                time_range: Time range for analysis (e.g., "last-3-months") - currently not implemented
                improvement_categories: Types of improvements to identify (comma-separated: process,tools,automation,quality)

            Returns:
                Workflow analysis results as JSON including patterns, opportunities, and recommendations
            """
            try:
                await self._ensure_initialized()

                # Parse focus areas
                focus_list = None
                if focus_areas:
                    focus_list = [area.strip() for area in focus_areas.split(',') if area.strip()]

                # Parse improvement categories
                categories_list = [cat.strip() for cat in improvement_categories.split(',') if cat.strip()]

                # Perform workflow analysis in thread pool
                loop = asyncio.get_event_loop()

                def run_workflow_analysis():
                    from .workflow_analysis import WorkflowAnalyzer
                    workflow_analyzer = WorkflowAnalyzer(self.query_engine)
                    return workflow_analyzer.analyze_development_workflow(
                        focus_areas=focus_list,
                        time_range=time_range,
                        improvement_categories=categories_list
                    )

                analysis_result = await loop.run_in_executor(self.executor, run_workflow_analysis)

                # Convert to JSON-serializable format
                result_data = {
                    'topic_groups': [],
                    'actionable_insights': [],
                    'theoretical_insights': [],
                    'improvement_opportunities': [],
                    'workflow_patterns': [],
                    'development_metrics': analysis_result.development_metrics,
                    'recommendations': analysis_result.recommendations
                }

                # Convert topic groups
                for group in analysis_result.topic_groups:
                    group_data = {
                        'name': group.name,
                        'document_count': len(group.documents),
                        'documents': [
                            {
                                'path': doc['path'],
                                'title': doc.get('title'),
                                'word_count': doc.get('word_count', 0),
                                'tags': doc.get('tags', []),
                                'quality_score': doc.get('quality_score', 0.5)
                            }
                            for doc in group.documents
                        ],
                        'key_themes': group.key_themes,
                        'related_groups': group.related_groups,
                        'tag_patterns': group.tag_patterns,
                        'content_quality_score': group.content_quality_score
                    }
                    result_data['topic_groups'].append(group_data)

                # Convert actionable insights
                for insight in analysis_result.actionable_insights:
                    insight_data = {
                        'title': insight.title,
                        'description': insight.description,
                        'implementation_difficulty': insight.implementation_difficulty,
                        'expected_impact': insight.expected_impact,
                        'category': insight.category,
                        'source_files': insight.source_files,
                        'confidence_score': insight.confidence_score
                    }
                    result_data['actionable_insights'].append(insight_data)

                # Convert theoretical insights
                for insight in analysis_result.theoretical_insights:
                    insight_data = {
                        'title': insight.title,
                        'description': insight.description,
                        'related_concepts': insight.related_concepts,
                        'research_directions': insight.research_directions,
                        'source_files': insight.source_files,
                        'confidence_score': insight.confidence_score
                    }
                    result_data['theoretical_insights'].append(insight_data)

                # Convert improvement opportunities
                for opportunity in analysis_result.improvement_opportunities:
                    opportunity_data = {
                        'title': opportunity.title,
                        'description': opportunity.description,
                        'category': opportunity.category,
                        'implementation_difficulty': opportunity.implementation_difficulty,
                        'expected_impact': opportunity.expected_impact,
                        'priority_score': opportunity.priority_score,
                        'source_files': opportunity.source_files,
                        'related_patterns': opportunity.related_patterns,
                        'suggested_actions': opportunity.suggested_actions
                    }
                    result_data['improvement_opportunities'].append(opportunity_data)

                # Convert workflow patterns
                for pattern in analysis_result.workflow_patterns:
                    pattern_data = {
                        'pattern_name': pattern.pattern_name,
                        'description': pattern.description,
                        'frequency': pattern.frequency,
                        'files_involved': pattern.files_involved,
                        'tags_involved': pattern.tags_involved,
                        'pattern_type': pattern.pattern_type,
                        'confidence_score': pattern.confidence_score
                    }
                    result_data['workflow_patterns'].append(pattern_data)

                return json.dumps(result_data, indent=2, default=str)

            except Exception as e:
                logger.error(f"Development workflow analysis failed: {e}")
                raise MCPServerError(f"Development workflow analysis failed: {e}")

        @self.server.tool()
        async def get_query_guidance(
            analysis_type: str,
            content_description: str = ""
        ) -> str:
            """
            Provide query syntax guidance and examples for specific analysis needs.

            This tool provides comprehensive query assistance including syntax documentation,
            templates for common analysis patterns, optimization suggestions, and examples
            library for tag-based and workflow analysis queries.

            Args:
                analysis_type: Type of analysis needed (e.g., "tag-analysis", "workflow-review",
                             "content-analysis", "research", "performance")
                content_description: Optional description of the content to analyze for more
                                   specific guidance

            Returns:
                Query guidance as JSON including suggested queries, optimization tips,
                common patterns, syntax reference, and relevant examples
            """
            try:
                # Initialize query guidance engine if not already done
                if self.query_guidance_engine is None:
                    self.query_guidance_engine = QueryGuidanceEngine()

                # Get guidance in thread pool
                loop = asyncio.get_event_loop()

                def run_query_guidance():
                    return self.query_guidance_engine.get_query_guidance(
                        analysis_type=analysis_type,
                        content_description=content_description
                    )

                guidance = await loop.run_in_executor(self.executor, run_query_guidance)

                # Convert to JSON-serializable format
                result_data = {
                    'analysis_type': analysis_type,
                    'content_description': content_description,
                    'suggested_queries': [],
                    'optimization_tips': guidance.optimization_tips,
                    'common_patterns': guidance.common_patterns,
                    'syntax_reference': guidance.syntax_reference,
                    'examples': guidance.examples
                }

                # Convert suggested queries
                for template in guidance.suggested_queries:
                    template_data = {
                        'name': template.name,
                        'description': template.description,
                        'category': template.category,
                        'sql_template': template.sql_template,
                        'parameters': [
                            {
                                'name': param.name,
                                'type': param.type,
                                'description': param.description,
                                'default': param.default,
                                'required': param.required,
                                'examples': param.examples
                            }
                            for param in template.parameters
                        ],
                        'example_usage': template.example_usage,
                        'complexity': template.complexity,
                        'performance_notes': template.performance_notes
                    }
                    result_data['suggested_queries'].append(template_data)

                return json.dumps(result_data, indent=2, default=str)

            except Exception as e:
                logger.error(f"Query guidance failed: {e}")
                raise MCPServerError(f"Query guidance failed: {e}")

        @self.server.tool()
        async def get_query_templates(
            category: Optional[str] = None,
            complexity: Optional[str] = None
        ) -> str:
            """
            Get query templates filtered by category and complexity.

            This tool provides access to the library of pre-built query templates
            for common analysis patterns, filtered by category and complexity level.

            Args:
                category: Filter by category ('tag-analysis', 'workflow', 'content',
                         'research', 'performance') - optional
                complexity: Filter by complexity ('basic', 'intermediate', 'advanced') - optional

            Returns:
                List of matching query templates as JSON
            """
            try:
                # Initialize query guidance engine if not already done
                if self.query_guidance_engine is None:
                    self.query_guidance_engine = QueryGuidanceEngine()

                # Get templates in thread pool
                loop = asyncio.get_event_loop()

                def run_get_templates():
                    return self.query_guidance_engine.get_query_templates(
                        category=category,
                        complexity=complexity
                    )

                templates = await loop.run_in_executor(self.executor, run_get_templates)

                # Convert to JSON-serializable format
                result_data = {
                    'filter_category': category,
                    'filter_complexity': complexity,
                    'template_count': len(templates),
                    'templates': []
                }

                for template in templates:
                    template_data = {
                        'name': template.name,
                        'description': template.description,
                        'category': template.category,
                        'sql_template': template.sql_template,
                        'parameters': [
                            {
                                'name': param.name,
                                'type': param.type,
                                'description': param.description,
                                'default': param.default,
                                'required': param.required,
                                'examples': param.examples
                            }
                            for param in template.parameters
                        ],
                        'example_usage': template.example_usage,
                        'complexity': template.complexity,
                        'performance_notes': template.performance_notes
                    }
                    result_data['templates'].append(template_data)

                return json.dumps(result_data, indent=2, default=str)

            except Exception as e:
                logger.error(f"Query templates retrieval failed: {e}")
                raise MCPServerError(f"Query templates retrieval failed: {e}")

        @self.server.tool()
        async def get_query_optimization_suggestions(query: str) -> str:
            """
            Analyze a query and provide optimization suggestions.

            This tool analyzes SQL queries for common performance issues and provides
            specific suggestions for optimization, including before/after examples.

            Args:
                query: SQL query to analyze for optimization opportunities

            Returns:
                List of optimization suggestions as JSON with examples and performance impact
            """
            try:
                # Initialize query guidance engine if not already done
                if self.query_guidance_engine is None:
                    self.query_guidance_engine = QueryGuidanceEngine()

                # Get optimization suggestions in thread pool
                loop = asyncio.get_event_loop()

                def run_optimization_analysis():
                    return self.query_guidance_engine.get_optimization_suggestions(query)

                suggestions = await loop.run_in_executor(self.executor, run_optimization_analysis)

                # Convert to JSON-serializable format
                result_data = {
                    'analyzed_query': query,
                    'suggestion_count': len(suggestions),
                    'suggestions': []
                }

                for suggestion in suggestions:
                    suggestion_data = {
                        'issue': suggestion.issue,
                        'suggestion': suggestion.suggestion,
                        'example_before': suggestion.example_before,
                        'example_after': suggestion.example_after,
                        'performance_impact': suggestion.performance_impact
                    }
                    result_data['suggestions'].append(suggestion_data)

                # Add general optimization tips if no specific suggestions found
                if not suggestions:
                    result_data['general_tips'] = [
                        "Query appears to be well-optimized",
                        "Consider adding LIMIT clause if expecting large result sets",
                        "Use content_fts table for text search instead of LIKE on content",
                        "Ensure WHERE conditions are as specific as possible"
                    ]

                return json.dumps(result_data, indent=2, default=str)

            except Exception as e:
                logger.error(f"Query optimization analysis failed: {e}")
                raise MCPServerError(f"Query optimization analysis failed: {e}")

        @self.server.tool()
        async def get_query_syntax_reference() -> str:
            """
            Get comprehensive query syntax reference documentation.

            This tool provides complete syntax reference including table schemas,
            operators, functions, FTS syntax, and common patterns for mdquery.

            Returns:
                Complete syntax reference documentation as JSON
            """
            try:
                # Initialize query guidance engine if not already done
                if self.query_guidance_engine is None:
                    self.query_guidance_engine = QueryGuidanceEngine()

                # Get syntax reference
                syntax_ref = self.query_guidance_engine.syntax_reference
                common_patterns = self.query_guidance_engine.common_patterns

                result_data = {
                    'syntax_reference': syntax_ref,
                    'common_patterns': common_patterns,
                    'quick_reference': {
                        'basic_query': "SELECT columns FROM table WHERE conditions ORDER BY column LIMIT number",
                        'tag_search': "JOIN tags t ON f.id = t.file_id WHERE t.tag = 'your_tag'",
                        'text_search': "JOIN content_fts fts ON f.id = fts.file_id WHERE content_fts MATCH 'search_terms'",
                        'date_filter': "WHERE modified_date > date('now', '-30 days')",
                        'aggregation': "SELECT tag, COUNT(*) FROM tags GROUP BY tag ORDER BY COUNT(*) DESC"
                    }
                }

                return json.dumps(result_data, indent=2, default=str)

            except Exception as e:
                logger.error(f"Syntax reference retrieval failed: {e}")
                raise MCPServerError(f"Syntax reference retrieval failed: {e}")

    async def _ensure_initialized(self) -> None:
        """
        Ensure all components are initialized with retry logic.

        Implements requirements 1.5, 4.2, 4.3 for automatic initialization,
        graceful error handling, and retry logic.
        """
        if self.db_manager is None:
            with self._lock:
                if self.db_manager is None:
                    # Check if initialization was already attempted and failed
                    if self._initialization_attempted and not self._initialization_successful:
                        if self._initialization_error:
                            # Re-raise the previous initialization error with helpful context
                            error_message = create_helpful_error_message(
                                self._initialization_error,
                                str(self.notes_dirs[0]) if self.notes_dirs else None
                            )
                            raise MCPServerError(f"Previous initialization failed: {error_message}")
                        else:
                            raise MCPServerError("Previous initialization failed with unknown error")

                    # Initialize in thread pool to avoid blocking
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(self.executor, self._initialize_components_with_retry)

    def _initialize_components_with_retry(self) -> None:
        """
        Initialize database and related components with retry logic.

        Implements requirements 1.5, 4.2, 4.3 for automatic initialization,
        graceful error handling, and retry logic.
        """
        self._initialization_attempted = True
        max_retries = 3
        retry_delay = 1.0  # seconds

        for attempt in range(max_retries):
            try:
                logger.info(f"Initializing MCP server components (attempt {attempt + 1}/{max_retries})")

                # Initialize core components
                self._initialize_core_components()

                # Perform auto-indexing if enabled
                if self.auto_index:
                    self._perform_auto_indexing()
                else:
                    logger.info("Auto-indexing disabled")

                # Mark initialization as successful
                self._initialization_successful = True
                logger.info("MCP server components initialized successfully")
                return

            except Exception as e:
                self._initialization_error = e
                logger.error(f"Initialization attempt {attempt + 1} failed: {e}")

                if attempt < max_retries - 1:
                    logger.info(f"Retrying initialization in {retry_delay} seconds...")
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error("All initialization attempts failed")
                    # Create helpful error message
                    error_message = create_helpful_error_message(
                        e,
                        str(self.notes_dirs[0]) if self.notes_dirs else None
                    )
                    raise MCPServerError(f"Initialization failed after {max_retries} attempts: {error_message}")

    def _initialize_core_components(self) -> None:
        """Initialize core database and query components."""
        try:
            # Initialize database
            logger.debug(f"Initializing database at: {self.db_path}")
            self.db_manager = create_database(self.db_path)

            # Initialize cache manager
            logger.debug(f"Initializing cache manager with cache dir: {self.cache_dir}")
            self.cache_manager = CacheManager(
                cache_path=self.cache_dir,  # Use cache directory, not database path
                database_manager=self.db_manager
            )

            # Initialize query engine
            logger.debug("Initializing query engine")
            self.query_engine = QueryEngine(self.db_manager)

            # Initialize indexer
            logger.debug("Initializing indexer")
            self.indexer = Indexer(
                database_manager=self.db_manager,
                cache_manager=self.cache_manager
            )

            logger.info("Core components initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize core components: {e}")
            # Clean up partially initialized components
            self._cleanup_partial_initialization()
            raise

    def _perform_auto_indexing(self) -> None:
        """
        Perform automatic indexing of notes directories with error recovery.

        Implements requirement 1.5 for automatic initial indexing.
        """
        if not self.notes_dirs:
            logger.info("Auto-indexing enabled but no notes directories specified")
            return

        successful_indexes = 0
        total_directories = len(self.notes_dirs)

        for notes_dir in self.notes_dirs:
            try:
                if not notes_dir.exists():
                    logger.warning(f"Notes directory does not exist: {notes_dir}")
                    continue

                logger.info(f"Auto-indexing notes directory: {notes_dir}")

                # Try incremental indexing first for better performance
                try:
                    stats = self.indexer.incremental_index_directory(notes_dir, recursive=True)
                    logger.info(f"Incremental indexing completed for {notes_dir}: {stats}")
                    successful_indexes += 1

                except Exception as incremental_error:
                    logger.warning(f"Incremental indexing failed for {notes_dir}: {incremental_error}")
                    logger.info(f"Falling back to full indexing for {notes_dir}")

                    # Fallback to full indexing
                    try:
                        stats = self.indexer.index_directory(notes_dir, recursive=True)
                        logger.info(f"Full indexing completed for {notes_dir}: {stats}")
                        successful_indexes += 1

                    except Exception as full_error:
                        logger.error(f"Both incremental and full indexing failed for {notes_dir}: {full_error}")
                        # Continue with other directories

            except Exception as e:
                logger.error(f"Unexpected error during auto-indexing of {notes_dir}: {e}")
                # Continue with other directories

        # Log summary
        if successful_indexes == 0:
            logger.warning("Auto-indexing completed but no directories were successfully indexed")
        elif successful_indexes < total_directories:
            logger.warning(f"Auto-indexing partially completed: {successful_indexes}/{total_directories} directories indexed")
        else:
            logger.info(f"Auto-indexing completed successfully: {successful_indexes}/{total_directories} directories indexed")

    def _cleanup_partial_initialization(self) -> None:
        """Clean up partially initialized components."""
        try:
            if self.indexer:
                self.indexer = None
            if self.query_engine:
                self.query_engine = None
            if self.cache_manager:
                self.cache_manager = None
            if self.db_manager:
                self.db_manager = None
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")

    async def run(self) -> None:
        """Run the MCP server."""
        try:
            logger.info("Starting mdquery MCP server")
            await self.server.run()

        except Exception as e:
            logger.error(f"MCP server error: {e}")
            raise
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        """Shutdown the MCP server and cleanup resources."""
        try:
            logger.info("Shutting down mdquery MCP server")

            # Shutdown thread pool
            self.executor.shutdown(wait=True)

            # Close database connections
            if self.db_manager:
                self.db_manager.close()

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


# Legacy compatibility class
class MCPServer(MDQueryMCPServer):
    """Legacy compatibility class."""

    def __init__(self, db_path: Optional[Path] = None, cache_dir: Optional[Path] = None):
        """Initialize with legacy interface."""
        super().__init__(db_path, cache_dir)

        # Legacy attributes for backward compatibility
        self.query_engine = None
        self.indexer = None

    async def query_markdown(self, sql: str) -> Dict[str, Any]:
        """Legacy method for querying markdown."""
        await self._ensure_initialized()
        result = self.query_engine.execute_query(sql)
        return result.to_dict()

    async def get_schema(self) -> Dict[str, Any]:
        """Legacy method for getting schema."""
        await self._ensure_initialized()
        return self.query_engine.get_schema()

    async def index_directory(self, path: str, recursive: bool = True) -> Dict[str, Any]:
        """Legacy method for indexing directory."""
        await self._ensure_initialized()
        path_obj = Path(path).expanduser().resolve()
        stats = self.indexer.index_directory(path_obj, recursive)
        return {"indexed_files": stats.get("files_processed", 0), "errors": []}

    async def get_file_content(self, file_path: str) -> Dict[str, Any]:
        """Legacy method for getting file content."""
        file_path_obj = Path(file_path).expanduser().resolve()

        if not file_path_obj.exists():
            return {"content": "", "metadata": {}}

        try:
            with open(file_path_obj, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(file_path_obj, 'r', encoding='latin-1') as f:
                content = f.read()

        stat = file_path_obj.stat()
        metadata = {
            "path": str(file_path_obj),
            "size": stat.st_size,
            "modified": stat.st_mtime
        }

        return {"content": content, "metadata": metadata}


def main():
    """Main entry point for MCP server."""
    import sys
    import argparse
    import os

    # Set up logging
    log_level = os.getenv('MDQUERY_LOG_LEVEL', 'INFO').upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stderr)  # MCP uses stdout for protocol
        ]
    )

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="mdquery MCP Server")
    parser.add_argument(
        "--notes-dir",
        type=Path,
        help="Directory containing markdown files (required for simplified config)"
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        help="Path to SQLite database file (optional, defaults to notes-dir/.mdquery/mdquery.db)"
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        help="Directory for cache files (optional, defaults to notes-dir/.mdquery/cache)"
    )
    parser.add_argument(
        "--no-auto-index",
        action="store_true",
        help="Disable automatic indexing on startup"
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Load configuration from JSON file"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Try to create simplified configuration
        config = None

        if args.config:
            # Load from configuration file
            logger.info(f"Loading configuration from: {args.config}")
            config = SimplifiedConfig.load_config(args.config)
        else:
            # Get notes directory from args or environment
            notes_dir = args.notes_dir
            if not notes_dir:
                notes_dir = os.getenv('MDQUERY_NOTES_DIR')

            if notes_dir:
                # Create simplified configuration
                logger.info(f"Creating simplified configuration for notes directory: {notes_dir}")
                config = SimplifiedConfig(
                    notes_dir=notes_dir,
                    db_path=args.db_path,
                    cache_dir=args.cache_dir,
                    auto_index=not args.no_auto_index
                )

                # Save configuration for future use
                try:
                    config.save_config()
                    logger.info("Configuration saved for future use")
                except Exception as e:
                    logger.warning(f"Could not save configuration: {e}")
            else:
                # Fall back to legacy configuration for backward compatibility
                logger.warning("No notes directory specified, using legacy configuration")

                # Get legacy configuration from environment variables
                db_path = args.db_path
                if not db_path and os.getenv('MDQUERY_DB_PATH'):
                    db_path = Path(os.getenv('MDQUERY_DB_PATH')).expanduser()

                cache_dir = args.cache_dir
                if not cache_dir and os.getenv('MDQUERY_CACHE_DIR'):
                    cache_dir = Path(os.getenv('MDQUERY_CACHE_DIR')).expanduser()

                # Handle notes directories (can be comma-separated)
                notes_dirs = []
                if os.getenv('MDQUERY_NOTES_DIR'):
                    notes_dir_env = os.getenv('MDQUERY_NOTES_DIR')
                    if ',' in notes_dir_env:
                        notes_dirs = [Path(p.strip()).expanduser() for p in notes_dir_env.split(',')]
                    else:
                        notes_dirs = [Path(notes_dir_env).expanduser()]

                # Create server with legacy configuration
                server = MDQueryMCPServer(
                    db_path=db_path,
                    cache_dir=cache_dir,
                    notes_dirs=notes_dirs
                )

        if config:
            # Create server with simplified configuration
            logger.info(f"Starting MCP server with configuration: {config}")
            server = MDQueryMCPServer(config=config)

        # Run the server
        asyncio.run(server.run())

    except (ConfigurationError, MdqueryError) as e:
        # Handle configuration errors with helpful messages
        error_message = create_helpful_error_message(e, args.notes_dir)
        print(error_message, file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server failed: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()