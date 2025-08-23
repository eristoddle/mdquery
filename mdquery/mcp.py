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

    def __init__(self, db_path: Optional[Path] = None, cache_dir: Optional[Path] = None):
        """
        Initialize MCP server with database and indexing components.

        Args:
            db_path: Path to SQLite database file
            cache_dir: Directory for cache files
        """
        self.db_path = db_path or Path.home() / ".mdquery" / "mdquery.db"
        self.cache_dir = cache_dir or Path.home() / ".mdquery" / "cache"

        # Ensure directories exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.db_manager: Optional[DatabaseManager] = None
        self.query_engine: Optional[QueryEngine] = None
        self.indexer: Optional[Indexer] = None
        self.cache_manager: Optional[CacheManager] = None

        # Thread pool for blocking operations
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="mdquery-mcp")

        # Thread safety lock
        self._lock = threading.RLock()

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

    async def _ensure_initialized(self) -> None:
        """Ensure all components are initialized."""
        if self.db_manager is None:
            with self._lock:
                if self.db_manager is None:
                    # Initialize in thread pool to avoid blocking
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(self.executor, self._initialize_components)

    def _initialize_components(self) -> None:
        """Initialize database and related components."""
        try:
            # Initialize database
            self.db_manager = create_database(self.db_path)

            # Initialize cache manager
            self.cache_manager = CacheManager(
                cache_path=self.db_path,  # Use same path as database
                database_manager=self.db_manager
            )

            # Initialize query engine
            self.query_engine = QueryEngine(self.db_manager)

            # Initialize indexer
            self.indexer = Indexer(
                database_manager=self.db_manager,
                cache_manager=self.cache_manager
            )

            logger.info("MCP server components initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise MCPServerError(f"Initialization failed: {e}")

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

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stderr)  # MCP uses stdout for protocol
        ]
    )

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="mdquery MCP Server")
    parser.add_argument(
        "--db-path",
        type=Path,
        help="Path to SQLite database file"
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        help="Directory for cache files"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create and run server
    server = MDQueryMCPServer(
        db_path=args.db_path,
        cache_dir=args.cache_dir
    )

    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()