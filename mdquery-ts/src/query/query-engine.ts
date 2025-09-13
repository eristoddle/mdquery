/**
 * Main query engine that combines SQL and fluent APIs
 */

import { DatabaseAdapter, QueryResult, MDQueryConfig } from '../core/types.js';
import { FluentQueryBuilder, QueryBuilderExtensions } from './query-builder.js';
import { SQLQueryEngine, QueryOptions } from './sql-engine.js';

export class QueryEngine {
  private sqlEngine: SQLQueryEngine;
  private config: MDQueryConfig;

  constructor(db: DatabaseAdapter, config: MDQueryConfig) {
    this.sqlEngine = new SQLQueryEngine(db);
    this.config = config;
  }

  /**
   * Execute a raw SQL query
   */
  async sql(query: string, params: any[] = [], options: QueryOptions = {}): Promise<QueryResult> {
    return this.sqlEngine.executeQuery(query, params, options);
  }

  /**
   * Create a fluent query builder
   */
  query(): FluentQueryBuilder {
    return new FluentQueryBuilder(this.getDatabase());
  }

  /**
   * Get query builder extensions with common patterns
   */
  get patterns(): QueryBuilderExtensions {
    return new QueryBuilderExtensions(this.query());
  }

  /**
   * Full-text search across all content
   */
  async search(
    searchTerm: string, 
    options: { limit?: number; includeSnippets?: boolean } = {}
  ): Promise<QueryResult> {
    const { limit = 20, includeSnippets = true } = options;
    
    const columns = includeSnippets ? 
      ['f.path', 'f.name', 'f.modified', 'f.word_count', 'snippet(content_fts, 2, "<mark>", "</mark>", "...", 32) as snippet'] :
      ['f.path', 'f.name', 'f.modified', 'f.word_count'];

    return this.query()
      .select(columns)
      .from('files f')
      .join('content_fts ON f.path = content_fts.file_path')
      .where('content_fts', 'MATCH', searchTerm)
      .orderBy('rank')
      .limit(limit)
      .execute();
  }

  /**
   * Find files by tags (supports multiple tags with AND/OR logic)
   */
  async findByTags(
    tags: string | string[], 
    logic: 'AND' | 'OR' = 'OR',
    options: { limit?: number } = {}
  ): Promise<QueryResult> {
    const tagList = Array.isArray(tags) ? tags : [tags];
    const { limit = 100 } = options;

    if (tagList.length === 1) {
      return this.patterns.filesByTag(tagList[0]).limit(limit).execute();
    }

    // Multiple tags
    const placeholders = tagList.map(() => '?').join(', ');
    const operator = logic === 'AND' ? 'AND' : 'OR';
    
    let sql: string;
    let params: any[];

    if (logic === 'AND') {
      // Files that have ALL specified tags
      sql = `
        SELECT DISTINCT f.*
        FROM files f
        WHERE (
          SELECT COUNT(DISTINCT t.tag)
          FROM tags t
          WHERE t.file_path = f.path AND t.tag IN (${placeholders})
        ) = ?
        ORDER BY f.modified DESC
        LIMIT ?
      `;
      params = [...tagList, tagList.length, limit];
    } else {
      // Files that have ANY of the specified tags
      sql = `
        SELECT DISTINCT f.*
        FROM files f
        JOIN tags t ON f.path = t.file_path
        WHERE t.tag IN (${placeholders})
        ORDER BY f.modified DESC
        LIMIT ?
      `;
      params = [...tagList, limit];
    }

    return this.sql(sql, params);
  }

  /**
   * Find files by frontmatter properties
   */
  async findByFrontmatter(
    properties: Record<string, any>,
    options: { limit?: number; matchAll?: boolean } = {}
  ): Promise<QueryResult> {
    const { limit = 100, matchAll = true } = options;
    const entries = Object.entries(properties);
    
    if (entries.length === 0) {
      throw new Error('At least one frontmatter property must be specified');
    }

    if (entries.length === 1) {
      const [key, value] = entries[0];
      return this.patterns.filesByFrontmatter(key, value).limit(limit).execute();
    }

    // Multiple properties
    const conditions = entries.map(() => 'fm.key = ? AND fm.parsed_value = ?');
    const operator = matchAll ? 'AND' : 'OR';
    const params: any[] = [];
    
    for (const [key, value] of entries) {
      params.push(key, JSON.stringify(value));
    }

    let sql: string;

    if (matchAll) {
      // Files that have ALL specified properties
      sql = `
        SELECT DISTINCT f.*
        FROM files f
        WHERE (
          SELECT COUNT(DISTINCT fm.key)
          FROM frontmatter fm
          WHERE fm.file_path = f.path AND (${conditions.join(' OR ')})
        ) = ?
        ORDER BY f.modified DESC
        LIMIT ?
      `;
      params.push(entries.length, limit);
    } else {
      // Files that have ANY of the specified properties
      sql = `
        SELECT DISTINCT f.*
        FROM files f
        JOIN frontmatter fm ON f.path = fm.file_path
        WHERE ${conditions.join(' OR ')}
        ORDER BY f.modified DESC
        LIMIT ?
      `;
      params.push(limit);
    }

    return this.sql(sql, params);
  }

