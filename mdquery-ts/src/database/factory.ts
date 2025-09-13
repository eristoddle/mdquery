/**
 * Database factory for creating platform-specific adapters
 */

import { DatabaseAdapter } from '../core/types.js';
import { NodeSqliteAdapter } from './node-sqlite-adapter.js';
import { BrowserSqliteAdapter } from './browser-sqlite-adapter.js';

export type DatabasePlatform = 'node' | 'browser' | 'auto';

export class DatabaseFactory {
  /**
   * Create a database adapter for the specified platform
   */
  static async createAdapter(platform: DatabasePlatform = 'auto'): Promise<DatabaseAdapter> {
    const actualPlatform = platform === 'auto' ? DatabaseFactory.detectPlatform() : platform;

    switch (actualPlatform) {
      case 'node':
        return new NodeSqliteAdapter();
      
      case 'browser':
        return new BrowserSqliteAdapter();
      
      default:
        throw new Error(`Unsupported platform: ${actualPlatform}`);
    }
  }

  /**
   * Detect the current platform
   */
  static detectPlatform(): 'node' | 'browser' {
    // Check for Node.js environment
    if (typeof process !== 'undefined' && 
        process.versions && 
        process.versions.node) {
      return 'node';
    }

    // Check for browser environment
    if (typeof window !== 'undefined' && 
        typeof document !== 'undefined') {
      return 'browser';
    }

    // Default to browser if uncertain
    return 'browser';
  }

  /**
   * Check if better-sqlite3 is available (Node.js)
   */
  static async isBetterSqlite3Available(): Promise<boolean> {
    try {
      await import('better-sqlite3');
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Check if wa-sqlite is available (Browser)
   */
  static async isWaSqliteAvailable(): Promise<boolean> {
    try {
      await import('wa-sqlite/dist/wa-sqlite.mjs');
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Get platform capabilities
   */
  static async getPlatformCapabilities(): Promise<{
    platform: 'node' | 'browser';
    sqliteAvailable: boolean;
    persistentStorage: boolean;
    fileSystemAccess: boolean;
    features: string[];
  }> {
    const platform = DatabaseFactory.detectPlatform();
    
    if (platform === 'node') {
      const sqliteAvailable = await DatabaseFactory.isBetterSqlite3Available();
      
      return {
        platform: 'node',
        sqliteAvailable,
        persistentStorage: true,
        fileSystemAccess: true,
        features: [
          'file-system-access',
          'persistent-storage',
          'prepared-statements',
          'transactions',
          'fts5'
        ]
      };
    } else {
      const sqliteAvailable = await DatabaseFactory.isWaSqliteAvailable();
      const opfsAvailable = BrowserSqliteAdapter.isOPFSAvailable();
      const idbAvailable = BrowserSqliteAdapter.isIndexedDBAvailable();
      
      return {
        platform: 'browser',
        sqliteAvailable,
        persistentStorage: opfsAvailable || idbAvailable,
        fileSystemAccess: 'showOpenFilePicker' in window,
        features: [
          ...(opfsAvailable ? ['opfs-storage'] : []),
          ...(idbAvailable ? ['indexeddb-storage'] : []),
          'transactions',
          'export-import',
          ...(sqliteAvailable ? ['fts5'] : [])
        ]
      };
    }
  }
}

export { NodeSqliteAdapter } from './node-sqlite-adapter.js';
export { BrowserSqliteAdapter } from './browser-sqlite-adapter.js';