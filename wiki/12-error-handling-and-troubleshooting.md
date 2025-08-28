# Error Handling and Troubleshooting

## Exceptions Reference

mdquery provides a comprehensive exception hierarchy for different types of errors that can occur during operation. Understanding these exceptions helps in debugging and implementing proper error handling.

### Base Exception Classes

#### MDQueryError

The base exception class for all mdquery-specific errors.

```python
class MDQueryError(Exception):
    """Base exception for all mdquery errors"""
    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.error_code = error_code
        self.timestamp = datetime.now()
```

**Common Usage:**
```python
try:
    result = query_engine.execute_query(sql)
except MDQueryError as e:
    logger.error(f"MDQuery error [{e.error_code}]: {e}")
```

### Configuration Exceptions

#### ConfigurationError

Raised when configuration-related issues occur.

```python
class ConfigurationError(MDQueryError):
    """Configuration-related errors"""
    pass
```

**Common Scenarios:**
- Invalid configuration file format
- Missing required configuration values
- Invalid path specifications
- Conflicting configuration options

**Example:**
```python
from mdquery.exceptions import ConfigurationError

try:
    config = SimplifiedConfig(notes_dir="/nonexistent/path")
except ConfigurationError as e:
    print(f"Configuration error: {e}")
    # Handle: Create directory, use default, or prompt user
```

### Indexing Exceptions

#### IndexingError

Raised during file indexing operations.

```python
class IndexingError(MDQueryError):
    """Indexing operation errors"""
    def __init__(self, message: str, file_path: Optional[str] = None):
        super().__init__(message)
        self.file_path = file_path
```

**Common Scenarios:**
- File permission errors
- Corrupted markdown files
- Unsupported file formats
- Database write failures
- Memory exhaustion during large indexing operations

**Example:**
```python
from mdquery.exceptions import IndexingError

try:
    result = indexer.index_directory("/path/to/notes")
except IndexingError as e:
    logger.error(f"Indexing failed for {e.file_path}: {e}")
    # Handle: Skip file, retry, or abort operation
```

#### ParsingError

Raised when markdown parsing fails.

```python
class ParsingError(IndexingError):
    """Markdown parsing errors"""
    def __init__(self, message: str, file_path: str, line_number: Optional[int] = None):
        super().__init__(message, file_path)
        self.line_number = line_number
```

**Common Scenarios:**
- Malformed frontmatter (invalid YAML/TOML)
- Encoding issues
- Extremely large files
- Circular reference detection

**Example:**
```python
from mdquery.exceptions import ParsingError

try:
    metadata = parser.parse_frontmatter(content)
except ParsingError as e:
    logger.warning(f"Parsing failed in {e.file_path}:{e.line_number}: {e}")
    # Handle: Use default metadata, skip frontmatter, or flag for review
```

### Query Exceptions

#### QueryValidationError

Raised when SQL query validation fails.

```python
class QueryValidationError(MDQueryError):
    """Query validation errors"""
    def __init__(self, message: str, query: str, error_details: Optional[Dict] = None):
        super().__init__(message)
        self.query = query
        self.error_details = error_details or {}
```

**Common Scenarios:**
- Invalid SQL syntax
- Forbidden operations (INSERT, DELETE, etc.)
- Security violations
- Table/column name errors
- Multiple statement attempts

**Example:**
```python
from mdquery.exceptions import QueryValidationError

try:
    result = query_engine.execute_query("DROP TABLE files")
except QueryValidationError as e:
    print(f"Query validation failed: {e}")
    print(f"Problematic query: {e.query}")
    # Handle: Show error to user, suggest corrections
```

#### QueryExecutionError

Raised when query execution fails after validation.

```python
class QueryExecutionError(MDQueryError):
    """Query execution errors"""
    def __init__(self, message: str, query: str, sql_error: Optional[str] = None):
        super().__init__(message)
        self.query = query
        self.sql_error = sql_error
```