  /**
   * Find files linking to a target (backlinks)
   */
  async findBacklinks(target: string, options: { limit?: number } = {}): Promise<QueryResult> {
    const { limit = 100 } = options;
    
    return this.patterns.filesLinkingTo(target).limit(limit).execute();
  }

  /**
   * Get file statistics
   */
  async getStats(): Promise<{
    totalFiles: number;
    totalTags: number;
    totalLinks: number;
    avgFileSize: number;
    avgWordCount: number;
    lastModified: Date | null;
  }> {
    const statsQuery = `
      SELECT 
        COUNT(*) as total_files,
        AVG(size) as avg_size,
        AVG(word_count) as avg_words,
        MAX(modified) as last_modified
      FROM files
    `;

    const tagCountQuery = 'SELECT COUNT(*) as count FROM tags';
    const linkCountQuery = 'SELECT COUNT(*) as count FROM links';

    const [stats, tagCount, linkCount] = await Promise.all([
      this.sql(statsQuery),
      this.sql(tagCountQuery),
      this.sql(linkCountQuery)
    ]);

    const fileStats = stats.data[0] || {};
    
    return {
      totalFiles: fileStats.total_files || 0,
      totalTags: tagCount.data[0]?.count || 0,
      totalLinks: linkCount.data[0]?.count || 0,
      avgFileSize: fileStats.avg_size || 0,
      avgWordCount: fileStats.avg_words || 0,
      lastModified: fileStats.last_modified ? new Date(fileStats.last_modified) : null
    };
  }

  /**
   * Get tag cloud data
   */
  async getTagCloud(limit: number = 50): Promise<Array<{ tag: string; count: number; weight: number }>> {
    const result = await this.patterns.tagStats(limit).execute();
    
    if (result.data.length === 0) return [];

    const maxCount = Math.max(...result.data.map(item => item.count));
    
    return result.data.map(item => ({
      tag: item.tag,
      count: item.count,
      weight: item.count / maxCount // Normalized weight 0-1
    }));
  }

  /**
   * Find similar files based on shared tags
   */
  async findSimilarFiles(filePath: string, options: { limit?: number; minSharedTags?: number } = {}): Promise<QueryResult> {
    const { limit = 10, minSharedTags = 2 } = options;
    
    const sql = `
      SELECT 
        f.*,
        COUNT(shared_tags.tag) as shared_tag_count
      FROM files f
      JOIN tags shared_tags ON f.path = shared_tags.file_path
      WHERE shared_tags.tag IN (
        SELECT t.tag
        FROM tags t
        WHERE t.file_path = ?
      )
      AND f.path != ?
      GROUP BY f.path
      HAVING shared_tag_count >= ?
      ORDER BY shared_tag_count DESC, f.modified DESC
      LIMIT ?
    `;

    return this.sql(sql, [filePath, filePath, minSharedTags, limit]);
  }

  /**
   * Get broken links report
   */
  async getBrokenLinks(): Promise<QueryResult> {
    return this.patterns.brokenLinks().execute();
  }

  /**
   * Get orphaned files (no incoming links)
   */
  async getOrphanedFiles(options: { limit?: number } = {}): Promise<QueryResult> {
    const { limit = 100 } = options;
    
    return this.patterns.orphanedFiles().limit(limit).execute();
  }

  /**
   * Get most linked files
   */
  async getMostLinkedFiles(limit: number = 10): Promise<QueryResult> {
    return this.patterns.mostLinkedFiles(limit).execute();
  }

  /**
   * Get recent files
   */
  async getRecentFiles(days: number = 7, limit: number = 20): Promise<QueryResult> {
    return this.patterns.recentFiles(days).limit(limit).execute();
  }

  /**
   * Analyze query performance
   */
  async analyzeQuery(sql: string): Promise<{
    usesIndex: boolean;
    scanType: string;
    estimatedCost: number;
    recommendations: string[];
  }> {
    return this.sqlEngine.analyzeQuery(sql);
  }

  /**
   * Get available query templates
   */
  getTemplates(): Record<string, string> {
    return SQLQueryEngine.getQueryTemplates();
  }

  /**
   * Get the underlying database adapter
   */
  private getDatabase(): DatabaseAdapter {
    return (this.sqlEngine as any).db;
  }
}