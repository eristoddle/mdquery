/**
 * Query builder for fluent API
 */

import { QueryBuilder, QueryResult, DatabaseAdapter } from '../core/types.js';
import { QUERY_LIMITS } from '../core/constants.js';

export class FluentQueryBuilder implements QueryBuilder {
  private selectColumns: string[] = ['*'];
  private fromTable: string = '';
  private whereConditions: string[] = [];
  private whereParams: any[] = [];
  private joinClauses: string[] = [];
  private orderByClause: string = '';
  private groupByColumns: string[] = [];
  private havingCondition: string = '';
  private havingParams: any[] = [];
  private limitCount?: number;
  private offsetCount?: number;

  constructor(private db: DatabaseAdapter) {}

  select(columns: string | string[]): QueryBuilder {
    this.selectColumns = Array.isArray(columns) ? columns : [columns];
    return this;
  }

  from(table: string): QueryBuilder {
    this.fromTable = table;
    return this;
  }

  where(column: string, operator: string, value: any): QueryBuilder {
    const condition = `${column} ${operator} ?`;
    this.whereConditions.push(condition);
    this.whereParams.push(value);
    return this;
  }

  whereRaw(sql: string, params: any[] = []): QueryBuilder {
    this.whereConditions.push(sql);
    this.whereParams.push(...params);
    return this;
  }

  join(table: string, on: string): QueryBuilder {
    this.joinClauses.push(`JOIN ${table} ON ${on}`);
    return this;
  }

  leftJoin(table: string, on: string): QueryBuilder {
    this.joinClauses.push(`LEFT JOIN ${table} ON ${on}`);
    return this;
  }

  orderBy(column: string, direction: 'asc' | 'desc' = 'asc'): QueryBuilder {
    this.orderByClause = `ORDER BY ${column} ${direction.toUpperCase()}`;
    return this;
  }

  groupBy(column: string | string[]): QueryBuilder {
    this.groupByColumns = Array.isArray(column) ? column : [column];
    return this;
  }

  having(column: string, operator: string, value: any): QueryBuilder {
    this.havingCondition = `${column} ${operator} ?`;
    this.havingParams.push(value);
    return this;
  }

  limit(count: number): QueryBuilder {
    this.limitCount = Math.min(count, QUERY_LIMITS.MAX_RESULTS);
    return this;
  }

  offset(count: number): QueryBuilder {
    this.offsetCount = count;
    return this;
  }

  toSQL(): string {
    let sql = `SELECT ${this.selectColumns.join(', ')} FROM ${this.fromTable}`;

    if (this.joinClauses.length > 0) {
      sql += ' ' + this.joinClauses.join(' ');
    }

    if (this.whereConditions.length > 0) {
      sql += ' WHERE ' + this.whereConditions.join(' AND ');
    }

    if (this.groupByColumns.length > 0) {
      sql += ' GROUP BY ' + this.groupByColumns.join(', ');
    }

    if (this.havingCondition) {
      sql += ' HAVING ' + this.havingCondition;
    }

    if (this.orderByClause) {
      sql += ' ' + this.orderByClause;
    }

    if (this.limitCount !== undefined) {
      sql += ' LIMIT ' + this.limitCount;
    }

    if (this.offsetCount !== undefined) {
      sql += ' OFFSET ' + this.offsetCount;
    }

    return sql;
  }

  async execute(): Promise<QueryResult> {
    const sql = this.toSQL();
    const params = [...this.whereParams, ...this.havingParams];
    
    const startTime = Date.now();
    const data = await this.db.query(sql, params);
    const executionTime = Date.now() - startTime;

    return {
      query: sql,
      data,
      count: data.length,
      executionTime,
      metadata: {
        tables: this.extractTablesFromQuery(sql),
        columns: this.selectColumns,
        usedFts: sql.includes('_fts'),
        cached: false // Would be set by caching layer
      }
    };
  }

