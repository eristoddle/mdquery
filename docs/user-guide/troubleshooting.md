# mdquery Troubleshooting Guide

A comprehensive guide to diagnosing and fixing common mdquery setup and configuration issues.

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Installation Issues](#installation-issues)
3. [MCP Configuration Problems](#mcp-configuration-problems)
4. [Database and Indexing Issues](#database-and-indexing-issues)
5. [Performance Problems](#performance-problems)
6. [AI Assistant Connection Issues](#ai-assistant-connection-issues)
7. [Platform-Specific Issues](#platform-specific-issues)
8. [Advanced Troubleshooting](#advanced-troubleshooting)
9. [Getting Help](#getting-help)

## Quick Diagnostics

### 🔍 Step 1: Basic Health Check

Run these commands to quickly identify the problem area:

```bash
# Check Python version (must be 3.8+)
python --version

# Check if mdquery is installed
python -c "import mdquery; print('mdquery version:', mdquery.__version__)"

# Test MCP server startup
python -m mdquery.mcp_server --help

# Check if your notes directory exists
ls -la "/path/to/your/notes"

# Check database permissions
ls -la ~/.mdquery/
```

### 🚨 Common Error Patterns

**Error Pattern → Section to Check**

- `ModuleNotFoundError: No module named 'mdquery'` → [Installation Issues](#installation-issues)
- `FileNotFoundError: [Errno 2] No such file or directory` → [Database and Indexing Issues](#database-and-indexing-issues)
- `Permission denied` → [Platform-Specific Issues](#platform-specific-issues)
- `database is locked` → [Database and Indexing Issues](#database-and-indexing-issues)
- `Connection refused` / `Server not responding` → [AI Assistant Connection Issues](#ai-assistant-connection-issues)
- Slow responses or timeouts → [Performance Problems](#performance-problems)

### 🎯 Quick Fixes (Try These First)

1. **Restart Claude Desktop** completely (Quit → Reopen)
2. **Check file paths** for typos and spaces
3. **Use absolute paths** instead of relative paths
4. **Verify Python environment** is correct
5. **Clear database** if corrupted: `rm -rf ~/.mdquery/`

## Installation Issues

### Problem: `ModuleNotFoundError: No module named 'mdquery'`

**Symptoms:**
```
ModuleNotFoundError: No module named 'mdquery'
ImportError: cannot import name 'mdquery'
```

**Cause:** mdquery is not installed or not in the correct Python environment.

**Solutions:**

#### Solution 1: Install mdquery
```bash
# Install from PyPI
pip install mdquery

# Or install from source
git clone https://github.com/your-org/mdquery.git
cd mdquery
pip install -e .
```

#### Solution 2: Check Python Environment
```bash
# Check which Python you're using
which python
python --version

# Check which pip you're using
which pip

# List installed packages
pip list | grep mdquery
```

#### Solution 3: Virtual Environment Issues
```bash
# If using virtual environment, activate it first
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Then install mdquery
pip install mdquery
```

#### Solution 4: Multiple Python Versions
```bash
# Try python3 instead of python
python3 -c "import mdquery; print('Success!')"

# Update Claude config to use python3
# In claude_desktop_config.json:
{
  "mcpServers": {
    "mdquery": {
      "command": "python3",  // Changed from "python"
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/path/to/notes"
      }
    }
  }
}
```

### Problem: Package Installation Fails

**Symptoms:**
```
ERROR: Could not install packages due to an EnvironmentError
Permission denied
```

**Solutions:**

#### Solution 1: Use --user flag
```bash
pip install --user mdquery
```

#### Solution 2: Check permissions
```bash
# On macOS/Linux
sudo pip install mdquery

# Better: Use user installation
pip install --user mdquery
```

#### Solution 3: Use virtual environment
```bash
python -m venv mdquery_env
source mdquery_env/bin/activate
pip install mdquery
```

## MCP Configuration Problems

### Problem: Claude Can't Find mdquery Tools

**Symptoms:**
- No mdquery tools appear in Claude
- "Server not responding" errors
- Claude acts like mdquery doesn't exist

**Step-by-Step Diagnosis:**

#### Step 1: Check Configuration File Location
```bash
# macOS
ls -la ~/.claude/claude_desktop_config.json

# Windows
dir "%APPDATA%\Claude\claude_desktop_config.json"

# Linux
ls -la ~/.config/claude/claude_desktop_config.json
```

#### Step 2: Verify Configuration Syntax
```bash
# Check JSON syntax
python -m json.tool ~/.claude/claude_desktop_config.json
```

**Common JSON Errors:**
- Missing commas
- Trailing commas
- Unescaped backslashes in Windows paths
- Missing quotes around values

#### Step 3: Test Server Manually
```bash
# Test server startup
python -m mdquery.mcp_server

# Should show something like:
# MCP Server starting...
# Listening on stdio...
```

#### Step 4: Check Environment Variables
```bash
# Test the exact command Claude will run
MDQUERY_NOTES_DIR="/path/to/notes" python -m mdquery.mcp_server
```

### Problem: Configuration File Format Issues

**Common Format Errors:**

#### Error 1: Windows Path Escaping
```json
// ❌ Wrong - backslashes need escaping
{
  "mcpServers": {
    "mdquery": {
      "env": {
        "MDQUERY_NOTES_DIR": "C:\Users\Name\Documents\Notes"
      }
    }
  }
}

// ✅ Correct - escaped backslashes
{
  "mcpServers": {
    "mdquery": {
      "env": {
        "MDQUERY_NOTES_DIR": "C:\\Users\\Name\\Documents\\Notes"
      }
    }
  }
}

// ✅ Better - forward slashes work on Windows too
{
  "mcpServers": {
    "mdquery": {
      "env": {
        "MDQUERY_NOTES_DIR": "C:/Users/Name/Documents/Notes"
      }
    }
  }
}
```

#### Error 2: Missing Required Fields
```json
// ❌ Wrong - missing command and args
{
  "mcpServers": {
    "mdquery": {
      "env": {
        "MDQUERY_NOTES_DIR": "/path/to/notes"
      }
    }
  }
}

// ✅ Correct - all required fields
{
  "mcpServers": {
    "mdquery": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/path/to/notes"
      }
    }
  }
}
```

### Problem: Environment Variables Not Working

**Symptoms:**
- Server starts but can't find notes
- "No notes directory specified" errors

**Solutions:**

#### Solution 1: Use Absolute Paths
```json
{
  "mcpServers": {
    "mdquery": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/Users/username/Documents/Obsidian Vault"
      }
    }
  }
}
```

#### Solution 2: Check Path Exists
```bash
# Verify the path exists
ls -la "/Users/username/Documents/Obsidian Vault"

# Check for .obsidian folder (for Obsidian vaults)
ls -la "/Users/username/Documents/Obsidian Vault/.obsidian"
```

#### Solution 3: Test Environment Variables
```bash
# Test manually
export MDQUERY_NOTES_DIR="/path/to/notes"
python -c "import os; print('Notes dir:', os.getenv('MDQUERY_NOTES_DIR'))"
```

## Database and Indexing Issues

### Problem: Database Permission Errors

**Symptoms:**
```
sqlite3.OperationalError: attempt to write a readonly database
PermissionError: [Errno 13] Permission denied: '/Users/username/.mdquery/mdquery.db'
```

**Solutions:**

#### Solution 1: Check Directory Permissions
```bash
# Check .mdquery directory
ls -la ~/.mdquery/

# If directory doesn't exist, create it
mkdir -p ~/.mdquery/
chmod 755 ~/.mdquery/
```

#### Solution 2: Fix Database Permissions
```bash
# Remove corrupted database
rm ~/.mdquery/mdquery.db

# Recreate with correct permissions
touch ~/.mdquery/mdquery.db
chmod 644 ~/.mdquery/mdquery.db
```

#### Solution 3: Change Database Location
```json
{
  "mcpServers": {
    "mdquery": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/path/to/notes",
        "MDQUERY_DB_PATH": "/tmp/mdquery.db"
      }
    }
  }
}
```

### Problem: Database Corruption

**Symptoms:**
```
sqlite3.DatabaseError: database disk image is malformed
sqlite3.OperationalError: database is locked
```

**Automatic Recovery:**
mdquery includes automatic corruption recovery, but you can manually fix it:

#### Solution 1: Let mdquery Auto-Recover
```
# Ask Claude: "My database seems corrupted. Can you help?"
# mdquery will detect corruption and automatically rebuild
```

#### Solution 2: Manual Database Reset
```bash
# Backup current database (optional)
cp ~/.mdquery/mdquery.db ~/.mdquery/mdquery.db.backup

# Remove corrupted database
rm ~/.mdquery/mdquery.db

# Restart Claude Desktop - database will be recreated
```

#### Solution 3: Integrity Check
```bash
# Check database integrity
sqlite3 ~/.mdquery/mdquery.db "PRAGMA integrity_check;"

# If corrupted, dump and recreate
sqlite3 ~/.mdquery/mdquery.db ".dump" > backup.sql
rm ~/.mdquery/mdquery.db
sqlite3 ~/.mdquery/mdquery.db < backup.sql
```

### Problem: Notes Not Being Indexed

**Symptoms:**
- "No notes found" when notes directory has files
- Empty query results
- Claude says vault is empty

**Diagnostic Steps:**

#### Step 1: Check File Extensions
```bash
# Check what files are in your notes directory
find "/path/to/notes" -name "*.md" | head -10
find "/path/to/notes" -name "*.markdown" | head -10

# Count markdown files
find "/path/to/notes" -name "*.md" | wc -l
```

#### Step 2: Check File Permissions
```bash
# Check if files are readable
ls -la "/path/to/notes"/*.md | head -5

# Check directory permissions
ls -ld "/path/to/notes"
```

#### Step 3: Manual Indexing Test
```
# Ask Claude: "Can you manually index my notes directory at /exact/path/to/notes"
```

#### Step 4: Check for Hidden Files
```bash
# Some note systems use hidden directories
ls -la "/path/to/notes"

# Check for .obsidian, .git, etc.
ls -la "/path/to/notes"/.obsidian
```

### Problem: Indexing Performance Issues

**Symptoms:**
- Indexing takes very long (>10 minutes)
- Timeout errors during indexing
- High memory usage

**Solutions:**

#### Solution 1: Enable Performance Mode
```json
{
  "mcpServers": {
    "mdquery": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/path/to/notes",
        "MDQUERY_PERFORMANCE_MODE": "high",
        "MDQUERY_LAZY_LOADING": "true"
      }
    }
  }
}
```

#### Solution 2: Incremental Indexing
```
# Ask Claude: "Can you perform incremental indexing of my notes?"
```

#### Solution 3: Exclude Large Directories
```bash
# Identify large directories
du -sh "/path/to/notes"/*

# Move large non-text files
mkdir "/path/to/notes/attachments"
mv "/path/to/notes"/*.pdf "/path/to/notes/attachments/"
```

## Performance Problems

### Problem: Slow Query Responses

**Symptoms:**
- Queries take >5 seconds
- Timeouts
- Claude seems unresponsive

**Diagnostic Commands:**
```
# Ask Claude these diagnostic questions:
"Show me performance statistics for my mdquery server"
"What's the current cache hit rate and average query time?"
"Can you optimize my query performance?"
```

**Solutions:**

#### Solution 1: Enable Auto-Optimization
```json
{
  "mcpServers": {
    "mdquery": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/path/to/notes",
        "MDQUERY_AUTO_OPTIMIZE": "true",
        "MDQUERY_PERFORMANCE_MODE": "high"
      }
    }
  }
}
```

#### Solution 2: Increase Cache Settings
```json
{
  "mcpServers": {
    "mdquery": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/path/to/notes",
        "MDQUERY_CACHE_TTL": "240",
        "MDQUERY_CONCURRENT_QUERIES": "5"
      }
    }
  }
}
```

#### Solution 3: Database Optimization
```bash
# Optimize database
sqlite3 ~/.mdquery/mdquery.db "VACUUM;"
sqlite3 ~/.mdquery/mdquery.db "ANALYZE;"
```

### Problem: High Memory Usage

**Symptoms:**
- System becomes slow when using mdquery
- Out of memory errors
- Large RAM consumption

**Solutions:**

#### Solution 1: Enable Lazy Loading
```json
{
  "mcpServers": {
    "mdquery": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/path/to/notes",
        "MDQUERY_LAZY_LOADING": "true",
        "MDQUERY_PERFORMANCE_MODE": "low"
      }
    }
  }
}
```

#### Solution 2: Limit Concurrent Queries
```json
{
  "mcpServers": {
    "mdquery": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/path/to/notes",
        "MDQUERY_CONCURRENT_QUERIES": "1",
        "MDQUERY_MAX_RESULTS": "50"
      }
    }
  }
}
```

## AI Assistant Connection Issues

### Problem: Claude Desktop Can't Connect

**Symptoms:**
- "Server not responding" in Claude
- mdquery tools don't appear
- Connection timeout errors

**Diagnostic Steps:**

#### Step 1: Check Server Process
```bash
# Check if Python process is running
ps aux | grep mdquery

# Check if port is in use
lsof -i :8000  # or whatever port MCP uses
```

#### Step 2: Test Server Directly
```bash
# Start server manually with debug output
MDQUERY_LOG_LEVEL=DEBUG python -m mdquery.mcp_server
```

#### Step 3: Check Claude Desktop Logs
```bash
# macOS Claude Desktop logs
tail -f ~/Library/Logs/Claude/claude_desktop.log

# Windows (check Event Viewer or application logs)
# Linux (check system logs)
journalctl -f | grep claude
```

**Solutions:**

#### Solution 1: Restart Everything
```bash
# 1. Quit Claude Desktop completely
# 2. Kill any mdquery processes
pkill -f mdquery

# 3. Clear any locks
rm /tmp/mdquery_*

# 4. Restart Claude Desktop
```

#### Solution 2: Use Full Python Path
```json
{
  "mcpServers": {
    "mdquery": {
      "command": "/usr/bin/python3",  // Full path
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/path/to/notes"
      }
    }
  }
}
```

#### Solution 3: Debug Configuration
```json
{
  "mcpServers": {
    "mdquery": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/path/to/notes",
        "MDQUERY_LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

### Problem: Multiple AI Assistants Conflict

**Symptoms:**
- Database locked errors when using multiple assistants
- Inconsistent results
- Performance degradation

**Solutions:**

#### Solution 1: Separate Databases
```json
{
  "mcpServers": {
    "mdquery-claude": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/path/to/notes",
        "MDQUERY_DB_PATH": "/Users/username/.mdquery/claude.db"
      }
    },
    "mdquery-gpt": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/path/to/notes",
        "MDQUERY_DB_PATH": "/Users/username/.mdquery/gpt.db"
      }
    }
  }
}
```

#### Solution 2: Enable Concurrent Access
```json
{
  "mcpServers": {
    "mdquery": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/path/to/notes",
        "MDQUERY_CONCURRENT_QUERIES": "5",
        "MDQUERY_AUTO_OPTIMIZE": "true"
      }
    }
  }
}
```

## Platform-Specific Issues

### macOS Issues

#### Problem: Python Path Issues
```bash
# Check which Python is being used
which python
which python3

# Use specific Python version
/usr/bin/python3 -c "import mdquery"
```

#### Problem: Permission Issues with iCloud
```bash
# For iCloud Obsidian vaults
ls -la "/Users/username/Library/Mobile Documents/iCloud~md~obsidian/Documents"

# Fix permissions if needed
chmod -R u+rw "/Users/username/Library/Mobile Documents/iCloud~md~obsidian/Documents/VaultName"
```

### Windows Issues

#### Problem: Path Length Limits
```json
{
  "mcpServers": {
    "mdquery": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "C:/Users/Name/Documents/Notes",
        "MDQUERY_DB_PATH": "C:/Users/Name/.mdquery/notes.db"
      }
    }
  }
}
```

#### Problem: PowerShell vs Command Prompt
```batch
REM Test in Command Prompt
python -c "import mdquery; print('OK')"

REM Test in PowerShell
python -c "import mdquery; print('OK')"
```

### Linux Issues

#### Problem: Package Manager Conflicts
```bash
# Use pip3 instead of pip
pip3 install mdquery

# Or use package manager
sudo apt install python3-pip
pip3 install --user mdquery
```

#### Problem: Permission Issues
```bash
# Check file permissions
ls -la ~/.mdquery/

# Fix permissions
chmod 755 ~/.mdquery/
chmod 644 ~/.mdquery/mdquery.db
```

## Advanced Troubleshooting

### Enable Debug Logging

Add debug logging to get detailed information:

```json
{
  "mcpServers": {
    "mdquery": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/path/to/notes",
        "MDQUERY_LOG_LEVEL": "DEBUG",
        "MDQUERY_ENABLE_METRICS": "true"
      }
    }
  }
}
```

### Database Debugging

```bash
# Check database schema
sqlite3 ~/.mdquery/mdquery.db ".schema"

# Check table contents
sqlite3 ~/.mdquery/mdquery.db "SELECT COUNT(*) FROM files;"

# Check for corruption
sqlite3 ~/.mdquery/mdquery.db "PRAGMA integrity_check;"

# Analyze performance
sqlite3 ~/.mdquery/mdquery.db "PRAGMA table_info(files);"
```

### Network Debugging

```bash
# Check network connectivity (for cloud storage)
ping drive.google.com
ping onedrive.live.com

# Check DNS resolution
nslookup your-cloud-storage.com

# Test file access
ls -la "/path/to/cloud/storage/notes"
```

### Process Debugging

```bash
# Monitor mdquery processes
ps aux | grep mdquery

# Check system resources
top | grep python

# Monitor file access
lsof +D "/path/to/notes" | grep python
```

## Troubleshooting Checklist

When encountering issues, go through this checklist:

### ✅ Basic Checks

- [ ] Python 3.8+ installed and accessible
- [ ] mdquery package installed: `python -c "import mdquery"`
- [ ] Notes directory exists and is readable
- [ ] Claude Desktop configuration file exists
- [ ] JSON configuration syntax is valid
- [ ] All file paths use absolute paths
- [ ] Claude Desktop has been restarted after configuration changes

### ✅ Configuration Checks

- [ ] `command` field points to correct Python executable
- [ ] `args` field includes `["-m", "mdquery.mcp_server"]`
- [ ] `MDQUERY_NOTES_DIR` points to correct directory
- [ ] Environment variables use proper path format for OS
- [ ] No typos in configuration keys or values

### ✅ Permission Checks

- [ ] Notes directory is readable: `ls -la "/path/to/notes"`
- [ ] Database directory is writable: `ls -la ~/.mdquery/`
- [ ] No file system restrictions (network drives, etc.)
- [ ] Python has permission to create files in database location

### ✅ Performance Checks

- [ ] Database size is reasonable: `du -sh ~/.mdquery/`
- [ ] No memory constraints
- [ ] Network connectivity for cloud storage
- [ ] Sufficient disk space for database and cache

### ✅ Process Checks

- [ ] No conflicting mdquery processes running
- [ ] No database locks: `lsof ~/.mdquery/mdquery.db`
- [ ] MCP server responds to manual testing
- [ ] Claude Desktop can communicate with server

## Common Configuration Templates

### Minimal Working Configuration

```json
{
  "mcpServers": {
    "mdquery": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/absolute/path/to/notes"
      }
    }
  }
}
```

### High-Performance Configuration

```json
{
  "mcpServers": {
    "mdquery": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/path/to/notes",
        "MDQUERY_PERFORMANCE_MODE": "high",
        "MDQUERY_AUTO_OPTIMIZE": "true",
        "MDQUERY_CONCURRENT_QUERIES": "5",
        "MDQUERY_CACHE_TTL": "240",
        "MDQUERY_LAZY_LOADING": "true"
      }
    }
  }
}
```

### Debug Configuration

```json
{
  "mcpServers": {
    "mdquery": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/path/to/notes",
        "MDQUERY_LOG_LEVEL": "DEBUG",
        "MDQUERY_ENABLE_METRICS": "true",
        "MDQUERY_PERFORMANCE_MODE": "low"
      }
    }
  }
}
```

## Getting Help

### Before Asking for Help

1. **Run the diagnostic checklist** above
2. **Check the error message** carefully
3. **Try the quick fixes** mentioned
4. **Enable debug logging** and check output
5. **Test with minimal configuration** first

### What Information to Include

When asking for help, include:

1. **Operating System**: macOS/Windows/Linux version
2. **Python Version**: `python --version`
3. **mdquery Version**: `python -c "import mdquery; print(mdquery.__version__)"`
4. **Configuration File**: Your `claude_desktop_config.json` (remove sensitive paths)
5. **Error Messages**: Full error text and stack traces
6. **Debug Logs**: Output with `MDQUERY_LOG_LEVEL=DEBUG`
7. **Steps to Reproduce**: What you were trying to do

### Where to Get Help

1. **GitHub Issues**: [mdquery repository](https://github.com/your-org/mdquery/issues)
2. **Documentation**: [Complete docs](../README.md)
3. **Community Forums**: Discord/Reddit communities
4. **Stack Overflow**: Tag questions with `mdquery` and `mcp`

### Self-Help Resources

1. **[MCP Integration Guide](mcp-integration.md)**: Comprehensive setup guide
2. **[Obsidian Setup Guide](obsidian-setup.md)**: Obsidian-specific instructions
3. **[API Documentation](../api/README.md)**: Technical reference
4. **[Examples](examples/README.md)**: Working examples and use cases

---

## Emergency Recovery

If nothing else works, try this emergency recovery procedure:

```bash
# 1. Stop all processes
pkill -f mdquery
pkill -f claude

# 2. Clear all mdquery data
rm -rf ~/.mdquery/

# 3. Reinstall mdquery
pip uninstall mdquery
pip install mdquery

# 4. Test basic functionality
python -c "import mdquery; print('Working!')"

# 5. Use minimal configuration
# Create claude_desktop_config.json with only:
{
  "mcpServers": {
    "mdquery": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/path/to/your/notes"
      }
    }
  }
}

# 6. Restart Claude Desktop
```

This should resolve most issues and get you back to a working state.