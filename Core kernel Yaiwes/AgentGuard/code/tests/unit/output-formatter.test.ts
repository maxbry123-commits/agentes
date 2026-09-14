/**
 * Unit tests for OutputFormatter
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { OutputFormatter } from '../../src/output-formatter';
import { Rule, RuleType, RuleSource } from '../../src/types';

describe('OutputFormatter', () => {
  let formatter: OutputFormatter;
  let consoleLogSpy: any;
  let consoleErrorSpy: any;
  let consoleWarnSpy: any;

  beforeEach(() => {
    formatter = new OutputFormatter();
    consoleLogSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('displayBanner', () => {
    it('should display banner with version, command, rules count, and mode', () => {
      formatter.displayBanner({
        version: '1.0.0',
        command: 'claude',
        rulesCount: 27,
        mode: 'interactive'
      });

      expect(consoleLogSpy).toHaveBeenCalledOnce();
      const output = consoleLogSpy.mock.calls[0][0];
      
      expect(output).toContain('AgentGuard v1.0.0');
      expect(output).toContain('Protecting: claude');
      expect(output).toContain('27 rules loaded');
      expect(output).toContain('Mode: interactive');
      expect(output).toContain('🛡️');
    });
  });

  describe('displayBlocked', () => {
    it('should display blocked message with emoji, command, rule, and reason', () => {
      const rule: Rule = {
        type: RuleType.BLOCK,
        pattern: '!rm -rf /',
        source: RuleSource.PROJECT,
        lineNumber: 1,
        specificity: 8
      };

      formatter.displayBlocked('rm -rf /', rule, 'Catastrophic - would delete entire filesystem');

      expect(consoleErrorSpy).toHaveBeenCalledOnce();
      const output = consoleErrorSpy.mock.calls[0][0];
      
      expect(output).toContain('🚫 BLOCKED: rm -rf /');
      expect(output).toContain('Rule: !rm -rf /');
      expect(output).toContain('Reason: Catastrophic - would delete entire filesystem');
    });
  });

  describe('displayAllowed', () => {
    it('should display allowed message with emoji, command, and rule', () => {
      const rule: Rule = {
        type: RuleType.ALLOW,
        pattern: '+rm -rf node_modules',
        source: RuleSource.PROJECT,
        lineNumber: 5,
        specificity: 20
      };

      formatter.displayAllowed('rm -rf node_modules', rule);

      expect(consoleLogSpy).toHaveBeenCalledOnce();
      const output = consoleLogSpy.mock.calls[0][0];
      
      expect(output).toContain('✅ ALLOWED: rm -rf node_modules');
      expect(output).toContain('Rule: +rm -rf node_modules');
    });
  });

  describe('displayConfirm', () => {
    it('should display confirmation prompt with command, rule, and timeout', () => {
      const rule: Rule = {
        type: RuleType.CONFIRM,
        pattern: '?rm -rf *',
        source: RuleSource.PROJECT,
        lineNumber: 3,
        specificity: 6
      };

      formatter.displayConfirm({
        command: 'rm -rf temp',
        rule,
        timeout: 30
      });

      expect(consoleLogSpy).toHaveBeenCalledOnce();
      const output = consoleLogSpy.mock.calls[0][0];
      
      expect(output).toContain('⚠️  CONFIRM: rm -rf temp');
      expect(output).toContain('Rule: ?rm -rf *');
      expect(output).toContain('Proceed? [y/N] (timeout in 30s):');
    });

    it('should include scope information when provided', () => {
      const rule: Rule = {
        type: RuleType.CONFIRM,
        pattern: '?rm -rf *',
        source: RuleSource.PROJECT,
        lineNumber: 3,
        specificity: 6
      };

      formatter.displayConfirm({
        command: 'rm -rf temp',
        rule,
        metadata: {
          affectedFiles: 847,
          targetPaths: ['/home/user/temp']
        },
        timeout: 30
      });

      expect(consoleLogSpy).toHaveBeenCalledOnce();
      const output = consoleLogSpy.mock.calls[0][0];
      
      expect(output).toContain('Scope: Would affect 847 files');
      expect(output).toContain('Targets: /home/user/temp');
    });
  });

  describe('displayError', () => {
    it('should display error message with emoji', () => {
      formatter.displayError('Something went wrong');

      expect(consoleErrorSpy).toHaveBeenCalledWith('❌ Error: Something went wrong');
    });
  });

  describe('displayWarning', () => {
    it('should display warning message with emoji', () => {
      formatter.displayWarning('This is a warning');

      expect(consoleWarnSpy).toHaveBeenCalledWith('⚠️  Warning: This is a warning');
    });
  });

  describe('displayInfo', () => {
    it('should display info message with emoji', () => {
      formatter.displayInfo('This is information');

      expect(consoleLogSpy).toHaveBeenCalledWith('ℹ️  This is information');
    });
  });

  describe('passThrough', () => {
    it('should write output to stdout without modification', () => {
      const stdoutSpy = vi.spyOn(process.stdout, 'write').mockImplementation(() => true);
      
      const output = '\x1b[32mGreen text\x1b[0m';
      formatter.passThrough(output);

      expect(stdoutSpy).toHaveBeenCalledWith(output);
      
      stdoutSpy.mockRestore();
    });

    it('should write output to stderr when specified', () => {
      const stderrSpy = vi.spyOn(process.stderr, 'write').mockImplementation(() => true);
      
      const output = '\x1b[31mRed error text\x1b[0m';
      formatter.passThrough(output, true);

      expect(stderrSpy).toHaveBeenCalledWith(output);
      
      stderrSpy.mockRestore();
    });

    it('should preserve ANSI escape codes', () => {
      const stdoutSpy = vi.spyOn(process.stdout, 'write').mockImplementation(() => true);
      
      const ansiOutput = '\x1b[1m\x1b[33mBold Yellow\x1b[0m \x1b[4mUnderlined\x1b[0m';
      formatter.passThrough(ansiOutput);

      expect(stdoutSpy).toHaveBeenCalledWith(ansiOutput);
      expect(stdoutSpy.mock.calls[0][0]).toBe(ansiOutput);
      
      stdoutSpy.mockRestore();
    });
  });
});
