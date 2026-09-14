/**
 * Unit tests for PatternMatcher
 */

import { describe, test, expect } from 'vitest';
import { PatternMatcher } from '../../src/pattern-matcher';
import { ParsedCommand, Rule, RuleType, RuleSource } from '../../src/types';

describe('PatternMatcher', () => {
  const matcher = new PatternMatcher();

  // Helper to create a simple parsed command
  const createCommand = (normalized: string): ParsedCommand => ({
    original: normalized,
    normalized,
    tokens: [],
    segments: [],
    isChained: false,
    isPiped: false
  });

  // Helper to create a rule
  const createRule = (
    type: RuleType,
    pattern: string,
    specificity: number = 10,
    source: RuleSource = RuleSource.PROJECT
  ): Rule => ({
    type,
    pattern,
    source,
    lineNumber: 1,
    specificity
  });

  describe('matchPattern - wildcards', () => {
    test('matches literal patterns exactly', () => {
      const command = createCommand('rm -rf /');
      const rules = [createRule(RuleType.BLOCK, 'rm -rf /')];
      
      const result = matcher.match(command, rules);
      
      expect(result.matched).toBe(true);
      expect(result.rule?.pattern).toBe('rm -rf /');
    });

    test('matches * wildcard for zero or more characters', () => {
      const command = createCommand('rm -rf node_modules');
      const rules = [createRule(RuleType.ALLOW, 'rm -rf *')];
      
      const result = matcher.match(command, rules);
      
      expect(result.matched).toBe(true);
      expect(result.rule?.pattern).toBe('rm -rf *');
    });

    test('matches ? wildcard for exactly one character', () => {
      const command = createCommand('rm -rf a');
      const rules = [createRule(RuleType.BLOCK, 'rm -rf ?')];
      
      const result = matcher.match(command, rules);
      
      expect(result.matched).toBe(true);
    });

    test('does not match ? wildcard for zero characters', () => {
      const command = createCommand('rm -rf ');
      const rules = [createRule(RuleType.BLOCK, 'rm -rf ?')];
      
      const result = matcher.match(command, rules);
      
      expect(result.matched).toBe(false);
    });

    test('does not match ? wildcard for multiple characters', () => {
      const command = createCommand('rm -rf abc');
      const rules = [createRule(RuleType.BLOCK, 'rm -rf ?')];
      
      const result = matcher.match(command, rules);
      
      expect(result.matched).toBe(false);
    });

    test('matches multiple wildcards in pattern', () => {
      const command = createCommand('git push origin main --force');
      const rules = [createRule(RuleType.CONFIRM, 'git push * --force')];
      
      const result = matcher.match(command, rules);
      
      expect(result.matched).toBe(true);
    });
  });

  describe('rule precedence - type', () => {
    test('BLOCK takes precedence over ALLOW', () => {
      const command = createCommand('rm -rf /tmp');
      const rules = [
        createRule(RuleType.ALLOW, 'rm -rf *', 5),
        createRule(RuleType.BLOCK, 'rm -rf *', 5)
      ];
      
      const result = matcher.match(command, rules);
      
      expect(result.matched).toBe(true);
      expect(result.rule?.type).toBe(RuleType.BLOCK);
    });

    test('BLOCK takes precedence over CONFIRM', () => {
      const command = createCommand('rm -rf /tmp');
      const rules = [
        createRule(RuleType.CONFIRM, 'rm -rf *', 5),
        createRule(RuleType.BLOCK, 'rm -rf *', 5)
      ];
      
      const result = matcher.match(command, rules);
      
      expect(result.matched).toBe(true);
      expect(result.rule?.type).toBe(RuleType.BLOCK);
    });

    test('CONFIRM takes precedence over ALLOW', () => {
      const command = createCommand('rm -rf /tmp');
      const rules = [
        createRule(RuleType.ALLOW, 'rm -rf *', 5),
        createRule(RuleType.CONFIRM, 'rm -rf *', 5)
      ];
      
      const result = matcher.match(command, rules);
      
      expect(result.matched).toBe(true);
      expect(result.rule?.type).toBe(RuleType.CONFIRM);
    });
  });

  describe('rule precedence - specificity', () => {
    test('higher specificity wins with same type', () => {
      const command = createCommand('rm -rf /tmp');
      const rules = [
        createRule(RuleType.BLOCK, 'rm -rf *', 5),
        createRule(RuleType.BLOCK, 'rm -rf /tmp', 10)
      ];
      
      const result = matcher.match(command, rules);
      
      expect(result.matched).toBe(true);
      expect(result.rule?.pattern).toBe('rm -rf /tmp');
      expect(result.rule?.specificity).toBe(10);
    });

    test('BLOCK always wins over ALLOW regardless of specificity', () => {
      const command = createCommand('rm -rf /tmp');
      const rules = [
        createRule(RuleType.ALLOW, 'rm -rf /tmp', 20),
        createRule(RuleType.BLOCK, 'rm -rf *', 5)
      ];

      const result = matcher.match(command, rules);

      expect(result.matched).toBe(true);
      expect(result.rule?.type).toBe(RuleType.BLOCK);
      expect(result.rule?.specificity).toBe(5);
    });

    test('specific ALLOW beats general CONFIRM', () => {
      const command = createCommand('rm -rf /tmp/node_modules');
      const rules = [
        createRule(RuleType.CONFIRM, 'rm -rf *', 5),
        createRule(RuleType.ALLOW, 'rm -rf */node_modules', 20)
      ];

      const result = matcher.match(command, rules);

      expect(result.matched).toBe(true);
      expect(result.rule?.type).toBe(RuleType.ALLOW);
      expect(result.rule?.specificity).toBe(20);
    });

    test('CONFIRM wins over ALLOW with same specificity', () => {
      const command = createCommand('rm -rf /tmp');
      const rules = [
        createRule(RuleType.ALLOW, 'rm -rf *', 5),
        createRule(RuleType.CONFIRM, 'rm -rf *', 5)
      ];

      const result = matcher.match(command, rules);

      expect(result.matched).toBe(true);
      expect(result.rule?.type).toBe(RuleType.CONFIRM);
    });
  });

  describe('rule precedence - source', () => {
    test('PROJECT source takes precedence over USER', () => {
      const command = createCommand('rm -rf /tmp');
      const rules = [
        createRule(RuleType.BLOCK, 'rm -rf *', 5, RuleSource.USER),
        createRule(RuleType.BLOCK, 'rm -rf *', 5, RuleSource.PROJECT)
      ];
      
      const result = matcher.match(command, rules);
      
      expect(result.matched).toBe(true);
      expect(result.rule?.source).toBe(RuleSource.PROJECT);
    });

    test('USER source takes precedence over GLOBAL', () => {
      const command = createCommand('rm -rf /tmp');
      const rules = [
        createRule(RuleType.BLOCK, 'rm -rf *', 5, RuleSource.GLOBAL),
        createRule(RuleType.BLOCK, 'rm -rf *', 5, RuleSource.USER)
      ];
      
      const result = matcher.match(command, rules);
      
      expect(result.matched).toBe(true);
      expect(result.rule?.source).toBe(RuleSource.USER);
    });

    test('type and specificity precedence override source', () => {
      const command = createCommand('rm -rf /tmp');
      const rules = [
        createRule(RuleType.ALLOW, 'rm -rf *', 5, RuleSource.PROJECT),
        createRule(RuleType.BLOCK, 'rm -rf *', 5, RuleSource.GLOBAL)
      ];
      
      const result = matcher.match(command, rules);
      
      expect(result.matched).toBe(true);
      expect(result.rule?.type).toBe(RuleType.BLOCK);
      expect(result.rule?.source).toBe(RuleSource.GLOBAL);
    });
  });

  describe('no match scenarios', () => {
    test('returns no match when no rules provided', () => {
      const command = createCommand('rm -rf /tmp');
      const rules: Rule[] = [];
      
      const result = matcher.match(command, rules);
      
      expect(result.matched).toBe(false);
      expect(result.rule).toBeUndefined();
    });

    test('returns no match when no rules match', () => {
      const command = createCommand('echo hello');
      const rules = [
        createRule(RuleType.BLOCK, 'rm -rf *'),
        createRule(RuleType.BLOCK, 'git push --force')
      ];
      
      const result = matcher.match(command, rules);
      
      expect(result.matched).toBe(false);
      expect(result.rule).toBeUndefined();
    });
  });

  describe('special characters in patterns', () => {
    test('escapes regex special characters in patterns', () => {
      const command = createCommand('echo (test)');
      const rules = [createRule(RuleType.ALLOW, 'echo (test)')];
      
      const result = matcher.match(command, rules);
      
      expect(result.matched).toBe(true);
    });

    test('handles patterns with dots', () => {
      const command = createCommand('rm file.txt');
      const rules = [createRule(RuleType.BLOCK, 'rm file.txt')];
      
      const result = matcher.match(command, rules);
      
      expect(result.matched).toBe(true);
    });

    test('handles patterns with brackets', () => {
      const command = createCommand('echo [test]');
      const rules = [createRule(RuleType.ALLOW, 'echo [test]')];
      
      const result = matcher.match(command, rules);
      
      expect(result.matched).toBe(true);
    });
  });

  describe('confidence calculation', () => {
    test('calculates confidence based on specificity', () => {
      const command = createCommand('rm -rf /tmp');
      const rules = [createRule(RuleType.BLOCK, 'rm -rf /tmp', 50)];
      
      const result = matcher.match(command, rules);
      
      expect(result.matched).toBe(true);
      expect(result.confidence).toBe(0.5);
    });

    test('caps confidence at 1.0', () => {
      const command = createCommand('rm -rf /tmp');
      const rules = [createRule(RuleType.BLOCK, 'rm -rf /tmp', 150)];
      
      const result = matcher.match(command, rules);
      
      expect(result.matched).toBe(true);
      expect(result.confidence).toBe(1.0);
    });
  });
});
