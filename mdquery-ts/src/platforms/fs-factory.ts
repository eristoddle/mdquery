/**
 * File system adapter factory
 */

import { FileSystemAdapter } from '../core/types.js';
import { NodeFileSystemAdapter } from './node-fs-adapter.js';
import { BrowserFileSystemAdapter, BrowserFallbackFileSystemAdapter } from './browser-fs-adapter.js';

export type FileSystemPlatform = 'node' | 'browser' | 'browser-fallback' | 'auto';

export class FileSystemFactory {
  /**
   * Create a file system adapter for the specified platform
   */
  static async createAdapter(platform: FileSystemPlatform = 'auto'): Promise<FileSystemAdapter> {
    const actualPlatform = platform === 'auto' ? FileSystemFactory.detectPlatform() : platform;

    switch (actualPlatform) {
      case 'node':
        return new NodeFileSystemAdapter();
      
      case 'browser':
        if (BrowserFileSystemAdapter.isAvailable()) {
          return new BrowserFileSystemAdapter();
        } else {
          throw new Error('File System Access API not available in this browser');
        }
      
      case 'browser-fallback':
        return new BrowserFallbackFileSystemAdapter();
      
      default:
        throw new Error(`Unsupported platform: ${actualPlatform}`);
    }
  }

  /**
   * Detect the current platform
   */
  static detectPlatform(): 'node' | 'browser' | 'browser-fallback' {
    // Check for Node.js environment
    if (typeof process !== 'undefined' && 
        process.versions && 
        process.versions.node) {
      return 'node';
    }

    // Check for browser with File System Access API
    if (typeof window !== 'undefined' && BrowserFileSystemAdapter.isAvailable()) {
      return 'browser';
    }

    // Fallback for browsers without File System Access API
    if (typeof window !== 'undefined') {
      return 'browser-fallback';
    }

    // Default to browser if uncertain
    return 'browser-fallback';
  }

  /**
   * Get platform capabilities
   */
  static getPlatformCapabilities(): {
    platform: string;
    fileSystemAccess: boolean;
    directoryTraversal: boolean;
    fileWatching: boolean;
    features: string[];
  } {
    const platform = FileSystemFactory.detectPlatform();
    
    switch (platform) {
      case 'node':
        return {
          platform: 'node',
          fileSystemAccess: true,
          directoryTraversal: true,
          fileWatching: true,
          features: [
            'full-file-system-access',
            'recursive-directory-traversal',
            'file-watching',
            'file-stats',
            'path-resolution'
          ]
        };
      
      case 'browser':
        return {
          platform: 'browser',
          fileSystemAccess: true,
          directoryTraversal: true,
          fileWatching: false,
          features: [
            'file-system-access-api',
            'directory-traversal',
            'file-stats-limited',
            'user-permission-required'
          ]
        };
      
      case 'browser-fallback':
        return {
          platform: 'browser-fallback',
          fileSystemAccess: false,
          directoryTraversal: false,
          fileWatching: false,
          features: [
            'file-input-only',
            'drag-drop-support',
            'no-directory-traversal',
            'limited-file-access'
          ]
        };
      
      default:
        return {
          platform: 'unknown',
          fileSystemAccess: false,
          directoryTraversal: false,
          fileWatching: false,
          features: []
        };
    }
  }
}

export { NodeFileSystemAdapter } from './node-fs-adapter.js';
export { BrowserFileSystemAdapter, BrowserFallbackFileSystemAdapter } from './browser-fs-adapter.js';
export { BaseFileSystemAdapter } from './base-fs-adapter.js';