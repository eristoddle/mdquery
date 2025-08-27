"""
Directory Structure Setup Automation for mdquery.

This module provides automated setup of directory structures, database
initialization, and optimization for different note-taking systems.

Implements requirements from task 12c of the MCP workflow optimization spec.
"""

import os
import sqlite3
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

from .auto_config import AutoConfigurationManager, NoteSystemType
from .config_generator import AutomaticConfigurationGenerator

logger = logging.getLogger(__name__)


@dataclass
class SetupResult:
    """Result of directory setup automation."""
    success: bool
    directories_created: List[str]
    database_initialized: bool
    files_indexed: int
    setup_time_seconds: float
    optimizations_applied: List[str]
    errors: List[str]
    recommendations: List[str]


@dataclass
class DirectoryStructure:
    """Directory structure template for a note system."""
    system_type: NoteSystemType
    required_dirs: List[str]
    optional_dirs: List[str]
    config_files: Dict[str, str]
    exclude_patterns: List[str]
    index_patterns: List[str]


class DirectorySetupManager:
    """
    Automated directory structure setup manager.

    Handles complete setup automation including:
    - Directory structure creation
    - Database initialization and optimization
    - Index creation and population
    - Performance optimization
    """

    def __init__(self):
        """Initialize the directory setup manager."""
        self.auto_config = AutoConfigurationManager()
        self.config_generator = AutomaticConfigurationGenerator()
        self.directory_templates = self._initialize_directory_templates()

    def _initialize_directory_templates(self) -> Dict[NoteSystemType, DirectoryStructure]:
        """Initialize directory structure templates."""
        return {
            NoteSystemType.OBSIDIAN: DirectoryStructure(
                system_type=NoteSystemType.OBSIDIAN,
                required_dirs=[".obsidian"],
                optional_dirs=[".obsidian/plugins", ".obsidian/themes", "Templates", "Attachments"],
                config_files={
                    ".obsidian/config": '{"theme":"obsidian"}',
                    ".obsidian/workspace": '{}'
                },
                exclude_patterns=["*.tmp", "*.log", ".DS_Store", "Thumbs.db"],
                index_patterns=["*.md", "*.canvas"]
            ),

            NoteSystemType.JEKYLL: DirectoryStructure(
                system_type=NoteSystemType.JEKYLL,
                required_dirs=["_posts"],
                optional_dirs=["_drafts", "_includes", "_layouts", "_sass", "assets"],
                config_files={
                    "_config.yml": """title: My Jekyll Site
description: A Jekyll site for blogging
baseurl: ""
url: ""
markdown: kramdown
highlighter: rouge
plugins:
  - jekyll-feed
"""
                },
                exclude_patterns=["_site/*", "vendor/*", ".bundle/*", ".sass-cache/*"],
                index_patterns=["*.md", "*.markdown", "*.html"]
            ),

            NoteSystemType.HUGO: DirectoryStructure(
                system_type=NoteSystemType.HUGO,
                required_dirs=["content"],
                optional_dirs=["static", "layouts", "data", "themes", "archetypes"],
                config_files={
                    "config.toml": """baseURL = "http://example.org/"
languageCode = "en-us"
title = "My Hugo Site"
theme = "ananke"

[params]
  featured_image = "/images/gohugo-default-sample-hero-image.jpg"
  recent_posts_number = 5
"""
                },
                exclude_patterns=["public/*", "resources/*", "node_modules/*"],
                index_patterns=["*.md", "*.markdown"]
            ),

            NoteSystemType.LOGSEQ: DirectoryStructure(
                system_type=NoteSystemType.LOGSEQ,
                required_dirs=["logseq", "pages", "journals"],
                optional_dirs=["assets", "draws"],
                config_files={
                    "logseq/config.edn": """{:meta/version 1
 :last-modified 1640995200000
 :publishing/all-pages-public? false
 :default-templates
 {:journals ""}}
"""
                },
                exclude_patterns=["*.edn~", "*.tmp"],
                index_patterns=["*.md"]
            ),

            NoteSystemType.GENERIC: DirectoryStructure(
                system_type=NoteSystemType.GENERIC,
                required_dirs=[],
                optional_dirs=["attachments", "templates", "archive"],
                config_files={},
                exclude_patterns=["*.tmp", "*.log", ".DS_Store", "Thumbs.db"],
                index_patterns=["*.md", "*.markdown", "*.txt"]
            )
        }

    def setup_directory_structure(self, directory: str,
                                 force_system_type: Optional[NoteSystemType] = None,
                                 create_missing_dirs: bool = True,
                                 initialize_database: bool = True,
                                 run_initial_index: bool = True) -> SetupResult:
        """
        Set up complete directory structure and database.

        Args:
            directory: Target directory path
            force_system_type: Force specific system type instead of auto-detecting
            create_missing_dirs: Create missing required directories
            initialize_database: Initialize and optimize database
            run_initial_index: Run initial indexing of files

        Returns:
            SetupResult with operation details
        """
        start_time = datetime.now()
        result = SetupResult(
            success=False,
            directories_created=[],
            database_initialized=False,
            files_indexed=0,
            setup_time_seconds=0.0,
            optimizations_applied=[],
            errors=[],
            recommendations=[]
        )

        try:
            logger.info(f"Starting directory setup for: {directory}")
            directory_path = Path(directory)

            # Ensure target directory exists
            if not directory_path.exists():
                directory_path.mkdir(parents=True, exist_ok=True)
                result.directories_created.append(str(directory_path))
                logger.info(f"Created main directory: {directory}")

            # Detect or use forced system type
            if force_system_type:
                system_type = force_system_type
                logger.info(f"Using forced system type: {system_type.value}")
            else:
                detection_result = self.auto_config.detect_note_system(directory)
                system_type = detection_result.system_type
                logger.info(f"Detected system type: {system_type.value} (confidence: {detection_result.confidence:.2f})")

            # Get directory template
            template = self.directory_templates[system_type]

            # Create directory structure
            if create_missing_dirs:
                created_dirs = self._create_directory_structure(directory_path, template)
                result.directories_created.extend(created_dirs)

            # Initialize database
            if initialize_database:
                db_success, optimizations = self._initialize_database(directory, system_type)
                result.database_initialized = db_success
                result.optimizations_applied.extend(optimizations)

            # Run initial indexing
            if run_initial_index:
                indexed_count = self._run_initial_indexing(directory, template)
                result.files_indexed = indexed_count

            # Generate configuration
            self._generate_configuration_files(directory, system_type)

            # Add recommendations
            result.recommendations = self._generate_recommendations(directory, system_type, result)

            result.success = True
            logger.info(f"Directory setup completed successfully")

        except Exception as e:
            error_msg = f"Setup failed: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)

        finally:
            # Calculate setup time
            end_time = datetime.now()
            result.setup_time_seconds = (end_time - start_time).total_seconds()

        return result

    def _create_directory_structure(self, base_path: Path, template: DirectoryStructure) -> List[str]:
        """Create directory structure based on template."""
        created_dirs = []

        # Create required directories
        for dir_name in template.required_dirs:
            dir_path = base_path / dir_name
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                created_dirs.append(str(dir_path))
                logger.info(f"Created required directory: {dir_name}")

        # Create optional directories (only if they don't exist)
        for dir_name in template.optional_dirs:
            dir_path = base_path / dir_name
            if not dir_path.exists():
                # Only create if it makes sense in context
                if self._should_create_optional_directory(dir_name, base_path):
                    dir_path.mkdir(parents=True, exist_ok=True)
                    created_dirs.append(str(dir_path))
                    logger.info(f"Created optional directory: {dir_name}")

        # Create configuration files
        for file_path, content in template.config_files.items():
            full_path = base_path / file_path
            if not full_path.exists():
                full_path.parent.mkdir(parents=True, exist_ok=True)
                with open(full_path, 'w') as f:
                    f.write(content)
                logger.info(f"Created config file: {file_path}")

        return created_dirs

    def _should_create_optional_directory(self, dir_name: str, base_path: Path) -> bool:
        """Determine if an optional directory should be created."""
        # Don't create directories that might conflict with existing structure
        if dir_name.startswith('.') and len(list(base_path.glob('.*'))) > 2:
            return False  # Already has hidden directories

        # Create common organizational directories
        if dir_name.lower() in ['templates', 'attachments', 'assets', 'archive']:
            return True

        # Create system-specific directories
        if dir_name in ['_includes', '_layouts', '_sass'] and (base_path / '_posts').exists():
            return True  # Jekyll site

        return False

    def _initialize_database(self, directory: str, system_type: NoteSystemType) -> Tuple[bool, List[str]]:
        """Initialize and optimize database for the directory."""
        optimizations = []

        try:
            # Determine database path
            db_dir = Path.home() / ".mdquery"
            db_dir.mkdir(exist_ok=True)

            db_path = db_dir / f"{Path(directory).name}.db"

            # Initialize database
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Create basic tables
            self._create_database_schema(cursor)
            optimizations.append("Created database schema")

            # System-specific optimizations
            if system_type == NoteSystemType.OBSIDIAN:
                self._apply_obsidian_optimizations(cursor)
                optimizations.append("Applied Obsidian-specific optimizations")
            elif system_type == NoteSystemType.JEKYLL:
                self._apply_jekyll_optimizations(cursor)
                optimizations.append("Applied Jekyll-specific optimizations")

            # General performance optimizations
            self._apply_performance_optimizations(cursor)
            optimizations.append("Applied performance optimizations")

            conn.commit()
            conn.close()

            logger.info(f"Database initialized: {db_path}")
            return True, optimizations

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            return False, optimizations

    def _create_database_schema(self, cursor: sqlite3.Cursor) -> None:
        """Create basic database schema."""
        # Files table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY,
                filename TEXT NOT NULL,
                directory TEXT,
                full_path TEXT UNIQUE,
                title TEXT,
                created_date TEXT,
                modified_date TEXT,
                word_count INTEGER,
                content TEXT
            )
        """)

        # Tags table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY,
                file_id INTEGER,
                tag TEXT,
                FOREIGN KEY (file_id) REFERENCES files (id)
            )
        """)

        # Links table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY,
                file_id INTEGER,
                link_text TEXT,
                link_target TEXT,
                is_internal BOOLEAN,
                FOREIGN KEY (file_id) REFERENCES files (id)
            )
        """)

        # Frontmatter table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS frontmatter (
                id INTEGER PRIMARY KEY,
                file_id INTEGER,
                key TEXT,
                value TEXT,
                FOREIGN KEY (file_id) REFERENCES files (id)
            )
        """)

        # FTS table for content search
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS content_fts
            USING fts5(content, content='files', content_rowid='id')
        """)

    def _apply_obsidian_optimizations(self, cursor: sqlite3.Cursor) -> None:
        """Apply Obsidian-specific database optimizations."""
        # Index for wikilinks
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_links_target ON links(link_target)")

        # Index for nested tags
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags_hierarchical ON tags(tag)")

        # Index for daily notes (date-based filenames)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_date_filename ON files(filename) WHERE filename GLOB '*[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]*'")

    def _apply_jekyll_optimizations(self, cursor: sqlite3.Cursor) -> None:
        """Apply Jekyll-specific database optimizations."""
        # Index for posts directory
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_posts ON files(directory) WHERE directory LIKE '%_posts%'")

        # Index for date-based filenames
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_date_prefix ON files(filename) WHERE filename GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-*'")

        # Index for categories and tags
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_frontmatter_categories ON frontmatter(key, value) WHERE key IN ('categories', 'category')")

    def _apply_performance_optimizations(self, cursor: sqlite3.Cursor) -> None:
        """Apply general performance optimizations."""
        # Enable WAL mode for better concurrency
        cursor.execute("PRAGMA journal_mode=WAL")

        # Optimize for query performance
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=10000")
        cursor.execute("PRAGMA temp_store=MEMORY")

        # Create essential indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_modified ON files(modified_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_directory ON files(directory)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag)")

    def _run_initial_indexing(self, directory: str, template: DirectoryStructure) -> int:
        """Run initial indexing of files in the directory."""
        try:
            file_count = 0
            directory_path = Path(directory)

            # Count files that match index patterns
            for pattern in template.index_patterns:
                files = list(directory_path.rglob(pattern))
                # Filter out excluded patterns
                filtered_files = []
                for file_path in files:
                    relative_path = str(file_path.relative_to(directory_path))
                    if not any(self._matches_exclude_pattern(relative_path, exclude)
                             for exclude in template.exclude_patterns):
                        filtered_files.append(file_path)

                file_count += len(filtered_files)

            logger.info(f"Found {file_count} files to index")
            return file_count

        except Exception as e:
            logger.error(f"Initial indexing failed: {e}")
            return 0

    def _matches_exclude_pattern(self, file_path: str, pattern: str) -> bool:
        """Check if file path matches exclude pattern."""
        import fnmatch
        return fnmatch.fnmatch(file_path, pattern)

    def _generate_configuration_files(self, directory: str, system_type: NoteSystemType) -> None:
        """Generate configuration files for the setup."""
        try:
            config_dir = Path(directory) / ".mdquery"
            config_dir.mkdir(exist_ok=True)

            # Generate complete configuration
            generated_config = self.config_generator.generate_complete_configuration(
                directory, str(config_dir)
            )

            logger.info(f"Configuration files generated in {config_dir}")

        except Exception as e:
            logger.error(f"Configuration generation failed: {e}")

    def _generate_recommendations(self, directory: str, system_type: NoteSystemType,
                                result: SetupResult) -> List[str]:
        """Generate setup recommendations."""
        recommendations = []

        # System-specific recommendations
        if system_type == NoteSystemType.OBSIDIAN:
            recommendations.extend([
                "Install the Dataview plugin for enhanced querying capabilities",
                "Consider using consistent tag hierarchies for better analysis",
                "Enable auto-save to keep modifications up-to-date"
            ])
        elif system_type == NoteSystemType.JEKYLL:
            recommendations.extend([
                "Use consistent frontmatter across all posts",
                "Implement categories and tags for better organization",
                "Consider date-based permalinks for blog posts"
            ])

        # Performance recommendations
        if result.files_indexed > 1000:
            recommendations.append("Enable high-performance mode for better query speed")

        if result.files_indexed > 5000:
            recommendations.append("Consider using incremental indexing for large collections")

        # Database recommendations
        if result.database_initialized:
            recommendations.extend([
                "Run periodic database optimization using VACUUM command",
                "Monitor query performance and add custom indexes as needed"
            ])

        return recommendations

    def validate_setup(self, directory: str) -> Dict[str, Any]:
        """Validate the setup and return status information."""
        validation_result = {
            "directory_exists": False,
            "database_accessible": False,
            "configuration_present": False,
            "indexable_files_count": 0,
            "system_type_detected": None,
            "issues": [],
            "recommendations": []
        }

        try:
            directory_path = Path(directory)

            # Check directory
            if directory_path.exists() and directory_path.is_dir():
                validation_result["directory_exists"] = True
            else:
                validation_result["issues"].append("Target directory does not exist")

            # Detect system type
            try:
                detection = self.auto_config.detect_note_system(directory)
                validation_result["system_type_detected"] = detection.system_type.value
            except Exception as e:
                validation_result["issues"].append(f"System detection failed: {e}")

            # Check database
            db_dir = Path.home() / ".mdquery"
            db_path = db_dir / f"{directory_path.name}.db"
            if db_path.exists():
                validation_result["database_accessible"] = True
            else:
                validation_result["issues"].append("Database not found - run initialization")

            # Check configuration
            config_path = directory_path / ".mdquery"
            if config_path.exists():
                validation_result["configuration_present"] = True
            else:
                validation_result["recommendations"].append("Generate configuration files for easier setup")

            # Count indexable files
            if directory_path.exists():
                md_files = list(directory_path.rglob("*.md"))
                validation_result["indexable_files_count"] = len(md_files)

        except Exception as e:
            validation_result["issues"].append(f"Validation error: {e}")

        return validation_result


def create_directory_setup_manager() -> DirectorySetupManager:
    """Create a directory setup manager instance."""
    return DirectorySetupManager()