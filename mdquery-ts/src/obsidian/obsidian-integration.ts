/**
 * Obsidian-specific functionality and integrations
 */

import { MDQuery } from '../mdquery.js';
import { QueryResult, ObsidianCallout, ObsidianEmbed, ObsidianTemplate } from '../core/types.js';
import { ObsidianMarkdownParser } from '../parsers/obsidian.js';

export class ObsidianIntegration {
  constructor(private mdquery: MDQuery) {}

  /**
   * Get all callouts in the vault
   */
  async getCallouts(type?: string, options: { limit?: number } = {}): Promise<QueryResult> {
    const { limit = 100 } = options;
    
    let sql = `
      SELECT oc.*, f.name as file_name, f.path
      FROM obsidian_callouts oc
      JOIN files f ON oc.file_path = f.path
    `;
    const params: any[] = [];

    if (type) {
      sql += ' WHERE oc.type = ?';
      params.push(type);
    }

    sql += ' ORDER BY f.modified DESC LIMIT ?';
    params.push(limit);

    return this.mdquery.sql(sql, params);
  }

  /**
   * Get all embeds in the vault
   */
  async getEmbeds(embedPath?: string, options: { limit?: number } = {}): Promise<QueryResult> {
    const { limit = 100 } = options;
    
    let sql = `
      SELECT oe.*, f.name as file_name, f.path
      FROM obsidian_embeds oe
      JOIN files f ON oe.file_path = f.path
    `;
    const params: any[] = [];

    if (embedPath) {
      sql += ' WHERE oe.embed_path = ?';
      params.push(embedPath);
    }

    sql += ' ORDER BY f.modified DESC LIMIT ?';
    params.push(limit);

    return this.mdquery.sql(sql, params);
  }

  /**
   * Get all template variables
   */
  async getTemplates(type?: string, options: { limit?: number } = {}): Promise<QueryResult> {
    const { limit = 100 } = options;
    
    let sql = `
      SELECT ot.*, f.name as file_name, f.path
      FROM obsidian_templates ot
      JOIN files f ON ot.file_path = f.path
    `;
    const params: any[] = [];

    if (type) {
      sql += ' WHERE ot.type = ?';
      params.push(type);
    }

    sql += ' ORDER BY f.modified DESC LIMIT ?';
    params.push(limit);

    return this.mdquery.sql(sql, params);
  }

  /**
   * Find files containing specific callout types
   */
  async findFilesByCallout(calloutType: string, options: { limit?: number } = {}): Promise<QueryResult> {
    const { limit = 100 } = options;
    
    const sql = `
      SELECT DISTINCT f.*
      FROM files f
      JOIN obsidian_callouts oc ON f.path = oc.file_path
      WHERE oc.type = ?
      ORDER BY f.modified DESC
      LIMIT ?
    `;

    return this.mdquery.sql(sql, [calloutType, limit]);
  }

  /**
   * Get wikilink network data for graph visualization
   */
  async getWikilinkNetwork(): Promise<{
    nodes: Array<{ id: string; name: string; type: 'file' | 'orphan' }>;
    links: Array<{ source: string; target: string; type: string }>;
  }> {
    // Get all files as nodes
    const filesResult = await this.mdquery.sql('SELECT path, name FROM files');
    const fileSet = new Set(filesResult.data.map(f => f.path));
    
    const nodes: Array<{ id: string; name: string; type: 'file' | 'orphan' }> = 
      filesResult.data.map(f => ({
        id: f.path,
        name: f.name,
        type: 'file' as const
      }));

    // Get all wikilinks
    const linksResult = await this.mdquery.sql(`
      SELECT DISTINCT file_path, target, resolved_path, is_valid
      FROM obsidian_links
      WHERE is_embed = false
    `);

    const links: Array<{ source: string; target: string; type: string }> = [];
    
    for (const link of linksResult.data) {
      const targetPath = link.resolved_path || link.target;
      
      // Add orphan nodes for unresolved links
      if (!link.is_valid && !fileSet.has(targetPath)) {
        nodes.push({
          id: targetPath,
          name: link.target,
          type: 'orphan'
        });
        fileSet.add(targetPath);
      }

      links.push({
        source: link.file_path,
        target: targetPath,
        type: link.is_valid ? 'valid' : 'broken'
      });
    }

    return { nodes, links };
  }

