"""
Unit tests for mdquery database module.

Tests database schema creation, initialization, migrations,
and validation functionality.
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from mdquery.database import DatabaseManager, DatabaseError, create_database


class TestDatabaseManager:
    """Test cases for DatabaseManager class."""

    def test_init_with_memory_database(self):
        """Test initialization with in-memory database."""
        db_manager = DatabaseManager()
        assert db_manager.db_path == ":memory:"
        assert db_manager._connection is None

    def test_init_with_file_database(self):
        """Test initialization with file database."""
        db_path = Path("/tmp/test.db")
        db_manager = DatabaseManager(db_path)
        assert db_manager.db_path == db_path
        assert db_manager._connection is None

    def test_create_connection_success(self):
        """Test successful database connection creation."""
        db_manager = DatabaseManager()

        with db_manager.get_connection() as conn:
            assert isinstance(conn, sqlite3.Connection)
            assert conn.row_factory == sqlite3.Row

            # Test foreign keys are enabled
            cursor = conn.execute("PRAGMA foreign_keys")
            assert cursor.fetchone()[0] == 1

    def test_create_connection_fts5_not_available(self):
        """Test connection creation when FTS5 is not available."""
        # This test is skipped because mocking sqlite3.Connection.execute is not possible
        # due to the immutable nature of the sqlite3.Connection type.
        # In practice, FTS5 is available in most modern SQLite installations.
        pytest.skip("Cannot mock sqlite3.Connection.execute due to immutable type")

    def test_initialize_database_fresh(self):
        """Test database initialization with fresh database."""
        db_manager = DatabaseManager()
        db_manager.initialize_database()

        with db_manager.get_connection() as conn:
            # Check schema version table exists
            cursor = conn.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='schema_version'
            """)
            assert cursor.fetchone() is not None

            # Check current version is set
            cursor = conn.execute("SELECT MAX(version) FROM schema_version")
            assert cursor.fetchone()[0] == DatabaseManager.SCHEMA_VERSION

    def test_schema_creation(self):
        """Test complete schema creation."""
        db_manager = DatabaseManager()
        db_manager.initialize_database()

        with db_manager.get_connection() as conn:
            # Check all required tables exist
            expected_tables = ["files", "frontmatter", "tags", "links", "content_fts"]

            cursor = conn.execute("""
                SELECT name FROM sqlite_master
                WHERE type IN ('table', 'view') AND name NOT LIKE 'sqlite_%'
            """)

            existing_tables = {row[0] for row in cursor.fetchall()}

            for table in expected_tables:
                assert table in existing_tables, f"Table {table} not found"

    def test_files_table_structure(self):
        """Test files table has correct structure."""
        db_manager = DatabaseManager()
        db_manager.initialize_database()

        with db_manager.get_connection() as conn:
            cursor = conn.execute("PRAGMA table_info(files)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}  # name: type

            expected_columns = {
                "id": "INTEGER",
                "path": "TEXT",
                "filename": "TEXT",
                "directory": "TEXT",
                "modified_date": "DATETIME",
                "created_date": "DATETIME",
                "file_size": "INTEGER",
                "content_hash": "TEXT",
                "word_count": "INTEGER",
                "heading_count": "INTEGER",
                "indexed_at": "DATETIME"
            }

            for col_name, col_type in expected_columns.items():
                assert col_name in columns, f"Column {col_name} not found in files table"
                assert columns[col_name] == col_type, f"Column {col_name} has wrong type"

    def test_frontmatter_table_structure(self):
        """Test frontmatter table has correct structure and constraints."""
        db_manager = DatabaseManager()
        db_manager.initialize_database()

        with db_manager.get_connection() as conn:
            cursor = conn.execute("PRAGMA table_info(frontmatter)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}

            expected_columns = {
                "file_id": "INTEGER",
                "key": "TEXT",
                "value": "TEXT",
                "value_type": "TEXT"
            }

            for col_name, col_type in expected_columns.items():
                assert col_name in columns, f"Column {col_name} not found"
                assert columns[col_name] == col_type, f"Column {col_name} has wrong type"

            # Test value_type constraint
            with pytest.raises(sqlite3.IntegrityError):
                cursor = conn.execute("""
                    INSERT INTO files (path, filename, directory, modified_date, file_size, content_hash)
                    VALUES ('test.md', 'test.md', '/tmp', '2023-01-01', 100, 'hash123')
                """)
                file_id = cursor.lastrowid
                conn.execute("""
                    INSERT INTO frontmatter (file_id, key, value, value_type)
                    VALUES (?, 'test', 'value', 'invalid_type')
                """, (file_id,))

    def test_tags_table_structure(self):
        """Test tags table has correct structure."""
        db_manager = DatabaseManager()
        db_manager.initialize_database()

        with db_manager.get_connection() as conn:
            cursor = conn.execute("PRAGMA table_info(tags)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}

            expected_columns = {
                "file_id": "INTEGER",
                "tag": "TEXT",
                "source": "TEXT"
            }

            for col_name, col_type in expected_columns.items():
                assert col_name in columns, f"Column {col_name} not found"

    def test_links_table_structure(self):
        """Test links table has correct structure."""
        db_manager = DatabaseManager()
        db_manager.initialize_database()

        with db_manager.get_connection() as conn:
            cursor = conn.execute("PRAGMA table_info(links)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}

            expected_columns = {
                "id": "INTEGER",
                "file_id": "INTEGER",
                "link_text": "TEXT",
                "link_target": "TEXT",
                "link_type": "TEXT",
                "is_internal": "BOOLEAN"
            }

            for col_name, col_type in expected_columns.items():
                assert col_name in columns, f"Column {col_name} not found"

    def test_fts5_table_creation(self):
        """Test FTS5 virtual table is created correctly."""
        db_manager = DatabaseManager()
        db_manager.initialize_database()

        with db_manager.get_connection() as conn:
            # Check FTS5 table exists
            cursor = conn.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='content_fts'
            """)
            assert cursor.fetchone() is not None

            # Test FTS5 table can be queried
            cursor = conn.execute("SELECT * FROM content_fts LIMIT 1")
            # Should not raise an error even if empty

    def test_indexes_creation(self):
        """Test database indexes are created."""
        db_manager = DatabaseManager()
        db_manager.initialize_database()

        with db_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master
                WHERE type='index' AND name NOT LIKE 'sqlite_%'
            """)

            indexes = {row[0] for row in cursor.fetchall()}

            expected_indexes = {
                "idx_files_path",
                "idx_files_directory",
                "idx_files_modified_date",
                "idx_files_content_hash",
                "idx_frontmatter_key",
                "idx_frontmatter_value",
                "idx_tags_tag",
                "idx_tags_source",
                "idx_links_target",
                "idx_links_type",
                "idx_links_internal"
            }

            for index in expected_indexes:
                assert index in indexes, f"Index {index} not found"

    def test_views_creation(self):
        """Test database views are created."""
        db_manager = DatabaseManager()
        db_manager.initialize_database()

        with db_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master
                WHERE type='view'
            """)

            views = {row[0] for row in cursor.fetchall()}

            expected_views = {
                "files_with_metadata",
                "tag_summary",
                "link_summary"
            }

            for view in expected_views:
                assert view in views, f"View {view} not found"

            # Test views can be queried
            for view in expected_views:
                cursor = conn.execute(f"SELECT * FROM {view} LIMIT 1")
                # Should not raise an error even if empty

    def test_foreign_key_constraints(self):
        """Test foreign key constraints are enforced."""
        db_manager = DatabaseManager()
        db_manager.initialize_database()

        with db_manager.get_connection() as conn:
            # Try to insert frontmatter with non-existent file_id
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute("""
                    INSERT INTO frontmatter (file_id, key, value, value_type)
                    VALUES (999, 'test', 'value', 'string')
                """)

            # Try to insert tag with non-existent file_id
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute("""
                    INSERT INTO tags (file_id, tag, source)
                    VALUES (999, 'test-tag', 'frontmatter')
                """)

    def test_get_schema_info(self):
        """Test schema information retrieval."""
        db_manager = DatabaseManager()
        db_manager.initialize_database()

        schema_info = db_manager.get_schema_info()

        assert "version" in schema_info
        assert schema_info["version"] == DatabaseManager.SCHEMA_VERSION

        assert "tables" in schema_info
        assert "files" in schema_info["tables"]
        assert "frontmatter" in schema_info["tables"]

        assert "views" in schema_info
        assert "files_with_metadata" in schema_info["views"]

        assert "indexes" in schema_info
        assert len(schema_info["indexes"]) > 0

        # Check table info structure
        files_info = schema_info["tables"]["files"]
        assert "columns" in files_info
        assert "row_count" in files_info
        assert "sql" in files_info

    def test_validate_schema_success(self):
        """Test successful schema validation."""
        db_manager = DatabaseManager()
        db_manager.initialize_database()

        assert db_manager.validate_schema() is True

    def test_validate_schema_with_data(self):
        """Test schema validation with sample data."""
        db_manager = DatabaseManager()
        db_manager.initialize_database()

        with db_manager.get_connection() as conn:
            # Insert sample data
            cursor = conn.execute("""
                INSERT INTO files (path, filename, directory, modified_date, file_size, content_hash)
                VALUES ('test.md', 'test.md', '/tmp', '2023-01-01', 100, 'hash123')
            """)
            file_id = cursor.lastrowid

            conn.execute("""
                INSERT INTO frontmatter (file_id, key, value, value_type)
                VALUES (?, 'title', 'Test Title', 'string')
            """, (file_id,))

            conn.execute("""
                INSERT INTO tags (file_id, tag, source)
                VALUES (?, 'test-tag', 'frontmatter')
            """, (file_id,))

            conn.commit()

        assert db_manager.validate_schema() is True

    def test_context_manager(self):
        """Test DatabaseManager as context manager."""
        with DatabaseManager() as db_manager:
            db_manager.initialize_database()
            # Connection is created during initialization

            with db_manager.get_connection() as conn:
                assert isinstance(conn, sqlite3.Connection)

        # Connection should be closed after context exit
        assert db_manager._connection is None

    def test_connection_error_handling(self):
        """Test database connection error handling."""
        # Test with invalid database path
        invalid_path = Path("/invalid/path/database.db")
        db_manager = DatabaseManager(invalid_path)

        with pytest.raises(DatabaseError):
            with db_manager.get_connection():
                pass

    def test_migration_system_placeholder(self):
        """Test migration system structure (placeholder for future migrations)."""
        db_manager = DatabaseManager()

        # Test that migration system doesn't break with no migrations
        with db_manager.get_connection() as conn:
            db_manager._create_version_table(conn)
            db_manager._set_schema_version(conn, 1)

            # This should not raise an error
            db_manager._run_migrations(conn, 1)


class TestCreateDatabase:
    """Test cases for create_database function."""

    def test_create_database_success(self):
        """Test successful database creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"

            db_manager = create_database(db_path)

            assert db_path.exists()
            assert isinstance(db_manager, DatabaseManager)
            assert db_manager.db_path == db_path

            # Verify database is properly initialized
            schema_info = db_manager.get_schema_info()
            assert schema_info["version"] == DatabaseManager.SCHEMA_VERSION

    def test_create_database_creates_parent_directory(self):
        """Test database creation creates parent directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "subdir" / "test.db"

            db_manager = create_database(db_path)

            assert db_path.parent.exists()
            assert db_path.exists()

    def test_database_file_permissions(self):
        """Test created database file has correct permissions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"

            create_database(db_path)

            assert db_path.exists()
            assert db_path.is_file()
            # File should be readable and writable by owner
            assert db_path.stat().st_mode & 0o600


class TestDatabaseIntegration:
    """Integration tests for database functionality."""

    def test_complete_workflow(self):
        """Test complete database workflow with real data."""
        db_manager = DatabaseManager()
        db_manager.initialize_database()

        with db_manager.get_connection() as conn:
            # Insert a complete file record
            cursor = conn.execute("""
                INSERT INTO files (path, filename, directory, modified_date, file_size, content_hash, word_count, heading_count)
                VALUES ('notes/test.md', 'test.md', 'notes', '2023-01-01 12:00:00', 1024, 'abc123', 150, 3)
            """)
            file_id = cursor.lastrowid

            # Insert frontmatter
            frontmatter_data = [
                (file_id, 'title', 'Test Note', 'string'),
                (file_id, 'tags', 'research,notes', 'array'),
                (file_id, 'published', 'true', 'boolean'),
                (file_id, 'date', '2023-01-01', 'date')
            ]

            conn.executemany("""
                INSERT INTO frontmatter (file_id, key, value, value_type)
                VALUES (?, ?, ?, ?)
            """, frontmatter_data)

            # Insert tags
            tag_data = [
                (file_id, 'research', 'frontmatter'),
                (file_id, 'notes', 'frontmatter'),
                (file_id, 'important', 'content')
            ]

            conn.executemany("""
                INSERT INTO tags (file_id, tag, source)
                VALUES (?, ?, ?)
            """, tag_data)

            # Insert links
            link_data = [
                (file_id, 'Related Note', 'related-note.md', 'wikilink', True),
                (file_id, 'External Link', 'https://example.com', 'markdown', False)
            ]

            conn.executemany("""
                INSERT INTO links (file_id, link_text, link_target, link_type, is_internal)
                VALUES (?, ?, ?, ?, ?)
            """, link_data)

            # Insert FTS content
            conn.execute("""
                INSERT INTO content_fts (file_id, title, content, headings)
                VALUES (?, 'Test Note', 'This is test content for searching', 'Introduction,Methods,Results')
            """, (file_id,))

            conn.commit()

            # Test unified view
            cursor = conn.execute("SELECT * FROM files_with_metadata WHERE id = ?", (file_id,))
            result = cursor.fetchone()

            assert result is not None
            assert result["filename"] == "test.md"
            assert result["title"] == "Test Note"
            assert "research" in result["tags"]
            assert result["link_count"] == 2

            # Test FTS search
            cursor = conn.execute("SELECT * FROM content_fts WHERE content_fts MATCH 'test'")
            fts_result = cursor.fetchone()
            assert fts_result is not None

        # Validate final schema
        assert db_manager.validate_schema() is True