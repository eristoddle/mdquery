/**
 * Main entry point for the MDQuery TypeScript library
 */

// Core exports
export * from './core/index.js';
export * from './database/index.js';
export * from './platforms/index.js';
export * from './parsers/index.js';
export * from './indexer/index.js';
export * from './query/index.js';
export * from './obsidian/index.js';

// Main class
export { MDQuery as default, MDQuery } from './mdquery.js';

// Type-only exports for better tree-shaking
export type {
  MDQueryConfig,
  QueryResult,
  FileMetadata,
  ParsedContent,
  Tag,
  Link,
  FrontmatterEntry,
  Heading,
  ObsidianLink,
  ObsidianCallout,
  ObsidianEmbed,
  ObsidianTemplate,
  DatabaseAdapter,
  FileSystemAdapter,
  QueryBuilder
} from './core/types.js';