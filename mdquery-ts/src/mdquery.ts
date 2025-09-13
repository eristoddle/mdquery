/**
 * Main MDQuery class - the primary interface for the library
 */

import { 
  DatabaseAdapter, 
  FileSystemAdapter, 
  MDQueryConfig, 
  QueryResult 
} from './core/types.js';
import { DEFAULT_CONFIG } from './core/constants.js';
import { DatabaseFactory } from './database/factory.js';
import { FileSystemFactory } from './platforms/fs-factory.js';
import { MarkdownIndexer, IndexingOptions, IndexingStats } from './indexer/indexer.js';
import { QueryEngine } from './query/query-engine.js';
import { ParserFactory } from './parsers/index.js';

export class MDQuery {
  private db: DatabaseAdapter;
  private fs: FileSystemAdapter;
  private config: MDQueryConfig;
  private indexer: MarkdownIndexer;
  private queryEngine: QueryEngine;
  private initialized = false;

  constructor(config: Partial<MDQueryConfig>) {
    this.config = {
      ...DEFAULT_CONFIG,
      ...config
    } as MDQueryConfig;

    if (!this.config.notesDir) {
      throw new Error('notesDir is required in configuration');
    }
  }

  /**
   * Initialize the MDQuery instance
   */
  async init(): Promise<void> {
    if (this.initialized) {
      return;
    }

    try {
      // Initialize database adapter
      this.db = await DatabaseFactory.createAdapter();
      const dbPath = this.config.dbPath || `${this.config.notesDir}/.mdquery/mdquery.db`;
      await this.db.init(dbPath);

      // Initialize file system adapter
      this.fs = await FileSystemFactory.createAdapter();
      
      // For browser file system adapter, we might need special initialization
      if ('initialize' in this.fs && typeof this.fs.initialize === 'function') {
        // Browser environment - might need user directory selection
        try {
          await this.fs.initialize();
        } catch (error) {
          console.warn('File system initialization failed:', error);
          // Continue with limited functionality
        }
      }

      // Initialize indexer and query engine
      this.indexer = new MarkdownIndexer(this.db, this.fs, this.config);
      this.queryEngine = new QueryEngine(this.db, this.config);

      this.initialized = true;
    } catch (error) {
      throw new Error(`Failed to initialize MDQuery: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Index all files in the configured directory
   */
  async index(options?: IndexingOptions): Promise<IndexingStats> {
    this.ensureInitialized();
    return this.indexer.indexAll(options);
  }

  /**
   * Index a specific file
   */
  async indexFile(filePath: string, options?: IndexingOptions): Promise<{ updated: boolean; error?: Error }> {
    this.ensureInitialized();
    return this.indexer.indexFile(filePath, options);
  }

  /**
   * Remove a file from the index
   */
  async removeFile(filePath: string): Promise<void> {
    this.ensureInitialized();
    return this.indexer.removeFile(filePath);
  }

  /**
   * Execute a SQL query
   */
  async sql(query: string, params?: any[]): Promise<QueryResult> {
    this.ensureInitialized();
    return this.queryEngine.sql(query, params);
  }

  /**
   * Get the fluent query builder
   */
  query() {
    this.ensureInitialized();
    return this.queryEngine.query();
  }

  /**
   * Get query patterns/shortcuts
   */
  get patterns() {
    this.ensureInitialized();
    return this.queryEngine.patterns;
  }

  /**
   * Full-text search
   */
  async search(searchTerm: string, options?: { limit?: number; includeSnippets?: boolean }): Promise<QueryResult> {
    this.ensureInitialized();
    return this.queryEngine.search(searchTerm, options);
  }

  /**
   * Find files by tags
   */
  async findByTags(tags: string | string[], logic?: 'AND' | 'OR', options?: { limit?: number }): Promise<QueryResult> {
    this.ensureInitialized();
    return this.queryEngine.findByTags(tags, logic, options);
  }

  /**
   * Find files by frontmatter
   */
  async findByFrontmatter(properties: Record<string, any>, options?: { limit?: number; matchAll?: boolean }): Promise<QueryResult> {
    this.ensureInitialized();
    return this.queryEngine.findByFrontmatter(properties, options);
  }

  /**
   * Find backlinks to a file
   */
  async findBacklinks(target: string, options?: { limit?: number }): Promise<QueryResult> {
    this.ensureInitialized();
    return this.queryEngine.findBacklinks(target, options);
  }

  /**
   * Find similar files
   */
  async findSimilar(filePath: string, options?: { limit?: number; minSharedTags?: number }): Promise<QueryResult> {
    this.ensureInitialized();
    return this.queryEngine.findSimilarFiles(filePath, options);
  }

  /**
   * Get statistics about the indexed content
   */
  async getStats(): Promise<{
    totalFiles: number;
    totalTags: number;
    totalLinks: number;
    avgFileSize: number;
    avgWordCount: number;
    lastModified: Date | null;
  }> {
    this.ensureInitialized();
    return this.queryEngine.getStats();
  }

  /**
   * Get tag cloud data
   */
  async getTagCloud(limit?: number): Promise<Array<{ tag: string; count: number; weight: number }>> {
    this.ensureInitialized();
    return this.queryEngine.getTagCloud(limit);
  }

  /**
   * Get broken links
   */
  async getBrokenLinks(): Promise<QueryResult> {
    this.ensureInitialized();
    return this.queryEngine.getBrokenLinks();
  }

  /**
   * Get orphaned files
   */
  async getOrphanedFiles(options?: { limit?: number }): Promise<QueryResult> {
    this.ensureInitialized();
    return this.queryEngine.getOrphanedFiles(options);
  }

  /**
   * Get most linked files
   */
  async getMostLinkedFiles(limit?: number): Promise<QueryResult> {
    this.ensureInitialized();
    return this.queryEngine.getMostLinkedFiles(limit);
  }

  /**
   * Get recent files
   */
  async getRecentFiles(days?: number, limit?: number): Promise<QueryResult> {
    this.ensureInitialized();
    return this.queryEngine.getRecentFiles(days, limit);
  }

  /**
   * Get outdated files that need re-indexing
   */
  async getOutdatedFiles(): Promise<string[]> {
    this.ensureInitialized();
    return this.indexer.getOutdatedFiles();
  }

  /**
   * Clean up the database (remove orphaned records)
   */
  async cleanup(): Promise<void> {
    this.ensureInitialized();
    await this.db.cleanup();
  }

  /**
   * Vacuum the database to reclaim space
   */
  async vacuum(): Promise<void> {
    this.ensureInitialized();
    await this.db.vacuum();
  }

  /**
   * Close the database connection
   */
  async close(): Promise<void> {
    if (this.initialized && this.db) {
      await this.db.close();
      this.initialized = false;
    }
  }

  /**
   * Get the current configuration
   */
  getConfig(): MDQueryConfig {
    return { ...this.config };
  }

  /**
   * Update configuration (requires re-initialization)
   */
  async updateConfig(newConfig: Partial<MDQueryConfig>): Promise<void> {
    await this.close();
    this.config = {
      ...this.config,
      ...newConfig
    };
    await this.init();
  }

  /**
   * Get platform capabilities
   */
  static async getPlatformCapabilities(): Promise<{
    database: any;
    fileSystem: any;
    parsers: string[];
  }> {
    const [dbCapabilities, fsCapabilities] = await Promise.all([
      DatabaseFactory.getPlatformCapabilities(),
      Promise.resolve(FileSystemFactory.getPlatformCapabilities())
    ]);

    return {
      database: dbCapabilities,
      fileSystem: fsCapabilities,
      parsers: ParserFactory.getSupportedTypes()
    };
  }

  /**
   * Create a pre-configured instance for Obsidian
   */
  static forObsidian(notesDir: string, options: Partial<MDQueryConfig> = {}): MDQuery {
    return new MDQuery({
      notesDir,
      systemType: 'obsidian',
      parseObsidian: true,
      enableFts: true,
      extensions: ['.md', '.canvas'],
      excludeDirs: ['.obsidian', '.trash'],
      ...options
    });
  }

  /**
   * Create a pre-configured instance for Jekyll
   */
  static forJekyll(notesDir: string, options: Partial<MDQueryConfig> = {}): MDQuery {
    return new MDQuery({
      notesDir,
      systemType: 'jekyll',
      parseObsidian: false,
      enableFts: true,
      extensions: ['.md', '.markdown'],
      excludeDirs: ['_site', '.jekyll-cache', '.sass-cache'],
      ...options
    });
  }

  /**
   * Create a generic markdown instance
   */
  static forMarkdown(notesDir: string, options: Partial<MDQueryConfig> = {}): MDQuery {
    return new MDQuery({
      notesDir,
      systemType: 'generic',
      parseObsidian: false,
      enableFts: true,
      extensions: ['.md', '.markdown', '.txt'],
      ...options
    });
  }

  private ensureInitialized(): void {
    if (!this.initialized) {
      throw new Error('MDQuery not initialized. Call init() first.');
    }
  }
}

// Convenience exports
export default MDQuery;
export { MDQuery };