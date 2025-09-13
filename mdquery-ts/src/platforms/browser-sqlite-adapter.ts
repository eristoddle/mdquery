/**
 * Browser SQLite database adapter using wa-sqlite
 */

import { BaseDatabaseAdapter } from '../database/base-adapter.js';
import { DatabaseError } from '../core/types.js';

// Type declarations for wa-sqlite
declare global {
  interface Window {
    SQLite?: any;
  }
}

export class BrowserSqliteAdapter extends BaseDatabaseAdapter {
  private sqlite: any = null;
  private db: any = null;

  async init(dbPath: string): Promise<void> {
    try {
      // Try to load wa-sqlite
      if (typeof window !== 'undefined' && !window.SQLite) {
        // Dynamic import for browser environment
        const SQLiteModule = await import('wa-sqlite/dist/wa-sqlite.mjs');
        const SQLiteESMFactory = await import('wa-sqlite/dist/wa-sqlite-async.mjs');
        
        // Initialize SQLite
        this.sqlite = await SQLiteESMFactory.default(SQLiteModule.default());
      } else if (typeof window !== 'undefined') {
        this.sqlite = window.SQLite;
      } else {
        throw new Error('Browser SQLite not available in this environment');
      }

      this.dbPath = dbPath;
      
      // Open database with OPFS if available, fallback to IndexedDB
      const dbName = dbPath.split('/').pop() || 'mdquery.db';
      
      try {
        // Try OPFS first (Chrome 102+)
        if ('storage' in navigator && 'getDirectory' in navigator.storage) {
          this.db = await this.sqlite.open(dbName, undefined, 'opfs');
        } else {
          // Fallback to IDB
          this.db = await this.sqlite.open(dbName, undefined, 'idb');
        }
      } catch (error) {
        // Final fallback to memory
        this.db = await this.sqlite.open(':memory:');
        console.warn('Using in-memory SQLite database - data will not persist');
      }

      // Configure for better performance
      await this.sqlite.exec(this.db, 'PRAGMA cache_size = 1000');
      await this.sqlite.exec(this.db, 'PRAGMA temp_store = MEMORY');
      
      this.isConnected = true;
      await this.initializeSchema();
    } catch (error) {
      throw new DatabaseError(
        `Failed to initialize browser SQLite: ${error instanceof Error ? error.message : 'Unknown error'}`,
        error instanceof Error ? error : undefined
      );
    }
  }

  async close(): Promise<void> {
    if (this.sqlite && this.db) {
      try {
        await this.sqlite.close(this.db);
        this.db = null;
        this.isConnected = false;
      } catch (error) {
        throw new DatabaseError(
          `Failed to close database: ${error instanceof Error ? error.message : 'Unknown error'}`,
          error instanceof Error ? error : undefined
        );
      }
    }
  }

  async query(sql: string, params: any[] = []): Promise<any[]> {
    if (!this.sqlite || !this.db) {
      throw new DatabaseError('Database not initialized');
    }

    try {
      const results: any[] = [];
      
      for await (const row of this.sqlite.statements(this.db, sql, params)) {
        const columns = this.sqlite.columns(row);
        const values = this.sqlite.values(row);
        
        const rowObj: any = {};
        columns.forEach((col: string, idx: number) => {
          rowObj[col] = values[idx];
        });
        
        results.push(rowObj);
      }
      
      return results;
    } catch (error) {
      throw new DatabaseError(
        `Query failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
        error instanceof Error ? error : undefined
      );
    }
  }

  async exec(sql: string, params: any[] = []): Promise<void> {
    if (!this.sqlite || !this.db) {
      throw new DatabaseError('Database not initialized');
    }

    try {
      if (params.length > 0) {
        // For parameterized queries, prepare and run
        const stmt = await this.sqlite.prepare(this.db, sql);
        await this.sqlite.bind(stmt, params);
        await this.sqlite.step(stmt);
        await this.sqlite.finalize(stmt);
      } else {
        // For simple SQL, use exec
        await this.sqlite.exec(this.db, sql);
      }
    } catch (error) {
      throw new DatabaseError(
        `Execution failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
        error instanceof Error ? error : undefined
      );
    }
  }

