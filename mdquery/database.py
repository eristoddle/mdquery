"""
SQLite database schema and initialization for mdquery.

This module handles database connection management, schema creation,
and migrations for the mdquery SQLite database with FTS5 support.
"""

import sqlite3
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

from .exceptions import (
    DatabaseError, DatabaseConnectionError, DatabaseCorruptionError, SchemaError
)
from .logging_config import performance_timer, monitor_performance, log_error

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages SQLite database connections, schema, and migrations.

    Handles database initialization, schema creation, and version management
    for the mdquery system using SQLite with FTS5 extension.
    """

    # Current schema version
    SCHEMA_VERSION = 1

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database file. If None, uses in-memory database.
        """
        self.db_path = db_path or ":memory:"
        self._connection: Optional[sqlite3.Connection] = None

    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections with comprehensive error handling.

        Yields:
            sqlite3.Connection: Database connection with proper configuration

        Raises:
            DatabaseConnectionError: If connection cannot be established
            DatabaseCorruptionError: If database corruption is detected
        """
        if self._connection is None:
            self._connection = self._create_connection()

        try:
            # Test connection health
            self._connection.execute("SELECT 1").fetchone()
            yield self._connection
        except sqlite3.DatabaseError as e:
            if "database disk image is malformed" in str(e).lower():
                error = DatabaseCorruptionError(f"Database corruption detected: {e}")
                log_error(error, logger, {'database_path': str(self.db_path)})
                raise error from e
            else:
                error = DatabaseError(f"Database operation failed: {e}")
                log_error(error, logger, {'database_path': str(self.db_path)})
                raise error from e
        except Exception as e:
            try:
                self._connection.rollback()
            except Exception:
                pass  # Ignore rollback errors

            error = DatabaseError(f"Unexpected database error: {e}")
            log_error(error, logger, {'database_path': str(self.db_path)})
            raise error from e

    def _create_connection(self) -> sqlite3.Connection:
        """
        Create and configure SQLite connection with comprehensive error handling.

        Returns:
            sqlite3.Connection: Configured database connection

        Raises:
            DatabaseConnectionError: If connection cannot be established
        """
        max_retries = 3
        retry_delay = 1.0

        for attempt in range(max_retries):
            try:
                conn = sqlite3.connect(
                    self.db_path,
                    timeout=30.0,  # 30 second timeout
                    check_same_thread=False
                )

                # Configure connection
                conn.row_factory = sqlite3.Row  # Enable column access by name

                # Set pragmas with error handling
                try:
                    conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
                    conn.execute("PRAGMA journal_mode = WAL")  # Enable WAL mode for better concurrency
                    conn.execute("PRAGMA synchronous = NORMAL")  # Balance safety and performance
                    conn.execute("PRAGMA temp_store = MEMORY")  # Use memory for temp storage
                    conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
                except sqlite3.Error as e:
                    logger.warning(f"Failed to set some PRAGMA options: {e}")

                # Check FTS5 availability
                try:
                    cursor = conn.execute("PRAGMA compile_options")
                    compile_options = [row[0] for row in cursor.fetchall()]
                    if not any("FTS5" in option for option in compile_options):
                        raise DatabaseConnectionError("SQLite FTS5 extension is not available")
                except sqlite3.Error as e:
                    raise DatabaseConnectionError(f"Failed to check FTS5 availability: {e}") from e

                # Test basic functionality
                try:
                    conn.execute("SELECT 1").fetchone()
                except sqlite3.Error as e:
                    raise DatabaseConnectionError(f"Database connection test failed: {e}") from e

                logger.info(f"Database connection established: {self.db_path}")
                return conn

            except sqlite3.OperationalError as e:
                if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                    logger.warning(f"Database locked, retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    raise DatabaseConnectionError(f"Failed to connect to database after {max_retries} attempts: {e}") from e
            except sqlite3.Error as e:
                raise DatabaseConnectionError(f"Failed to connect to database: {e}") from e
            except Exception as e:
                raise DatabaseConnectionError(f"Unexpected error connecting to database: {e}") from e

        # This should never be reached, but just in case
        raise DatabaseConnectionError(f"Failed to connect to database after {max_retries} attempts")

    def initialize_database(self) -> None:
        """
        Initialize database with schema and migrations.

        Creates all necessary tables, indexes, and views if they don't exist.
        Runs any pending migrations to bring schema up to current version.
        """
        with self.get_connection() as conn:
            # Create schema version table first
            self._create_version_table(conn)

            # Get current schema version
            current_version = self._get_schema_version(conn)

            if current_version == 0:
                # Fresh database - create all tables
                self._create_schema(conn)
                self._set_schema_version(conn, self.SCHEMA_VERSION)
                logger.info("Database schema created successfully")
            elif current_version < self.SCHEMA_VERSION:
                # Run migrations
                self._run_migrations(conn, current_version)
                logger.info(f"Database migrated from version {current_version} to {self.SCHEMA_VERSION}")
            elif current_version > self.SCHEMA_VERSION:
                raise DatabaseError(
                    f"Database version {current_version} is newer than supported version {self.SCHEMA_VERSION}"
                )
            else:
                logger.debug("Database schema is up to date")

            conn.commit()

    def _create_version_table(self, conn: sqlite3.Connection) -> None:
        """Create schema version tracking table."""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

    def _get_schema_version(self, conn: sqlite3.Connection) -> int:
        """Get current schema version."""
        cursor = conn.execute("SELECT MAX(version) FROM schema_version")
        result = cursor.fetchone()
        return result[0] if result[0] is not None else 0

    def _set_schema_version(self, conn: sqlite3.Connection, version: int) -> None:
        """Set schema version."""
        conn.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))

    def _create_schema(self, conn: sqlite3.Connection) -> None:
        """
        Create complete database schema.

        Creates all tables, indexes, views, and FTS5 virtual tables
        according to the design specification.
        """
        # Files table - core file metadata
        conn.execute("""
            CREATE TABLE files (
                id INTEGER PRIMARY KEY,
                path TEXT UNIQUE NOT NULL,
                filename TEXT NOT NULL,
                directory TEXT NOT NULL,
                modified_date DATETIME NOT NULL,
                created_date DATETIME,
                file_size INTEGER NOT NULL,
                content_hash TEXT NOT NULL,
                word_count INTEGER DEFAULT 0,
                heading_count INTEGER DEFAULT 0,
                indexed_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Frontmatter table - key-value pairs from YAML frontmatter
        conn.execute("""
            CREATE TABLE frontmatter (
                file_id INTEGER NOT NULL,
                key TEXT NOT NULL,
                value TEXT,
                value_type TEXT NOT NULL CHECK (value_type IN ('string', 'number', 'boolean', 'array', 'date')),
                PRIMARY KEY (file_id, key),
                FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
            )
        """)

        # Tags table - extracted tags from frontmatter and content
        conn.execute("""
            CREATE TABLE tags (
                file_id INTEGER NOT NULL,
                tag TEXT NOT NULL,
                source TEXT NOT NULL CHECK (source IN ('frontmatter', 'content', 'unknown')),
                PRIMARY KEY (file_id, tag),
                FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
            )
        """)

        # Links table - extracted links from markdown content
        conn.execute("""
            CREATE TABLE links (
                id INTEGER PRIMARY KEY,
                file_id INTEGER NOT NULL,
                link_text TEXT,
                link_target TEXT NOT NULL,
                link_type TEXT NOT NULL CHECK (link_type IN ('markdown', 'wikilink', 'reference', 'autolink')),
                is_internal BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
            )
        """)

        # FTS5 virtual table for full-text search
        conn.execute("""
            CREATE VIRTUAL TABLE content_fts USING fts5(
                file_id UNINDEXED,
                title,
                content,
                headings
            )
        """)

        # Create indexes for performance
        self._create_indexes(conn)

        # Create views for convenient querying
        self._create_views(conn)

    def _create_indexes(self, conn: sqlite3.Connection) -> None:
        """Create database indexes for query performance."""
        indexes = [
            "CREATE INDEX idx_files_path ON files(path)",
            "CREATE INDEX idx_files_directory ON files(directory)",
            "CREATE INDEX idx_files_modified_date ON files(modified_date)",
            "CREATE INDEX idx_files_content_hash ON files(content_hash)",
            "CREATE INDEX idx_frontmatter_key ON frontmatter(key)",
            "CREATE INDEX idx_frontmatter_value ON frontmatter(value)",
            "CREATE INDEX idx_tags_tag ON tags(tag)",
            "CREATE INDEX idx_tags_source ON tags(source)",
            "CREATE INDEX idx_links_target ON links(link_target)",
            "CREATE INDEX idx_links_type ON links(link_type)",
            "CREATE INDEX idx_links_internal ON links(is_internal)"
        ]

        for index_sql in indexes:
            conn.execute(index_sql)

    def _create_views(self, conn: sqlite3.Connection) -> None:
        """Create database views for convenient querying."""

        # Unified files view with common metadata
        conn.execute("""
            CREATE VIEW files_with_metadata AS
            SELECT
                f.*,
                GROUP_CONCAT(DISTINCT t.tag) as tags,
                COUNT(DISTINCT l.link_target) as link_count,
                fm_title.value as title,
                fm_description.value as description,
                fm_category.value as category,
                fm_author.value as author,
                fm_date.value as date
            FROM files f
            LEFT JOIN tags t ON f.id = t.file_id
            LEFT JOIN links l ON f.id = l.file_id
            LEFT JOIN frontmatter fm_title ON f.id = fm_title.file_id AND fm_title.key = 'title'
            LEFT JOIN frontmatter fm_description ON f.id = fm_description.file_id AND fm_description.key = 'description'
            LEFT JOIN frontmatter fm_category ON f.id = fm_category.file_id AND fm_category.key = 'category'
            LEFT JOIN frontmatter fm_author ON f.id = fm_author.file_id AND fm_author.key = 'author'
            LEFT JOIN frontmatter fm_date ON f.id = fm_date.file_id AND fm_date.key = 'date'
            GROUP BY f.id
        """)

        # Tag summary view
        conn.execute("""
            CREATE VIEW tag_summary AS
            SELECT
                tag,
                COUNT(*) as file_count,
                source
            FROM tags
            GROUP BY tag, source
            ORDER BY file_count DESC
        """)

        # Link summary view
        conn.execute("""
            CREATE VIEW link_summary AS
            SELECT
                link_target,
                COUNT(*) as reference_count,
                link_type,
                is_internal
            FROM links
            GROUP BY link_target, link_type, is_internal
            ORDER BY reference_count DESC
        """)

    def _run_migrations(self, conn: sqlite3.Connection, from_version: int) -> None:
        """
        Run database migrations from current version to latest.

        Args:
            conn: Database connection
            from_version: Current schema version
        """
        migrations = {
            # Future migrations will be added here
            # Example:
            # 2: self._migrate_to_version_2,
            # 3: self._migrate_to_version_3,
        }

        for version in range(from_version + 1, self.SCHEMA_VERSION + 1):
            if version in migrations:
                logger.info(f"Running migration to version {version}")
                migrations[version](conn)
                self._set_schema_version(conn, version)
            else:
                raise DatabaseError(f"No migration available for version {version}")

    def get_schema_info(self) -> Dict[str, Any]:
        """
        Get database schema information.

        Returns:
            Dict containing schema version, table info, and statistics
        """
        with self.get_connection() as conn:
            schema_info = {
                "version": self._get_schema_version(conn),
                "tables": {},
                "views": {},
                "indexes": []
            }

            # Get table information
            cursor = conn.execute("""
                SELECT name, sql FROM sqlite_master
                WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)

            for row in cursor.fetchall():
                table_name = row["name"]

                # Get column info
                col_cursor = conn.execute(f"PRAGMA table_info({table_name})")
                columns = [
                    {
                        "name": col["name"],
                        "type": col["type"],
                        "not_null": bool(col["notnull"]),
                        "primary_key": bool(col["pk"])
                    }
                    for col in col_cursor.fetchall()
                ]

                # Get row count
                count_cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = count_cursor.fetchone()[0]

                schema_info["tables"][table_name] = {
                    "columns": columns,
                    "row_count": row_count,
                    "sql": row["sql"]
                }

            # Get view information
            cursor = conn.execute("""
                SELECT name, sql FROM sqlite_master
                WHERE type = 'view'
                ORDER BY name
            """)

            for row in cursor.fetchall():
                schema_info["views"][row["name"]] = {
                    "sql": row["sql"]
                }

            # Get index information
            cursor = conn.execute("""
                SELECT name, sql FROM sqlite_master
                WHERE type = 'index' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)

            schema_info["indexes"] = [
                {"name": row["name"], "sql": row["sql"]}
                for row in cursor.fetchall()
            ]

            return schema_info

    def validate_schema(self) -> bool:
        """
        Validate database schema integrity.

        Returns:
            True if schema is valid, False otherwise
        """
        try:
            with self.get_connection() as conn:
                # Check foreign key constraints
                cursor = conn.execute("PRAGMA foreign_key_check")
                fk_violations = cursor.fetchall()

                if fk_violations:
                    logger.error(f"Foreign key violations found: {fk_violations}")
                    return False

                # Check table integrity
                tables = ["files", "frontmatter", "tags", "links"]
                for table in tables:
                    cursor = conn.execute(f"PRAGMA integrity_check({table})")
                    result = cursor.fetchone()
                    if result[0] != "ok":
                        logger.error(f"Integrity check failed for table {table}: {result[0]}")
                        return False

                # Check FTS5 table
                try:
                    conn.execute("SELECT * FROM content_fts LIMIT 1")
                except sqlite3.Error as e:
                    logger.error(f"FTS5 table validation failed: {e}")
                    return False

                return True

        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            return False

    def close(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.debug("Database connection closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def create_database(db_path: Path) -> DatabaseManager:
    """
    Create and initialize a new database.

    Args:
        db_path: Path where database file should be created

    Returns:
        DatabaseManager: Initialized database manager
    """
    # Ensure parent directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Create and initialize database
    db_manager = DatabaseManager(db_path)
    db_manager.initialize_database()

    return db_manager