  private extractTablesFromQuery(sql: string): string[] {
    const tables: string[] = [];
    
    // Extract main table
    const fromMatch = sql.match(/FROM\s+(\w+)/i);
    if (fromMatch) {
      tables.push(fromMatch[1]);
    }

    // Extract joined tables
    const joinMatches = sql.matchAll(/JOIN\s+(\w+)/gi);
    for (const match of joinMatches) {
      tables.push(match[1]);
    }

    return tables;
  }
}

/**
 * Convenience methods for common query patterns
 */
export class QueryBuilderExtensions {
  constructor(private builder: FluentQueryBuilder) {}

  /**
   * Search for files containing text
   */
  searchFiles(searchTerm: string): QueryBuilder {
    return this.builder
      .select(['f.path', 'f.name', 'f.modified', 'snippet(content_fts, 2, "<mark>", "</mark>", "...", 32) as snippet'])
      .from('files f')
      .join('content_fts ON f.path = content_fts.file_path')
      .where('content_fts', 'MATCH', searchTerm)
      .orderBy('rank');
  }

  /**
   * Find files by tag
   */
  filesByTag(tag: string): QueryBuilder {
    return this.builder
      .select(['DISTINCT f.*'])
      .from('files f')
      .join('tags t ON f.path = t.file_path')
      .where('t.tag', '=', tag);
  }

  /**
   * Find files by frontmatter key-value
   */
  filesByFrontmatter(key: string, value?: any): QueryBuilder {
    const query = this.builder
      .select(['DISTINCT f.*'])
      .from('files f')
      .join('frontmatter fm ON f.path = fm.file_path')
      .where('fm.key', '=', key);

    if (value !== undefined) {
      query.where('fm.parsed_value', '=', JSON.stringify(value));
    }

    return query;
  }

  /**
   * Find files linking to a target
   */
  filesLinkingTo(target: string): QueryBuilder {
    return this.builder
      .select(['DISTINCT f.*'])
      .from('files f')
      .join('links l ON f.path = l.file_path')
      .where('l.target', '=', target)
      .where('l.is_valid', '=', true);
  }

  /**
   * Get recent files
   */
  recentFiles(days: number = 7): QueryBuilder {
    const sinceDate = new Date();
    sinceDate.setDate(sinceDate.getDate() - days);

    return this.builder
      .select('*')
      .from('files')
      .where('modified', '>=', sinceDate.toISOString())
      .orderBy('modified', 'desc');
  }

  /**
   * Get largest files
   */
  largestFiles(count: number = 10): QueryBuilder {
    return this.builder
      .select('*')
      .from('files')
      .orderBy('size', 'desc')
      .limit(count);
  }

  /**
   * Get most linked files
   */
  mostLinkedFiles(count: number = 10): QueryBuilder {
    return this.builder
      .select(['f.*', 'COUNT(l.id) as link_count'])
      .from('files f')
      .leftJoin('links l ON f.path = l.resolved_path')
      .groupBy('f.path')
      .orderBy('link_count', 'desc')
      .limit(count);
  }

  /**
   * Get tag statistics
   */
  tagStats(limit: number = 50): QueryBuilder {
    return this.builder
      .select(['tag', 'COUNT(*) as count'])
      .from('tags')
      .groupBy('tag')
      .orderBy('count', 'desc')
      .limit(limit);
  }

  /**
   * Get orphaned files (files with no incoming links)
   */
  orphanedFiles(): QueryBuilder {
    return this.builder
      .select('f.*')
      .from('files f')
      .leftJoin('links l ON f.path = l.resolved_path')
      .where('l.id', 'IS', null);
  }

  /**
   * Find broken links
   */
  brokenLinks(): QueryBuilder {
    return this.builder
      .select(['l.*', 'f.name as source_file'])
      .from('links l')
      .join('files f ON l.file_path = f.path')
      .where('l.is_valid', '=', false)
      .where('l.type', '!=', 'external');
  }
}