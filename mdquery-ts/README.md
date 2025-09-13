# MDQuery TypeScript

A powerful TypeScript library for SQL-like querying of markdown files, optimized for Obsidian plugins and JavaScript-based markdown analysis tools.

## Features

- **SQL-like Querying**: Familiar SQL syntax for querying markdown files
- **Full-Text Search**: Fast search across all content using SQLite FTS5
- **Fluent API**: JavaScript-native query builder for type-safe queries
- **Cross-Platform**: Works in both Node.js and browser environments
- **Obsidian Integration**: Specialized features for Obsidian vault analysis
- **Universal Compatibility**: Supports Obsidian, Jekyll, Joplin, and generic markdown
- **TypeScript Support**: Full type safety with comprehensive type definitions
- **Browser SQLite**: Uses wa-sqlite with OPFS for persistent browser storage

## Installation

```bash
npm install mdquery-ts
```

### Peer Dependencies

For Node.js:
```bash
npm install better-sqlite3
```

For browser (optional, will fallback to bundled version):
```bash
npm install wa-sqlite
```

## Quick Start

### Basic Usage

```typescript
import MDQuery from 'mdquery-ts';

// Create instance for Obsidian vault
const mdquery = MDQuery.forObsidian('/path/to/vault');

// Initialize
await mdquery.init();

// Index the vault
await mdquery.index();

// Search for content
const results = await mdquery.search('machine learning');

// Find files by tags
const taggedFiles = await mdquery.findByTags(['research', 'ai']);

// SQL queries
const recentFiles = await mdquery.sql(`
  SELECT * FROM files 
  WHERE modified > date('now', '-7 days')
  ORDER BY modified DESC
`);
```

### Obsidian Plugin Usage

```typescript
import { ObsidianPluginHelper } from 'mdquery-ts/obsidian';

export default class MyPlugin extends Plugin {
  helper: ObsidianPluginHelper;

  async onload() {
    // Initialize helper
    this.helper = new ObsidianPluginHelper({
      app: this.app,
      vault: this.app.vault,
      workspace: this.app.workspace
    });
    
    await this.helper.init();
    
    // Setup auto-indexing
    this.helper.setupAutoIndexing();
    
    // Use the helper
    const backlinks = await this.helper.getBacklinks(currentFile);
    const graphData = await this.helper.getGraphData();
  }
}
```

## API Reference

### Core Classes

#### MDQuery

The main class for interacting with markdown files.

```typescript
class MDQuery {
  constructor(config: Partial<MDQueryConfig>)
  
  // Lifecycle
  async init(): Promise<void>
  async close(): Promise<void>
  
  // Indexing
  async index(options?: IndexingOptions): Promise<IndexingStats>
  async indexFile(path: string): Promise<{updated: boolean}>
  async removeFile(path: string): Promise<void>
  
  // Querying
  async sql(query: string, params?: any[]): Promise<QueryResult>
  query(): FluentQueryBuilder
  async search(term: string, options?: SearchOptions): Promise<QueryResult>
  
  // Convenience methods
  async findByTags(tags: string | string[]): Promise<QueryResult>
  async findByFrontmatter(props: Record<string, any>): Promise<QueryResult>
  async findBacklinks(target: string): Promise<QueryResult>
  async getStats(): Promise<VaultStats>
}
```

#### Configuration

```typescript
interface MDQueryConfig {
  notesDir: string;              // Required: path to notes directory
  systemType: 'obsidian' | 'jekyll' | 'joplin' | 'generic';
  dbPath?: string;               // Optional: custom database path
  extensions: string[];          // File extensions to index
  excludeDirs: string[];         // Directories to exclude
  excludeFiles: string[];        // File patterns to exclude
  enableFts: boolean;            // Enable full-text search
  parseObsidian: boolean;        // Parse Obsidian-specific features
  maxFileSize: number;           // Maximum file size to process
}
```

### Fluent Query API

```typescript
// Fluent query building
const results = await mdquery
  .query()
  .select(['name', 'path', 'modified'])
  .from('files')
  .where('extension', '=', '.md')
  .where('word_count', '>', 1000)
  .orderBy('modified', 'desc')
  .limit(20)
  .execute();

// Pre-built patterns
const taggedFiles = await mdquery.patterns.filesByTag('research').execute();
const recentFiles = await mdquery.patterns.recentFiles(7).execute();
const brokenLinks = await mdquery.patterns.brokenLinks().execute();
```

