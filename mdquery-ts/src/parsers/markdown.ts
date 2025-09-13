/**
 * Standard markdown parser using marked library
 */

import { marked } from 'marked';
import { BaseMarkdownParser, ParserOptions } from './base-parser.js';
import { FrontmatterParser } from './frontmatter.js';
import { Tag, Link } from '../core/types.js';
import { 
  extractTagsFromContent, 
  extractMarkdownLinks, 
  isValidUrl 
} from '../core/utils.js';

export class StandardMarkdownParser extends BaseMarkdownParser {
  private markedInstance: typeof marked;

  constructor(options: ParserOptions = {}) {
    super(options);
    
    // Configure marked instance
    this.markedInstance = new marked.Marked({
      gfm: true,
      breaks: false,
      pedantic: false
    });
  }

  /**
   * Parse frontmatter using the frontmatter parser
   */
  async parseFrontmatter(frontmatterText: string): Promise<Record<string, any>> {
    return FrontmatterParser.parse(frontmatterText);
  }

  /**
   * Extract tags from content and frontmatter
   */
  async extractTags(filePath: string, content: string, frontmatter: Record<string, any>): Promise<Tag[]> {
    const tags: Tag[] = [];

    // Extract tags from frontmatter
    if (frontmatter.tags) {
      const fmTags = Array.isArray(frontmatter.tags) ? frontmatter.tags : [frontmatter.tags];
      
      for (const tag of fmTags) {
        const tagStr = String(tag);
        const { isNested, parentTag } = this.parseNestedTag(tagStr);
        
        tags.push({
          filePath,
          tag: tagStr,
          source: 'frontmatter',
          isNested,
          parentTag
        });
      }
    }

    // Check for other frontmatter fields that might contain tags
    for (const [key, value] of Object.entries(frontmatter)) {
      if (key.toLowerCase().includes('tag') && key !== 'tags' && Array.isArray(value)) {
        for (const tag of value) {
          const tagStr = String(tag);
          const { isNested, parentTag } = this.parseNestedTag(tagStr);
          
          tags.push({
            filePath,
            tag: tagStr,
            source: 'frontmatter',
            isNested,
            parentTag
          });
        }
      }
    }

    // Extract tags from content
    const contentTags = extractTagsFromContent(content);
    for (const { tag, lineNumber } of contentTags) {
      const { isNested, parentTag } = this.parseNestedTag(tag);
      
      tags.push({
        filePath,
        tag,
        source: 'content',
        lineNumber,
        isNested,
        parentTag
      });
    }

    return tags;
  }

  /**
   * Extract markdown links from content
   */
  async extractLinks(filePath: string, content: string): Promise<Link[]> {
    const links: Link[] = [];

    // Extract standard markdown links
    const markdownLinks = extractMarkdownLinks(content);
    
    for (const { target, text, lineNumber } of markdownLinks) {
      const linkType = this.determineLinkType(target);
      const isValid = await this.isLinkValid(target, filePath);
      const resolvedPath = linkType === 'external' ? undefined : 
        this.resolveLinkPath(target, this.options.basePath || filePath);

      links.push({
        filePath,
        target,
        text,
        type: linkType,
        lineNumber,
        isValid,
        resolvedPath
      });
    }

    // Extract reference links
    const referenceLinks = this.extractReferenceLinks(content);
    
    for (const { target, text, lineNumber } of referenceLinks) {
      const linkType = this.determineLinkType(target);
      const isValid = await this.isLinkValid(target, filePath);
      const resolvedPath = linkType === 'external' ? undefined : 
        this.resolveLinkPath(target, this.options.basePath || filePath);

      links.push({
        filePath,
        target,
        text,
        type: 'reference',
        lineNumber,
        isValid,
        resolvedPath
      });
    }

    return links;
  }

  /**
   * Determine the type of a link
   */
  private determineLinkType(target: string): Link['type'] {
    if (isValidUrl(target)) {
      return 'external';
    }

    if (target.startsWith('#')) {
      return 'reference';
    }

    return 'markdown';
  }

  /**
   * Extract reference links from content
   */
  private extractReferenceLinks(content: string): Array<{ target: string; text: string; lineNumber: number }> {
    const links: Array<{ target: string; text: string; lineNumber: number }> = [];
    const lines = content.split('\n');
    
    // Pattern for reference link definitions: [label]: url "title"
    const refPattern = /^\s*\[([^\]]+)\]:\s*(.+?)(?:\s+"([^"]*)")?\s*$/;
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const match = line.match(refPattern);
      
      if (match) {
        const [, text, target] = match;
        links.push({
          text: text.trim(),
          target: target.trim(),
          lineNumber: i + 1
        });
      }
    }

    return links;
  }

  /**
   * Parse markdown to AST (useful for advanced parsing)
   */
  async parseToAST(content: string): Promise<any> {
    return this.markedInstance.lexer(content);
  }

  /**
   * Convert markdown to HTML
   */
  async parseToHTML(content: string): Promise<string> {
    return this.markedInstance.parse(content);
  }

  /**
   * Extract all text from markdown (strip formatting)
   */
  extractPlainText(content: string): string {
    // Remove code blocks
    let text = content.replace(/```[\s\S]*?```/g, '');
    
    // Remove inline code
    text = text.replace(/`[^`]+`/g, '');
    
    // Remove links but keep text
    text = text.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1');
    
    // Remove images
    text = text.replace(/!\[([^\]]*)\]\([^)]+\)/g, '$1');
    
    // Remove bold/italic
    text = text.replace(/\*\*([^*]+)\*\*/g, '$1');
    text = text.replace(/\*([^*]+)\*/g, '$1');
    text = text.replace(/__([^_]+)__/g, '$1');
    text = text.replace(/_([^_]+)_/g, '$1');
    
    // Remove headings markers
    text = text.replace(/^#{1,6}\s+/gm, '');
    
    // Remove horizontal rules
    text = text.replace(/^---+$/gm, '');
    
    // Remove blockquotes
    text = text.replace(/^>\s*/gm, '');
    
    // Clean up extra whitespace
    text = text.replace(/\n{3,}/g, '\n\n');
    
    return text.trim();
  }
}