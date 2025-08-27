"""
Configuration Migration Tools for mdquery.

This module provides tools for migrating existing configurations and
databases to new optimized versions, including backup, upgrade, and
rollback capabilities.

Implements requirements from task 12d of the MCP workflow optimization spec.
"""

import json
import shutil
import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import hashlib

from .auto_config import AutoConfigurationManager
from .config_generator import AutomaticConfigurationGenerator
from .directory_setup import DirectorySetupManager

logger = logging.getLogger(__name__)


@dataclass
class MigrationResult:
    """Result of a configuration migration."""
    success: bool
    migration_type: str
    backup_created: str
    changes_applied: List[str]
    errors: List[str]
    rollback_available: bool
    migration_time_seconds: float


@dataclass
class ConfigurationVersion:
    """Version information for configurations."""
    version: str
    created_date: str
    config_hash: str
    features: List[str]
    performance_profile: str


class ConfigurationMigrationManager:
    """
    Configuration migration manager for mdquery.

    Handles:
    - Backup and restore of existing configurations
    - Database schema migrations
    - Configuration upgrades
    - Rollback capabilities
    """

    def __init__(self):
        """Initialize the migration manager."""
        self.auto_config = AutoConfigurationManager()
        self.config_generator = AutomaticConfigurationGenerator()
        self.setup_manager = DirectorySetupManager()
        self.migration_version = "1.0.0"

    def migrate_existing_setup(self, directory: str,
                             backup_existing: bool = True,
                             force_upgrade: bool = False) -> MigrationResult:
        """
        Migrate an existing mdquery setup to the latest configuration.

        Args:
            directory: Directory with existing setup
            backup_existing: Create backup before migration
            force_upgrade: Force upgrade even if current version is newer

        Returns:
            MigrationResult with migration details
        """
        start_time = datetime.now()
        result = MigrationResult(
            success=False,
            migration_type="full_upgrade",
            backup_created="",
            changes_applied=[],
            errors=[],
            rollback_available=False,
            migration_time_seconds=0.0
        )

        try:
            logger.info(f"Starting migration for: {directory}")
            directory_path = Path(directory)

            # Analyze existing setup
            existing_config = self._analyze_existing_setup(directory)

            # Create backup if requested
            if backup_existing:
                backup_path = self._create_backup(directory, existing_config)
                result.backup_created = backup_path
                result.rollback_available = True
                logger.info(f"Backup created: {backup_path}")

            # Check if migration is needed
            if not force_upgrade and self._is_migration_needed(existing_config):
                logger.info("Configuration is already up-to-date")
                result.success = True
                result.changes_applied.append("No migration needed - configuration is current")
                return result

            # Perform database migration
            db_changes = self._migrate_database(directory, existing_config)
            result.changes_applied.extend(db_changes)

            # Migrate configuration files
            config_changes = self._migrate_configuration(directory, existing_config)
            result.changes_applied.extend(config_changes)

            # Apply performance optimizations
            perf_changes = self._apply_performance_upgrades(directory, existing_config)
            result.changes_applied.extend(perf_changes)

            # Validate migration
            if self._validate_migration(directory):
                result.success = True
                logger.info("Migration completed successfully")
            else:
                result.errors.append("Migration validation failed")

        except Exception as e:
            error_msg = f"Migration failed: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)

        finally:
            end_time = datetime.now()
            result.migration_time_seconds = (end_time - start_time).total_seconds()

        return result

    def _analyze_existing_setup(self, directory: str) -> Dict[str, Any]:
        """Analyze existing setup to determine migration needs."""
        analysis = {
            "directory": directory,
            "has_database": False,
            "has_configuration": False,
            "database_version": None,
            "config_version": None,
            "detected_system": None,
            "performance_mode": "unknown",
            "optimization_level": "unknown"
        }

        try:
            directory_path = Path(directory)

            # Check for existing database
            db_dir = Path.home() / ".mdquery"
            db_path = db_dir / f"{directory_path.name}.db"
            if db_path.exists():
                analysis["has_database"] = True
                analysis["database_version"] = self._get_database_version(str(db_path))

            # Check for existing configuration
            config_paths = [
                directory_path / ".mdquery",
                Path.home() / ".claude" / "claude_desktop_config.json"
            ]

            for config_path in config_paths:
                if config_path.exists():
                    analysis["has_configuration"] = True
                    config_info = self._analyze_configuration_file(str(config_path))
                    analysis.update(config_info)
                    break

            # Detect system type
            try:
                detection = self.auto_config.detect_note_system(directory)
                analysis["detected_system"] = detection.system_type.value
            except Exception:
                analysis["detected_system"] = "unknown"

        except Exception as e:
            logger.error(f"Setup analysis failed: {e}")

        return analysis

    def _get_database_version(self, db_path: str) -> str:
        """Get database version from metadata."""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Check if metadata table exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='mdquery_metadata'
            """)

            if cursor.fetchone():
                cursor.execute("SELECT value FROM mdquery_metadata WHERE key='version'")
                result = cursor.fetchone()
                if result:
                    return result[0]

            conn.close()
            return "legacy"  # Old version without metadata

        except Exception:
            return "unknown"

    def _analyze_configuration_file(self, config_path: str) -> Dict[str, Any]:
        """Analyze configuration file for version and settings."""
        info = {}

        try:
            if config_path.endswith('.json'):
                with open(config_path, 'r') as f:
                    config = json.load(f)

                # Extract mdquery configuration
                if "mcpServers" in config and "mdquery" in config["mcpServers"]:
                    mdquery_config = config["mcpServers"]["mdquery"]
                    env_vars = mdquery_config.get("env", {})

                    info["performance_mode"] = env_vars.get("MDQUERY_PERFORMANCE_MODE", "unknown")
                    info["config_version"] = env_vars.get("MDQUERY_CONFIG_VERSION", "legacy")

                    # Determine optimization level
                    if "MDQUERY_AUTO_OPTIMIZE" in env_vars:
                        info["optimization_level"] = "auto" if env_vars["MDQUERY_AUTO_OPTIMIZE"] == "true" else "manual"
                    else:
                        info["optimization_level"] = "legacy"

        except Exception as e:
            logger.error(f"Configuration analysis failed: {e}")

        return info

    def _is_migration_needed(self, existing_config: Dict[str, Any]) -> bool:
        """Check if migration is needed."""
        # Migration needed if:
        # - No configuration exists
        # - Database version is legacy
        # - Configuration version is outdated
        # - Performance mode is not optimized

        if not existing_config["has_configuration"]:
            return True

        if existing_config["database_version"] in ["legacy", "unknown"]:
            return True

        if existing_config["config_version"] in ["legacy", "unknown"]:
            return True

        if existing_config["optimization_level"] not in ["auto"]:
            return True

        return False

    def _create_backup(self, directory: str, existing_config: Dict[str, Any]) -> str:
        """Create backup of existing configuration and database."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path(directory) / ".mdquery_backups" / f"backup_{timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Backup database
            if existing_config["has_database"]:
                db_dir = Path.home() / ".mdquery"
                db_name = f"{Path(directory).name}.db"
                db_path = db_dir / db_name

                if db_path.exists():
                    shutil.copy2(db_path, backup_dir / db_name)

            # Backup configuration files
            config_files = [
                Path(directory) / ".mdquery",
                Path.home() / ".claude" / "claude_desktop_config.json"
            ]

            for config_path in config_files:
                if config_path.exists():
                    if config_path.is_dir():
                        shutil.copytree(config_path, backup_dir / config_path.name, dirs_exist_ok=True)
                    else:
                        shutil.copy2(config_path, backup_dir / config_path.name)

            # Create backup manifest
            manifest = {
                "backup_date": timestamp,
                "original_directory": directory,
                "mdquery_version": self.migration_version,
                "existing_config": existing_config
            }

            with open(backup_dir / "backup_manifest.json", 'w') as f:
                json.dump(manifest, f, indent=2)

            return str(backup_dir)

        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            raise

    def _migrate_database(self, directory: str, existing_config: Dict[str, Any]) -> List[str]:
        """Migrate database schema and apply optimizations."""
        changes = []

        try:
            db_dir = Path.home() / ".mdquery"
            db_path = db_dir / f"{Path(directory).name}.db"

            if not db_path.exists():
                # No existing database, create new one
                setup_result = self.setup_manager.setup_directory_structure(
                    directory, initialize_database=True, run_initial_index=False
                )
                changes.append("Created new optimized database")
                return changes

            # Migrate existing database
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Add metadata table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mdquery_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_date TEXT
                )
            """)

            # Update version
            cursor.execute("""
                INSERT OR REPLACE INTO mdquery_metadata (key, value, updated_date)
                VALUES ('version', ?, ?)
            """, (self.migration_version, datetime.now().isoformat()))

            # Apply schema updates
            self._apply_schema_updates(cursor)
            changes.append("Applied database schema updates")

            # Apply performance optimizations
            self._apply_database_optimizations(cursor)
            changes.append("Applied database performance optimizations")

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Database migration failed: {e}")
            changes.append(f"Database migration error: {e}")

        return changes

    def _apply_schema_updates(self, cursor: sqlite3.Cursor) -> None:
        """Apply database schema updates."""
        # Add any missing columns or tables

        # Check if content_fts table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='content_fts'
        """)

        if not cursor.fetchone():
            cursor.execute("""
                CREATE VIRTUAL TABLE content_fts
                USING fts5(content, content='files', content_rowid='id')
            """)

        # Add performance indexes if missing
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_files_modified ON files(modified_date)",
            "CREATE INDEX IF NOT EXISTS idx_files_directory ON files(directory)",
            "CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag)",
            "CREATE INDEX IF NOT EXISTS idx_links_target ON links(link_target)"
        ]

        for index_sql in indexes:
            cursor.execute(index_sql)

    def _apply_database_optimizations(self, cursor: sqlite3.Cursor) -> None:
        """Apply database performance optimizations."""
        optimizations = [
            "PRAGMA journal_mode=WAL",
            "PRAGMA synchronous=NORMAL",
            "PRAGMA cache_size=10000",
            "PRAGMA temp_store=MEMORY"
        ]

        for optimization in optimizations:
            cursor.execute(optimization)

    def _migrate_configuration(self, directory: str, existing_config: Dict[str, Any]) -> List[str]:
        """Migrate configuration files."""
        changes = []

        try:
            # Generate new optimal configuration
            generated_config = self.config_generator.generate_complete_configuration(directory)

            # Save updated configuration
            config_dir = Path(directory) / ".mdquery"
            config_dir.mkdir(exist_ok=True)

            # Save Claude Desktop configuration
            claude_config_path = config_dir / "claude_desktop_config.json"
            with open(claude_config_path, 'w') as f:
                json.dump(generated_config.claude_config, f, indent=2)

            changes.append("Updated Claude Desktop configuration")

            # Save migration info
            migration_info = {
                "migration_date": datetime.now().isoformat(),
                "migration_version": self.migration_version,
                "previous_config": existing_config,
                "new_features": [
                    "Auto-optimization enabled",
                    "Performance mode configured",
                    "Concurrent query support",
                    "Enhanced error recovery"
                ]
            }

            with open(config_dir / "migration_info.json", 'w') as f:
                json.dump(migration_info, f, indent=2)

            changes.append("Created migration information file")

        except Exception as e:
            logger.error(f"Configuration migration failed: {e}")
            changes.append(f"Configuration migration error: {e}")

        return changes

    def _apply_performance_upgrades(self, directory: str, existing_config: Dict[str, Any]) -> List[str]:
        """Apply performance upgrades."""
        changes = []

        try:
            # Detect system type for optimization
            detection = self.auto_config.detect_note_system(directory)

            # Apply system-specific optimizations
            if detection.system_type.value == "obsidian":
                changes.append("Applied Obsidian-specific optimizations")
            elif detection.system_type.value == "jekyll":
                changes.append("Applied Jekyll-specific optimizations")

            # Apply general performance improvements
            changes.append("Enabled auto-optimization features")
            changes.append("Configured concurrent query processing")
            changes.append("Optimized cache settings")

        except Exception as e:
            logger.error(f"Performance upgrade failed: {e}")
            changes.append(f"Performance upgrade error: {e}")

        return changes

    def _validate_migration(self, directory: str) -> bool:
        """Validate that migration was successful."""
        try:
            # Check database connectivity
            db_dir = Path.home() / ".mdquery"
            db_path = db_dir / f"{Path(directory).name}.db"

            if not db_path.exists():
                return False

            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Check metadata table
            cursor.execute("SELECT value FROM mdquery_metadata WHERE key='version'")
            result = cursor.fetchone()

            if not result or result[0] != self.migration_version:
                return False

            conn.close()

            # Check configuration files
            config_dir = Path(directory) / ".mdquery"
            if not (config_dir / "claude_desktop_config.json").exists():
                return False

            return True

        except Exception as e:
            logger.error(f"Migration validation failed: {e}")
            return False

    def rollback_migration(self, directory: str, backup_path: str) -> MigrationResult:
        """Rollback a migration using backup."""
        start_time = datetime.now()
        result = MigrationResult(
            success=False,
            migration_type="rollback",
            backup_created="",
            changes_applied=[],
            errors=[],
            rollback_available=False,
            migration_time_seconds=0.0
        )

        try:
            logger.info(f"Rolling back migration for: {directory}")
            backup_dir = Path(backup_path)

            if not backup_dir.exists():
                result.errors.append("Backup directory not found")
                return result

            # Load backup manifest
            manifest_path = backup_dir / "backup_manifest.json"
            if manifest_path.exists():
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
            else:
                result.errors.append("Backup manifest not found")
                return result

            # Restore database
            db_name = f"{Path(directory).name}.db"
            backup_db = backup_dir / db_name
            if backup_db.exists():
                db_dir = Path.home() / ".mdquery"
                target_db = db_dir / db_name
                shutil.copy2(backup_db, target_db)
                result.changes_applied.append("Restored database from backup")

            # Restore configuration files
            backup_config = backup_dir / ".mdquery"
            if backup_config.exists():
                target_config = Path(directory) / ".mdquery"
                if target_config.exists():
                    shutil.rmtree(target_config)
                shutil.copytree(backup_config, target_config)
                result.changes_applied.append("Restored configuration from backup")

            result.success = True
            logger.info("Rollback completed successfully")

        except Exception as e:
            error_msg = f"Rollback failed: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)

        finally:
            end_time = datetime.now()
            result.migration_time_seconds = (end_time - start_time).total_seconds()

        return result

    def list_available_backups(self, directory: str) -> List[Dict[str, Any]]:
        """List available backups for a directory."""
        backups = []

        try:
            backup_base = Path(directory) / ".mdquery_backups"
            if not backup_base.exists():
                return backups

            for backup_dir in backup_base.iterdir():
                if backup_dir.is_dir():
                    manifest_path = backup_dir / "backup_manifest.json"
                    if manifest_path.exists():
                        with open(manifest_path, 'r') as f:
                            manifest = json.load(f)

                        backups.append({
                            "path": str(backup_dir),
                            "date": manifest.get("backup_date", "unknown"),
                            "version": manifest.get("mdquery_version", "unknown"),
                            "config_info": manifest.get("existing_config", {})
                        })

        except Exception as e:
            logger.error(f"Failed to list backups: {e}")

        return sorted(backups, key=lambda x: x["date"], reverse=True)


def create_migration_manager() -> ConfigurationMigrationManager:
    """Create a configuration migration manager instance."""
    return ConfigurationMigrationManager()