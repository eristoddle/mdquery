"""
Error recovery and resilience system for mdquery.

This module implements comprehensive error recovery strategies to handle
various failure scenarios gracefully, including database corruption,
indexing failures, and configuration issues. It provides automatic
recovery mechanisms and helpful error messages to guide users to solutions.
"""

import logging
import shutil
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

from .exceptions import (
    MdqueryError, DatabaseError, DatabaseConnectionError, DatabaseCorruptionError,
    IndexingError, ConfigurationError, FileAccessError, DirectoryNotFoundError,
    ParsingError, PerformanceError, ResourceError
)
from .database import DatabaseManager
from .config import SimplifiedConfig, create_helpful_error_message
from .logging_config import log_error

logger = logging.getLogger(__name__)


class RecoveryStrategy(Enum):
    """Available recovery strategies for different error types."""
    RETRY = "retry"
    REBUILD = "rebuild"
    INCREMENTAL = "incremental"
    FALLBACK = "fallback"
    MANUAL = "manual"


class RecoveryResult(Enum):
    """Results of recovery attempts."""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    REQUIRES_MANUAL_INTERVENTION = "requires_manual_intervention"


@dataclass
class RecoveryAction:
    """Represents a recovery action to be taken."""
    strategy: RecoveryStrategy
    description: str
    automatic: bool = True
    estimated_time: Optional[str] = None
    user_guidance: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/reporting."""
        return {
            "strategy": self.strategy.value,
            "description": self.description,
            "automatic": self.automatic,
            "estimated_time": self.estimated_time,
            "user_guidance": self.user_guidance
        }


@dataclass
class RecoveryReport:
    """Report of recovery attempt results."""
    result: RecoveryResult
    actions_taken: List[RecoveryAction]
    error_resolved: bool
    time_taken: float
    additional_info: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/reporting."""
        return {
            "result": self.result.value,
            "actions_taken": [action.to_dict() for action in self.actions_taken],
            "error_resolved": self.error_resolved,
            "time_taken": self.time_taken,
            "additional_info": self.additional_info
        }


