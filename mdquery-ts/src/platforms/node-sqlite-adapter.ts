/**
 * Node.js SQLite database adapter using better-sqlite3
 */

import { BaseDatabaseAdapter } from './base-adapter.js';
import { DatabaseError } from '../core/types.js';

// Type-only import to avoid runtime dependency
type Database = any;
type Statement = any;

export class NodeSqliteAdapter extends BaseDatabaseAdapter {
  private db: Database | null = null;
  private Database: any = null;

  async init(dbPath: string): Promise<void> {
    try {
      // Dynamic import to avoid bundling in browser
      const BetterSqlite3 = await import('better-sqlite3');
      this.Database = BetterSqlite3.default || BetterSqlite3;
      
      this.dbPath = dbPath;
      this.db = new this.Database(dbPath, {
        verbose: process.env.NODE_ENV === 'development' ? console.log : undefined
      });

      // Configure SQLite for better performance
      this.db.pragma('journal_mode = WAL');
      this.db.pragma('synchronous = NORMAL');
      this.db.pragma('cache_size = 1000');
      this.db.pragma('temp_store = MEMORY');
      
      this.isConnected = true;
      await this.initializeSchema();
    } catch (error) {
      throw new DatabaseError(
        `Failed to initialize SQLite database: ${error instanceof Error ? error.message : 'Unknown error'}`,
        error instanceof Error ? error : undefined
      );
    }
  }

  async close(): Promise<void> {
    if (this.db) {
      try {
        this.db.close();
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
    if (!this.db) {
      throw new DatabaseError('Database not initialized');
    }

    try {
      const stmt = this.db.prepare(sql);
      const result = stmt.all(...params);
      return Array.isArray(result) ? result : [];
    } catch (error) {
      throw new DatabaseError(
        `Query failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
        error instanceof Error ? error : undefined
      );
    }
  }

  async exec(sql: string, params: any[] = []): Promise<void> {
    if (!this.db) {
      throw new DatabaseError('Database not initialized');
    }

    try {
      if (params.length > 0) {
        const stmt = this.db.prepare(sql);
        stmt.run(...params);
      } else {
        this.db.exec(sql);
      }
    } catch (error) {
      throw new DatabaseError(
        `Execution failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
        error instanceof Error ? error : undefined
      );
    }
  }

  async beginTransaction(): Promise<void> {
    if (!this.db) {
      throw new DatabaseError('Database not initialized');
    }

    try {
      this.db.exec('BEGIN TRANSACTION');
    } catch (error) {
      throw new DatabaseError(
        `Failed to begin transaction: ${error instanceof Error ? error.message : 'Unknown error'}`,
        error instanceof Error ? error : undefined
      );
    }
  }

  async commitTransaction(): Promise<void> {
    if (!this.db) {
      throw new DatabaseError('Database not initialized');
    }

    try {
      this.db.exec('COMMIT');
    } catch (error) {
      throw new DatabaseError(
        `Failed to commit transaction: ${error instanceof Error ? error.message : 'Unknown error'}`,
        error instanceof Error ? error : undefined
      );
    }
  }

  async rollbackTransaction(): Promise<void> {
    if (!this.db) {
      throw new DatabaseError('Database not initialized');
    }

    try {
      this.db.exec('ROLLBACK');
    } catch (error) {
      throw new DatabaseError(
        `Failed to rollback transaction: ${error instanceof Error ? error.message : 'Unknown error'}`,
        error instanceof Error ? error : undefined
      );
    }
  }

  async tableExists(tableName: string): Promise<boolean> {
    if (!this.db) {
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
   * Prepare a statement for reuse (Node.js specific optimization)
   */
  prepareStatement(sql: string): Statement {
    if (!this.db) {
      throw new DatabaseError('Database not initialized');
    }

    return this.db.prepare(sql);
  }

  /**
   * Execute multiple statements in a transaction (Node.js specific)
   */
  async executeBatch(statements: Array<{ sql: string; params?: any[] }>): Promise<void> {
    if (!this.db) {
      throw new DatabaseError('Database not initialized');
    }

    const transaction = this.db.transaction((statements: Array<{ sql: string; params?: any[] }>) => {
      for (const { sql, params = [] } of statements) {
        const stmt = this.db.prepare(sql);
        stmt.run(...params);
      }
    });

    try {
      transaction(statements);
    } catch (error) {
      throw new DatabaseError(
        `Batch execution failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
        error instanceof Error ? error : undefined
      );
    }
  }

  /**
   * Get database file size (Node.js specific)
   */
  async getDatabaseSize(): Promise<number> {
    if (!this.db) {
      throw new DatabaseError('Database not initialized');
    }

    try {
      const fs = await import('fs');
      const stats = fs.statSync(this.dbPath);
      return stats.size;
    } catch (error) {
      throw new DatabaseError(
        `Failed to get database size: ${error instanceof Error ? error.message : 'Unknown error'}`,
        error instanceof Error ? error : undefined
      );
    }
  }
}