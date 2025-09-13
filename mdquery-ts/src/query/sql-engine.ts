/**
 * SQL query engine with validation and execution
 */

import { DatabaseAdapter, QueryResult, QueryError } from '../core/types.js';
import { QUERY_LIMITS } from '../core/constants.js';
import { sanitizeSqlInput } from '../core/utils.js';

export interface QueryOptions {
  /** Maximum number of results to return */
  limit?: number;
  /** Query timeout in milliseconds */
  timeout?: number;
  /** Whether to use prepared statements */
  usePreparedStatement?: boolean;
  /** Whether to sanitize input */
  sanitizeInput?: boolean;
}

export class SQLQueryEngine {
  private preparedStatements = new Map<string, any>();

  constructor(private db: DatabaseAdapter) {}

  /**
   * Execute a SQL query with validation
   */
  async executeQuery(sql: string, params: any[] = [], options: QueryOptions = {}): Promise<QueryResult> {
    // Validate query
    this.validateQuery(sql);

    // Apply options
    const processedSql = this.processQuery(sql, options);
    const processedParams = options.sanitizeInput ? 
      params.map(p => typeof p === 'string' ? sanitizeSqlInput(p) : p) : 
      params;

    const startTime = Date.now();
    
    try {
      // Execute with timeout if specified
      const data = await this.executeWithTimeout(
        processedSql, 
        processedParams, 
        options.timeout || QUERY_LIMITS.QUERY_TIMEOUT
      );

      const executionTime = Date.now() - startTime;

      return {
        query: processedSql,
        data,
        count: data.length,
        executionTime,
        metadata: {
          tables: this.extractTables(processedSql),
          columns: this.extractColumns(processedSql),
          usedFts: processedSql.toLowerCase().includes('_fts'),
          cached: false
        }
      };
    } catch (error) {
      throw new QueryError(
        `Query execution failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
        processedSql
      );
    }
  }

  /**
   * Validate SQL query for security and correctness
   */
  private validateQuery(sql: string): void {
    const normalizedSql = sql.toLowerCase().trim();

    // Check query length
    if (sql.length > QUERY_LIMITS.MAX_QUERY_LENGTH) {
      throw new QueryError('Query too long');
    }

    // Only allow SELECT statements
    if (!normalizedSql.startsWith('select')) {
      throw new QueryError('Only SELECT queries are allowed');
    }

    // Check for dangerous keywords
    const dangerousKeywords = [
      'drop', 'delete', 'insert', 'update', 'create', 'alter', 
      'truncate', 'replace', 'pragma', 'attach', 'detach'
    ];

    for (const keyword of dangerousKeywords) {
      if (normalizedSql.includes(keyword)) {
        throw new QueryError(`Keyword '${keyword}' is not allowed`);
      }
    }

    // Check for suspicious patterns
    const suspiciousPatterns = [
      /--/,           // SQL comments
      /\/\*/,         // Block comments
      /;.*select/i,   // Multiple statements
      /union.*select/i, // UNION injection attempts
    ];

    for (const pattern of suspiciousPatterns) {
      if (pattern.test(sql)) {
        throw new QueryError('Query contains suspicious patterns');
      }
    }

    // Validate basic SQL syntax
    if (!this.hasValidSyntax(sql)) {
      throw new QueryError('Invalid SQL syntax');
    }
  }

  /**
   * Check basic SQL syntax
   */
  private hasValidSyntax(sql: string): boolean {
    try {
      // Basic checks
      const selectMatch = sql.match(/select\s+(.+?)\s+from\s+(\w+)/i);
      if (!selectMatch) {
        return false;
      }

      // Check balanced parentheses
      let balance = 0;
      for (const char of sql) {
        if (char === '(') balance++;
        if (char === ')') balance--;
        if (balance < 0) return false;
      }
      
      return balance === 0;
    } catch {
      return false;
    }
  }

  /**
   * Process query based on options
   */
  private processQuery(sql: string, options: QueryOptions): string {
    let processedSql = sql;

    // Apply limit if not already present and limit is specified
    if (options.limit && !sql.toLowerCase().includes('limit')) {
      const limit = Math.min(options.limit, QUERY_LIMITS.MAX_RESULTS);
      processedSql += ` LIMIT ${limit}`;
    }

    // Ensure we don't exceed maximum results
    const limitMatch = processedSql.match(/limit\s+(\d+)/i);
    if (limitMatch) {
      const specifiedLimit = parseInt(limitMatch[1], 10);
      if (specifiedLimit > QUERY_LIMITS.MAX_RESULTS) {
        processedSql = processedSql.replace(
          /limit\s+\d+/i, 
          `LIMIT ${QUERY_LIMITS.MAX_RESULTS}`
        );
      }
    }

    return processedSql;
  }

  /**
   * Execute query with timeout
   */
  private async executeWithTimeout(sql: string, params: any[], timeoutMs: number): Promise<any[]> {
    return new Promise((resolve, reject) => {
      const timeoutId = setTimeout(() => {
        reject(new QueryError('Query timeout exceeded', sql));
      }, timeoutMs);

      this.db.query(sql, params)
        .then(result => {
          clearTimeout(timeoutId);
          resolve(result);
        })
        .catch(error => {
          clearTimeout(timeoutId);
          reject(error);
        });
    });
  }

  /**
   * Extract table names from SQL query
   */
  private extractTables(sql: string): string[] {
    const tables: string[] = [];
    
    // FROM clause
    const fromMatch = sql.match(/from\s+(\w+)/i);
    if (fromMatch) {
      tables.push(fromMatch[1]);
    }

    // JOIN clauses
    const joinMatches = sql.matchAll(/join\s+(\w+)/gi);
    for (const match of joinMatches) {
      tables.push(match[1]);
    }

    return [...new Set(tables)]; // Remove duplicates
  }

  /**
   * Extract column names from SELECT clause
   */
  private extractColumns(sql: string): string[] {
    try {
      const selectMatch = sql.match(/select\s+(.+?)\s+from/i);
      if (!selectMatch) return [];

      const columnsPart = selectMatch[1];
      
      // Handle SELECT *
      if (columnsPart.trim() === '*') {
        return ['*'];
      }

      // Split by comma, but handle functions and aliases
      const columns = columnsPart
        .split(',')
        .map(col => col.trim())
        .map(col => {
          // Extract alias if present
          const aliasMatch = col.match(/(.+?)\s+as\s+(\w+)/i);
          return aliasMatch ? aliasMatch[2] : col;
        });

      return columns;
    } catch {
      return [];
    }
  }

  /**
   * Get query execution plan (if supported by database)
   */
  async getQueryPlan(sql: string): Promise<any[]> {
    try {
      return await this.db.query(`EXPLAIN QUERY PLAN ${sql}`);
    } catch {
      return [];
    }
  }

  /**
   * Check if query uses indexes efficiently
   */
  async analyzeQuery(sql: string): Promise<{
    usesIndex: boolean;
    scanType: string;
    estimatedCost: number;
    recommendations: string[];
  }> {
    try {
      const plan = await this.getQueryPlan(sql);
      const recommendations: string[] = [];
      let usesIndex = false;
      let scanType = 'unknown';
      let estimatedCost = 0;

      for (const row of plan) {
        const detail = row.detail || '';
        
        if (detail.includes('INDEX')) {
          usesIndex = true;
          scanType = 'index';
        } else if (detail.includes('SCAN')) {
          scanType = 'scan';
          if (!usesIndex) {
            recommendations.push('Consider adding an index for better performance');
          }
        }

        // Simple cost estimation based on operation type
        if (detail.includes('SCAN TABLE')) {
          estimatedCost += 100;
        } else if (detail.includes('SEARCH TABLE')) {
          estimatedCost += 10;
        }
      }

      // Additional recommendations
      if (sql.toLowerCase().includes('like \'%')) {
        recommendations.push('LIKE queries with leading wildcards cannot use indexes efficiently');
      }

      if (sql.toLowerCase().includes('order by') && !usesIndex) {
        recommendations.push('ORDER BY without index may be slow for large result sets');
      }

      return {
        usesIndex,
        scanType,
        estimatedCost,
        recommendations
      };
    } catch {
      return {
        usesIndex: false,
        scanType: 'unknown',
        estimatedCost: 0,
        recommendations: ['Unable to analyze query']
      };
    }
  }

  /**
   * Get common query templates
   */
  static getQueryTemplates(): Record<string, string> {
    return {
      searchFiles: `
        SELECT f.path, f.name, f.modified, 
               snippet(content_fts, 2, '<mark>', '</mark>', '...', 32) as snippet
        FROM files f
        JOIN content_fts ON f.path = content_fts.file_path
        WHERE content_fts MATCH ?
        ORDER BY rank
        LIMIT 20
      `,

      filesByTag: `
        SELECT DISTINCT f.*
        FROM files f
        JOIN tags t ON f.path = t.file_path
        WHERE t.tag = ?
        ORDER BY f.modified DESC
      `,

      tagStats: `
        SELECT tag, COUNT(*) as count
        FROM tags
        GROUP BY tag
        ORDER BY count DESC
        LIMIT 50
      `,

      recentFiles: `
        SELECT *
        FROM files
        WHERE modified >= date('now', '-7 days')
        ORDER BY modified DESC
        LIMIT 20
      `,

      brokenLinks: `
        SELECT l.*, f.name as source_file
        FROM links l
        JOIN files f ON l.file_path = f.path
        WHERE l.is_valid = false AND l.type != 'external'
      `,

      orphanedFiles: `
        SELECT f.*
        FROM files f
        LEFT JOIN links l ON f.path = l.resolved_path
        WHERE l.id IS NULL
      `,

      filesByFrontmatter: `
        SELECT DISTINCT f.*
        FROM files f
        JOIN frontmatter fm ON f.path = fm.file_path
        WHERE fm.key = ? AND fm.parsed_value = ?
      `,

      mostLinkedFiles: `
        SELECT f.*, COUNT(l.id) as link_count
        FROM files f
        LEFT JOIN links l ON f.path = l.resolved_path
        GROUP BY f.path
        ORDER BY link_count DESC
        LIMIT 10
      `
    };
  }
}