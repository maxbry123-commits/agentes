/**
 * Rule Parser - Loads and parses .agentguard rule files
 */

import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { Rule, RuleType, RuleSource, ParseResult, ParseError } from './types';

export class RuleParser {
  /**
   * Parse a single rule file
   */
  parse(filePath: string, source: RuleSource): ParseResult {
    const rules: Rule[] = [];
    const errors: ParseError[] = [];

    // Check if file exists
    if (!fs.existsSync(filePath)) {
      // Not an error - just return empty result
      return { rules, errors };
    }

    try {
      const content = fs.readFileSync(filePath, 'utf-8');
      const lines = content.split('\n');

      for (let i = 0; i < lines.length; i++) {
        const lineNumber = i + 1;
        const line = lines[i].trim();

        // Skip blank lines
        if (line === '') {
          continue;
        }

        // Skip comments
        if (line.startsWith('#')) {
          continue;
        }

        // Try to parse the rule
        try {
          const rule = this.parseLine(line, source, lineNumber);
          if (rule) {
            rules.push(rule);
          }
        } catch (error) {
          // Record error but continue parsing
          errors.push({
            line: lineNumber,
            message: error instanceof Error ? error.message : String(error),
            source
          });
        }
      }
    } catch (error) {
      // File read error - add to errors
      errors.push({
        line: 0,
        message: `Cannot read file: ${error instanceof Error ? error.message : String(error)}`,
        source
      });
    }

    return { rules, errors };
  }

  /**
   * Parse a single line into a Rule
   */
  private parseLine(line: string, source: RuleSource, lineNumber: number): Rule | null {
    // BLOCK rule: !pattern
    if (line.startsWith('!')) {
      const pattern = line.substring(1).trim();
      if (!pattern) {
        throw new Error('BLOCK rule missing pattern');
      }
      return {
        type: RuleType.BLOCK,
        pattern,
        source,
        lineNumber,
        specificity: this.calculateSpecificity(pattern)
      };
    }

    // CONFIRM rule: ?pattern
    if (line.startsWith('?')) {
      const pattern = line.substring(1).trim();
      if (!pattern) {
        throw new Error('CONFIRM rule missing pattern');
      }
      return {
        type: RuleType.CONFIRM,
        pattern,
        source,
        lineNumber,
        specificity: this.calculateSpecificity(pattern)
      };
    }

    // ALLOW rule: +pattern
    if (line.startsWith('+')) {
      const pattern = line.substring(1).trim();
      if (!pattern) {
        throw new Error('ALLOW rule missing pattern');
      }
      return {
        type: RuleType.ALLOW,
        pattern,
        source,
        lineNumber,
        specificity: this.calculateSpecificity(pattern)
      };
    }

    // PROTECT directive: @protect path
    if (line.startsWith('@protect')) {
      const pathPart = line.substring('@protect'.length).trim();
      if (!pathPart) {
        throw new Error('PROTECT directive missing path');
      }
      return {
        type: RuleType.PROTECT,
        pattern: pathPart,
        source,
        lineNumber,
        specificity: this.calculateSpecificity(pathPart),
        metadata: { path: pathPart }
      };
    }

    // SANDBOX directive: @sandbox path
    if (line.startsWith('@sandbox')) {
      const pathPart = line.substring('@sandbox'.length).trim();
      if (!pathPart) {
        throw new Error('SANDBOX directive missing path');
      }
      return {
        type: RuleType.SANDBOX,
        pattern: pathPart,
        source,
        lineNumber,
        specificity: this.calculateSpecificity(pathPart),
        metadata: { path: pathPart }
      };
    }

    // Invalid rule syntax
    throw new Error(`Invalid rule syntax: ${line}`);
  }

  /**
   * Calculate rule specificity based on pattern complexity
   * Higher specificity = more specific pattern
   */
  private calculateSpecificity(pattern: string): number {
    let score = 0;

    // Base score for each literal character
    for (const char of pattern) {
      if (char === '*') {
        // Wildcard matches anything - no specificity
        score += 0;
      } else if (char === '?') {
        // Single char wildcard - some specificity
        score += 0.5;
      } else {
        // Literal character - high specificity
        score += 1;
      }
    }

    // Bonus for absolute paths
    if (pattern.startsWith('/')) {
      score += 10;
    }

    return score;
  }

  /**
   * Load rules from all standard locations and merge with precedence
   */
  loadAll(): Rule[] {
    const allRules: Rule[] = [];

    // Load from global location
    const globalPath = '/etc/agentguard/rules';
    const globalResult = this.parse(globalPath, RuleSource.GLOBAL);
    allRules.push(...globalResult.rules);
    this.logErrors(globalResult.errors);

    // Load from user location
    const userPath = path.join(os.homedir(), '.config', 'agentguard', 'rules');
    const userResult = this.parse(userPath, RuleSource.USER);
    allRules.push(...userResult.rules);
    this.logErrors(userResult.errors);

    // Load from project location
    const projectPath = path.join(process.cwd(), '.agentguard');
    const projectResult = this.parse(projectPath, RuleSource.PROJECT);
    allRules.push(...projectResult.rules);
    this.logErrors(projectResult.errors);

    // Merge rules with precedence
    return this.mergeRules(allRules);
  }

  /**
   * Merge rules with precedence: rule type (BLOCK > CONFIRM > ALLOW), then specificity, then source (project > user > global)
   * For identical patterns, keep only the rule with highest precedence
   */
  private mergeRules(rules: Rule[]): Rule[] {
    // Group rules by pattern
    const patternGroups = new Map<string, Rule[]>();
    
    for (const rule of rules) {
      const pattern = rule.pattern;
      if (!patternGroups.has(pattern)) {
        patternGroups.set(pattern, []);
      }
      patternGroups.get(pattern)!.push(rule);
    }

    // For each pattern group, select the winner based on precedence
    const winners: Rule[] = [];
    
    for (const [pattern, groupRules] of patternGroups) {
      // Define type precedence order (higher number = higher precedence)
      const typePrecedence = {
        [RuleType.BLOCK]: 3,
        [RuleType.CONFIRM]: 2,
        [RuleType.ALLOW]: 1,
        [RuleType.PROTECT]: 0,
        [RuleType.SANDBOX]: 0
      };

      // Define source precedence order (higher number = higher precedence)
      const sourcePrecedence = {
        [RuleSource.PROJECT]: 3,
        [RuleSource.USER]: 2,
        [RuleSource.GLOBAL]: 1
      };

      // Sort rules by precedence: type (desc), then source (desc), then specificity (desc)
      const sortedRules = groupRules.sort((a, b) => {
        // First, compare by type precedence
        const typeDiff = typePrecedence[b.type] - typePrecedence[a.type];
        if (typeDiff !== 0) return typeDiff;

        // If types are equal, compare by source precedence
        const sourceDiff = sourcePrecedence[b.source] - sourcePrecedence[a.source];
        if (sourceDiff !== 0) return sourceDiff;

        // If sources are equal, compare by specificity
        return b.specificity - a.specificity;
      });

      // The first rule after sorting is the winner
      winners.push(sortedRules[0]);
    }

    return winners;
  }

  /**
   * Log parse errors to stderr
   */
  private logErrors(errors: ParseError[]): void {
    for (const error of errors) {
      if (error.line === 0) {
        // File-level error
        console.error(`Warning: ${error.message} (${error.source})`);
      } else {
        // Line-level error
        console.error(`Warning: Invalid rule syntax at line ${error.line} in ${error.source}: ${error.message}`);
      }
    }
  }
}
