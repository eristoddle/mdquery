/**
 * Obsidian-specific markdown parser with support for wikilinks, callouts, embeds, etc.
 */

import { StandardMarkdownParser } from './markdown.js';
import { ParserOptions } from './base-parser.js';
import { 
  Tag, 
  Link, 
  ObsidianLink, 
  ObsidianCallout, 
  ObsidianEmbed, 
  ObsidianTemplate 
} from '../core/types.js';
import { 
  extractWikilinks, 
  isValidUrl 
} from '../core/utils.js';
import { OBSIDIAN_PATTERNS } from '../core/constants.js';

export class ObsidianMarkdownParser extends StandardMarkdownParser {
  constructor(options: ParserOptions = {}) {
    super({
      parseObsidian: true,
      ...options
    });
  }

  /**
   * Extract links including Obsidian wikilinks and embeds
   */
  async extractLinks(filePath: string, content: string): Promise<Link[]> {
    const links: Link[] = [];

    // Get standard markdown links first
    const standardLinks = await super.extractLinks(filePath, content);
    links.push(...standardLinks);

    if (!this.options.parseObsidian) {
      return links;
    }

    // Extract Obsidian wikilinks
    const wikilinks = extractWikilinks(content);
    
    for (const { target, text, lineNumber, section, blockId } of wikilinks) {
      const isValid = await this.isLinkValid(target, filePath);
      const resolvedPath = this.resolveObsidianLink(target, this.options.basePath || filePath);

      const obsidianLink: ObsidianLink = {
        filePath,
        target,
        text,
        type: 'wikilink',
        lineNumber,
        isValid,
        resolvedPath,
        section,
        blockId,
        isEmbed: false
      };

      links.push(obsidianLink);
    }

    // Extract embeds (![[...]])
    const embeds = this.extractEmbeds(content);
    
    for (const { target, text, lineNumber, section, blockId } of embeds) {
      const isValid = await this.isLinkValid(target, filePath);
      const resolvedPath = this.resolveObsidianLink(target, this.options.basePath || filePath);

      const embedLink: ObsidianLink = {
        filePath,
        target,
        text,
        type: 'wikilink',
        lineNumber,
        isValid,
        resolvedPath,
        section,
        blockId,
        isEmbed: true
      };

      links.push(embedLink);
    }

    return links;
  }

  /**
   * Extract Obsidian callouts
   */
  extractCallouts(content: string): ObsidianCallout[] {
    const callouts: ObsidianCallout[] = [];
    const lines = content.split('\n');
    
    let currentCallout: Partial<ObsidianCallout> | null = null;
    let currentContent: string[] = [];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const calloutMatch = line.match(OBSIDIAN_PATTERNS.CALLOUT);

      if (calloutMatch) {
        // Save previous callout if exists
        if (currentCallout) {
          callouts.push({
            ...currentCallout,
            content: currentContent.join('\n'),
            endLine: i
          } as ObsidianCallout);
        }

        // Start new callout
        const [, type, foldableMarker, title] = calloutMatch;
        currentCallout = {
          filePath: '', // Will be set by caller
          type: type.toLowerCase(),
          title: title?.trim(),
          startLine: i + 1,
          foldable: foldableMarker === '+' || foldableMarker === '-',
          folded: foldableMarker === '-'
        };
        currentContent = [];
      } else if (currentCallout && line.startsWith('>')) {
        // Continue callout content
        currentContent.push(line.substring(1).trim());
      } else if (currentCallout) {
        // End of callout
        callouts.push({
          ...currentCallout,
          content: currentContent.join('\n'),
          endLine: i
        } as ObsidianCallout);
        currentCallout = null;
        currentContent = [];
      }
    }

    // Handle callout at end of file
    if (currentCallout) {
      callouts.push({
        ...currentCallout,
        content: currentContent.join('\n'),
        endLine: lines.length
      } as ObsidianCallout);
    }