**Common Scenarios:**
- Database connection failures
- Query timeout
- Resource exhaustion
- Lock conflicts
- Corrupted database

**Example:**
```python
from mdquery.exceptions import QueryExecutionError

try:
    result = query_engine.execute_query(complex_query, timeout=60)
except QueryExecutionError as e:
    logger.error(f"Query execution failed: {e}")
    logger.error(f"SQL error: {e.sql_error}")
    # Handle: Retry with simpler query, increase timeout, or show error
```

### Database Exceptions

#### DatabaseError

Raised for database-related operations.

```python
class DatabaseError(MDQueryError):
    """Database operation errors"""
    def __init__(self, message: str, operation: str, db_path: Optional[str] = None):
        super().__init__(message)
        self.operation = operation
        self.db_path = db_path
```

**Common Scenarios:**
- Database file corruption
- Insufficient disk space
- Permission errors
- Schema migration failures
- Connection pool exhaustion

**Example:**
```python
from mdquery.exceptions import DatabaseError

try:
    db_manager.connect()
except DatabaseError as e:
    logger.error(f"Database {e.operation} failed for {e.db_path}: {e}")
    # Handle: Recreate database, check permissions, free disk space
```

### Cache Exceptions

#### CacheError

Raised for cache-related operations.

```python
class CacheError(MDQueryError):
    """Cache operation errors"""
    def __init__(self, message: str, cache_operation: str):
        super().__init__(message)
        self.cache_operation = cache_operation
```

**Common Scenarios:**
- Cache directory not writable
- Cache corruption
- Disk space exhaustion
- Cache eviction failures

**Example:**
```python
from mdquery.exceptions import CacheError

try:
    cached_result = cache_manager.get(cache_key)
except CacheError as e:
    logger.warning(f"Cache {e.cache_operation} failed: {e}")
    # Handle: Disable cache, clear cache, or continue without caching
```

## Error Recovery Mechanisms

### Automatic Recovery Strategies

mdquery implements several automatic recovery mechanisms to handle common error scenarios gracefully.

#### Indexing Recovery

```python
class IndexingRecoveryManager:
    def __init__(self, indexer, max_retries=3):
        self.indexer = indexer
        self.max_retries = max_retries
        self.failed_files = []

    def index_with_recovery(self, directory_path):
        """Index with automatic error recovery"""
        try:
            return self.indexer.index_directory(directory_path)
        except IndexingError as e:
            return self._handle_indexing_error(e, directory_path)

    def _handle_indexing_error(self, error, directory_path):
        """Handle indexing errors with recovery strategies"""
        if "permission" in str(error).lower():
            # Skip files with permission issues
            self._skip_permission_errors(directory_path)
        elif "memory" in str(error).lower():
            # Reduce batch size and retry
            self._retry_with_smaller_batches(directory_path)
        elif "encoding" in str(error).lower():
            # Retry with different encodings
            self._retry_with_encoding_detection(directory_path)
        else:
            # Generic retry with exponential backoff
            self._retry_with_backoff(directory_path)
```

#### Query Recovery

```python
class QueryRecoveryManager:
    def __init__(self, query_engine):
        self.query_engine = query_engine
        self.fallback_strategies = [
            self._add_limit_clause,
            self._simplify_joins,
            self._split_complex_query,
            self._use_basic_select
        ]

    def execute_with_recovery(self, sql):
        """Execute query with automatic recovery"""
        for attempt, strategy in enumerate(self.fallback_strategies):
            try:
                modified_sql = strategy(sql) if attempt > 0 else sql
                return self.query_engine.execute_query(modified_sql)
            except QueryExecutionError as e:
                if attempt == len(self.fallback_strategies) - 1:
                    raise e
                logger.warning(f"Query attempt {attempt + 1} failed, trying fallback")
```

#### Database Recovery

