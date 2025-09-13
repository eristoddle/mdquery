/**
 * Main indexer class for scanning and indexing markdown files
 */

import { 
  DatabaseAdapter, 
  FileSystemAdapter, 
  MDQueryConfig, 
  ParsedContent, 
  FileMetadata 
} from '../core/types.js';
import { BaseMarkdownParser } from '../parsers/base-parser.js';
import { ParserFactory } from '../parsers/index.js';
import { COMMON_QUERIES } from '../database/schema.js';
import { 
  generateContentHash, 
  generateContentHashAsync, 
  getFileNameWithoutExtension, 
  getFileExtension, 
  getRelativePath 
} from '../core/utils.js';
import { PERFORMANCE_CONFIG } from '../core/constants.js';

export interface IndexingOptions {
  /** Whether to update existing files */
  forceUpdate?: boolean;
  /** Whether to show progress */
  showProgress?: boolean;
  /** Maximum number of files to process concurrently */
  maxConcurrent?: number;
  /** Callback for progress updates */
  onProgress?: (processed: number, total: number, currentFile: string) => void;
  /** Callback for errors */
  onError?: (error: Error, filePath: string) => void;
}

export interface IndexingStats {
  /** Total files found */
  totalFiles: number;
  /** Files processed */
  processedFiles: number;
  /** Files skipped (no changes) */
  skippedFiles: number;
  /** Files with errors */
  errorFiles: number;
  /** Start time */
  startTime: Date;
  /** End time */
  endTime?: Date;
  /** Duration in milliseconds */
  duration?: number;
  /** Files per second */
  filesPerSecond?: number;
}

export class MarkdownIndexer {
  private db: DatabaseAdapter;
  private fs: FileSystemAdapter;
  private parser: BaseMarkdownParser;
  private config: MDQueryConfig;

  constructor(
    db: DatabaseAdapter,
    fs: FileSystemAdapter,
    config: MDQueryConfig
  ) {
    this.db = db;
    this.fs = fs;
    this.config = config;
    this.parser = ParserFactory.createFromConfig(config);
  }

  /**
   * Index all markdown files in the configured directory
   */
  async indexAll(options: IndexingOptions = {}): Promise<IndexingStats> {
    const stats: IndexingStats = {
      totalFiles: 0,
      processedFiles: 0,
      skippedFiles: 0,
      errorFiles: 0,
      startTime: new Date()
    };

    try {
      // Collect all files first
      const filePaths: string[] = [];
      
      for await (const filePath of this.fs.walkDir(this.config.notesDir, {
        extensions: this.config.extensions,
        excludeDirs: this.config.excludeDirs,
        excludeFiles: this.config.excludeFiles
      })) {
        filePaths.push(filePath);
      }

      stats.totalFiles = filePaths.length;
      
      if (stats.totalFiles === 0) {
        console.log('No markdown files found to index');
        return this.finalizeStats(stats);
      }

      console.log(`Found ${stats.totalFiles} files to process`);

      // Process files in batches for better performance
      const batchSize = options.maxConcurrent || PERFORMANCE_CONFIG.MAX_CONCURRENT_FILES;
      
      for (let i = 0; i < filePaths.length; i += batchSize) {
        const batch = filePaths.slice(i, i + batchSize);
        
        await Promise.all(
          batch.map(async (filePath) => {
            try {
              const result = await this.indexFile(filePath, options);
              
              if (result.updated) {
                stats.processedFiles++;
              } else {
                stats.skippedFiles++;
              }

              // Report progress
              if (options.onProgress) {
                options.onProgress(
                  stats.processedFiles + stats.skippedFiles,
                  stats.totalFiles,
                  filePath
                );
              }
            } catch (error) {
              stats.errorFiles++;
              
              if (options.onError) {
                options.onError(error as Error, filePath);
              } else {
                console.error(`Error processing ${filePath}:`, error);
              }
            }
          })
        );
      }

      return this.finalizeStats(stats);
    } catch (error) {
      console.error('Indexing failed:', error);
      return this.finalizeStats(stats);
    }
  }

