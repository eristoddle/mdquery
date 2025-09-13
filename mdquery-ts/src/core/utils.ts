/**
 * Utility functions for MDQuery
 */

import * as crypto from 'crypto';
import { OBSIDIAN_PATTERNS, MARKDOWN_PATTERNS } from './constants.js';

/**
 * Generate MD5 hash of string content
 */
export function generateContentHash(content: string): string {
  if (typeof crypto !== 'undefined' && crypto.createHash) {
    // Node.js environment
    return crypto.createHash('md5').update(content).digest('hex');
  } else if (typeof window !== 'undefined' && window.crypto && window.crypto.subtle) {
    // Browser environment - this is async, but we'll provide a sync fallback
    throw new Error('Use generateContentHashAsync in browser environment');
  } else {
    // Fallback simple hash for browser
    return simpleHash(content);
  }
}

/**
 * Generate content hash asynchronously (for browser)
 */
export async function generateContentHashAsync(content: string): Promise<string> {
  if (typeof window !== 'undefined' && window.crypto && window.crypto.subtle) {
    const encoder = new TextEncoder();
    const data = encoder.encode(content);
    const hashBuffer = await window.crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  } else {
    return generateContentHash(content);
  }
}

/**
 * Simple hash function for browser fallback
 */
function simpleHash(str: string): string {
  let hash = 0;
  if (str.length === 0) return hash.toString();
  
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  
  return Math.abs(hash).toString(16);
}

/**
 * Extract file name without extension
 */
export function getFileNameWithoutExtension(filePath: string): string {
  const fileName = filePath.split('/').pop() || '';
  const lastDot = fileName.lastIndexOf('.');
  return lastDot > 0 ? fileName.substring(0, lastDot) : fileName;
}

/**
 * Get file extension from path
 */
export function getFileExtension(filePath: string): string {
  const fileName = filePath.split('/').pop() || '';
  const lastDot = fileName.lastIndexOf('.');
  return lastDot > 0 ? fileName.substring(lastDot) : '';
}

/**
 * Normalize path separators and resolve relative paths
 */
export function normalizePath(path: string): string {
  return path.replace(/\\/g, '/').replace(/\/+/g, '/');
}

/**
 * Get relative path from base directory
 */
export function getRelativePath(fullPath: string, basePath: string): string {
  const normalizedFull = normalizePath(fullPath);
  const normalizedBase = normalizePath(basePath);
  
  if (normalizedFull.startsWith(normalizedBase)) {
    return normalizedFull.substring(normalizedBase.length).replace(/^\//, '');
  }
  
  return normalizedFull;
}

/**
 * Extract frontmatter from markdown content
 */
export function extractFrontmatter(content: string): { frontmatter: string; body: string } {
  const match = content.match(MARKDOWN_PATTERNS.FRONTMATTER);
  
  if (match) {
    return {
      frontmatter: match[1],
      body: content.substring(match[0].length).trim()
    };
  }
  
  return {
    frontmatter: '',
    body: content
  };
}

/**
 * Count words in text
 */
export function countWords(text: string): number {
  // Remove code blocks and inline code first
  const withoutCode = text
    .replace(MARKDOWN_PATTERNS.CODE_BLOCK, '')
    .replace(MARKDOWN_PATTERNS.INLINE_CODE, '');
  
  // Split by whitespace and filter empty strings
  const words = withoutCode
    .trim()
    .split(/\s+/)
    .filter(word => word.length > 0);
  
  return words.length;
}

/**
 * Count lines in text
 */
export function countLines(text: string): number {
  if (!text) return 0;
  return text.split('\n').length;
}

/**
 * Extract headings from markdown content
 */
export function extractHeadings(content: string): Array<{ text: string; level: number; lineNumber: number; id: string }> {
  const headings: Array<{ text: string; level: number; lineNumber: number; id: string }> = [];
  const lines = content.split('\n');
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const match = line.match(/^(#{1,6})\s+(.+)$/);
    
    if (match) {
      const level = match[1].length;
      const text = match[2].trim();
      const id = generateHeadingId(text);
      
      headings.push({
        text,
        level,
        lineNumber: i + 1,
        id
      });
    }
  }
  
  return headings;
}

/**
 * Generate heading ID for anchor links
 */
export function generateHeadingId(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, '') // Remove special characters
    .replace(/\s+/g, '-') // Replace spaces with hyphens
    .replace(/-+/g, '-') // Replace multiple hyphens with single
    .replace(/^-|-$/g, ''); // Remove leading/trailing hyphens
}

/**
 * Extract tags from text content
 */
export function extractTagsFromContent(content: string): Array<{ tag: string; lineNumber: number }> {
  const tags: Array<{ tag: string; lineNumber: number }> = [];
  const lines = content.split('\n');
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const matches = Array.from(line.matchAll(MARKDOWN_PATTERNS.TAG));
    
    for (const match of matches) {
      tags.push({
        tag: match[1],
        lineNumber: i + 1
      });
    }
  }
  
  return tags;
}

