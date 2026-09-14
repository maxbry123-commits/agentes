/**
 * Pattern Matcher - Matches commands against rule patterns
 */

import * as path from 'path';
import * as fs from 'fs';
import * as os from 'os';
import { ParsedCommand, Rule, MatchResult, RuleType } from './types';

export class PatternMatcher {
  /**
   * Match a parsed command against a list of rules
   * Returns the best matching rule based on precedence
   */
  match(command: ParsedCommand, rules: Rule[]): MatchResult {
    const matches: MatchResult[] = [];
    
    // Try to match against each rule
    for (const rule of rules) {
      if (this.matchPattern(rule.pattern, command.normalized)) {
        // Calculate confidence based on specificity (0-1 scale)
        // Higher specificity = higher confidence
        const confidence = Math.min(rule.specificity / 100, 1);
        
        matches.push({
          matched: true,
          rule,
          confidence
        });
      }
    }
    
    // If no matches, return no match
    if (matches.length === 0) {
      return { matched: false, confidence: 0 };
    }
    
    // Select best match based on precedence
    return this.selectBestMatch(matches);
  }

  /**
   * Match a glob pattern against text
   * Supports * (zero or more chars) and ? (exactly one char)
   */
  private matchPattern(pattern: string, text: string): boolean {
    // Expand environment variables in pattern (e.g., $HOME, ${HOME})
    const expandedPattern = this.expandVariables(pattern);

    // Convert glob pattern to regex
    // Escape special regex characters except * and ?
    let regexPattern = expandedPattern
      .replace(/[.+^${}()|[\]\\]/g, '\\$&')  // Escape regex special chars
      .replace(/\*/g, '.*')                   // * matches zero or more chars
      .replace(/\?/g, '.');                   // ? matches exactly one char

    // Match full string (anchor at start and end)
    const regex = new RegExp(`^${regexPattern}$`);

    return regex.test(text);
  }

  /**
   * Expand environment variables in a string
   * Supports $VAR and ${VAR} formats
   */
  private expandVariables(str: string): string {
    let expanded = str;

    // Handle ${VAR} format
    expanded = expanded.replace(/\$\{([^}]+)\}/g, (match, varName) => {
      return process.env[varName] || match;
    });

    // Handle $VAR format (word boundary aware)
    expanded = expanded.replace(/\$([A-Za-z_][A-Za-z0-9_]*)/g, (match, varName) => {
      return process.env[varName] || match;
    });

    // Handle ~ for home directory
    if (expanded.startsWith('~/')) {
      expanded = path.join(os.homedir(), expanded.slice(2));
    } else if (expanded === '~') {
      expanded = os.homedir();
    }

    return expanded;
  }

  /**
   * Normalize a path for consistent matching
   * - Resolves symlinks
   * - Removes trailing slashes
   * - Converts to absolute path
   */
  private normalizePath(pathStr: string): string {
    try {
      // Resolve symlinks and get real path
      const realPath = fs.realpathSync(pathStr);
      
      // Remove trailing slash (except for root /)
      if (realPath.length > 1 && realPath.endsWith('/')) {
        return realPath.slice(0, -1);
      }
      
      return realPath;
    } catch (error) {
      // If path doesn't exist or can't be resolved, normalize without resolving
      const normalized = path.normalize(pathStr);
      
      // Remove trailing slash (except for root /)
      if (normalized.length > 1 && normalized.endsWith('/')) {
        return normalized.slice(0, -1);
      }
      
      return normalized;
    }
  }

  /**
   * Select the best match from multiple matching rules
   * Precedence order:
   * 1. Rule type: BLOCK > CONFIRM > ALLOW
   * 2. Specificity: Higher specificity wins
   * 3. Source: PROJECT > USER > GLOBAL
   */
  private selectBestMatch(matches: MatchResult[]): MatchResult {
    if (matches.length === 0) {
      return { matched: false, confidence: 0 };
    }
    
    if (matches.length === 1) {
      return matches[0];
    }
    
    // Sort by precedence
    // Precedence order:
    // 1. BLOCK always wins (security-first)
    // 2. Between CONFIRM and ALLOW, more specific rule wins
    // 3. If same specificity, CONFIRM > ALLOW
    // 4. If same type and specificity, PROJECT > USER > GLOBAL
    const sorted = [...matches].sort((a, b) => {
      const ruleA = a.rule!;
      const ruleB = b.rule!;

      const typePrecedence = {
        [RuleType.BLOCK]: 3,
        [RuleType.CONFIRM]: 2,
        [RuleType.ALLOW]: 1,
        [RuleType.PROTECT]: 0,
        [RuleType.SANDBOX]: 0
      };

      // 1. BLOCK always wins over non-BLOCK
      if (ruleA.type === RuleType.BLOCK && ruleB.type !== RuleType.BLOCK) {
        return -1;
      }
      if (ruleB.type === RuleType.BLOCK && ruleA.type !== RuleType.BLOCK) {
        return 1;
      }

      // 2. For same type rules, higher specificity wins
      if (ruleA.type === ruleB.type) {
        const specificityComparison = ruleB.specificity - ruleA.specificity;
        if (specificityComparison !== 0) {
          return specificityComparison;
        }
      }

      // 3. For CONFIRM vs ALLOW, specificity wins first
      // This allows specific ALLOW rules to bypass general CONFIRM rules
      if ((ruleA.type === RuleType.CONFIRM || ruleA.type === RuleType.ALLOW) &&
          (ruleB.type === RuleType.CONFIRM || ruleB.type === RuleType.ALLOW)) {
        const specificityComparison = ruleB.specificity - ruleA.specificity;
        if (specificityComparison !== 0) {
          return specificityComparison;
        }
        // If same specificity, CONFIRM > ALLOW
        const typeComparison = typePrecedence[ruleB.type] - typePrecedence[ruleA.type];
        if (typeComparison !== 0) {
          return typeComparison;
        }
      }

      // 4. Source precedence: PROJECT > USER > GLOBAL
      const sourcePrecedence = {
        'project': 3,
        'user': 2,
        'global': 1
      };

      return sourcePrecedence[ruleB.source] - sourcePrecedence[ruleA.source];
    });
    
    return sorted[0];
  }
}
