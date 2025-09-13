/**
 * Database schema definitions and SQL statements
 */

import { DATABASE_SCHEMA } from '../core/constants.js';

export const CREATE_TABLES_SQL = {
  // Core metadata table
  metadata: `
    CREATE TABLE IF NOT EXISTS ${DATABASE_SCHEMA.TABLES.METADATA} (
      key TEXT PRIMARY KEY,
      value TEXT NOT NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `,

  // Files table - core file metadata
  files: `
    CREATE TABLE IF NOT EXISTS ${DATABASE_SCHEMA.TABLES.FILES} (
      path TEXT PRIMARY KEY,
      relative_path TEXT NOT NULL,
      name TEXT NOT NULL,
      extension TEXT NOT NULL,
      size INTEGER NOT NULL,
      created DATETIME NOT NULL,
      modified DATETIME NOT NULL,
      accessed DATETIME NOT NULL,
      word_count INTEGER DEFAULT 0,
      char_count INTEGER DEFAULT 0,
      line_count INTEGER DEFAULT 0,
      content_hash TEXT NOT NULL,
      has_frontmatter BOOLEAN DEFAULT FALSE,
      tag_count INTEGER DEFAULT 0,
      link_count INTEGER DEFAULT 0,
      indexed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      UNIQUE(path)
    )
  `,

  // Frontmatter key-value pairs
  frontmatter: `
    CREATE TABLE IF NOT EXISTS ${DATABASE_SCHEMA.TABLES.FRONTMATTER} (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      file_path TEXT NOT NULL,
      key TEXT NOT NULL,
      value TEXT NOT NULL,
      type TEXT NOT NULL,
      parsed_value TEXT,
      FOREIGN KEY (file_path) REFERENCES ${DATABASE_SCHEMA.TABLES.FILES}(path) ON DELETE CASCADE,
      UNIQUE(file_path, key)
    )
  `,

  // Tags extracted from files
  tags: `
    CREATE TABLE IF NOT EXISTS ${DATABASE_SCHEMA.TABLES.TAGS} (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      file_path TEXT NOT NULL,
      tag TEXT NOT NULL,
      source TEXT NOT NULL,
      line_number INTEGER,
      is_nested BOOLEAN DEFAULT FALSE,
      parent_tag TEXT,
      FOREIGN KEY (file_path) REFERENCES ${DATABASE_SCHEMA.TABLES.FILES}(path) ON DELETE CASCADE
    )
  `,

  // Links between files
  links: `
    CREATE TABLE IF NOT EXISTS ${DATABASE_SCHEMA.TABLES.LINKS} (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      file_path TEXT NOT NULL,
      target TEXT NOT NULL,
      text TEXT NOT NULL,
      type TEXT NOT NULL,
      line_number INTEGER NOT NULL,
      is_valid BOOLEAN DEFAULT FALSE,
      resolved_path TEXT,
      FOREIGN KEY (file_path) REFERENCES ${DATABASE_SCHEMA.TABLES.FILES}(path) ON DELETE CASCADE
    )
  `,

  // Full-text search virtual table
  contentFts: `
    CREATE VIRTUAL TABLE IF NOT EXISTS ${DATABASE_SCHEMA.TABLES.CONTENT_FTS} USING fts5(
      file_path UNINDEXED,
      title,
      content,
      frontmatter,
      tags,
      tokenize = 'porter'
    )
  `,

  // Obsidian-specific tables
  obsidianLinks: `
    CREATE TABLE IF NOT EXISTS ${DATABASE_SCHEMA.TABLES.OBSIDIAN_LINKS} (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      file_path TEXT NOT NULL,
      target TEXT NOT NULL,
      text TEXT NOT NULL,
      section TEXT,
      block_id TEXT,
      is_embed BOOLEAN DEFAULT FALSE,
      line_number INTEGER NOT NULL,
      is_valid BOOLEAN DEFAULT FALSE,
      resolved_path TEXT,
      FOREIGN KEY (file_path) REFERENCES ${DATABASE_SCHEMA.TABLES.FILES}(path) ON DELETE CASCADE
    )
  `,

  obsidianCallouts: `
    CREATE TABLE IF NOT EXISTS ${DATABASE_SCHEMA.TABLES.OBSIDIAN_CALLOUTS} (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      file_path TEXT NOT NULL,
      type TEXT NOT NULL,
      title TEXT,
      content TEXT NOT NULL,
      start_line INTEGER NOT NULL,
      end_line INTEGER NOT NULL,
      foldable BOOLEAN DEFAULT FALSE,
      folded BOOLEAN DEFAULT FALSE,
      FOREIGN KEY (file_path) REFERENCES ${DATABASE_SCHEMA.TABLES.FILES}(path) ON DELETE CASCADE
    )
  `,

  obsidianEmbeds: `
    CREATE TABLE IF NOT EXISTS ${DATABASE_SCHEMA.TABLES.OBSIDIAN_EMBEDS} (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      file_path TEXT NOT NULL,
      embed_path TEXT NOT NULL,
      section TEXT,
      block_id TEXT,
      line_number INTEGER NOT NULL,
      display_text TEXT,
      FOREIGN KEY (file_path) REFERENCES ${DATABASE_SCHEMA.TABLES.FILES}(path) ON DELETE CASCADE
    )
  `,

  obsidianTemplates: `
    CREATE TABLE IF NOT EXISTS ${DATABASE_SCHEMA.TABLES.OBSIDIAN_TEMPLATES} (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      file_path TEXT NOT NULL,
      variable TEXT NOT NULL,
      value TEXT NOT NULL,
      line_number INTEGER NOT NULL,
      type TEXT NOT NULL,
      FOREIGN KEY (file_path) REFERENCES ${DATABASE_SCHEMA.TABLES.FILES}(path) ON DELETE CASCADE
    )
  `
};