### Database Schema

The library creates the following tables:

- `files` - File metadata (path, size, dates, word count, etc.)
- `frontmatter` - Key-value pairs from YAML frontmatter
- `tags` - Extracted tags with source tracking
- `links` - All links (markdown, wikilinks, external)
- `content_fts` - Full-text search index
- `obsidian_*` - Obsidian-specific tables (callouts, embeds, templates)

### Search Examples

```typescript
// Full-text search
await mdquery.search('artificial intelligence');

// Tag-based search
await mdquery.findByTags(['machine-learning', 'ai'], 'AND');

// Frontmatter search
await mdquery.findByFrontmatter({ 
  status: 'published',
  category: 'research' 
});

// Complex SQL queries
await mdquery.sql(`
  SELECT f.name, COUNT(t.tag) as tag_count
  FROM files f
  LEFT JOIN tags t ON f.path = t.file_path
  GROUP BY f.path
  HAVING tag_count > 5
  ORDER BY tag_count DESC
`);

// Find similar files (by shared tags)
await mdquery.findSimilar('/path/to/file.md', { minSharedTags: 3 });
```

## Obsidian Integration

### Features

- **Graph Analysis**: Get network data for visualization
- **Hub Detection**: Find highly connected files
- **Broken Link Detection**: Identify and fix broken wikilinks
- **Callout Analysis**: Search and analyze callout blocks
- **Template Tracking**: Find template usage
- **Daily Notes**: Analyze daily note patterns

### Example: Graph Visualization

```typescript
const { nodes, links } = await helper.getGraphData();

// nodes: Array<{id: string, name: string, type: 'file' | 'orphan'}>
// links: Array<{source: string, target: string, type: 'valid' | 'broken'}>

// Use with D3.js, vis.js, or other graph libraries
```

### Example: Content Analysis

```typescript
// Find hub files (highly connected)
const hubs = await integration.getHubFiles({ limit: 10 });

// Get unresolved links (potential new files)
const unresolved = await integration.getUnresolvedLinks();

// Find files by callout type
const warningFiles = await integration.findFilesByCallout('warning');

// Analyze MOCs (Maps of Content)
const mocs = await integration.getMOCAnalysis();
```

## Browser Usage

### File System Access API

```typescript
import MDQuery from 'mdquery-ts';

// For modern browsers with File System Access API
const mdquery = new MDQuery({
  notesDir: '/', // Will prompt user for directory
  systemType: 'obsidian'
});

await mdquery.init(); // Will request directory access
```

### File Input Fallback

```typescript
import { BrowserFallbackFileSystemAdapter } from 'mdquery-ts/platforms';

// For older browsers or when user denies directory access
const fs = new BrowserFallbackFileSystemAdapter();

// Add files from input element
const input = document.createElement('input');
input.type = 'file';
input.webkitdirectory = true;
input.onchange = (e) => {
  fs.addFiles(e.target.files);
};
```

## Performance Tips

1. **Indexing**: Index incrementally rather than full re-indexing
2. **Queries**: Use indexes - query by `path`, `extension`, `modified`, `tag`
3. **FTS**: Use full-text search for content queries rather than LIKE
4. **Limits**: Always use LIMIT in queries to avoid large result sets
5. **Caching**: Results are automatically cached for repeated queries

## Platform Support

| Feature | Node.js | Browser | Browser (Fallback) |
|---------|---------|---------|-------------------|
| File System | ✅ Full | ✅ With permission | ⚠️ Limited |
| SQLite | ✅ better-sqlite3 | ✅ wa-sqlite | ✅ wa-sqlite |
| Persistence | ✅ File | ✅ OPFS/IndexedDB | ✅ IndexedDB |
| File Watching | ✅ Yes | ❌ No | ❌ No |
| Performance | ⭐⭐⭐ | ⭐⭐ | ⭐ |

## License

MIT - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Changelog

### 0.1.0 (Initial Release)
- Core querying functionality
- SQL and fluent APIs
- Obsidian integration
- Browser and Node.js support
- Full-text search
- TypeScript support