  /**
   * Find hub files (files with many incoming or outgoing links)
   */
  async getHubFiles(options: { limit?: number; direction?: 'incoming' | 'outgoing' | 'both' } = {}): Promise<QueryResult> {
    const { limit = 10, direction = 'both' } = options;
    
    let sql: string;
    
    switch (direction) {
      case 'incoming':
        sql = `
          SELECT f.*, COUNT(ol.id) as link_count
          FROM files f
          LEFT JOIN obsidian_links ol ON f.path = ol.resolved_path
          GROUP BY f.path
          ORDER BY link_count DESC
          LIMIT ?
        `;
        break;
        
      case 'outgoing':
        sql = `
          SELECT f.*, COUNT(ol.id) as link_count
          FROM files f
          LEFT JOIN obsidian_links ol ON f.path = ol.file_path
          GROUP BY f.path
          ORDER BY link_count DESC
          LIMIT ?
        `;
        break;
        
      case 'both':
      default:
        sql = `
          SELECT f.*, 
                 (incoming.count + outgoing.count) as link_count,
                 incoming.count as incoming_links,
                 outgoing.count as outgoing_links
          FROM files f
          LEFT JOIN (
            SELECT resolved_path, COUNT(*) as count
            FROM obsidian_links
            WHERE is_valid = true
            GROUP BY resolved_path
          ) incoming ON f.path = incoming.resolved_path
          LEFT JOIN (
            SELECT file_path, COUNT(*) as count
            FROM obsidian_links
            GROUP BY file_path
          ) outgoing ON f.path = outgoing.file_path
          ORDER BY link_count DESC
          LIMIT ?
        `;
        break;
    }

    return this.mdquery.sql(sql, [limit]);
  }

  /**
   * Get files by canvas references
   */
  async getCanvasFiles(): Promise<QueryResult> {
    const sql = `
      SELECT *
      FROM files
      WHERE extension = '.canvas'
      ORDER BY modified DESC
    `;

    return this.mdquery.sql(sql);
  }

  /**
   * Find files that embed a specific file
   */
  async getEmbedReferences(targetFile: string): Promise<QueryResult> {
    const sql = `
      SELECT f.*, oe.line_number, oe.section, oe.block_id
      FROM files f
      JOIN obsidian_embeds oe ON f.path = oe.file_path
      WHERE oe.embed_path = ?
      ORDER BY f.modified DESC
    `;

    return this.mdquery.sql(sql, [targetFile]);
  }

  /**
   * Get unresolved wikilinks (potential new files to create)
   */
  async getUnresolvedLinks(): Promise<QueryResult> {
    const sql = `
      SELECT ol.target, COUNT(*) as reference_count, 
             GROUP_CONCAT(DISTINCT f.name) as referencing_files
      FROM obsidian_links ol
      JOIN files f ON ol.file_path = f.path
      WHERE ol.is_valid = false AND ol.target NOT LIKE 'http%'
      GROUP BY ol.target
      ORDER BY reference_count DESC
    `;

    return this.mdquery.sql(sql);
  }

  /**
   * Get Daily Notes pattern files (if using daily notes)
   */
  async getDailyNotes(year?: number, month?: number): Promise<QueryResult> {
    let sql = `
      SELECT *
      FROM files
      WHERE name REGEXP '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'
    `;
    const params: any[] = [];

    if (year) {
      sql += ' AND name LIKE ?';
      params.push(`${year}-%`);
      
      if (month) {
        const monthStr = month.toString().padStart(2, '0');
        sql = sql.replace('?', `${year}-${monthStr}-%`);
      }
    }

    sql += ' ORDER BY name DESC';

    return this.mdquery.sql(sql, params);
  }

  /**
   * Get MOC (Map of Content) analysis
   */
  async getMOCAnalysis(): Promise<QueryResult> {
    const sql = `
      SELECT f.*,
             (SELECT COUNT(*) FROM obsidian_links ol WHERE ol.file_path = f.path) as outgoing_links,
             (SELECT COUNT(*) FROM obsidian_links ol WHERE ol.resolved_path = f.path) as incoming_links,
             f.word_count
      FROM files f
      WHERE (
        SELECT COUNT(*)
        FROM obsidian_links ol
        WHERE ol.file_path = f.path
      ) > 10
      ORDER BY outgoing_links DESC
    `;

    return this.mdquery.sql(sql);
  }

  /**
   * Parse Obsidian-specific features from content
   */
  async parseObsidianFeatures(filePath: string, content: string): Promise<{
    callouts: ObsidianCallout[];
    embeds: ObsidianEmbed[];
    templates: ObsidianTemplate[];
    dataviewQueries: Array<{ query: string; lineNumber: number; type: string }>;
  }> {
    const parser = new ObsidianMarkdownParser();
    return parser.parseObsidianFeatures(filePath, content);
  }
}