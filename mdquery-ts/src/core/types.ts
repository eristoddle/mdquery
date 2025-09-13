/**
 * Core type definitions for MDQuery TypeScript library
 */

export interface FileMetadata {
  /** Absolute file path */
  path: string;
  /** Relative path from vault root */
  relativePath: string;
  /** File name without extension */
  name: string;
  /** File extension */
  extension: string;
  /** File size in bytes */
  size: number;
  /** Creation timestamp */
  created: Date;
  /** Last modified timestamp */
  modified: Date;
  /** Last accessed timestamp */
  accessed: Date;
  /** Word count in content */
  wordCount: number;
  /** Character count in content */
  charCount: number;
  /** Line count in content */
  lineCount: number;
  /** MD5 hash of content for change detection */
  contentHash: string;
  /** Whether file has frontmatter */
  hasFrontmatter: boolean;
  /** Number of tags in file */
  tagCount: number;
  /** Number of links in file */
  linkCount: number;
}

export interface FrontmatterEntry {
  /** File path */
  filePath: string;
  /** Frontmatter key */
  key: string;
  /** Raw value as string */
  value: string;
  /** Inferred type */
  type: 'string' | 'number' | 'boolean' | 'date' | 'array' | 'object';
  /** Parsed value with proper type */
  parsedValue: any;
}

export interface Tag {
  /** File path */
  filePath: string;
  /** Tag name without # prefix */
  tag: string;
  /** Source where tag was found */
  source: 'frontmatter' | 'content' | 'inline';
  /** Line number where tag appears (for content tags) */
  lineNumber?: number;
  /** Whether this is a nested tag (contains /) */
  isNested: boolean;
  /** Parent tag if nested */
  parentTag?: string;
}

export interface Link {
  /** File path */
  filePath: string;
  /** Link target/destination */
  target: string;
  /** Link text/display name */
  text: string;
  /** Link type */
  type: 'markdown' | 'wikilink' | 'external' | 'reference';
  /** Line number where link appears */
  lineNumber: number;
  /** Whether link is valid/exists */
  isValid: boolean;
  /** Resolved target path if internal link */
  resolvedPath?: string;
}

export interface ParsedContent {
  /** File metadata */
  metadata: FileMetadata;
  /** Raw markdown content */
  content: string;
  /** Extracted frontmatter */
  frontmatter: Record<string, any>;
  /** Parsed frontmatter entries */
  frontmatterEntries: FrontmatterEntry[];
  /** Extracted tags */
  tags: Tag[];
  /** Extracted links */
  links: Link[];
  /** Content without frontmatter */
  bodyContent: string;
  /** Markdown headings */
  headings: Heading[];
}

export interface Heading {
  /** Heading text */
  text: string;
  /** Heading level (1-6) */
  level: number;
  /** Line number */
  lineNumber: number;
  /** Unique anchor ID */
  id: string;
}

export interface QueryResult {
  /** Query that was executed */
  query: string;
  /** Result data */
  data: any[];
  /** Number of rows returned */
  count: number;
  /** Execution time in milliseconds */
  executionTime: number;
  /** Query metadata */
  metadata: {
    /** Tables accessed */
    tables: string[];
    /** Columns selected */
    columns: string[];
    /** Whether full-text search was used */
    usedFts: boolean;
    /** Whether query was cached */
    cached: boolean;
  };
}

// Obsidian-specific types

export interface ObsidianLink extends Link {
  /** Section reference (#section) */
  section?: string;
  /** Block reference (^block-id) */
  blockId?: string;
  /** Whether this is an embed (![[...]]) */
  isEmbed: boolean;
}

export interface ObsidianCallout {
  /** File path */
  filePath: string;
  /** Callout type (note, warning, etc.) */
  type: string;
  /** Callout title */
  title?: string;
  /** Callout content */
  content: string;
  /** Starting line number */
  startLine: number;
  /** Ending line number */
  endLine: number;
  /** Whether callout is foldable */
  foldable: boolean;
  /** Whether callout is initially folded */
  folded: boolean;
}

export interface ObsidianEmbed {
  /** File path */
  filePath: string;
  /** Embedded file path */
  embedPath: string;
  /** Section if specified */
  section?: string;
  /** Block ID if specified */
  blockId?: string;
  /** Line number */
  lineNumber: number;
  /** Display text/alias */
  displayText?: string;
}

export interface ObsidianTemplate {
  /** File path */
  filePath: string;
  /** Template variable name */
  variable: string;
  /** Template value/expression */
  value: string;
  /** Line number */
  lineNumber: number;
  /** Template type */
  type: 'templater' | 'core-templates' | 'dataview';
}