  /**
   * Index a single file
   */
  async indexFile(
    filePath: string, 
    options: IndexingOptions = {}
  ): Promise<{ updated: boolean; error?: Error }> {
    try {
      // Check if file exists
      if (!(await this.fs.exists(filePath))) {
        throw new Error(`File not found: ${filePath}`);
      }

      // Get file stats
      const fileStats = await this.fs.stat(filePath);
      
      // Check file size limit
      if (fileStats.size > this.config.maxFileSize) {
        throw new Error(`File too large: ${filePath} (${fileStats.size} bytes)`);
      }

      // Read file content
      const content = await this.fs.readFile(filePath);
      
      // Generate content hash
      const contentHash = typeof window !== 'undefined' ? 
        await generateContentHashAsync(content) : 
        generateContentHash(content);

      // Check if file needs updating
      if (!options.forceUpdate) {
        const existing = await this.db.query(COMMON_QUERIES.selectFileByPath, [filePath]);
        if (existing.length > 0 && existing[0].content_hash === contentHash) {
          return { updated: false };
        }
      }

      // Create file metadata
      const metadata: FileMetadata = {
        path: filePath,
        relativePath: getRelativePath(filePath, this.config.notesDir),
        name: getFileNameWithoutExtension(filePath),
        extension: getFileExtension(filePath),
        size: fileStats.size,
        created: fileStats.created,
        modified: fileStats.modified,
        accessed: fileStats.accessed,
        wordCount: 0, // Will be updated by parser
        charCount: 0, // Will be updated by parser
        lineCount: 0, // Will be updated by parser
        contentHash,
        hasFrontmatter: false, // Will be updated by parser
        tagCount: 0, // Will be updated by parser
        linkCount: 0 // Will be updated by parser
      };

      // Parse the file
      const parsedContent = await this.parser.parseFile(filePath, content, metadata);

      // Store in database
      await this.storeInDatabase(parsedContent);

      return { updated: true };
    } catch (error) {
      return { updated: false, error: error as Error };
    }
  }

  /**
   * Remove a file from the index
   */
  async removeFile(filePath: string): Promise<void> {
    await this.db.beginTransaction();
    
    try {
      // Delete from all tables
      await this.db.exec(COMMON_QUERIES.deleteFile, [filePath]);
      await this.db.exec(COMMON_QUERIES.deleteFrontmatterByFile, [filePath]);
      await this.db.exec(COMMON_QUERIES.deleteTagsByFile, [filePath]);
      await this.db.exec(COMMON_QUERIES.deleteLinksByFile, [filePath]);
      await this.db.exec(COMMON_QUERIES.deleteContentFts, [filePath]);

      // Delete Obsidian-specific data if applicable
      if (this.config.parseObsidian) {
        await this.db.exec(`DELETE FROM obsidian_links WHERE file_path = ?`, [filePath]);
        await this.db.exec(`DELETE FROM obsidian_callouts WHERE file_path = ?`, [filePath]);
        await this.db.exec(`DELETE FROM obsidian_embeds WHERE file_path = ?`, [filePath]);
        await this.db.exec(`DELETE FROM obsidian_templates WHERE file_path = ?`, [filePath]);
      }

      await this.db.commitTransaction();
    } catch (error) {
      await this.db.rollbackTransaction();
      throw error;
    }
  }