/**
 * Extract markdown links from content
 */
export function extractMarkdownLinks(content: string): Array<{ target: string; text: string; lineNumber: number }> {
  const links: Array<{ target: string; text: string; lineNumber: number }> = [];
  const lines = content.split('\n');
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const matches = Array.from(line.matchAll(MARKDOWN_PATTERNS.LINK));
    
    for (const match of matches) {
      links.push({
        text: match[1],
        target: match[2],
        lineNumber: i + 1
      });
    }
  }
  
  return links;
}

/**
 * Extract Obsidian wikilinks from content
 */
export function extractWikilinks(content: string): Array<{ target: string; text: string; lineNumber: number; section?: string; blockId?: string }> {
  const links: Array<{ target: string; text: string; lineNumber: number; section?: string; blockId?: string }> = [];
  const lines = content.split('\n');
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const matches = Array.from(line.matchAll(OBSIDIAN_PATTERNS.WIKILINK));
    
    for (const match of matches) {
      const fullTarget = match[1];
      const { target, text, section, blockId } = parseWikilinkTarget(fullTarget);
      
      links.push({
        target,
        text,
        lineNumber: i + 1,
        section,
        blockId
      });
    }
  }
  
  return links;
}

/**
 * Parse wikilink target to extract file, section, and block references
 */
function parseWikilinkTarget(target: string): { target: string; text: string; section?: string; blockId?: string } {
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
 * Check if a string is a valid URL
 */
export function isValidUrl(string: string): boolean {
  try {
    new URL(string);
    return true;
  } catch {
    return false;
  }
}

/**
 * Sanitize SQL input to prevent injection
 */
export function sanitizeSqlInput(input: string): string {
  // Basic sanitization - remove or escape dangerous characters
  return input
    .replace(/'/g, "''") // Escape single quotes
    .replace(/;/g, '') // Remove semicolons
    .replace(/--/g, '') // Remove SQL comments
    .replace(/\/\*/g, '') // Remove block comment start
    .replace(/\*\//g, ''); // Remove block comment end
}

/**
 * Debounce function for performance optimization
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | number | undefined;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeout as NodeJS.Timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

/**
 * Throttle function for performance optimization
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean;
  
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

/**
 * Deep clone an object
 */
export function deepClone<T>(obj: T): T {
  if (obj === null || typeof obj !== 'object') {
    return obj;
  }
  
  if (obj instanceof Date) {
    return new Date(obj.getTime()) as T;
  }
  
  if (obj instanceof Array) {
    return obj.map(item => deepClone(item)) as T;
  }
  
  if (typeof obj === 'object') {
    const clonedObj = {} as { [key: string]: any };
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        clonedObj[key] = deepClone(obj[key]);
      }
    }
    return clonedObj as T;
  }
  
  return obj;
}