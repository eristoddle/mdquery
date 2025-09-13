/**
 * Parser factory for creating appropriate parsers based on system type
 */

import { BaseMarkdownParser, ParserOptions } from './base-parser.js';
import { StandardMarkdownParser } from './markdown.js';
import { ObsidianMarkdownParser } from './obsidian.js';
import { MDQueryConfig } from '../core/types.js';

export type ParserType = 'standard' | 'obsidian' | 'joplin' | 'jekyll';

export class ParserFactory {
  /**
   * Create a parser based on system type
   */
  static createParser(systemType: ParserType, options: ParserOptions = {}): BaseMarkdownParser {
    switch (systemType) {
      case 'obsidian':
        return new ObsidianMarkdownParser({
          parseObsidian: true,
          ...options
        });
      
      case 'joplin':
        return new StandardMarkdownParser({
          parseObsidian: false,
          ...options
        });
      
      case 'jekyll':
        return new StandardMarkdownParser({
          parseObsidian: false,
          parseFrontmatter: true,
          ...options
        });
      
      case 'standard':
      default:
        return new StandardMarkdownParser(options);
    }
  }

  /**
   * Create parser from config
   */
  static createFromConfig(config: MDQueryConfig): BaseMarkdownParser {
    const options: ParserOptions = {
      parseObsidian: config.parseObsidian,
      extractTags: true,
      extractLinks: true,
      parseFrontmatter: true,
      basePath: config.notesDir
    };

    return ParserFactory.createParser(config.systemType as ParserType, options);
  }

  /**
   * Get supported parser types
   */
  static getSupportedTypes(): ParserType[] {
    return ['standard', 'obsidian', 'joplin', 'jekyll'];
  }

  /**
   * Get parser capabilities
   */
  static getParserCapabilities(type: ParserType): {
    frontmatter: boolean;
    tags: boolean;
    links: boolean;
    wikilinks: boolean;
    callouts: boolean;
    embeds: boolean;
    templates: boolean;
    features: string[];
  } {
    switch (type) {
      case 'obsidian':
        return {
          frontmatter: true,
          tags: true,
          links: true,
          wikilinks: true,
          callouts: true,
          embeds: true,
          templates: true,
          features: [
            'yaml-frontmatter',
            'json-frontmatter',
            'inline-tags',
            'frontmatter-tags',
            'markdown-links',
            'wikilinks',
            'callouts',
            'embeds',
            'templates',
            'dataview-queries',
            'block-references',
            'section-references'
          ]
        };
      
      case 'joplin':
        return {
          frontmatter: false,
          tags: true,
          links: true,
          wikilinks: false,
          callouts: false,
          embeds: false,
          templates: false,
          features: [
            'inline-tags',
            'markdown-links',
            'joplin-tags'
          ]
        };
      
      case 'jekyll':
        return {
          frontmatter: true,
          tags: true,
          links: true,
          wikilinks: false,
          callouts: false,
          embeds: false,
          templates: false,
          features: [
            'yaml-frontmatter',
            'frontmatter-tags',
            'frontmatter-categories',
            'markdown-links',
            'liquid-templates'
          ]
        };
      
      case 'standard':
      default:
        return {
          frontmatter: true,
          tags: true,
          links: true,
          wikilinks: false,
          callouts: false,
          embeds: false,
          templates: false,
          features: [
            'yaml-frontmatter',
            'json-frontmatter',
            'toml-frontmatter',
            'inline-tags',
            'frontmatter-tags',
            'markdown-links',
            'reference-links'
          ]
        };
    }
  }
}

export * from './base-parser.js';
export * from './frontmatter.js';
export * from './markdown.js';
export * from './obsidian.js';