  async beginTransaction(): Promise<void> {
    if (!this.sqlite || !this.db) {
      throw new DatabaseError('Database not initialized');
    }

    try {
      await this.sqlite.exec(this.db, 'BEGIN TRANSACTION');
    } catch (error) {
      throw new DatabaseError(
        `Failed to begin transaction: ${error instanceof Error ? error.message : 'Unknown error'}`,
        error instanceof Error ? error : undefined
      );
    }
  }

  async commitTransaction(): Promise<void> {
    if (!this.sqlite || !this.db) {
      throw new DatabaseError('Database not initialized');
    }

    try {
      await this.sqlite.exec(this.db, 'COMMIT');
    } catch (error) {
      throw new DatabaseError(
        `Failed to commit transaction: ${error instanceof Error ? error.message : 'Unknown error'}`,
        error instanceof Error ? error : undefined
      );
    }
  }

  async rollbackTransaction(): Promise<void> {
    if (!this.sqlite || !this.db) {
      throw new DatabaseError('Database not initialized');
    }

    try {
      await this.sqlite.exec(this.db, 'ROLLBACK');
    } catch (error) {
      throw new DatabaseError(
        `Failed to rollback transaction: ${error instanceof Error ? error.message : 'Unknown error'}`,
        error instanceof Error ? error : undefined
      );
    }
  }

  async tableExists(tableName: string): Promise<boolean> {
    if (!this.sqlite || !this.db) {
      throw new DatabaseError('Database not initialized');
    }

    try {
      const result = await this.query(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        [tableName]
      );
      return result.length > 0;
    } catch (error) {
      throw new DatabaseError(
        `Failed to check table existence: ${error instanceof Error ? error.message : 'Unknown error'}`,
        error instanceof Error ? error : undefined
      );
    }
  }

  /**
   * Check if OPFS is available
   */
  static isOPFSAvailable(): boolean {
    return typeof navigator !== 'undefined' && 
           'storage' in navigator && 
           'getDirectory' in navigator.storage;
  }

  /**
   * Check if IndexedDB is available
   */
  static isIndexedDBAvailable(): boolean {
    return typeof window !== 'undefined' && 'indexedDB' in window;
  }

  /**
   * Get storage type being used
   */
  getStorageType(): 'opfs' | 'idb' | 'memory' {
    if (this.dbPath === ':memory:') return 'memory';
    if (BrowserSqliteAdapter.isOPFSAvailable()) return 'opfs';
    if (BrowserSqliteAdapter.isIndexedDBAvailable()) return 'idb';
    return 'memory';
  }

  /**
   * Export database (browser specific)
   */
  async exportDatabase(): Promise<ArrayBuffer> {
    if (!this.sqlite || !this.db) {
      throw new DatabaseError('Database not initialized');
    }

    try {
      return await this.sqlite.serialize(this.db);
    } catch (error) {
      throw new DatabaseError(
        `Failed to export database: ${error instanceof Error ? error.message : 'Unknown error'}`,
        error instanceof Error ? error : undefined
      );
    }
  }

  /**
   * Import database from ArrayBuffer (browser specific)
   */
  async importDatabase(data: ArrayBuffer): Promise<void> {
    if (!this.sqlite || !this.db) {
      throw new DatabaseError('Database not initialized');
    }

    try {
      await this.sqlite.deserialize(this.db, new Uint8Array(data));
    } catch (error) {
      throw new DatabaseError(
        `Failed to import database: ${error instanceof Error ? error.message : 'Unknown error'}`,
        error instanceof Error ? error : undefined
      );
    }
  }
}