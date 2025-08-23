"""
Simplified configuration system for mdquery MCP server.

This module provides a path-first configuration approach where users only need
to specify their notes directory, with intelligent defaults for database and
cache locations. The system automatically handles directory structure creation
and provides comprehensive error handling with helpful messages.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum

from .exceptions import (
    ConfigurationError,
    DirectoryNotFoundError,
    FileAccessError,
    MdqueryError
)

logger = logging.getLogger(__name__)


class NoteSystemType(Enum):
    """Supported note system types for optimized configuration."""
    GENERIC = "generic"
    OBSIDIAN = "obsidian"
    JOPLIN = "joplin"
    LOGSEQ = "logseq"
    FOAM = "foam"


@dataclass
class MCPServerConfig:
    """Configuration data class for MCP server settings."""
    notes_dir: Path
    db_path: Path
    cache_dir: Path
    auto_index: bool = True
    note_system_type: NoteSystemType = NoteSystemType.GENERIC

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary format."""
        return {
            "notes_dir": str(self.notes_dir),
            "db_path": str(self.db_path),
            "cache_dir": str(self.cache_dir),
            "auto_index": self.auto_index,
            "note_system_type": self.note_system_type.value
        }


class SimplifiedConfig:
    """
    Simplified configuration manager with path-first approach.

    This class implements the core requirement of needing only a notes directory
    path, with intelligent defaults for database and cache locations within
    the notes directory structure.
    """

    def __init__(
        self,
        notes_dir: Union[str, Path],
        db_path: Optional[Union[str, Path]] = None,
        cache_dir: Optional[Union[str, Path]] = None,
        auto_index: bool = True
    ):
        """
        Initialize simplified configuration.

        Args:
            notes_dir: Path to notes directory (required)
            db_path: Optional explicit database path (defaults to notes_dir/.mdquery/mdquery.db)
            cache_dir: Optional explicit cache directory (defaults to notes_dir/.mdquery/cache)
            auto_index: Whether to automatically index on startup

        Raises:
            ConfigurationError: If configuration is invalid
            DirectoryNotFoundError: If notes directory doesn't exist
            FileAccessError: If directories cannot be created or accessed
        """
        self._raw_notes_dir = notes_dir
        self._raw_db_path = db_path
        self._raw_cache_dir = cache_dir
        self._auto_index = auto_index

        # Initialize configuration
        self._config: Optional[MCPServerConfig] = None
        self._validate_and_setup()

    def _validate_and_setup(self) -> None:
        """
        Validate configuration and set up directory structure.

        This method implements requirements 1.1-1.4 for path validation,
        default path generation, and directory creation.
        """
        try:
            # Validate and resolve notes directory
            notes_dir = self._resolve_and_validate_notes_dir()

            # Generate default paths if not specified
            db_path = self._resolve_db_path(notes_dir)
            cache_dir = self._resolve_cache_dir(notes_dir)

            # Detect note system type
            note_system_type = self._detect_note_system_type(notes_dir)

            # Create configuration object
            self._config = MCPServerConfig(
                notes_dir=notes_dir,
                db_path=db_path,
                cache_dir=cache_dir,
                auto_index=self._auto_index,
                note_system_type=note_system_type
            )

            # Create necessary directories
            self._create_directory_structure()

            # Validate final configuration
            self._validate_final_config()

            logger.info(f"Configuration initialized successfully: {self._config.to_dict()}")

        except Exception as e:
            if isinstance(e, MdqueryError):
                raise
            else:
                raise ConfigurationError(
                    f"Unexpected error during configuration setup: {e}",
                    context={"notes_dir": str(self._raw_notes_dir)}
                )

    def _resolve_and_validate_notes_dir(self) -> Path:
        """
        Resolve and validate the notes directory path.

        Returns:
            Resolved and validated notes directory path

        Raises:
            ConfigurationError: If notes_dir is not provided or invalid
            DirectoryNotFoundError: If notes directory doesn't exist
            FileAccessError: If notes directory is not accessible
        """
        if not self._raw_notes_dir:
            raise ConfigurationError(
                "Notes directory path is required. Please provide the path to your notes directory.",
                context={
                    "suggestion": "Specify the path to your Obsidian vault, Joplin notebooks, or markdown files directory",
                    "example": "/Users/username/Documents/ObsidianVault"
                }
            )

        try:
            # Resolve path (handle ~, relative paths, etc.)
            notes_path = Path(self._raw_notes_dir).expanduser().resolve()

            # Check if directory exists
            if not notes_path.exists():
                raise DirectoryNotFoundError(
                    f"Notes directory does not exist: {notes_path}",
                    file_path=notes_path,
                    context={
                        "suggestion": "Please check the path and ensure the directory exists",
                        "provided_path": str(self._raw_notes_dir),
                        "resolved_path": str(notes_path)
                    }
                )

            # Check if it's actually a directory
            if not notes_path.is_dir():
                raise ConfigurationError(
                    f"Notes path is not a directory: {notes_path}",
                    context={
                        "suggestion": "Please provide a path to a directory, not a file",
                        "provided_path": str(self._raw_notes_dir),
                        "resolved_path": str(notes_path)
                    }
                )

            # Check if directory is readable
            if not self._check_directory_access(notes_path, check_read=True):
                raise FileAccessError(
                    f"Cannot read from notes directory: {notes_path}",
                    file_path=notes_path,
                    context={
                        "suggestion": "Please check directory permissions and ensure you have read access",
                        "required_permissions": "read"
                    }
                )

            return notes_path

        except (OSError, PermissionError) as e:
            raise FileAccessError(
                f"Cannot access notes directory: {e}",
                file_path=Path(str(self._raw_notes_dir)) if self._raw_notes_dir else None,
                context={
                    "original_error": str(e),
                    "suggestion": "Please check directory permissions and path validity"
                }
            )

    def _resolve_db_path(self, notes_dir: Path) -> Path:
        """
        Resolve database path with intelligent defaults.

        Args:
            notes_dir: Validated notes directory

        Returns:
            Resolved database path
        """
        if self._raw_db_path:
            # Use explicit path if provided
            db_path = Path(self._raw_db_path).expanduser().resolve()
        else:
            # Default to .mdquery/mdquery.db within notes directory
            db_path = notes_dir / ".mdquery" / "mdquery.db"

        logger.debug(f"Database path resolved to: {db_path}")
        return db_path

    def _resolve_cache_dir(self, notes_dir: Path) -> Path:
        """
        Resolve cache directory with intelligent defaults.

        Args:
            notes_dir: Validated notes directory

        Returns:
            Resolved cache directory path
        """
        if self._raw_cache_dir:
            # Use explicit path if provided
            cache_dir = Path(self._raw_cache_dir).expanduser().resolve()
        else:
            # Default to .mdquery/cache within notes directory
            cache_dir = notes_dir / ".mdquery" / "cache"

        logger.debug(f"Cache directory resolved to: {cache_dir}")
        return cache_dir

    def _detect_note_system_type(self, notes_dir: Path) -> NoteSystemType:
        """
        Detect the type of note system based on directory structure and files.

        Args:
            notes_dir: Notes directory to analyze

        Returns:
            Detected note system type
        """
        try:
            # Check for Obsidian vault indicators
            if (notes_dir / ".obsidian").exists():
                logger.debug("Detected Obsidian vault")
                return NoteSystemType.OBSIDIAN

            # Check for Joplin indicators
            if any(notes_dir.glob("*.jex")) or (notes_dir / "joplin").exists():
                logger.debug("Detected Joplin notebooks")
                return NoteSystemType.JOPLIN

            # Check for Logseq indicators
            if (notes_dir / "logseq").exists() or (notes_dir / ".logseq").exists():
                logger.debug("Detected Logseq graph")
                return NoteSystemType.LOGSEQ

            # Check for Foam indicators
            if (notes_dir / ".foam").exists() or (notes_dir / ".vscode" / "foam.json").exists():
                logger.debug("Detected Foam workspace")
                return NoteSystemType.FOAM

            # Default to generic
            logger.debug("Using generic note system type")
            return NoteSystemType.GENERIC

        except Exception as e:
            logger.warning(f"Error detecting note system type: {e}, defaulting to generic")
            return NoteSystemType.GENERIC

    def _create_directory_structure(self) -> None:
        """
        Create necessary directory structure.

        This method implements requirement 1.4 for automatic directory creation.

        Raises:
            FileAccessError: If directories cannot be created
        """
        if not self._config:
            raise ConfigurationError("Configuration not initialized")

        directories_to_create = [
            (self._config.db_path.parent, "database directory"),
            (self._config.cache_dir, "cache directory")
        ]

        for dir_path, description in directories_to_create:
            try:
                if not dir_path.exists():
                    dir_path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created {description}: {dir_path}")

                # Verify directory is writable
                if not self._check_directory_access(dir_path, check_write=True):
                    raise FileAccessError(
                        f"Cannot write to {description}: {dir_path}",
                        file_path=dir_path,
                        context={
                            "suggestion": "Please check directory permissions and ensure you have write access",
                            "required_permissions": "read, write"
                        }
                    )

            except (OSError, PermissionError) as e:
                raise FileAccessError(
                    f"Cannot create {description} at {dir_path}: {e}",
                    file_path=dir_path,
                    context={
                        "original_error": str(e),
                        "suggestion": "Please check parent directory permissions or specify a different location"
                    }
                )

    def _validate_final_config(self) -> None:
        """
        Validate the final configuration for consistency and accessibility.

        Raises:
            ConfigurationError: If final configuration is invalid
        """
        if not self._config:
            raise ConfigurationError("Configuration not initialized")

        # Ensure all paths are absolute
        if not self._config.notes_dir.is_absolute():
            raise ConfigurationError(
                f"Notes directory path must be absolute: {self._config.notes_dir}",
                context={"suggestion": "Use absolute paths for reliable configuration"}
            )

        if not self._config.db_path.is_absolute():
            raise ConfigurationError(
                f"Database path must be absolute: {self._config.db_path}",
                context={"suggestion": "Use absolute paths for reliable configuration"}
            )

        if not self._config.cache_dir.is_absolute():
            raise ConfigurationError(
                f"Cache directory path must be absolute: {self._config.cache_dir}",
                context={"suggestion": "Use absolute paths for reliable configuration"}
            )

        # Validate that database parent directory exists and is writable
        db_parent = self._config.db_path.parent
        if not db_parent.exists() or not self._check_directory_access(db_parent, check_write=True):
            raise ConfigurationError(
                f"Database directory is not accessible: {db_parent}",
                context={
                    "suggestion": "Ensure the database directory exists and is writable",
                    "db_path": str(self._config.db_path)
                }
            )

        # Validate that cache directory exists and is writable
        if not self._config.cache_dir.exists() or not self._check_directory_access(self._config.cache_dir, check_write=True):
            raise ConfigurationError(
                f"Cache directory is not accessible: {self._config.cache_dir}",
                context={
                    "suggestion": "Ensure the cache directory exists and is writable"
                }
            )

    def _check_directory_access(self, path: Path, check_read: bool = False, check_write: bool = False) -> bool:
        """
        Check directory access permissions.

        Args:
            path: Directory path to check
            check_read: Whether to check read permissions
            check_write: Whether to check write permissions

        Returns:
            True if all requested permissions are available
        """
        try:
            if check_read:
                # Try to list directory contents
                list(path.iterdir())

            if check_write:
                # Try to create a temporary file
                test_file = path / ".mdquery_access_test"
                try:
                    test_file.touch()
                    test_file.unlink()
                except (OSError, PermissionError):
                    return False

            return True

        except (OSError, PermissionError):
            return False

    @property
    def config(self) -> MCPServerConfig:
        """
        Get the validated configuration.

        Returns:
            MCPServerConfig instance

        Raises:
            ConfigurationError: If configuration is not initialized
        """
        if not self._config:
            raise ConfigurationError("Configuration not initialized")
        return self._config

    def get_mcp_config(self) -> Dict[str, Any]:
        """
        Generate MCP server configuration dictionary.

        Returns:
            Dictionary suitable for MCP server initialization
        """
        return self.config.to_dict()

    def save_config(self, config_path: Optional[Path] = None) -> None:
        """
        Save configuration to JSON file.

        Args:
            config_path: Optional path to save config file
                        (defaults to notes_dir/.mdquery/config.json)
        """
        if not self._config:
            raise ConfigurationError("Configuration not initialized")

        if config_path is None:
            config_path = self._config.notes_dir / ".mdquery" / "config.json"

        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)

            config_data = {
                "version": "1.0",
                "created_at": str(Path(__file__).stat().st_mtime),
                "config": self._config.to_dict()
            }

            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Configuration saved to: {config_path}")

        except (OSError, PermissionError) as e:
            raise FileAccessError(
                f"Cannot save configuration to {config_path}: {e}",
                file_path=config_path,
                context={
                    "original_error": str(e),
                    "suggestion": "Check directory permissions or specify a different location"
                }
            )

    @classmethod
    def load_config(cls, config_path: Path) -> 'SimplifiedConfig':
        """
        Load configuration from JSON file.

        Args:
            config_path: Path to configuration file

        Returns:
            SimplifiedConfig instance

        Raises:
            ConfigurationError: If configuration file is invalid
            FileAccessError: If configuration file cannot be read
        """
        try:
            if not config_path.exists():
                raise FileAccessError(
                    f"Configuration file does not exist: {config_path}",
                    file_path=config_path
                )

            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            if "config" not in config_data:
                raise ConfigurationError(
                    f"Invalid configuration file format: {config_path}",
                    context={"suggestion": "Configuration file must contain 'config' section"}
                )

            config = config_data["config"]

            return cls(
                notes_dir=config["notes_dir"],
                db_path=config.get("db_path"),
                cache_dir=config.get("cache_dir"),
                auto_index=config.get("auto_index", True)
            )

        except json.JSONDecodeError as e:
            raise ConfigurationError(
                f"Invalid JSON in configuration file: {config_path}",
                context={
                    "json_error": str(e),
                    "suggestion": "Check configuration file syntax"
                }
            )
        except (OSError, PermissionError) as e:
            raise FileAccessError(
                f"Cannot read configuration file: {config_path}",
                file_path=config_path,
                context={
                    "original_error": str(e),
                    "suggestion": "Check file permissions"
                }
            )

    def __str__(self) -> str:
        """String representation of configuration."""
        if not self._config:
            return "SimplifiedConfig(uninitialized)"

        return (
            f"SimplifiedConfig("
            f"notes_dir={self._config.notes_dir}, "
            f"db_path={self._config.db_path}, "
            f"cache_dir={self._config.cache_dir}, "
            f"note_system={self._config.note_system_type.value}"
            f")"
        )

    def __repr__(self) -> str:
        """Detailed representation of configuration."""
        return self.__str__()