export const CREATE_INDEXES_SQL = [
  // Files table indexes
  `CREATE INDEX IF NOT EXISTS idx_files_extension ON ${DATABASE_SCHEMA.TABLES.FILES}(extension)`,
  `CREATE INDEX IF NOT EXISTS idx_files_modified ON ${DATABASE_SCHEMA.TABLES.FILES}(modified)`,
  `CREATE INDEX IF NOT EXISTS idx_files_size ON ${DATABASE_SCHEMA.TABLES.FILES}(size)`,
  `CREATE INDEX IF NOT EXISTS idx_files_word_count ON ${DATABASE_SCHEMA.TABLES.FILES}(word_count)`,
  `CREATE INDEX IF NOT EXISTS idx_files_content_hash ON ${DATABASE_SCHEMA.TABLES.FILES}(content_hash)`,

  // Frontmatter indexes
  `CREATE INDEX IF NOT EXISTS idx_frontmatter_file_path ON ${DATABASE_SCHEMA.TABLES.FRONTMATTER}(file_path)`,
  `CREATE INDEX IF NOT EXISTS idx_frontmatter_key ON ${DATABASE_SCHEMA.TABLES.FRONTMATTER}(key)`,
  `CREATE INDEX IF NOT EXISTS idx_frontmatter_type ON ${DATABASE_SCHEMA.TABLES.FRONTMATTER}(type)`,

  // Tags indexes
  `CREATE INDEX IF NOT EXISTS idx_tags_file_path ON ${DATABASE_SCHEMA.TABLES.TAGS}(file_path)`,
  `CREATE INDEX IF NOT EXISTS idx_tags_tag ON ${DATABASE_SCHEMA.TABLES.TAGS}(tag)`,
  `CREATE INDEX IF NOT EXISTS idx_tags_source ON ${DATABASE_SCHEMA.TABLES.TAGS}(source)`,
  `CREATE INDEX IF NOT EXISTS idx_tags_nested ON ${DATABASE_SCHEMA.TABLES.TAGS}(is_nested)`,

  // Links indexes
  `CREATE INDEX IF NOT EXISTS idx_links_file_path ON ${DATABASE_SCHEMA.TABLES.LINKS}(file_path)`,
  `CREATE INDEX IF NOT EXISTS idx_links_target ON ${DATABASE_SCHEMA.TABLES.LINKS}(target)`,
  `CREATE INDEX IF NOT EXISTS idx_links_type ON ${DATABASE_SCHEMA.TABLES.LINKS}(type)`,
  `CREATE INDEX IF NOT EXISTS idx_links_valid ON ${DATABASE_SCHEMA.TABLES.LINKS}(is_valid)`,

  // Obsidian links indexes
  `CREATE INDEX IF NOT EXISTS idx_obsidian_links_file_path ON ${DATABASE_SCHEMA.TABLES.OBSIDIAN_LINKS}(file_path)`,
  `CREATE INDEX IF NOT EXISTS idx_obsidian_links_target ON ${DATABASE_SCHEMA.TABLES.OBSIDIAN_LINKS}(target)`,
  `CREATE INDEX IF NOT EXISTS idx_obsidian_links_embed ON ${DATABASE_SCHEMA.TABLES.OBSIDIAN_LINKS}(is_embed)`,

  // Obsidian callouts indexes
  `CREATE INDEX IF NOT EXISTS idx_obsidian_callouts_file_path ON ${DATABASE_SCHEMA.TABLES.OBSIDIAN_CALLOUTS}(file_path)`,
  `CREATE INDEX IF NOT EXISTS idx_obsidian_callouts_type ON ${DATABASE_SCHEMA.TABLES.OBSIDIAN_CALLOUTS}(type)`,

  // Obsidian embeds indexes
  `CREATE INDEX IF NOT EXISTS idx_obsidian_embeds_file_path ON ${DATABASE_SCHEMA.TABLES.OBSIDIAN_EMBEDS}(file_path)`,
  `CREATE INDEX IF NOT EXISTS idx_obsidian_embeds_embed_path ON ${DATABASE_SCHEMA.TABLES.OBSIDIAN_EMBEDS}(embed_path)`,

  // Obsidian templates indexes
  `CREATE INDEX IF NOT EXISTS idx_obsidian_templates_file_path ON ${DATABASE_SCHEMA.TABLES.OBSIDIAN_TEMPLATES}(file_path)`,
  `CREATE INDEX IF NOT EXISTS idx_obsidian_templates_type ON ${DATABASE_SCHEMA.TABLES.OBSIDIAN_TEMPLATES}(type)`
];

