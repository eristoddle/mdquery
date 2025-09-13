/**
 * File system abstraction for cross-platform file operations
 */

import { FileSystemAdapter, FileStats, WalkOptions, FileChangeEvent } from '../core/types.js';

export abstract class BaseFileSystemAdapter implements FileSystemAdapter {
  abstract exists(path: string): Promise<boolean>;
  abstract readFile(path: string): Promise<string>;
  abstract stat(path: string): Promise<FileStats>;
  abstract readDir(path: string): Promise<string[]>;
  abstract walkDir(path: string, options?: WalkOptions): AsyncIterableIterator<string>;
  
  // Optional file watching
  watchDir?(path: string, callback: (event: FileChangeEvent) => void): () => void;

  /**
   * Check if path matches exclusion patterns
   */
  protected shouldExclude(path: string, options?: WalkOptions): boolean {
    if (!options) return false;

    const fileName = path.split('/').pop() || '';
    const dirName = path.split('/').slice(-2, -1)[0] || '';

    // Check excluded directories
    if (options.excludeDirs?.some(dir => path.includes(dir) || dirName === dir)) {
      return true;
    }

    // Check excluded file patterns
    if (options.excludeFiles?.some(pattern => this.matchesGlob(fileName, pattern))) {
      return true;
    }

    // Check file extensions
    if (options.extensions && options.extensions.length > 0) {
      const ext = fileName.substring(fileName.lastIndexOf('.'));
      return !options.extensions.includes(ext);
    }

    return false;
  }

  /**
   * Simple glob pattern matching
   */
  protected matchesGlob(text: string, pattern: string): boolean {
    // Convert glob pattern to regex
    const regexPattern = pattern
      .replace(/\./g, '\\.')
      .replace(/\*/g, '.*')
      .replace(/\?/g, '.');
    
    const regex = new RegExp(`^${regexPattern}$`);
    return regex.test(text);
  }

  /**
   * Check if file extension is supported
   */
  protected isSupportedFile(filePath: string, extensions: string[]): boolean {
    const ext = filePath.substring(filePath.lastIndexOf('.'));
    return extensions.includes(ext);
  }

  /**
   * Normalize path separators
   */
  protected normalizePath(path: string): string {
    return path.replace(/\\/g, '/').replace(/\/+/g, '/');
  }
}