```python
class DatabaseRecoveryManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def recover_database(self, corruption_error):
        """Attempt to recover from database corruption"""
        recovery_steps = [
            self._run_integrity_check,
            self._attempt_vacuum,
            self._restore_from_backup,
            self._rebuild_from_source
        ]

        for step_name, step_func in recovery_steps:
            try:
                logger.info(f"Attempting recovery step: {step_name}")
                if step_func():
                    logger.info(f"Recovery successful using: {step_name}")
                    return True
            except Exception as e:
                logger.warning(f"Recovery step {step_name} failed: {e}")

        return False
```

### Manual Recovery Procedures

#### Database Corruption Recovery

```bash
# 1. Check database integrity
sqlite3 mdquery.db "PRAGMA integrity_check;"

# 2. If corruption detected, attempt vacuum
sqlite3 mdquery.db "VACUUM;"

# 3. If vacuum fails, dump and restore
sqlite3 mdquery.db ".dump" > backup.sql
rm mdquery.db
sqlite3 mdquery.db < backup.sql

# 4. If all else fails, rebuild index
mdquery index --force /path/to/notes
```

#### Cache Recovery

```python
def recover_cache():
    """Recover from cache corruption"""
    try:
        # Clear corrupted cache
        cache_manager.clear_cache()

        # Recreate cache directory structure
        cache_manager.initialize_cache_structure()

        # Verify cache is working
        cache_manager.test_cache_functionality()

        logger.info("Cache recovery successful")
        return True
    except Exception as e:
        logger.error(f"Cache recovery failed: {e}")
        return False
```

## Troubleshooting Guide

### Common Issues and Solutions

#### Issue: "Database locked" Error

**Symptoms:**
```
DatabaseError: database is locked
```

**Causes:**
- Another mdquery process is running
- SQLite connection not properly closed
- File system issues

**Solutions:**
```bash
# 1. Check for running processes
ps aux | grep mdquery

# 2. Kill hanging processes
killall python  # or specific PID

# 3. Remove lock files
rm /path/to/.mdquery/*.db-wal
rm /path/to/.mdquery/*.db-shm

# 4. Restart with WAL mode
export MDQUERY_DB_WAL_MODE=1
mdquery index
```

#### Issue: Out of Memory During Indexing

**Symptoms:**
```
MemoryError: Unable to allocate memory
IndexingError: Memory exhausted during processing
```

**Solutions:**
```python
# 1. Reduce batch size
config = {
    "index": {
        "batch_size": 10,  # Reduce from default 100
        "parallel_processing": False,
        "max_workers": 1
    }
}

# 2. Enable streaming processing
indexer.enable_streaming_mode(chunk_size=5)

# 3. Exclude large files
config["index"]["max_file_size_mb"] = 10
```

#### Issue: Query Timeout

**Symptoms:**
```
QueryExecutionError: Query timeout after 30 seconds
```

**Solutions:**
```python
# 1. Increase timeout
query_engine.set_query_timeout(120)  # 2 minutes

# 2. Optimize query
optimized_sql = optimizer.optimize_query(original_sql)

# 3. Add LIMIT clause
sql_with_limit = f"{original_sql} LIMIT 1000"

# 4. Use pagination
for offset in range(0, total_rows, 1000):
    page_sql = f"{original_sql} LIMIT 1000 OFFSET {offset}"
    page_result = query_engine.execute_query(page_sql)
```

#### Issue: File Permission Errors

**Symptoms:**
```
IndexingError: Permission denied: /path/to/file.md
```

**Solutions:**
```bash
# 1. Check file permissions
ls -la /path/to/notes/

# 2. Fix permissions
chmod -R 644 /path/to/notes/*.md
chmod -R 755 /path/to/notes/directories/

# 3. Change ownership if needed
chown -R $USER:$USER /path/to/notes/

# 4. Run with appropriate permissions
sudo -u owner mdquery index /path/to/notes
```