export const COMMON_QUERIES = {
  // File operations
  insertFile: `
    INSERT OR REPLACE INTO ${DATABASE_SCHEMA.TABLES.FILES} 
    (path, relative_path, name, extension, size, created, modified, accessed, 
     word_count, char_count, line_count, content_hash, has_frontmatter, tag_count, link_count)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `,

  selectFileByPath: `
    SELECT * FROM ${DATABASE_SCHEMA.TABLES.FILES} WHERE path = ?
  `,

  selectFilesByExtension: `
    SELECT * FROM ${DATABASE_SCHEMA.TABLES.FILES} WHERE extension = ?
  `,

  deleteFile: `
    DELETE FROM ${DATABASE_SCHEMA.TABLES.FILES} WHERE path = ?
  `,

  // Frontmatter operations
  insertFrontmatter: `
    INSERT OR REPLACE INTO ${DATABASE_SCHEMA.TABLES.FRONTMATTER}
    (file_path, key, value, type, parsed_value)
    VALUES (?, ?, ?, ?, ?)
  `,

  selectFrontmatterByFile: `
    SELECT * FROM ${DATABASE_SCHEMA.TABLES.FRONTMATTER} WHERE file_path = ?
  `,

  deleteFrontmatterByFile: `
    DELETE FROM ${DATABASE_SCHEMA.TABLES.FRONTMATTER} WHERE file_path = ?
  `,

  // Tag operations
  insertTag: `
    INSERT INTO ${DATABASE_SCHEMA.TABLES.TAGS}
    (file_path, tag, source, line_number, is_nested, parent_tag)
    VALUES (?, ?, ?, ?, ?, ?)
  `,

  selectTagsByFile: `
    SELECT * FROM ${DATABASE_SCHEMA.TABLES.TAGS} WHERE file_path = ?
  `,

  selectFilesByTag: `
    SELECT DISTINCT f.* FROM ${DATABASE_SCHEMA.TABLES.FILES} f
    JOIN ${DATABASE_SCHEMA.TABLES.TAGS} t ON f.path = t.file_path
    WHERE t.tag = ?
  `,

  deleteTagsByFile: `
    DELETE FROM ${DATABASE_SCHEMA.TABLES.TAGS} WHERE file_path = ?
  `,

  // Link operations
  insertLink: `
    INSERT INTO ${DATABASE_SCHEMA.TABLES.LINKS}
    (file_path, target, text, type, line_number, is_valid, resolved_path)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `,

  selectLinksByFile: `
    SELECT * FROM ${DATABASE_SCHEMA.TABLES.LINKS} WHERE file_path = ?
  `,

  selectLinksToFile: `
    SELECT * FROM ${DATABASE_SCHEMA.TABLES.LINKS} WHERE resolved_path = ? OR target = ?
  `,

  deleteLinksByFile: `
    DELETE FROM ${DATABASE_SCHEMA.TABLES.LINKS} WHERE file_path = ?
  `,

  // Full-text search operations
  insertContentFts: `
    INSERT OR REPLACE INTO ${DATABASE_SCHEMA.TABLES.CONTENT_FTS}
    (file_path, title, content, frontmatter, tags)
    VALUES (?, ?, ?, ?, ?)
  `,

  searchContentFts: `
    SELECT file_path, title, snippet(${DATABASE_SCHEMA.TABLES.CONTENT_FTS}, 2, '<mark>', '</mark>', '...', 32) as snippet,
           rank FROM ${DATABASE_SCHEMA.TABLES.CONTENT_FTS}
    WHERE ${DATABASE_SCHEMA.TABLES.CONTENT_FTS} MATCH ?
    ORDER BY rank
    LIMIT ?
  `,

  deleteContentFts: `
    DELETE FROM ${DATABASE_SCHEMA.TABLES.CONTENT_FTS} WHERE file_path = ?
  `,

  // Utility queries
  getSchemaVersion: `
    SELECT value FROM ${DATABASE_SCHEMA.TABLES.METADATA} WHERE key = 'schema_version'
  `,

  setSchemaVersion: `
    INSERT OR REPLACE INTO ${DATABASE_SCHEMA.TABLES.METADATA} (key, value) VALUES ('schema_version', ?)
  `,

  getFileCount: `
    SELECT COUNT(*) as count FROM ${DATABASE_SCHEMA.TABLES.FILES}
  `,

  getLastIndexed: `
    SELECT MAX(indexed_at) as last_indexed FROM ${DATABASE_SCHEMA.TABLES.FILES}
  `,

  getOutdatedFiles: `
    SELECT path FROM ${DATABASE_SCHEMA.TABLES.FILES} 
    WHERE content_hash != ? OR modified > indexed_at
  `,

  // Statistics queries
  getTagStats: `
    SELECT tag, COUNT(*) as count FROM ${DATABASE_SCHEMA.TABLES.TAGS}
    GROUP BY tag ORDER BY count DESC LIMIT ?
  `,

  getLinkStats: `
    SELECT type, COUNT(*) as count FROM ${DATABASE_SCHEMA.TABLES.LINKS}
    GROUP BY type ORDER BY count DESC
  `,

  getFileStats: `
    SELECT 
      COUNT(*) as total_files,
      AVG(word_count) as avg_words,
      AVG(size) as avg_size,
      MAX(modified) as last_modified
    FROM ${DATABASE_SCHEMA.TABLES.FILES}
  `
};

export function getCreateTablesSql(): string[] {
  return Object.values(CREATE_TABLES_SQL);
}

export function getCreateIndexesSql(): string[] {
  return CREATE_INDEXES_SQL;
}