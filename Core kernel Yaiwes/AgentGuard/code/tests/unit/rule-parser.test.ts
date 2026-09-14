/**
 * Unit tests for RuleParser
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { RuleParser } from '../../src/rule-parser';
import { RuleType, RuleSource } from '../../src/types';

describe('RuleParser', () => {
  let parser: RuleParser;
  let tempDir: string;

  beforeEach(() => {
    parser = new RuleParser();
    // Create a temporary directory for test files
    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'agentguard-test-'));
  });

  afterEach(() => {
    // Clean up temporary directory
    if (fs.existsSync(tempDir)) {
      fs.rmSync(tempDir, { recursive: true, force: true });
    }
  });

  describe('parse', () => {
    it('should parse BLOCK rules with ! prefix', () => {
      const filePath = path.join(tempDir, 'rules');
      fs.writeFileSync(filePath, '!rm -rf /\n');

      const result = parser.parse(filePath, RuleSource.PROJECT);

      expect(result.rules).toHaveLength(1);
      expect(result.rules[0].type).toBe(RuleType.BLOCK);
      expect(result.rules[0].pattern).toBe('rm -rf /');
      expect(result.rules[0].source).toBe(RuleSource.PROJECT);
      expect(result.rules[0].lineNumber).toBe(1);
      expect(result.errors).toHaveLength(0);
    });

    it('should parse CONFIRM rules with ? prefix', () => {
      const filePath = path.join(tempDir, 'rules');
      fs.writeFileSync(filePath, '?rm -rf *\n');

      const result = parser.parse(filePath, RuleSource.PROJECT);

      expect(result.rules).toHaveLength(1);
      expect(result.rules[0].type).toBe(RuleType.CONFIRM);
      expect(result.rules[0].pattern).toBe('rm -rf *');
      expect(result.errors).toHaveLength(0);
    });

    it('should parse ALLOW rules with + prefix', () => {
      const filePath = path.join(tempDir, 'rules');
      fs.writeFileSync(filePath, '+rm -rf node_modules\n');

      const result = parser.parse(filePath, RuleSource.PROJECT);

      expect(result.rules).toHaveLength(1);
      expect(result.rules[0].type).toBe(RuleType.ALLOW);
      expect(result.rules[0].pattern).toBe('rm -rf node_modules');
      expect(result.errors).toHaveLength(0);
    });

    it('should parse PROTECT directives with @protect prefix', () => {
      const filePath = path.join(tempDir, 'rules');
      fs.writeFileSync(filePath, '@protect ~/.ssh\n');

      const result = parser.parse(filePath, RuleSource.PROJECT);

      expect(result.rules).toHaveLength(1);
      expect(result.rules[0].type).toBe(RuleType.PROTECT);
      expect(result.rules[0].pattern).toBe('~/.ssh');
      expect(result.rules[0].metadata?.path).toBe('~/.ssh');
      expect(result.errors).toHaveLength(0);
    });

    it('should parse SANDBOX directives with @sandbox prefix', () => {
      const filePath = path.join(tempDir, 'rules');
      fs.writeFileSync(filePath, '@sandbox /tmp/workspace\n');

      const result = parser.parse(filePath, RuleSource.PROJECT);

      expect(result.rules).toHaveLength(1);
      expect(result.rules[0].type).toBe(RuleType.SANDBOX);
      expect(result.rules[0].pattern).toBe('/tmp/workspace');
      expect(result.rules[0].metadata?.path).toBe('/tmp/workspace');
      expect(result.errors).toHaveLength(0);
    });

    it('should skip comment lines starting with #', () => {
      const filePath = path.join(tempDir, 'rules');
      fs.writeFileSync(filePath, '# This is a comment\n!rm -rf /\n# Another comment\n');

      const result = parser.parse(filePath, RuleSource.PROJECT);

      expect(result.rules).toHaveLength(1);
      expect(result.rules[0].pattern).toBe('rm -rf /');
      expect(result.errors).toHaveLength(0);
    });

    it('should skip blank lines', () => {
      const filePath = path.join(tempDir, 'rules');
      fs.writeFileSync(filePath, '\n!rm -rf /\n\n+rm -rf node_modules\n\n');

      const result = parser.parse(filePath, RuleSource.PROJECT);

      expect(result.rules).toHaveLength(2);
      expect(result.errors).toHaveLength(0);
    });

    it('should handle invalid syntax and continue parsing', () => {
      const filePath = path.join(tempDir, 'rules');
      fs.writeFileSync(filePath, '!rm -rf /\ninvalid line\n+rm -rf node_modules\n');

      const result = parser.parse(filePath, RuleSource.PROJECT);

      expect(result.rules).toHaveLength(2);
      expect(result.rules[0].pattern).toBe('rm -rf /');
      expect(result.rules[1].pattern).toBe('rm -rf node_modules');
      expect(result.errors).toHaveLength(1);
      expect(result.errors[0].line).toBe(2);
      expect(result.errors[0].message).toContain('Invalid rule syntax');
    });

    it('should report errors with line numbers', () => {
      const filePath = path.join(tempDir, 'rules');
      fs.writeFileSync(filePath, '!rm -rf /\n!\n?pattern\ninvalid\n');

      const result = parser.parse(filePath, RuleSource.PROJECT);

      expect(result.rules).toHaveLength(2);
      expect(result.errors).toHaveLength(2);
      expect(result.errors[0].line).toBe(2);
      expect(result.errors[0].message).toContain('missing pattern');
      expect(result.errors[1].line).toBe(4);
    });

    it('should return empty result for non-existent file', () => {
      const filePath = path.join(tempDir, 'nonexistent');

      const result = parser.parse(filePath, RuleSource.PROJECT);

      expect(result.rules).toHaveLength(0);
      expect(result.errors).toHaveLength(0);
    });

    it('should calculate specificity correctly', () => {
      const filePath = path.join(tempDir, 'rules');
      fs.writeFileSync(filePath, '!rm -rf /\n!rm -rf *\n!*\n');

      const result = parser.parse(filePath, RuleSource.PROJECT);

      expect(result.rules).toHaveLength(3);
      // "rm -rf /" should have highest specificity (literal chars + absolute path bonus)
      expect(result.rules[0].specificity).toBeGreaterThan(result.rules[1].specificity);
      // "rm -rf *" should have higher specificity than "*"
      expect(result.rules[1].specificity).toBeGreaterThan(result.rules[2].specificity);
    });
  });

  describe('loadAll', () => {
    it('should merge rules from multiple sources with project precedence', () => {
      // Create a project rule file
      const projectPath = path.join(process.cwd(), '.agentguard');
      fs.writeFileSync(projectPath, '!rm -rf /\n+rm -rf node_modules\n');

      try {
        const rules = parser.loadAll();

        // Should have at least the project rules
        expect(rules.length).toBeGreaterThanOrEqual(2);
        
        // Check that project rules are present
        const blockRule = rules.find(r => r.pattern === 'rm -rf /' && r.type === RuleType.BLOCK);
        const allowRule = rules.find(r => r.pattern === 'rm -rf node_modules' && r.type === RuleType.ALLOW);
        
        expect(blockRule).toBeDefined();
        expect(blockRule?.source).toBe(RuleSource.PROJECT);
        expect(allowRule).toBeDefined();
        expect(allowRule?.source).toBe(RuleSource.PROJECT);
      } finally {
        // Clean up
        if (fs.existsSync(projectPath)) {
          fs.unlinkSync(projectPath);
        }
      }
    });
  });
});