  /**
   * Check which files need updating
   */
  async getOutdatedFiles(): Promise<string[]> {
    const outdatedFiles: string[] = [];
    
    // Get all files from database
    const dbFiles = await this.db.query('SELECT path, content_hash, modified FROM files');
    const dbFileMap = new Map(dbFiles.map(f => [f.path, { hash: f.content_hash, modified: new Date(f.modified) }]));

    // Check each file on disk
    for await (const filePath of this.fs.walkDir(this.config.notesDir, {
      extensions: this.config.extensions,
      excludeDirs: this.config.excludeDirs,
      excludeFiles: this.config.excludeFiles
    })) {
      try {
        const fileStats = await this.fs.stat(filePath);
        const dbEntry = dbFileMap.get(filePath);

        if (!dbEntry) {
          // New file
          outdatedFiles.push(filePath);
        } else if (fileStats.modified > dbEntry.modified) {
          // Modified file - we'd need to check content hash to be sure
          const content = await this.fs.readFile(filePath);
          const contentHash = typeof window !== 'undefined' ? 
            await generateContentHashAsync(content) : 
            generateContentHash(content);
          
          if (contentHash !== dbEntry.hash) {
            outdatedFiles.push(filePath);
          }
        }
      } catch (error) {
        console.warn(`Error checking file ${filePath}:`, error);
      }
    }

    return outdatedFiles;
  }

  /**
   * Store parsed content in database
   */
  private async storeInDatabase(parsedContent: ParsedContent): Promise<void> {
    await this.db.beginTransaction();
    
    try {
      const { metadata, frontmatterEntries, tags, links, bodyContent, frontmatter } = parsedContent;

      // Insert file metadata
      await this.db.exec(COMMON_QUERIES.insertFile, [
        metadata.path,
        metadata.relativePath,
        metadata.name,
        metadata.extension,
        metadata.size,
        metadata.created.toISOString(),
        metadata.modified.toISOString(),
        metadata.accessed.toISOString(),
        metadata.wordCount,
        metadata.charCount,
        metadata.lineCount,
        metadata.contentHash,
        metadata.hasFrontmatter,
        metadata.tagCount,
        metadata.linkCount
      ]);

      // Insert frontmatter entries
      for (const entry of frontmatterEntries) {
        await this.db.exec(COMMON_QUERIES.insertFrontmatter, [
          entry.filePath,
          entry.key,
          entry.value,
          entry.type,
          JSON.stringify(entry.parsedValue)
        ]);
      }

      // Insert tags
      for (const tag of tags) {
        await this.db.exec(COMMON_QUERIES.insertTag, [
          tag.filePath,
          tag.tag,
          tag.source,
          tag.lineNumber,
          tag.isNested,
          tag.parentTag
        ]);
      }

      // Insert links
      for (const link of links) {
        await this.db.exec(COMMON_QUERIES.insertLink, [
          link.filePath,
          link.target,
          link.text,
          link.type,
          link.lineNumber,
          link.isValid,
          link.resolvedPath
        ]);
      }

      // Insert full-text search content
      if (this.config.enableFts) {
        const title = metadata.name;
        const fmText = Object.entries(frontmatter).map(([k, v]) => `${k}: ${v}`).join(' ');
        const tagText = tags.map(t => t.tag).join(' ');

        await this.db.exec(COMMON_QUERIES.insertContentFts, [
          metadata.path,
          title,
          bodyContent,
          fmText,
          tagText
        ]);
      }

      await this.db.commitTransaction();
    } catch (error) {
      await this.db.rollbackTransaction();
      throw error;
    }
  }

  /**
   * Finalize indexing statistics
   */
  private finalizeStats(stats: IndexingStats): IndexingStats {
    stats.endTime = new Date();
    stats.duration = stats.endTime.getTime() - stats.startTime.getTime();
    stats.filesPerSecond = stats.duration > 0 ? 
      (stats.processedFiles / (stats.duration / 1000)) : 0;
    
    return stats;
  }

  /**
   * Get indexing statistics
   */
  async getStats(): Promise<{
    totalFiles: number;
    totalSize: number;
    lastIndexed: Date | null;
    avgFileSize: number;
  }> {
    const fileStats = await this.db.query(COMMON_QUERIES.getFileStats);
    const stats = fileStats[0] || {};

    return {
      totalFiles: stats.total_files || 0,
      totalSize: stats.total_files * (stats.avg_size || 0),
      lastIndexed: stats.last_modified ? new Date(stats.last_modified) : null,
      avgFileSize: stats.avg_size || 0
    };
  }
}