class ErrorRecoveryManager:
    """
    Comprehensive error recovery manager with specific strategies for different error types.

    This class implements requirement 4.1-4.4 for error recovery and resilience,
    providing automatic recovery mechanisms and helpful user guidance.
    """

    def __init__(self, config: Optional[SimplifiedConfig] = None):
        """
        Initialize error recovery manager.

        Args:
            config: Optional configuration for recovery operations
        """
        self.config = config
        self.recovery_history: List[RecoveryReport] = []

        # Recovery attempt limits
        self.max_retry_attempts = 3
        self.retry_delay_base = 1.0  # Base delay in seconds
        self.max_retry_delay = 30.0  # Maximum delay in seconds

        # Database backup settings
        self.max_backups = 5
        self.backup_retention_days = 30

    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> RecoveryReport:
        """
        Handle an error with appropriate recovery strategy.

        Args:
            error: Exception that occurred
            context: Optional context information about the error

        Returns:
            RecoveryReport with details of recovery attempt
        """
        start_time = time.time()
        context = context or {}

        logger.info(f"Starting error recovery for {type(error).__name__}: {error}")

        try:
            # Determine recovery strategy based on error type
            recovery_actions = self._determine_recovery_strategy(error, context)

            if not recovery_actions:
                return RecoveryReport(
                    result=RecoveryResult.FAILED,
                    actions_taken=[],
                    error_resolved=False,
                    time_taken=time.time() - start_time,
                    additional_info="No recovery strategy available for this error type"
                )

            # Execute recovery actions
            result = self._execute_recovery_actions(recovery_actions, error, context)

            # Record recovery attempt
            recovery_report = RecoveryReport(
                result=result,
                actions_taken=recovery_actions,
                error_resolved=(result == RecoveryResult.SUCCESS),
                time_taken=time.time() - start_time
            )

            self.recovery_history.append(recovery_report)

            logger.info(f"Error recovery completed: {result.value}")
            return recovery_report

        except Exception as recovery_error:
            logger.error(f"Error during recovery process: {recovery_error}")

            recovery_report = RecoveryReport(
                result=RecoveryResult.FAILED,
                actions_taken=[],
                error_resolved=False,
                time_taken=time.time() - start_time,
                additional_info=f"Recovery process failed: {recovery_error}"
            )

            self.recovery_history.append(recovery_report)
            return recovery_report

    def _determine_recovery_strategy(self, error: Exception, context: Dict[str, Any]) -> List[RecoveryAction]:
        """
        Determine appropriate recovery strategy based on error type and context.

        Args:
            error: Exception that occurred
            context: Context information about the error

        Returns:
            List of recovery actions to attempt
        """
        actions = []

        if isinstance(error, DatabaseCorruptionError):
            actions.extend(self._get_database_corruption_recovery(error, context))
        elif isinstance(error, DatabaseConnectionError):
            actions.extend(self._get_database_connection_recovery(error, context))
        elif isinstance(error, IndexingError):
            actions.extend(self._get_indexing_error_recovery(error, context))
        elif isinstance(error, ConfigurationError):
            actions.extend(self._get_configuration_error_recovery(error, context))
        elif isinstance(error, FileAccessError):
            actions.extend(self._get_file_access_error_recovery(error, context))
        elif isinstance(error, DirectoryNotFoundError):
            actions.extend(self._get_directory_error_recovery(error, context))
        elif isinstance(error, ParsingError):
            actions.extend(self._get_parsing_error_recovery(error, context))
        elif isinstance(error, PerformanceError):
            actions.extend(self._get_performance_error_recovery(error, context))
        elif isinstance(error, ResourceError):
            actions.extend(self._get_resource_error_recovery(error, context))
        else:
            # Generic recovery for unknown errors
            actions.extend(self._get_generic_error_recovery(error, context))

        return actions

    def _get_database_corruption_recovery(self, error: DatabaseCorruptionError, context: Dict[str, Any]) -> List[RecoveryAction]:
        """Get recovery actions for database corruption errors."""
        actions = []

        # First, try to backup the corrupted database
        actions.append(RecoveryAction(
            strategy=RecoveryStrategy.FALLBACK,
            description="Backup corrupted database for forensic analysis",
            automatic=True,
            estimated_time="5-10 seconds",
            user_guidance="The corrupted database will be backed up before attempting recovery"
        ))

        # Attempt database rebuild
        actions.append(RecoveryAction(
            strategy=RecoveryStrategy.REBUILD,
            description="Rebuild database from source markdown files",
            automatic=True,
            estimated_time="1-5 minutes depending on collection size",
            user_guidance="All markdown files will be re-indexed to rebuild the database"
        ))

        return actions

    def _get_database_connection_recovery(self, error: DatabaseConnectionError, context: Dict[str, Any]) -> List[RecoveryAction]:
        """Get recovery actions for database connection errors."""
        actions = []

        # Retry connection with exponential backoff
        actions.append(RecoveryAction(
            strategy=RecoveryStrategy.RETRY,
            description="Retry database connection with exponential backoff",
            automatic=True,
            estimated_time="10-30 seconds",
            user_guidance="Attempting to reconnect to database"
        ))

        # Check if database file is locked
        actions.append(RecoveryAction(
            strategy=RecoveryStrategy.FALLBACK,
            description="Check for database locks and wait for release",
            automatic=True,
            estimated_time="30-60 seconds",
            user_guidance="Waiting for database lock to be released"
        ))

        # If connection still fails, try rebuilding
        actions.append(RecoveryAction(
            strategy=RecoveryStrategy.REBUILD,
            description="Rebuild database if connection cannot be established",
            automatic=True,
            estimated_time="1-5 minutes",
            user_guidance="Creating new database if current one is inaccessible"
        ))

        return actions

    def _get_indexing_error_recovery(self, error: IndexingError, context: Dict[str, Any]) -> List[RecoveryAction]:
        """Get recovery actions for indexing errors."""
        actions = []

        # Try incremental indexing first
        actions.append(RecoveryAction(
            strategy=RecoveryStrategy.INCREMENTAL,
            description="Attempt incremental indexing of modified files only",
            automatic=True,
            estimated_time="30 seconds - 2 minutes",
            user_guidance="Trying to index only files that have changed"
        ))

        # If incremental fails, try full rebuild
        actions.append(RecoveryAction(
            strategy=RecoveryStrategy.REBUILD,
            description="Perform full re-indexing of all files",
            automatic=True,
            estimated_time="2-10 minutes depending on collection size",
            user_guidance="Re-indexing all markdown files from scratch"
        ))

        return actions

    def _get_configuration_error_recovery(self, error: ConfigurationError, context: Dict[str, Any]) -> List[RecoveryAction]:
        """Get recovery actions for configuration errors."""
        actions = []

        # Provide helpful guidance for configuration issues
        actions.append(RecoveryAction(
            strategy=RecoveryStrategy.MANUAL,
            description="Provide configuration guidance to user",
            automatic=False,
            user_guidance=create_helpful_error_message(error, context.get('notes_dir'))
        ))

        return actions

    def _get_file_access_error_recovery(self, error: FileAccessError, context: Dict[str, Any]) -> List[RecoveryAction]:
        """Get recovery actions for file access errors."""
        actions = []

        # Retry with delay (might be temporary lock)
        actions.append(RecoveryAction(
            strategy=RecoveryStrategy.RETRY,
            description="Retry file access after brief delay",
            automatic=True,
            estimated_time="5-15 seconds",
            user_guidance="Retrying file access (might be temporarily locked)"
        ))

        # Provide guidance for permission issues
        actions.append(RecoveryAction(
            strategy=RecoveryStrategy.MANUAL,
            description="Provide file access guidance",
            automatic=False,
            user_guidance=create_helpful_error_message(error)
        ))

        return actions

    def _get_directory_error_recovery(self, error: DirectoryNotFoundError, context: Dict[str, Any]) -> List[RecoveryAction]:
        """Get recovery actions for directory errors."""
        actions = []

        # Provide helpful guidance for directory issues
        actions.append(RecoveryAction(
            strategy=RecoveryStrategy.MANUAL,
            description="Provide directory setup guidance",
            automatic=False,
            user_guidance=create_helpful_error_message(error)
        ))

        return actions

    def _get_parsing_error_recovery(self, error: ParsingError, context: Dict[str, Any]) -> List[RecoveryAction]:
        """Get recovery actions for parsing errors."""
        actions = []

        # Skip problematic file and continue
        actions.append(RecoveryAction(
            strategy=RecoveryStrategy.FALLBACK,
            description="Skip problematic file and continue indexing",
            automatic=True,
            estimated_time="Immediate",
            user_guidance=f"Skipping file with parsing issues: {getattr(error, 'file_path', 'unknown')}"
        ))

        return actions

    def _get_performance_error_recovery(self, error: PerformanceError, context: Dict[str, Any]) -> List[RecoveryAction]:
        """Get recovery actions for performance errors."""
        actions = []

        # Switch to incremental processing
        actions.append(RecoveryAction(
            strategy=RecoveryStrategy.INCREMENTAL,
            description="Switch to incremental processing to improve performance",
            automatic=True,
            estimated_time="Varies",
            user_guidance="Using incremental processing to handle large collections"
        ))

        return actions

    def _get_resource_error_recovery(self, error: ResourceError, context: Dict[str, Any]) -> List[RecoveryAction]:
        """Get recovery actions for resource errors."""
        actions = []

        # Wait and retry
        actions.append(RecoveryAction(
            strategy=RecoveryStrategy.RETRY,
            description="Wait for resources to become available",
            automatic=True,
            estimated_time="30-60 seconds",
            user_guidance="Waiting for system resources to become available"
        ))

        return actions

    def _get_generic_error_recovery(self, error: Exception, context: Dict[str, Any]) -> List[RecoveryAction]:
        """Get recovery actions for unknown/generic errors."""
        actions = []

        # Basic retry strategy
        actions.append(RecoveryAction(
            strategy=RecoveryStrategy.RETRY,
            description="Retry operation after brief delay",
            automatic=True,
            estimated_time="5-10 seconds",
            user_guidance="Retrying operation"
        ))

        return actions

    def _execute_recovery_actions(self, actions: List[RecoveryAction], original_error: Exception, context: Dict[str, Any]) -> RecoveryResult:
        """
        Execute recovery actions in sequence.

        Args:
            actions: List of recovery actions to execute
            original_error: Original error that triggered recovery
            context: Context information

        Returns:
            RecoveryResult indicating success/failure
        """
        for action in actions:
            if not action.automatic:
                # Manual actions require user intervention
                logger.info(f"Manual intervention required: {action.description}")
                if action.user_guidance:
                    logger.info(f"User guidance: {action.user_guidance}")
                return RecoveryResult.REQUIRES_MANUAL_INTERVENTION

            try:
                logger.info(f"Executing recovery action: {action.description}")

                success = self._execute_single_recovery_action(action, original_error, context)

                if success:
                    logger.info(f"Recovery action succeeded: {action.description}")
                    return RecoveryResult.SUCCESS
                else:
                    logger.warning(f"Recovery action failed: {action.description}")
                    continue

            except Exception as e:
                logger.error(f"Error executing recovery action {action.description}: {e}")
                continue

        # If we get here, all automatic actions failed
        return RecoveryResult.FAILED

    def _execute_single_recovery_action(self, action: RecoveryAction, original_error: Exception, context: Dict[str, Any]) -> bool:
        """
        Execute a single recovery action.

        Args:
            action: Recovery action to execute
            original_error: Original error that triggered recovery
            context: Context information

        Returns:
            True if action succeeded, False otherwise
        """
        try:
            if action.strategy == RecoveryStrategy.RETRY:
                return self._execute_retry_action(action, original_error, context)
            elif action.strategy == RecoveryStrategy.REBUILD:
                return self._execute_rebuild_action(action, original_error, context)
            elif action.strategy == RecoveryStrategy.INCREMENTAL:
                return self._execute_incremental_action(action, original_error, context)
            elif action.strategy == RecoveryStrategy.FALLBACK:
                return self._execute_fallback_action(action, original_error, context)
            else:
                logger.warning(f"Unknown recovery strategy: {action.strategy}")
                return False

        except Exception as e:
            logger.error(f"Error executing recovery action: {e}")
            return False

    def _execute_retry_action(self, action: RecoveryAction, original_error: Exception, context: Dict[str, Any]) -> bool:
        """Execute retry recovery action with exponential backoff."""
        max_attempts = self.max_retry_attempts
        delay = self.retry_delay_base

        for attempt in range(max_attempts):
            if attempt > 0:
                logger.info(f"Retry attempt {attempt + 1}/{max_attempts} after {delay:.1f}s delay")
                time.sleep(delay)
                delay = min(delay * 2, self.max_retry_delay)

            try:
                # The specific retry logic depends on the original error type
                if isinstance(original_error, DatabaseConnectionError):
                    return self._retry_database_connection(context)
                elif isinstance(original_error, FileAccessError):
                    return self._retry_file_access(original_error, context)
                elif isinstance(original_error, ResourceError):
                    return self._retry_resource_operation(original_error, context)
                else:
                    # Generic retry - just wait and return True to indicate we should try the original operation
                    return True

            except Exception as e:
                logger.warning(f"Retry attempt {attempt + 1} failed: {e}")
                continue

        return False

    def _execute_rebuild_action(self, action: RecoveryAction, original_error: Exception, context: Dict[str, Any]) -> bool:
        """Execute database rebuild recovery action."""
        try:
            if not self.config:
                logger.error("Cannot rebuild database: no configuration available")
                return False

            # Backup existing database if it exists
            db_path = self.config.config.db_path
            if db_path.exists():
                backup_path = self._create_database_backup(db_path)
                logger.info(f"Created database backup: {backup_path}")

            # Remove corrupted database
            if db_path.exists():
                db_path.unlink()
                logger.info(f"Removed corrupted database: {db_path}")

            # Create new database and re-index
            return self._rebuild_database_from_source()

        except Exception as e:
            logger.error(f"Database rebuild failed: {e}")
            return False

    def _execute_incremental_action(self, action: RecoveryAction, original_error: Exception, context: Dict[str, Any]) -> bool:
        """Execute incremental indexing recovery action."""
        try:
            if not self.config:
                logger.error("Cannot perform incremental indexing: no configuration available")
                return False

            # Import here to avoid circular imports
            from .indexer import Indexer
            from .database import DatabaseManager

            # Create database manager and indexer
            db_manager = DatabaseManager(self.config.config.db_path)
            db_manager.initialize_database()

            indexer = Indexer(db_manager)

            # Perform incremental indexing
            stats = indexer.incremental_index_directory(self.config.config.notes_dir)

            logger.info(f"Incremental indexing completed: {stats}")

            # Consider it successful if we processed some files without too many errors
            error_rate = stats.get('errors', 0) / max(stats.get('files_processed', 1), 1)
            return error_rate < 0.5  # Less than 50% error rate

        except Exception as e:
            logger.error(f"Incremental indexing failed: {e}")
            return False

    def _execute_fallback_action(self, action: RecoveryAction, original_error: Exception, context: Dict[str, Any]) -> bool:
        """Execute fallback recovery action."""
        try:
            if isinstance(original_error, DatabaseCorruptionError):
                # Backup corrupted database
                if self.config and self.config.config.db_path.exists():
                    backup_path = self._create_database_backup(self.config.config.db_path)
                    logger.info(f"Backed up corrupted database to: {backup_path}")
                    return True
            elif isinstance(original_error, ParsingError):
                # Skip problematic file - this is handled by the indexer
                logger.info(f"Skipping problematic file: {getattr(original_error, 'file_path', 'unknown')}")
                return True
            elif isinstance(original_error, DatabaseConnectionError):
                # Wait for database lock to be released
                return self._wait_for_database_unlock(context)

            return False

        except Exception as e:
            logger.error(f"Fallback action failed: {e}")
            return False

    def _retry_database_connection(self, context: Dict[str, Any]) -> bool:
        """Retry database connection."""
        try:
            if not self.config:
                return False

            # Import here to avoid circular imports
            from .database import DatabaseManager

            db_manager = DatabaseManager(self.config.config.db_path)

            # Test connection
            with db_manager.get_connection() as conn:
                conn.execute("SELECT 1").fetchone()

            logger.info("Database connection retry successful")
            return True

        except Exception as e:
            logger.warning(f"Database connection retry failed: {e}")
            return False

    def _retry_file_access(self, error: FileAccessError, context: Dict[str, Any]) -> bool:
        """Retry file access operation."""
        try:
            file_path = error.file_path
            if not file_path or not file_path.exists():
                return False

            # Try to access the file
            if file_path.is_file():
                # Try to read a small portion
                with open(file_path, 'r', encoding='utf-8') as f:
                    f.read(100)
            elif file_path.is_dir():
                # Try to list directory
                list(file_path.iterdir())

            logger.info(f"File access retry successful: {file_path}")
            return True

        except Exception as e:
            logger.warning(f"File access retry failed: {e}")
            return False

    def _retry_resource_operation(self, error: ResourceError, context: Dict[str, Any]) -> bool:
        """Retry operation after resource constraint."""
        try:
            # Check if resources are now available
            import psutil

            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Check if we have sufficient resources now
            if memory.available > 100 * 1024 * 1024 and disk.free > 50 * 1024 * 1024:
                logger.info("System resources are now available")
                return True
            else:
                logger.warning(f"Resources still constrained: memory={memory.available/1024/1024:.1f}MB, disk={disk.free/1024/1024:.1f}MB")
                return False

        except Exception as e:
            logger.warning(f"Resource check failed: {e}")
            return False

    def _wait_for_database_unlock(self, context: Dict[str, Any]) -> bool:
        """Wait for database lock to be released."""
        try:
            if not self.config:
                return False

            db_path = self.config.config.db_path
            max_wait_time = 60  # Maximum wait time in seconds
            check_interval = 2  # Check every 2 seconds

            start_time = time.time()

            while time.time() - start_time < max_wait_time:
                try:
                    # Try to open database with a short timeout
                    conn = sqlite3.connect(str(db_path), timeout=1.0)
                    conn.execute("SELECT 1").fetchone()
                    conn.close()

                    logger.info("Database lock released")
                    return True

                except sqlite3.OperationalError as e:
                    if "database is locked" in str(e).lower():
                        logger.debug(f"Database still locked, waiting... ({time.time() - start_time:.1f}s)")
                        time.sleep(check_interval)
                        continue
                    else:
                        # Different error, not a lock issue
                        return False

            logger.warning(f"Database remained locked after {max_wait_time}s")
            return False

        except Exception as e:
            logger.error(f"Error waiting for database unlock: {e}")
            return False

    def _create_database_backup(self, db_path: Path) -> Path:
        """
        Create a backup of the database file.

        Args:
            db_path: Path to database file to backup

        Returns:
            Path to backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = db_path.parent / "backups"
        backup_dir.mkdir(exist_ok=True)

        backup_path = backup_dir / f"{db_path.stem}_backup_{timestamp}{db_path.suffix}"

        # Copy database file
        shutil.copy2(db_path, backup_path)

        # Clean up old backups
        self._cleanup_old_backups(backup_dir)

        return backup_path

    def _cleanup_old_backups(self, backup_dir: Path) -> None:
        """Clean up old backup files."""
        try:
            backup_files = list(backup_dir.glob("*_backup_*"))

            # Sort by modification time (newest first)
            backup_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

            # Remove excess backups
            if len(backup_files) > self.max_backups:
                for old_backup in backup_files[self.max_backups:]:
                    old_backup.unlink()
                    logger.debug(f"Removed old backup: {old_backup}")

            # Remove backups older than retention period
            cutoff_time = datetime.now() - timedelta(days=self.backup_retention_days)
            cutoff_timestamp = cutoff_time.timestamp()

            for backup_file in backup_files:
                if backup_file.stat().st_mtime < cutoff_timestamp:
                    backup_file.unlink()
                    logger.debug(f"Removed expired backup: {backup_file}")

        except Exception as e:
            logger.warning(f"Error cleaning up old backups: {e}")

    def _rebuild_database_from_source(self) -> bool:
        """
        Rebuild database from source markdown files.

        Returns:
            True if rebuild was successful
        """
        try:
            if not self.config:
                logger.error("Cannot rebuild database: no configuration available")
                return False

            # Import here to avoid circular imports
            from .indexer import Indexer
            from .database import DatabaseManager

            # Create new database
            db_manager = DatabaseManager(self.config.config.db_path)
            db_manager.initialize_database()

            # Create indexer and rebuild index
            indexer = Indexer(db_manager)
            stats = indexer.index_directory(self.config.config.notes_dir, recursive=True)

            logger.info(f"Database rebuild completed: {stats}")

            # Consider rebuild successful if we indexed some files
            return stats.get('files_processed', 0) > 0

        except Exception as e:
            logger.error(f"Database rebuild failed: {e}")
            return False

    def get_recovery_history(self) -> List[Dict[str, Any]]:
        """
        Get history of recovery attempts.

        Returns:
            List of recovery reports as dictionaries
        """
        return [report.to_dict() for report in self.recovery_history]

    def clear_recovery_history(self) -> None:
        """Clear recovery history."""
        self.recovery_history.clear()
        logger.info("Recovery history cleared")

    def get_recovery_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about recovery attempts.

        Returns:
            Dictionary with recovery statistics
        """
        if not self.recovery_history:
            return {
                "total_attempts": 0,
                "success_rate": 0.0,
                "average_time": 0.0,
                "most_common_strategies": []
            }

        total_attempts = len(self.recovery_history)
        successful_attempts = sum(1 for report in self.recovery_history if report.error_resolved)
        success_rate = successful_attempts / total_attempts if total_attempts > 0 else 0.0

        total_time = sum(report.time_taken for report in self.recovery_history)
        average_time = total_time / total_attempts if total_attempts > 0 else 0.0

        # Count strategy usage
        strategy_counts = {}
        for report in self.recovery_history:
            for action in report.actions_taken:
                strategy = action.strategy.value
                strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1

        # Sort strategies by usage
        most_common_strategies = sorted(
            strategy_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return {
            "total_attempts": total_attempts,
            "successful_attempts": successful_attempts,
            "success_rate": success_rate,
            "average_time": average_time,
            "most_common_strategies": most_common_strategies
        }


def create_error_recovery_manager(config: Optional[SimplifiedConfig] = None) -> ErrorRecoveryManager:
    """
    Create an error recovery manager instance.

    Args:
        config: Optional configuration for recovery operations

    Returns:
        ErrorRecoveryManager instance
    """
    return ErrorRecoveryManager(config)


def handle_error_with_recovery(error: Exception, config: Optional[SimplifiedConfig] = None, context: Optional[Dict[str, Any]] = None) -> RecoveryReport:
    """
    Convenience function to handle an error with automatic recovery.

    Args:
        error: Exception that occurred
        config: Optional configuration for recovery operations
        context: Optional context information about the error

    Returns:
        RecoveryReport with details of recovery attempt
    """
    recovery_manager = create_error_recovery_manager(config)
    return recovery_manager.handle_error(error, context)