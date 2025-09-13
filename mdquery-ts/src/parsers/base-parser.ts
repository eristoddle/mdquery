/**
 * Base markdown parser interface and common functionality
 */

import { ParsedContent, FileMetadata, FrontmatterEntry, Tag, Link, Heading } from '../core/types.js';
import { extractFrontmatter, extractHeadings, countWords, countLines } from '../core/utils.js';

export interface ParserOptions {
  /** Whether to parse Obsidian-specific features */
  parseObsidian?: boolean;
  /** Whether to extract tags from content */
  extractTags?: boolean;
  /** Whether to extract links */
  extractLinks?: boolean;
  /** Whether to parse frontmatter */
  parseFrontmatter?: boolean;
  /** Base path for resolving relative links */
  basePath?: string;
}

export abstract class BaseMarkdownParser {
  protected options: Required<ParserOptions>;

  constructor(options: ParserOptions = {}) {
    this.options = {
      parseObsidian: true,
      extractTags: true,
      extractLinks: true,
      parseFrontmatter: true,
      basePath: '',
      ...options
    };
  }

  /**
   * Parse a markdown file and extract all content
   */
  async parseFile(filePath: string, content: string, metadata: FileMetadata): Promise<ParsedContent> {
    const { frontmatter: frontmatterText, body } = extractFrontmatter(content);
    
    // Parse frontmatter
    const frontmatter = this.options.parseFrontmatter ? 
      await this.parseFrontmatter(frontmatterText) : {};
    const frontmatterEntries = this.options.parseFrontmatter ? 
      this.extractFrontmatterEntries(filePath, frontmatter) : [];

    // Extract headings
    const headings = extractHeadings(body);

    // Extract tags
    const tags = this.options.extractTags ? 
      await this.extractTags(filePath, body, frontmatter) : [];

    // Extract links
    const links = this.options.extractLinks ? 
      await this.extractLinks(filePath, body) : [];

    // Update metadata with parsed content info
    const updatedMetadata: FileMetadata = {
      ...metadata,
      wordCount: countWords(body),
      charCount: body.length,
      lineCount: countLines(content),
      hasFrontmatter: frontmatterText.length > 0,
      tagCount: tags.length,
      linkCount: links.length
    };

    return {
      metadata: updatedMetadata,
      content,
      frontmatter,
      frontmatterEntries,
      tags,
      links,
      bodyContent: body,
      headings
    };
  }

  /**
   * Parse YAML/JSON/TOML frontmatter
   */
  abstract parseFrontmatter(frontmatterText: string): Promise<Record<string, any>>;

  /**
   * Extract tags from content and frontmatter
   */
  abstract extractTags(filePath: string, content: string, frontmatter: Record<string, any>): Promise<Tag[]>;

  /**
   * Extract links from content
   */
  abstract extractLinks(filePath: string, content: string): Promise<Link[]>;

  /**
   * Convert frontmatter object to typed entries
   */
  protected extractFrontmatterEntries(filePath: string, frontmatter: Record<string, any>): FrontmatterEntry[] {
    const entries: FrontmatterEntry[] = [];

    for (const [key, value] of Object.entries(frontmatter)) {
      const { type, parsedValue } = this.inferFrontmatterType(value);
      
      entries.push({
        filePath,
        key,
        value: typeof value === 'string' ? value : JSON.stringify(value),
        type,
        parsedValue
      });
    }

    return entries;
  }

  /**
   * Infer the type of a frontmatter value
   */
  protected inferFrontmatterType(value: any): { type: FrontmatterEntry['type']; parsedValue: any } {
    if (value === null || value === undefined) {
      return { type: 'string', parsedValue: null };
    }

    if (typeof value === 'boolean') {
      return { type: 'boolean', parsedValue: value };
    }

    if (typeof value === 'number') {
      return { type: 'number', parsedValue: value };
    }

    if (Array.isArray(value)) {
      return { type: 'array', parsedValue: value };
    }

    if (typeof value === 'object') {
      return { type: 'object', parsedValue: value };
    }

    if (typeof value === 'string') {
      // Try to parse as date
      const dateRegex = /^\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2}(?:\.\d{3})?(?:Z|[+-]\d{2}:\d{2})?)?$/;
      if (dateRegex.test(value)) {
        const date = new Date(value);
        if (!isNaN(date.getTime())) {
          return { type: 'date', parsedValue: date };
        }
      }

      // Try to parse as number
      if (/^-?\d+(\.\d+)?$/.test(value)) {
        const num = parseFloat(value);
        if (!isNaN(num)) {
          return { type: 'number', parsedValue: num };
        }
      }

      // Try to parse as boolean
      if (value.toLowerCase() === 'true' || value.toLowerCase() === 'false') {
        return { type: 'boolean', parsedValue: value.toLowerCase() === 'true' };
      }
    }

    return { type: 'string', parsedValue: value };
  }

  /**
   * Resolve a relative link path
   */
  protected resolveLinkPath(target: string, basePath: string): string {
    if (target.startsWith('http://') || target.startsWith('https://') || target.startsWith('mailto:')) {
      return target;
    }

    if (target.startsWith('/')) {
      return target;
    }

    // Handle relative paths
    const baseDir = basePath.substring(0, basePath.lastIndexOf('/'));
    return `${baseDir}/${target}`.replace(/\/+/g, '/');
  }

  /**
   * Check if a link target is valid/exists
   */
  protected async isLinkValid(target: string, basePath: string): Promise<boolean> {
    // For now, just basic URL validation
    if (target.startsWith('http://') || target.startsWith('https://')) {
      return true;
    }

    // File existence checking would need to be implemented by the caller
    // since it depends on the file system adapter
    return false;
  }

  /**
   * Parse nested tags (tags with /)
   */
  protected parseNestedTag(tag: string): { isNested: boolean; parentTag?: string } {
    const parts = tag.split('/');
    if (parts.length > 1) {
      return {
        isNested: true,
        parentTag: parts.slice(0, -1).join('/')
      };
    }
    return { isNested: false };
  }
}