    return callouts;
  }

  /**
   * Extract Obsidian embeds
   */
  private extractEmbeds(content: string): Array<{ target: string; text: string; lineNumber: number; section?: string; blockId?: string }> {
    const embeds: Array<{ target: string; text: string; lineNumber: number; section?: string; blockId?: string }> = [];
    const lines = content.split('\n');
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const matches = Array.from(line.matchAll(OBSIDIAN_PATTERNS.EMBED));
      
      for (const match of matches) {
        const fullTarget = match[1];
        const { target, text, section, blockId } = this.parseWikilinkTarget(fullTarget);
        
        embeds.push({
          target,
          text,
          lineNumber: i + 1,
          section,
          blockId
        });
      }
    }
    
    return embeds;
  }

  /**
   * Extract Obsidian template variables
   */
  extractTemplates(content: string): ObsidianTemplate[] {
    const templates: ObsidianTemplate[] = [];
    const lines = content.split('\n');
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const matches = Array.from(line.matchAll(OBSIDIAN_PATTERNS.TEMPLATE_VAR));
      
      for (const match of matches) {
        const [, variable] = match;
        
        // Determine template type based on variable syntax
        let type: ObsidianTemplate['type'] = 'templater';
        if (variable.includes('date') || variable.includes('time')) {
          type = 'core-templates';
        } else if (variable.startsWith('dv.')) {
          type = 'dataview';
        }

        templates.push({
          filePath: '', // Will be set by caller
          variable: variable.trim(),
          value: match[0], // Full match including braces
          lineNumber: i + 1,
          type
        });
      }
    }
    
    return templates;
  }

  /**
   * Parse wikilink target to extract components
   */
  private parseWikilinkTarget(target: string): { target: string; text: string; section?: string; blockId?: string } {
    let filePart = target;
    let displayText = target;
    let section: string | undefined;
    let blockId: string | undefined;
    
    // Check for display text (|)
    const pipeSplit = target.split('|');
    if (pipeSplit.length > 1) {
      filePart = pipeSplit[0];
      displayText = pipeSplit[1];
    }
    
    // Check for block reference (^)
    const blockMatch = filePart.match(/^(.+)\^([a-zA-Z0-9-]+)$/);
    if (blockMatch) {
      filePart = blockMatch[1];
      blockId = blockMatch[2];
    }
    
    // Check for section reference (#)
    const sectionMatch = filePart.match(/^(.+)#(.+)$/);
    if (sectionMatch) {
      filePart = sectionMatch[1];
      section = sectionMatch[2];
    }
    
    return {
      target: filePart,
      text: displayText,
      section,
      blockId
    };
  }

  /**
   * Resolve Obsidian link to file path
   */
  private resolveObsidianLink(target: string, basePath: string): string {
    // Remove file extension if present for Obsidian-style resolution
    const cleanTarget = target.replace(/\.(md|markdown)$/, '');
    
    // In Obsidian, links are resolved relative to the vault root
    // For now, we'll use simple resolution - this could be enhanced
    // with actual vault structure knowledge
    return `${cleanTarget}.md`;
  }

  /**
   * Extract Dataview queries
   */
  extractDataviewQueries(content: string): Array<{ query: string; lineNumber: number; type: string }> {
    const queries: Array<{ query: string; lineNumber: number; type: string }> = [];
    const lines = content.split('\n');
    
    let inDataviewBlock = false;
    let currentQuery: string[] = [];
    let startLine = 0;
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      
      if (line.trim() === '```dataview') {
        inDataviewBlock = true;
        startLine = i + 1;
        currentQuery = [];
      } else if (line.trim() === '```' && inDataviewBlock) {
        inDataviewBlock = false;
        if (currentQuery.length > 0) {
          queries.push({
            query: currentQuery.join('\n'),
            lineNumber: startLine,
            type: 'dataview'
          });
        }
      } else if (inDataviewBlock) {
        currentQuery.push(line);
      }
    }
    
    return queries;
  }

  /**
   * Extract all Obsidian-specific features
   */
  async parseObsidianFeatures(filePath: string, content: string): Promise<{
    callouts: ObsidianCallout[];
    embeds: ObsidianEmbed[];
    templates: ObsidianTemplate[];
    dataviewQueries: Array<{ query: string; lineNumber: number; type: string }>;
  }> {
    const callouts = this.extractCallouts(content).map(c => ({ ...c, filePath }));
    const templates = this.extractTemplates(content).map(t => ({ ...t, filePath }));
    const dataviewQueries = this.extractDataviewQueries(content);
    
    // Convert embeds to proper format
    const embedsRaw = this.extractEmbeds(content);
    const embeds: ObsidianEmbed[] = embedsRaw.map(e => ({
      filePath,
      embedPath: e.target,
      section: e.section,
      blockId: e.blockId,
      lineNumber: e.lineNumber,
      displayText: e.text !== e.target ? e.text : undefined
    }));

    return {
      callouts,
      embeds,
      templates,
      dataviewQueries
    };
  }
}