/**
 * Browser file system adapter using File System Access API
 */

import { BaseFileSystemAdapter } from './base-fs-adapter.js';
import { FileStats, WalkOptions, FileChangeEvent } from '../core/types.js';

export class BrowserFileSystemAdapter extends BaseFileSystemAdapter {
  private directoryHandle: FileSystemDirectoryHandle | null = null;
  private fileHandles: Map<string, FileSystemFileHandle> = new Map();

  /**
   * Initialize with a directory handle (for File System Access API)
   */
  async initialize(directoryHandle?: FileSystemDirectoryHandle): Promise<void> {
    if (directoryHandle) {
      this.directoryHandle = directoryHandle;
    } else if ('showDirectoryPicker' in window) {
      // Request directory access from user
      try {
        this.directoryHandle = await window.showDirectoryPicker();
      } catch (error) {
        throw new Error('User cancelled directory selection or File System Access API not available');
      }
    } else {
      throw new Error('File System Access API not available in this browser');
    }
  }

  async exists(filePath: string): Promise<boolean> {
    try {
      await this.getFileHandle(filePath);
      return true;
    } catch {
      return false;
    }
  }

  async readFile(filePath: string): Promise<string> {
    try {
      const fileHandle = await this.getFileHandle(filePath);
      const file = await fileHandle.getFile();
      return await file.text();
    } catch (error) {
      throw new Error(`Failed to read file ${filePath}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async stat(filePath: string): Promise<FileStats> {
    try {
      const fileHandle = await this.getFileHandle(filePath);
      const file = await fileHandle.getFile();
      
      return {
        path: filePath,
        size: file.size,
        created: new Date(file.lastModified), // Browser doesn't provide creation date
        modified: new Date(file.lastModified),
        accessed: new Date(), // Browser doesn't provide access time
        isFile: true,
        isDirectory: false
      };
    } catch (error) {
      // Try as directory
      try {
        const dirHandle = await this.getDirectoryHandle(filePath);
        return {
          path: filePath,
          size: 0,
          created: new Date(),
          modified: new Date(),
          accessed: new Date(),
          isFile: false,
          isDirectory: true
        };
      } catch {
        throw new Error(`Failed to stat ${filePath}: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    }
  }

  async readDir(dirPath: string): Promise<string[]> {
    try {
      const dirHandle = await this.getDirectoryHandle(dirPath);
      const entries: string[] = [];
      
      for await (const [name, handle] of dirHandle.entries()) {
        const fullPath = dirPath === '/' || dirPath === '' ? name : `${dirPath}/${name}`;
        entries.push(fullPath);
      }
      
      return entries;
    } catch (error) {
      throw new Error(`Failed to read directory ${dirPath}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async *walkDir(dirPath: string, options: WalkOptions = {}): AsyncIterableIterator<string> {
    const { maxDepth = Infinity } = options;
    
    async function* walkRecursive(currentPath: string, currentDepth: number): AsyncIterableIterator<string> {
      if (currentDepth > maxDepth) return;

      try {
        const dirHandle = await this.getDirectoryHandle(currentPath);
        
        for await (const [name, handle] of dirHandle.entries()) {
          const fullPath = currentPath === '/' || currentPath === '' ? name : `${currentPath}/${name}`;
          
          if (handle.kind === 'directory') {
            // Check if directory should be excluded
            if (this.shouldExclude(fullPath, options)) {
              continue;
            }
            
            // Recurse into directory
            yield* walkRecursive.call(this, fullPath, currentDepth + 1);
          } else if (handle.kind === 'file') {
            // Check if file should be excluded
            if (this.shouldExclude(fullPath, options)) {
              continue;
            }
            
            yield fullPath;
          }
        }
      } catch (error) {
        console.warn(`Warning: Failed to read directory ${currentPath}: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    }

    yield* walkRecursive.call(this, dirPath, 0);
  }

  /**
   * Get file handle for a path
   */
  private async getFileHandle(filePath: string): Promise<FileSystemFileHandle> {
    if (!this.directoryHandle) {
      throw new Error('Directory handle not initialized');
    }

    // Check cache first
    if (this.fileHandles.has(filePath)) {
      return this.fileHandles.get(filePath)!;
    }

    const pathParts = filePath.split('/').filter(part => part !== '');
    let currentHandle: FileSystemDirectoryHandle = this.directoryHandle;

    // Navigate to the directory containing the file
    for (let i = 0; i < pathParts.length - 1; i++) {
      currentHandle = await currentHandle.getDirectoryHandle(pathParts[i]);
    }

    // Get the file handle
    const fileName = pathParts[pathParts.length - 1];
    const fileHandle = await currentHandle.getFileHandle(fileName);
    
    // Cache the handle
    this.fileHandles.set(filePath, fileHandle);
    
    return fileHandle;
  }

  /**
   * Get directory handle for a path
   */
  private async getDirectoryHandle(dirPath: string): Promise<FileSystemDirectoryHandle> {
    if (!this.directoryHandle) {
      throw new Error('Directory handle not initialized');
    }

    if (dirPath === '/' || dirPath === '') {
      return this.directoryHandle;
    }

    const pathParts = dirPath.split('/').filter(part => part !== '');
    let currentHandle: FileSystemDirectoryHandle = this.directoryHandle;

    for (const part of pathParts) {
      currentHandle = await currentHandle.getDirectoryHandle(part);
    }

    return currentHandle;
  }

  /**
   * Check if File System Access API is available
   */
  static isAvailable(): boolean {
    return 'showDirectoryPicker' in window;
  }

  /**
   * Request directory access from user
   */
  static async requestDirectoryAccess(): Promise<FileSystemDirectoryHandle> {
    if (!BrowserFileSystemAdapter.isAvailable()) {
      throw new Error('File System Access API not available');
    }

    try {
      return await window.showDirectoryPicker();
    } catch (error) {
      throw new Error('User cancelled directory selection');
    }
  }

  /**
   * Clear cached file handles
   */
  clearCache(): void {
    this.fileHandles.clear();
  }
}

/**
 * Fallback file system adapter for browsers without File System Access API
 * Uses File input or drag-and-drop for file access
 */
export class BrowserFallbackFileSystemAdapter extends BaseFileSystemAdapter {
  private files: Map<string, File> = new Map();

  async exists(path: string): Promise<boolean> {
    return this.files.has(path);
  }

  async readFile(path: string): Promise<string> {
    const file = this.files.get(path);
    if (!file) {
      throw new Error(`File not found: ${path}`);
    }
    
    return await file.text();
  }

  async stat(path: string): Promise<FileStats> {
    const file = this.files.get(path);
    if (!file) {
      throw new Error(`File not found: ${path}`);
    }

    return {
      path,
      size: file.size,
      created: new Date(file.lastModified),
      modified: new Date(file.lastModified),
      accessed: new Date(),
      isFile: true,
      isDirectory: false
    };
  }

  async readDir(path: string): Promise<string[]> {
    // Return all files that start with the path
    const files: string[] = [];
    for (const filePath of this.files.keys()) {
      if (filePath.startsWith(path)) {
        files.push(filePath);
      }
    }
    return files;
  }

  async *walkDir(path: string, options: WalkOptions = {}): AsyncIterableIterator<string> {
    for (const filePath of this.files.keys()) {
      if (filePath.startsWith(path) && !this.shouldExclude(filePath, options)) {
        yield filePath;
      }
    }
  }

  /**
   * Add files from FileList (e.g., from file input or drag-and-drop)
   */
  addFiles(fileList: FileList): void {
    for (let i = 0; i < fileList.length; i++) {
      const file = fileList[i];
      // Use the file's webkitRelativePath if available, otherwise just the name
      const path = (file as any).webkitRelativePath || file.name;
      this.files.set(path, file);
    }
  }

  /**
   * Add a single file
   */
  addFile(path: string, file: File): void {
    this.files.set(path, file);
  }

  /**
   * Clear all files
   */
  clear(): void {
    this.files.clear();
  }

  /**
   * Get all file paths
   */
  getAllPaths(): string[] {
    return Array.from(this.files.keys());
  }
}