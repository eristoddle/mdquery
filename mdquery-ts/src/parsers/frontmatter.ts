/**
 * Frontmatter parser for YAML, JSON, and TOML
 */

import * as yaml from 'js-yaml';

export class FrontmatterParser {
  /**
   * Parse frontmatter content based on format detection
   */
  static async parse(content: string): Promise<Record<string, any>> {
    if (!content.trim()) {
      return {};
    }

    // Try YAML first (most common)
    try {
      return FrontmatterParser.parseYaml(content);
    } catch {
      // Continue to other formats
    }

    // Try JSON
    try {
      return FrontmatterParser.parseJson(content);
    } catch {
      // Continue to other formats
    }

    // Try TOML (if available)
    try {
      return await FrontmatterParser.parseToml(content);
    } catch {
      // Return empty object if all parsing fails
    }

    // If all formats fail, return empty object
    console.warn('Failed to parse frontmatter, returning empty object');
    return {};
  }

  /**
   * Parse YAML frontmatter
   */
  static parseYaml(content: string): Record<string, any> {
    try {
      const result = yaml.load(content);
      return typeof result === 'object' && result !== null ? result as Record<string, any> : {};
    } catch (error) {
      throw new Error(`YAML parsing failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Parse JSON frontmatter
   */
  static parseJson(content: string): Record<string, any> {
    try {
      const result = JSON.parse(content);
      return typeof result === 'object' && result !== null ? result : {};
    } catch (error) {
      throw new Error(`JSON parsing failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Parse TOML frontmatter (requires toml library)
   */
  static async parseToml(content: string): Promise<Record<string, any>> {
    try {
      // Dynamic import to avoid bundling if not needed
      const toml = await import('toml');
      const result = toml.parse(content);
      return typeof result === 'object' && result !== null ? result : {};
    } catch (error) {
      throw new Error(`TOML parsing failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Detect frontmatter format based on content
   */
  static detectFormat(content: string): 'yaml' | 'json' | 'toml' | 'unknown' {
    const trimmed = content.trim();
    
    // JSON detection
    if (trimmed.startsWith('{') && trimmed.endsWith('}')) {
      return 'json';
    }

    // TOML detection (basic)
    if (trimmed.includes(' = ') || /\[.*\]/.test(trimmed)) {
      return 'toml';
    }

    // Default to YAML
    if (trimmed.includes(':')) {
      return 'yaml';
    }

    return 'unknown';
  }

  /**
   * Validate frontmatter content
   */
  static validate(content: string, format?: 'yaml' | 'json' | 'toml'): { valid: boolean; error?: string } {
    try {
      const detectedFormat = format || FrontmatterParser.detectFormat(content);
      
      switch (detectedFormat) {
        case 'yaml':
          FrontmatterParser.parseYaml(content);
          break;
        case 'json':
          FrontmatterParser.parseJson(content);
          break;
        case 'toml':
          // Note: This would require async validation for TOML
          break;
        default:
          return { valid: false, error: 'Unknown frontmatter format' };
      }
      
      return { valid: true };
    } catch (error) {
      return { 
        valid: false, 
        error: error instanceof Error ? error.message : 'Unknown error' 
      };
    }
  }
}