def create_helpful_error_message(error: Exception, notes_dir: Optional[str] = None) -> str:
    """
    Create helpful error messages for configuration issues.

    This function implements requirement 4.5 for helpful error messages
    that guide users to solutions.

    Args:
        error: Exception that occurred
        notes_dir: Notes directory that was being configured

    Returns:
        Helpful error message with guidance
    """
    if isinstance(error, DirectoryNotFoundError):
        return (
            f"❌ Notes directory not found: {error.file_path}\n\n"
            f"💡 Solutions:\n"
            f"   • Check that the path exists and is spelled correctly\n"
            f"   • Use an absolute path (e.g., /Users/username/Documents/Notes)\n"
            f"   • Ensure you have permission to access the directory\n\n"
            f"📝 Example valid paths:\n"
            f"   • /Users/username/Documents/ObsidianVault\n"
            f"   • ~/Documents/Notes\n"
            f"   • /home/user/notes"
        )

    elif isinstance(error, FileAccessError):
        return (
            f"❌ Cannot access directory: {error.file_path}\n\n"
            f"💡 Solutions:\n"
            f"   • Check directory permissions (should be readable and writable)\n"
            f"   • Ensure you own the directory or have appropriate access\n"
            f"   • Try running with appropriate permissions\n\n"
            f"🔧 Quick fixes:\n"
            f"   • chmod 755 {error.file_path}  (on Unix systems)\n"
            f"   • Check if the directory is on a read-only filesystem"
        )

    elif isinstance(error, ConfigurationError):
        context = getattr(error, 'context', {})
        suggestion = context.get('suggestion', 'Check your configuration settings')

        return (
            f"❌ Configuration error: {error.message}\n\n"
            f"💡 Suggestion: {suggestion}\n\n"
            f"📖 For more help, see the configuration documentation"
        )

    else:
        return (
            f"❌ Unexpected error: {error}\n\n"
            f"💡 This might be a bug. Please check:\n"
            f"   • Your notes directory path is correct\n"
            f"   • You have proper permissions\n"
            f"   • The directory contains markdown files\n\n"
            f"🐛 If the problem persists, please report this issue"
        )