// Configuration types

export interface MDQueryConfig {
  /** Path to notes directory */
  notesDir: string;
  /** Database file path (optional, will use default) */
  dbPath?: string;
  /** Cache directory path (optional, will use default) */
  cacheDir?: string;
  /** Markdown system type */
  systemType: 'obsidian' | 'joplin' | 'jekyll' | 'generic';
  /** File extensions to index */
  extensions: string[];
  /** Directories to exclude from indexing */
  excludeDirs: string[];
  /** Files to exclude from indexing (glob patterns) */
  excludeFiles: string[];
  /** Whether to enable full-text search */
  enableFts: boolean;
  /** Whether to parse Obsidian-specific features */
  parseObsidian: boolean;
  /** Maximum file size to process (in bytes) */
  maxFileSize: number;
}

// Platform abstraction interfaces

export interface DatabaseAdapter {
  /** Initialize database connection */
  init(dbPath: string): Promise<void>;
  /** Close database connection */
  close(): Promise<void>;
  /** Execute SQL query */
  query(sql: string, params?: any[]): Promise<any[]>;
  /** Execute SQL statement */
  exec(sql: string, params?: any[]): Promise<void>;
  /** Begin transaction */
  beginTransaction(): Promise<void>;
  /** Commit transaction */
  commitTransaction(): Promise<void>;
  /** Rollback transaction */
  rollbackTransaction(): Promise<void>;
  /** Check if table exists */
  tableExists(tableName: string): Promise<boolean>;
}

export interface FileSystemAdapter {
  /** Check if path exists */
  exists(path: string): Promise<boolean>;
  /** Read file as string */
  readFile(path: string): Promise<string>;
  /** Get file stats */
  stat(path: string): Promise<FileStats>;
  /** List directory contents */
  readDir(path: string): Promise<string[]>;
  /** Walk directory recursively */
  walkDir(path: string, options?: WalkOptions): AsyncIterableIterator<string>;
  /** Watch for file changes */
  watchDir?(path: string, callback: (event: FileChangeEvent) => void): () => void;
}

export interface FileStats {
  path: string;
  size: number;
  created: Date;
  modified: Date;
  accessed: Date;
  isFile: boolean;
  isDirectory: boolean;
}

export interface WalkOptions {
  /** File extensions to include */
  extensions?: string[];
  /** Directories to exclude */
  excludeDirs?: string[];
  /** Files to exclude (glob patterns) */
  excludeFiles?: string[];
  /** Maximum depth to traverse */
  maxDepth?: number;
}

export interface FileChangeEvent {
  type: 'created' | 'modified' | 'deleted' | 'renamed';
  path: string;
  oldPath?: string; // for rename events
}

// Query builder types

export interface QueryBuilder {
  /** Select columns */
  select(columns: string | string[]): QueryBuilder;
  /** From table */
  from(table: string): QueryBuilder;
  /** Where condition */
  where(column: string, operator: string, value: any): QueryBuilder;
  /** Where condition with custom SQL */
  whereRaw(sql: string, params?: any[]): QueryBuilder;
  /** Join tables */
  join(table: string, on: string): QueryBuilder;
  /** Left join tables */
  leftJoin(table: string, on: string): QueryBuilder;
  /** Order by column */
  orderBy(column: string, direction?: 'asc' | 'desc'): QueryBuilder;
  /** Group by column */
  groupBy(column: string | string[]): QueryBuilder;
  /** Having condition */
  having(column: string, operator: string, value: any): QueryBuilder;
  /** Limit results */
  limit(count: number): QueryBuilder;
  /** Offset results */
  offset(count: number): QueryBuilder;
  /** Execute query */
  execute(): Promise<QueryResult>;
  /** Get SQL string */
  toSQL(): string;
}

// Error types

export class MDQueryError extends Error {
  constructor(message: string, public code?: string) {
    super(message);
    this.name = 'MDQueryError';
  }
}

export class DatabaseError extends MDQueryError {
  constructor(message: string, public originalError?: Error) {
    super(message, 'DATABASE_ERROR');
  }
}

export class ParsingError extends MDQueryError {
  constructor(message: string, public filePath?: string, public lineNumber?: number) {
    super(message, 'PARSING_ERROR');
  }
}

export class QueryError extends MDQueryError {
  constructor(message: string, public query?: string) {
    super(message, 'QUERY_ERROR');
  }
}