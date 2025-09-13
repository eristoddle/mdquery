/**
 * Obsidian plugin helper functions and utilities
 */

import { MDQuery } from '../mdquery.js';
import { ObsidianIntegration } from './obsidian-integration.js';

export interface ObsidianPluginContext {
  app: any; // Obsidian App instance
  vault: any; // Obsidian Vault instance
  workspace: any; // Obsidian Workspace instance
}

export class ObsidianPluginHelper {
  private mdquery: MDQuery;
  private integration: ObsidianIntegration;

  constructor(private ctx: ObsidianPluginContext) {
    // Initialize MDQuery for Obsidian vault
    const vaultPath = (ctx.vault.adapter as any).basePath || ctx.vault.adapter.path;
    this.mdquery = MDQuery.forObsidian(vaultPath);
    this.integration = new ObsidianIntegration(this.mdquery);
  }

  /**
   * Initialize the helper
   */
  async init(): Promise<void> {
    await this.mdquery.init();
  }

  /**
   * Index the entire vault
   */
  async indexVault(options?: {
    showProgress?: boolean;
    onProgress?: (processed: number, total: number, file: string) => void;
  }): Promise<void> {
    await this.mdquery.index({
      showProgress: options?.showProgress,
      onProgress: options?.onProgress
    });
  }

  /**
   * Search across the vault
   */
  async search(query: string): Promise<Array<{
    file: any; // TFile
    path: string;
    name: string;
    snippet?: string;
  }>> {
    const results = await this.mdquery.search(query, { includeSnippets: true });
    
    return results.data.map(result => ({
      file: this.ctx.vault.getAbstractFileByPath(result.path),
      path: result.path,
      name: result.name,
      snippet: result.snippet
    })).filter(item => item.file); // Filter out files that don't exist
  }

  /**
   * Get backlinks for a file
   */
  async getBacklinks(file: any): Promise<Array<{
    file: any;
    path: string;
    name: string;
  }>> {
    const results = await this.mdquery.findBacklinks(file.path);
    
    return results.data.map(result => ({
      file: this.ctx.vault.getAbstractFileByPath(result.path),
      path: result.path,
      name: result.name
    })).filter(item => item.file);
  }

  /**
   * Get files by tag
   */
  async getFilesByTag(tag: string): Promise<Array<{
    file: any;
    path: string;
    name: string;
  }>> {
    const results = await this.mdquery.findByTags(tag);
    
    return results.data.map(result => ({
      file: this.ctx.vault.getAbstractFileByPath(result.path),
      path: result.path,
      name: result.name
    })).filter(item => item.file);
  }

  /**
   * Get graph data for visualization
   */
  async getGraphData(): Promise<{
    nodes: Array<{ id: string; name: string; type: 'file' | 'orphan' }>;
    links: Array<{ source: string; target: string; type: string }>;
  }> {
    return this.integration.getWikilinkNetwork();
  }

  /**
   * Get hub files (highly connected files)
   */
  async getHubFiles(limit: number = 10): Promise<Array<{
    file: any;
    path: string;
    name: string;
    linkCount: number;
    incomingLinks: number;
    outgoingLinks: number;
  }>> {
    const results = await this.integration.getHubFiles({ limit, direction: 'both' });
    
    return results.data.map(result => ({
      file: this.ctx.vault.getAbstractFileByPath(result.path),
      path: result.path,
      name: result.name,
      linkCount: result.link_count || 0,
      incomingLinks: result.incoming_links || 0,
      outgoingLinks: result.outgoing_links || 0
    })).filter(item => item.file);
  }

  /**
   * Get orphaned files
   */
  async getOrphanedFiles(): Promise<Array<{
    file: any;
    path: string;
    name: string;
  }>> {
    const results = await this.mdquery.getOrphanedFiles();
    
    return results.data.map(result => ({
      file: this.ctx.vault.getAbstractFileByPath(result.path),
      path: result.path,
      name: result.name
    })).filter(item => item.file);
  }

  /**
   * Get broken links
   */
  async getBrokenLinks(): Promise<Array<{
    sourceFile: any;
    sourcePath: string;
    target: string;
    lineNumber: number;
  }>> {
    const results = await this.mdquery.getBrokenLinks();
    
    return results.data.map(result => ({
      sourceFile: this.ctx.vault.getAbstractFileByPath(result.file_path),
      sourcePath: result.file_path,
      target: result.target,
      lineNumber: result.line_number
    })).filter(item => item.sourceFile);
  }

  /**
   * Get tag cloud data
   */
  async getTagCloud(limit: number = 50): Promise<Array<{
    tag: string;
    count: number;
    weight: number;
  }>> {
    return this.mdquery.getTagCloud(limit);
  }

  /**
   * Find similar files to the current file
   */
  async findSimilarFiles(file: any, limit: number = 5): Promise<Array<{
    file: any;
    path: string;
    name: string;
    sharedTagCount: number;
  }>> {
    const results = await this.mdquery.findSimilar(file.path, { limit });
    
    return results.data.map(result => ({
      file: this.ctx.vault.getAbstractFileByPath(result.path),
      path: result.path,
      name: result.name,
      sharedTagCount: result.shared_tag_count || 0
    })).filter(item => item.file);
  }

  /**
   * Get vault statistics
   */
  async getVaultStats(): Promise<{
    totalFiles: number;
    totalTags: number;
    totalLinks: number;
    avgFileSize: number;
    avgWordCount: number;
    lastModified: Date | null;
  }> {
    return this.mdquery.getStats();
  }

  /**
   * Listen to vault changes and update index
   */
  setupAutoIndexing(): void {
    // Listen to file creation
    this.ctx.vault.on('create', async (file: any) => {
      if (file.extension === 'md') {
        try {
          await this.mdquery.indexFile(file.path);
        } catch (error) {
          console.error('Failed to index new file:', error);
        }
      }
    });

    // Listen to file modification
    this.ctx.vault.on('modify', async (file: any) => {
      if (file.extension === 'md') {
        try {
          await this.mdquery.indexFile(file.path, { forceUpdate: true });
        } catch (error) {
          console.error('Failed to re-index modified file:', error);
        }
      }
    });

    // Listen to file deletion
    this.ctx.vault.on('delete', async (file: any) => {
      if (file.extension === 'md') {
        try {
          await this.mdquery.removeFile(file.path);
        } catch (error) {
          console.error('Failed to remove file from index:', error);
        }
      }
    });

    // Listen to file rename
    this.ctx.vault.on('rename', async (file: any, oldPath: string) => {
      if (file.extension === 'md') {
        try {
          await this.mdquery.removeFile(oldPath);
          await this.mdquery.indexFile(file.path);
        } catch (error) {
          console.error('Failed to handle file rename:', error);
        }
      }
    });
  }

  /**
   * Clean up resources
   */
  async cleanup(): Promise<void> {
    await this.mdquery.close();
  }

  /**
   * Get the underlying MDQuery instance
   */
  getMDQuery(): MDQuery {
    return this.mdquery;
  }

  /**
   * Get the Obsidian integration
   */
  getObsidianIntegration(): ObsidianIntegration {
    return this.integration;
  }
}