#### Issue: Encoding Problems

**Symptoms:**
```
ParsingError: 'utf-8' codec can't decode byte
UnicodeDecodeError: invalid start byte
```

**Solutions:**
```python
# 1. Enable automatic encoding detection
config = {
    "parsing": {
        "auto_detect_encoding": True,
        "fallback_encodings": ["utf-8", "latin1", "cp1252"]
    }
}

# 2. Fix encoding manually
import chardet

def fix_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        detected = chardet.detect(raw_data)
        encoding = detected['encoding']

    with open(file_path, 'r', encoding=encoding) as f:
        content = f.read()

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
```

### Logging and Diagnostics

#### Enable Debug Logging

```python
import logging

# Configure comprehensive logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mdquery_debug.log'),
        logging.StreamHandler()
    ]
)

# Enable specific module logging
logging.getLogger('mdquery.indexer').setLevel(logging.DEBUG)
logging.getLogger('mdquery.query').setLevel(logging.DEBUG)
logging.getLogger('mdquery.database').setLevel(logging.DEBUG)
```

#### Diagnostic Commands

```bash
# System information
mdquery --version
python --version
sqlite3 --version

# Database diagnostics
mdquery schema --stats --verbose

# Index diagnostics
mdquery index --dry-run /path/to/notes

# Query diagnostics
mdquery query "EXPLAIN QUERY PLAN SELECT * FROM files" --format table
```

#### Performance Diagnostics

```python
from mdquery.diagnostics import PerformanceDiagnostics

# Run comprehensive diagnostics
diagnostics = PerformanceDiagnostics()
report = diagnostics.run_full_diagnostic()

print(f"Database size: {report.db_size_mb:.1f} MB")
print(f"Index count: {report.file_count}")
print(f"Average query time: {report.avg_query_time:.3f}s")
print(f"Cache hit rate: {report.cache_hit_rate:.2%}")
print(f"Memory usage: {report.memory_usage_mb:.1f} MB")

# Identify performance bottlenecks
bottlenecks = diagnostics.identify_bottlenecks(report)
for bottleneck in bottlenecks:
    print(f"Bottleneck: {bottleneck.name}")
    print(f"Impact: {bottleneck.impact}")
    print(f"Recommendation: {bottleneck.recommendation}")
```

### Health Checks

#### System Health Check

```python
def run_health_check():
    """Comprehensive system health check"""
    health_status = {
        "database": check_database_health(),
        "cache": check_cache_health(),
        "indexing": check_indexing_health(),
        "query_engine": check_query_engine_health(),
        "file_system": check_file_system_health()
    }

    overall_health = all(health_status.values())

    return {
        "overall_healthy": overall_health,
        "components": health_status,
        "recommendations": generate_health_recommendations(health_status)
    }

def check_database_health():
    """Check database connectivity and integrity"""
    try:
        db_manager.connect()
        integrity_result = db_manager.execute_query("PRAGMA integrity_check;")
        return integrity_result.fetchone()[0] == "ok"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
```

#### Automated Monitoring

```python
class HealthMonitor:
    def __init__(self, check_interval=300):  # 5 minutes
        self.check_interval = check_interval
        self.health_history = []

    def start_monitoring(self):
        """Start continuous health monitoring"""
        while True:
            health_status = run_health_check()
            self.health_history.append({
                "timestamp": datetime.now(),
                "status": health_status
            })

            if not health_status["overall_healthy"]:
                self.handle_health_issue(health_status)

            time.sleep(self.check_interval)

    def handle_health_issue(self, health_status):
        """Handle detected health issues"""
        for component, healthy in health_status["components"].items():
            if not healthy:
                logger.warning(f"Health issue detected in {component}")
                self.attempt_automatic_recovery(component)
```

This comprehensive error handling and troubleshooting guide provides the tools and knowledge needed to diagnose and resolve issues that may arise when using mdquery.