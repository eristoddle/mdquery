/**
 * Node.js file system adapter
 */

import * as fs from 'fs/promises';
import * as path from 'path';
import { BaseFileSystemAdapter } from './base-fs-adapter.js';
import { FileStats, WalkOptions, FileChangeEvent } from '../core/types.js';

export class NodeFileSystemAdapter extends BaseFileSystemAdapter {
  async exists(filePath: string): Promise<boolean> {
    try {
      await fs.access(filePath);
      return true;
    } catch {
      return false;
    }
  }

  async readFile(filePath: string): Promise<string> {
    try {
      return await fs.readFile(filePath, 'utf-8');
    } catch (error) {
      throw new Error(`Failed to read file ${filePath}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async stat(filePath: string): Promise<FileStats> {
    try {
      const stats = await fs.stat(filePath);
      
      return {
        path: filePath,
        size: stats.size,
        created: stats.birthtime,
        modified: stats.mtime,
        accessed: stats.atime,
        isFile: stats.isFile(),
        isDirectory: stats.isDirectory()
      };
    } catch (error) {
      throw new Error(`Failed to stat file ${filePath}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async readDir(dirPath: string): Promise<string[]> {
    try {
      const entries = await fs.readdir(dirPath);
      return entries.map(entry => path.join(dirPath, entry));
    } catch (error) {
      throw new Error(`Failed to read directory ${dirPath}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async *walkDir(dirPath: string, options: WalkOptions = {}): AsyncIterableIterator<string> {
    const { maxDepth = Infinity, extensions, excludeDirs, excludeFiles } = options;
    
    async function* walkRecursive(currentPath: string, currentDepth: number): AsyncIterableIterator<string> {
      if (currentDepth > maxDepth) return;

      try {
        const entries = await fs.readdir(currentPath, { withFileTypes: true });
        
        for (const entry of entries) {
          const fullPath = path.join(currentPath, entry.name);
          const normalizedPath = this.normalizePath(fullPath);
          
          if (entry.isDirectory()) {
            // Check if directory should be excluded
            if (excludeDirs?.some(dir => entry.name === dir || normalizedPath.includes(dir))) {
              continue;
            }
            
            // Recurse into directory
            yield* walkRecursive.call(this, fullPath, currentDepth + 1);
          } else if (entry.isFile()) {
            // Check if file should be excluded
            if (this.shouldExclude(normalizedPath, options)) {
              continue;
            }
            
            yield normalizedPath;
          }
        }
      } catch (error) {
        console.warn(`Warning: Failed to read directory ${currentPath}: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    }

    yield* walkRecursive.call(this, dirPath, 0);
  }

  /**
   * Watch directory for changes (Node.js specific)
   */
  watchDir(dirPath: string, callback: (event: FileChangeEvent) => void): () => void {
    try {
      const fs = require('fs');
      const watcher = fs.watch(dirPath, { recursive: true }, (eventType: string, filename: string) => {
        if (!filename) return;
        
        const fullPath = path.join(dirPath, filename);
        
        let type: FileChangeEvent['type'];
        switch (eventType) {
          case 'rename':
            // In Node.js, 'rename' can mean create, delete, or actual rename
            // We'd need additional logic to determine which
            type = 'modified';
            break;
          case 'change':
            type = 'modified';
            break;
          default:
            type = 'modified';
        }
        
        callback({
          type,
          path: this.normalizePath(fullPath)
        });
      });

      return () => watcher.close();
    } catch (error) {
      console.warn(`Failed to watch directory ${dirPath}: ${error instanceof Error ? error.message : 'Unknown error'}`);
      return () => {}; // Return no-op function
    }
  }

  /**
   * Get absolute path (Node.js specific)
   */
  async getAbsolutePath(filePath: string): Promise<string> {
    return path.resolve(filePath);
  }

  /**
   * Check if path is directory
   */
  async isDirectory(dirPath: string): Promise<boolean> {
    try {
      const stats = await fs.stat(dirPath);
      return stats.isDirectory();
    } catch {
      return false;
    }
  }

  /**
   * Ensure directory exists
   */
  async ensureDir(dirPath: string): Promise<void> {
    try {
      await fs.mkdir(dirPath, { recursive: true });
    } catch (error) {
      throw new Error(`Failed to create directory ${dirPath}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }
}