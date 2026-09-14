/**
 * Unit tests for ProcessSpawner
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ProcessSpawner } from '../../src/process-spawner';
import { SpawnOptions, Rule, RuleType, RuleSource } from '../../src/types';
import { OutputFormatter } from '../../src/output-formatter';

describe('ProcessSpawner', () => {
  let spawner: ProcessSpawner;

  beforeEach(() => {
    spawner = new ProcessSpawner();
  });

  describe('detectRealShell', () => {
    it('should return AGENTGUARD_REAL_SHELL if already wrapped', () => {
      const originalEnv = process.env.AGENTGUARD_REAL_SHELL;
      process.env.AGENTGUARD_REAL_SHELL = '/bin/zsh';

      const result = spawner.detectRealShell();

      expect(result).toBe('/bin/zsh');

      // Restore
      if (originalEnv) {
        process.env.AGENTGUARD_REAL_SHELL = originalEnv;
      } else {
        delete process.env.AGENTGUARD_REAL_SHELL;
      }
    });

    it('should return SHELL if not wrapped', () => {
      const originalAgentGuard = process.env.AGENTGUARD_REAL_SHELL;
      const originalShell = process.env.SHELL;
      
      delete process.env.AGENTGUARD_REAL_SHELL;
      process.env.SHELL = '/bin/bash';

      const result = spawner.detectRealShell();

      expect(result).toBe('/bin/bash');

      // Restore
      if (originalAgentGuard) {
        process.env.AGENTGUARD_REAL_SHELL = originalAgentGuard;
      }
      if (originalShell) {
        process.env.SHELL = originalShell;
      }
    });

    it('should return /bin/bash as fallback', () => {
      const originalAgentGuard = process.env.AGENTGUARD_REAL_SHELL;
      const originalShell = process.env.SHELL;
      
      delete process.env.AGENTGUARD_REAL_SHELL;
      delete process.env.SHELL;

      const result = spawner.detectRealShell();

      expect(result).toBe('/bin/bash');

      // Restore
      if (originalAgentGuard) {
        process.env.AGENTGUARD_REAL_SHELL = originalAgentGuard;
      }
      if (originalShell) {
        process.env.SHELL = originalShell;
      }
    });
  });

  describe('displayBanner', () => {
    it('should display banner with correct information', () => {
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});

      const rules: Rule[] = [
        {
          type: RuleType.BLOCK,
          pattern: '!rm -rf /',
          source: RuleSource.PROJECT,
          lineNumber: 1,
          specificity: 8
        },
        {
          type: RuleType.ALLOW,
          pattern: '+rm -rf node_modules',
          source: RuleSource.PROJECT,
          lineNumber: 2,
          specificity: 20
        }
      ];

      spawner.displayBanner(rules, 'claude');

      expect(consoleSpy).toHaveBeenCalled();
      const output = consoleSpy.mock.calls[0][0];
      
      expect(output).toContain('AgentGuard');
      expect(output).toContain('claude');
      expect(output).toContain('2 rules loaded');

      consoleSpy.mockRestore();
    });
  });

  describe('buildEnvironment', () => {
    it('should set SHELL to guard shell path', () => {
      const options: SpawnOptions = {
        command: ['echo', 'test'],
        shellPath: '/path/to/agentguard-shell',
        realShell: '/bin/bash'
      };

      // Access private method via any cast for testing
      const env = (spawner as any).buildEnvironment(options);

      expect(env.SHELL).toBe('/path/to/agentguard-shell');
    });

    it('should set AGENTGUARD_REAL_SHELL to detected shell', () => {
      const options: SpawnOptions = {
        command: ['echo', 'test'],
        shellPath: '/path/to/agentguard-shell',
        realShell: '/bin/bash'
      };

      const env = (spawner as any).buildEnvironment(options);

      expect(env.AGENTGUARD_REAL_SHELL).toBeDefined();
      expect(typeof env.AGENTGUARD_REAL_SHELL).toBe('string');
    });

    it('should set AGENTGUARD_ORIGINAL_SHELL', () => {
      const options: SpawnOptions = {
        command: ['echo', 'test'],
        shellPath: '/path/to/agentguard-shell',
        realShell: '/bin/bash'
      };

      const env = (spawner as any).buildEnvironment(options);

      expect(env.AGENTGUARD_ORIGINAL_SHELL).toBeDefined();
      expect(typeof env.AGENTGUARD_ORIGINAL_SHELL).toBe('string');
    });

    it('should set AGENTGUARD_ACTIVE to 1', () => {
      const options: SpawnOptions = {
        command: ['echo', 'test'],
        shellPath: '/path/to/agentguard-shell',
        realShell: '/bin/bash'
      };

      const env = (spawner as any).buildEnvironment(options);

      expect(env.AGENTGUARD_ACTIVE).toBe('1');
    });

    it('should preserve existing environment variables', () => {
      const options: SpawnOptions = {
        command: ['echo', 'test'],
        shellPath: '/path/to/agentguard-shell',
        realShell: '/bin/bash'
      };

      const env = (spawner as any).buildEnvironment(options);

      // Check that some common env vars are preserved
      expect(env.PATH).toBeDefined();
      expect(env.HOME).toBeDefined();
    });
  });

  describe('spawn', () => {
    it('should spawn process with modified environment', async () => {
      // This is a basic integration test
      // We'll spawn a simple command that should succeed
      // Use the real shell directly for this unit test since we're testing
      // the environment setup, not the guard shell wrapper itself
      const options: SpawnOptions = {
        command: ['echo', 'test'],
        shellPath: '/bin/bash', // Use real shell for unit test
        realShell: '/bin/bash'
      };

      const exitCode = await spawner.spawn(options);

      // echo should succeed
      expect(exitCode).toBe(0);
    });

    it('should handle command not found', async () => {
      const options: SpawnOptions = {
        command: ['nonexistent-command-xyz'],
        shellPath: '/bin/bash', // Use real shell for unit test
        realShell: '/bin/bash'
      };

      const exitCode = await spawner.spawn(options);
      
      // Command not found should return non-zero exit code (typically 127)
      expect(exitCode).not.toBe(0);
    });
  });
});
