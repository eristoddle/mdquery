/**
 * Core constants and default configurations
 */

export const DEFAULT_CONFIG = {
  systemType: 'obsidian' as const,
  extensions: ['.md', '.markdown', '.txt'],
  excludeDirs: [
    '.git',
    '.obsidian',
    '.trash',
    'node_modules',
    '.vscode',
    '.idea',
    '__pycache__',
    '.cache'
  ],
  excludeFiles: [
    '*.tmp',
    '*.temp',
    '.*',
    'Thumbs.db',
    '.DS_Store'
  ],
  enableFts: true,
  parseObsidian: true,
  maxFileSize: 10 * 1024 * 1024, // 10MB
} as const;

export const DATABASE_SCHEMA = {
  VERSION: 1,
  TABLES: {
    FILES: 'files',
    FRONTMATTER: 'frontmatter',
    TAGS: 'tags',
    LINKS: 'links',
    CONTENT_FTS: 'content_fts',
    OBSIDIAN_LINKS: 'obsidian_links',
    OBSIDIAN_CALLOUTS: 'obsidian_callouts',
    OBSIDIAN_EMBEDS: 'obsidian_embeds',
    OBSIDIAN_TEMPLATES: 'obsidian_templates',
    METADATA: 'metadata'
  }
} as const;

export const QUERY_LIMITS = {
  MAX_RESULTS: 10000,
  DEFAULT_LIMIT: 100,
  MAX_QUERY_LENGTH: 10000,
  QUERY_TIMEOUT: 30000, // 30 seconds
} as const;

export const CACHE_CONFIG = {
  MAX_MEMORY_CACHE_SIZE: 100, // number of queries
  MAX_MEMORY_CACHE_AGE: 5 * 60 * 1000, // 5 minutes
  PERSISTENT_CACHE_TTL: 24 * 60 * 60 * 1000, // 24 hours
} as const;

export const OBSIDIAN_PATTERNS = {
  WIKILINK: /\[\[([^\]]+)\]\]/g,
  EMBED: /!\[\[([^\]]+)\]\]/g,
  TAG_INLINE: /#([a-zA-Z0-9_/-]+)/g,
  CALLOUT: /^>\s*\[!(\w+)\]([+-]?)(?:\s+(.+))?$/gm,
  TEMPLATE_VAR: /\{\{([^}]+)\}\}/g,
  BLOCK_REF: /\^([a-zA-Z0-9-]+)$/gm,
  SECTION_REF: /#([^#\]]+)/,
  DATAVIEW_QUERY: /```dataview\s*\n([\s\S]*?)\n```/g,
} as const;

export const MARKDOWN_PATTERNS = {
  FRONTMATTER: /^---\s*\n([\s\S]*?)\n---\s*$/,
  HEADING: /^(#{1,6})\s+(.+)$/gm,
  LINK: /\[([^\]]*)\]\(([^)]+)\)/g,
  REFERENCE_LINK: /\[([^\]]+)\]:\s*(.+)$/gm,
  TAG: /#([a-zA-Z0-9_/-]+)/g,
  CODE_BLOCK: /```[\s\S]*?```/g,
  INLINE_CODE: /`[^`]+`/g,
} as const;

export const FILE_EXTENSIONS = {
  MARKDOWN: ['.md', '.markdown', '.mdown', '.mkdn', '.mdx'],
  TEXT: ['.txt', '.text'],
  OBSIDIAN: ['.canvas'],
  CONFIG: ['.yml', '.yaml', '.json', '.toml'],
} as const;

export const ERROR_CODES = {
  // Database errors
  DATABASE_CONNECTION_FAILED: 'DATABASE_CONNECTION_FAILED',
  DATABASE_QUERY_FAILED: 'DATABASE_QUERY_FAILED',
  DATABASE_SCHEMA_ERROR: 'DATABASE_SCHEMA_ERROR',
  
  // File system errors
  FILE_NOT_FOUND: 'FILE_NOT_FOUND',
  FILE_READ_ERROR: 'FILE_READ_ERROR',
  FILE_TOO_LARGE: 'FILE_TOO_LARGE',
  DIRECTORY_NOT_FOUND: 'DIRECTORY_NOT_FOUND',
  
  // Parsing errors
  FRONTMATTER_PARSE_ERROR: 'FRONTMATTER_PARSE_ERROR',
  MARKDOWN_PARSE_ERROR: 'MARKDOWN_PARSE_ERROR',
  INVALID_YAML: 'INVALID_YAML',
  INVALID_JSON: 'INVALID_JSON',
  
  // Query errors
  INVALID_SQL: 'INVALID_SQL',
  QUERY_TIMEOUT: 'QUERY_TIMEOUT',
  QUERY_TOO_COMPLEX: 'QUERY_TOO_COMPLEX',
  TABLE_NOT_FOUND: 'TABLE_NOT_FOUND',
  
  // Configuration errors
  INVALID_CONFIG: 'INVALID_CONFIG',
  NOTES_DIR_NOT_FOUND: 'NOTES_DIR_NOT_FOUND',
  PERMISSION_DENIED: 'PERMISSION_DENIED',
  
  // Indexing errors
  INDEXING_FAILED: 'INDEXING_FAILED',
  CONCURRENT_INDEX_ERROR: 'CONCURRENT_INDEX_ERROR',
  INDEX_CORRUPTION: 'INDEX_CORRUPTION',
} as const;

export const PERFORMANCE_CONFIG = {
  // Indexing
  MAX_CONCURRENT_FILES: 10,
  BATCH_SIZE: 100,
  PROGRESS_UPDATE_INTERVAL: 1000, // ms
  
  // Query execution
  PREPARED_STATEMENT_CACHE_SIZE: 50,
  QUERY_PLAN_CACHE_SIZE: 100,
  
  // Memory management
  MAX_MEMORY_USAGE: 512 * 1024 * 1024, // 512MB
  GC_THRESHOLD: 100, // number of operations before GC hint
} as const;