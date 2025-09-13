/**
 * Base database adapter interface and common functionality
 */

import { DatabaseAdapter } from '../core/types.js';
import { getCreateTablesSql, getCreateIndexesSql, COMMON_QUERIES } from './schema.js';
import { DATABASE_SCHEMA } from '../core/constants.js';

export abstract class BaseDatabaseAdapter implements DatabaseAdapter {
  protected dbPath: string = '';
  protected isConnected: boolean = false;

  abstract init(dbPath: string): Promise<void>;
  abstract close(): Promise<void>;
  abstract query(sql: string, params?: any[]): Promise<any[]>;
  abstract exec(sql: string, params?: any[]): Promise<void>;
  abstract beginTransaction(): Promise<void>;
  abstract commitTransaction(): Promise<void>;
  abstract rollbackTransaction(): Promise<void>;
  abstract tableExists(tableName: string): Promise<boolean>;

  /**
   * Initialize database schema
   */
  async initializeSchema(): Promise<void> {
    const schemaVersion = await this.getSchemaVersion();
    
    if (schemaVersion < DATABASE_SCHEMA.VERSION) {
      await this.createTables();
      await this.createIndexes();
      await this.setSchemaVersion(DATABASE_SCHEMA.VERSION);
    }
  }

  /**
   * Create all tables
   */
  protected async createTables(): Promise<void> {
    const tableCreationSql = getCreateTablesSql();
    
    for (const sql of tableCreationSql) {
      await this.exec(sql);
    }
  }

  /**
   * Create all indexes
   */
  protected async createIndexes(): Promise<void> {
    const indexCreationSql = getCreateIndexesSql();
    
    for (const sql of indexCreationSql) {
      await this.exec(sql);
    }
  }

  /**
   * Get current schema version
   */
  async getSchemaVersion(): Promise<number> {
    try {
      const metadataExists = await this.tableExists(DATABASE_SCHEMA.TABLES.METADATA);
      if (!metadataExists) {
        return 0;
      }

      const result = await this.query(COMMON_QUERIES.getSchemaVersion);
      return result.length > 0 ? parseInt(result[0].value, 10) : 0;
    } catch {
      return 0;
    }
  }

  /**
   * Set schema version
   */
  async setSchemaVersion(version: number): Promise<void> {
    await this.exec(COMMON_QUERIES.setSchemaVersion, [version.toString()]);
  }

  /**
   * Check if database is properly initialized
   */
  async isInitialized(): Promise<boolean> {
    try {
      const filesTableExists = await this.tableExists(DATABASE_SCHEMA.TABLES.FILES);
      const metadataTableExists = await this.tableExists(DATABASE_SCHEMA.TABLES.METADATA);
      return filesTableExists && metadataTableExists;
    } catch {
      return false;
    }
  }

  /**
   * Get database statistics
   */
  async getStats(): Promise<{
    fileCount: number;
    tagCount: number;
    linkCount: number;
    lastIndexed: Date | null;
  }> {
    const [fileResult, tagResult, linkResult, indexResult] = await Promise.all([
      this.query('SELECT COUNT(*) as count FROM ' + DATABASE_SCHEMA.TABLES.FILES),
      this.query('SELECT COUNT(*) as count FROM ' + DATABASE_SCHEMA.TABLES.TAGS),
      this.query('SELECT COUNT(*) as count FROM ' + DATABASE_SCHEMA.TABLES.LINKS),
      this.query(COMMON_QUERIES.getLastIndexed)
    ]);

    return {
      fileCount: fileResult[0]?.count || 0,
      tagCount: tagResult[0]?.count || 0,
      linkCount: linkResult[0]?.count || 0,
      lastIndexed: indexResult[0]?.last_indexed ? new Date(indexResult[0].last_indexed) : null
    };
  }

  /**
   * Clean up orphaned records
   */
  async cleanup(): Promise<void> {
    const cleanupQueries = [
      `DELETE FROM ${DATABASE_SCHEMA.TABLES.FRONTMATTER} WHERE file_path NOT IN (SELECT path FROM ${DATABASE_SCHEMA.TABLES.FILES})`,
      `DELETE FROM ${DATABASE_SCHEMA.TABLES.TAGS} WHERE file_path NOT IN (SELECT path FROM ${DATABASE_SCHEMA.TABLES.FILES})`,
      `DELETE FROM ${DATABASE_SCHEMA.TABLES.LINKS} WHERE file_path NOT IN (SELECT path FROM ${DATABASE_SCHEMA.TABLES.FILES})`,
      `DELETE FROM ${DATABASE_SCHEMA.TABLES.CONTENT_FTS} WHERE file_path NOT IN (SELECT path FROM ${DATABASE_SCHEMA.TABLES.FILES})`
    ];

    if (await this.tableExists(DATABASE_SCHEMA.TABLES.OBSIDIAN_LINKS)) {
      cleanupQueries.push(
        `DELETE FROM ${DATABASE_SCHEMA.TABLES.OBSIDIAN_LINKS} WHERE file_path NOT IN (SELECT path FROM ${DATABASE_SCHEMA.TABLES.FILES})`,
        `DELETE FROM ${DATABASE_SCHEMA.TABLES.OBSIDIAN_CALLOUTS} WHERE file_path NOT IN (SELECT path FROM ${DATABASE_SCHEMA.TABLES.FILES})`,
        `DELETE FROM ${DATABASE_SCHEMA.TABLES.OBSIDIAN_EMBEDS} WHERE file_path NOT IN (SELECT path FROM ${DATABASE_SCHEMA.TABLES.FILES})`,
        `DELETE FROM ${DATABASE_SCHEMA.TABLES.OBSIDIAN_TEMPLATES} WHERE file_path NOT IN (SELECT path FROM ${DATABASE_SCHEMA.TABLES.FILES})`
      );
    }

    await this.beginTransaction();
    try {
      for (const query of cleanupQueries) {
        await this.exec(query);
      }
      await this.commitTransaction();
    } catch (error) {
      await this.rollbackTransaction();
      throw error;
    }
  }

  /**
   * Vacuum database to reclaim space
   */
  async vacuum(): Promise<void> {
    await this.exec('VACUUM');
  }

  /**
   * Analyze database for query optimization
   */
  async analyze(): Promise<void> {
    await this.exec('ANALYZE');
  }
}