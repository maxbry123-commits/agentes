/**
 * Integration tests for the confirmation handler
 *
 * Tests the CONFIRM rule behavior including:
 * - User approval flow
 * - User denial flow
 * - Timeout behavior
 */

import { describe, it, expect, beforeAll, beforeEach } from 'vitest';
import { execSync, spawn, spawnSync } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';

const SANDBOX_DIR = '/test-sandbox';
const SAFE_DIR = `${SANDBOX_DIR}/safe-to-delete`;

const isDocker = fs.existsSync('/.dockerenv') || process.env.RUNNING_IN_DOCKER === 'true';

describe.skipIf(!isDocker)('Confirmation Handler - Docker Integration', () => {

  beforeAll(() => {
    try {
      execSync('npm run build', { cwd: path.resolve(__dirname, '../..'), stdio: 'pipe' });
    } catch (e) {
      // Already built
    }
  });

  beforeEach(() => {
    execSync(`rm -rf ${SAFE_DIR} && mkdir -p ${SAFE_DIR}`, { stdio: 'pipe' });
    execSync(`echo "test content" > ${SAFE_DIR}/file.txt`, { stdio: 'pipe' });
  });

  describe('CONFIRM rules', () => {

    it('should prompt for confirmation and block on timeout', () => {
      const result = runCommandWithInput('rm -rf /tmp/test', {
        rules: '?rm -rf *',
        timeout: 2000,  // Short timeout
        input: '',      // No input = timeout
      });

      // Should block due to timeout
      expect(result.exitCode).not.toBe(0);
      expect(result.stderr).toMatch(/timeout|BLOCKED/i);
    });

    it('should prompt for confirmation and block on "n" response', () => {
      const result = runCommandWithInput('rm -rf /tmp/test', {
        rules: '?rm -rf *',
        timeout: 5000,
        input: 'n\n',  // User says no
      });

      // Should block due to user denial
      expect(result.exitCode).not.toBe(0);
      expect(result.stderr).toMatch(/denied|BLOCKED/i);
    });

    it('should prompt for confirmation and allow on "y" response', () => {
      const testDir = `${SAFE_DIR}/to-delete`;
      execSync(`mkdir -p ${testDir} && echo "bye" > ${testDir}/file.txt`, { stdio: 'pipe' });

      expect(fs.existsSync(testDir)).toBe(true);

      const result = runCommandWithInput(`rm -rf ${testDir}`, {
        rules: '?rm -rf *',
        timeout: 5000,
        input: 'y\n',  // User says yes
      });

      // Should allow and execute
      expect(result.exitCode).toBe(0);
      expect(fs.existsSync(testDir)).toBe(false);
    });

    it('should display command and rule in confirmation prompt', () => {
      const result = runCommandWithInput('rm -rf /tmp/test', {
        rules: '?rm -rf *',
        timeout: 2000,
        input: '',
      });

      // Should show the command being confirmed
      expect(result.stderr).toMatch(/CONFIRM.*rm -rf/i);
      // Should show the rule pattern
      expect(result.stderr).toMatch(/Rule.*rm -rf/i);
    });

    it('should show timeout countdown', () => {
      const result = runCommandWithInput('rm -rf /tmp/test', {
        rules: '?rm -rf *',
        timeout: 2000,
        input: '',
      });

      // Should mention timeout in the prompt
      expect(result.stderr).toMatch(/timeout/i);
    });

  });

  describe('CONFIRM vs BLOCK precedence', () => {

    it('should block rather than confirm when BLOCK rule matches', () => {
      const result = runCommandWithInput('rm -rf /', {
        rules: [
          '?rm -rf *',   // Confirm all rm -rf
          '!rm -rf /'    // But block rm -rf / specifically
        ].join('\n'),
        timeout: 5000,
        input: 'y\n',  // Even if user would approve
      });

      // Should be blocked, not confirmed
      expect(result.exitCode).not.toBe(0);
      expect(result.stderr).toMatch(/BLOCKED/i);
      // Should NOT show confirmation prompt
      expect(result.stderr).not.toMatch(/CONFIRM/i);
    });

  });

  describe('CONFIRM vs ALLOW precedence', () => {

    it('should allow without confirmation when ALLOW rule is more specific', () => {
      const nmPath = `${SAFE_DIR}/node_modules`;
      execSync(`mkdir -p ${nmPath}`, { stdio: 'pipe' });

      expect(fs.existsSync(nmPath)).toBe(true);

      const result = runCommandWithInput(`rm -rf ${nmPath}`, {
        rules: [
          '?rm -rf *',              // Confirm most rm -rf
          `+rm -rf */node_modules`  // But allow node_modules specifically
        ].join('\n'),
        timeout: 5000,
        input: '',  // No input - would timeout if confirmation was needed
      });

      // Should allow without confirmation
      expect(result.exitCode).toBe(0);
      expect(fs.existsSync(nmPath)).toBe(false);
      // Should NOT show confirmation prompt
      expect(result.stderr).not.toMatch(/CONFIRM/i);
    });

  });

  describe('Edge cases', () => {

    it('should handle empty input as denial', () => {
      const result = runCommandWithInput('rm /tmp/test.txt', {
        rules: '?rm *',
        timeout: 2000,
        input: '\n',  // Just enter (empty response)
      });

      // Empty should be treated as "N" (default)
      expect(result.exitCode).not.toBe(0);
    });

    it('should handle uppercase Y as approval', () => {
      const testFile = `${SAFE_DIR}/uppercase-test.txt`;
      execSync(`echo "test" > ${testFile}`, { stdio: 'pipe' });

      const result = runCommandWithInput(`rm ${testFile}`, {
        rules: '?rm *',
        timeout: 5000,
        input: 'Y\n',  // Uppercase Y
      });

      expect(result.exitCode).toBe(0);
      expect(fs.existsSync(testFile)).toBe(false);
    });

    it('should handle lowercase n as denial', () => {
      const result = runCommandWithInput('rm /tmp/test.txt', {
        rules: '?rm *',
        timeout: 5000,
        input: 'n\n',
      });

      expect(result.exitCode).not.toBe(0);
    });

    it('should handle uppercase N as denial', () => {
      const result = runCommandWithInput('rm /tmp/test.txt', {
        rules: '?rm *',
        timeout: 5000,
        input: 'N\n',
      });

      expect(result.exitCode).not.toBe(0);
    });

  });

});

/**
 * Helper to run a command through agentguard with stdin input
 */
function runCommandWithInput(
  command: string,
  options: {
    rules: string;
    timeout: number;
    input: string;
  }
): { exitCode: number; stdout: string; stderr: string } {
  const { rules, timeout, input } = options;

  // Write rules to a .agentguard file in a temp directory
  const tempDir = `/tmp/agentguard-confirm-test-${Date.now()}`;
  fs.mkdirSync(tempDir, { recursive: true });
  const rulesFile = `${tempDir}/.agentguard`;
  fs.writeFileSync(rulesFile, rules);

  try {
    // Use shell: false to prevent shell from interpreting && || ; |
    const result = spawnSync('node', [
      '/app/dist/cli.js',
      '--',
      command
    ], {
      cwd: tempDir,
      env: process.env,
      timeout,
      encoding: 'utf-8',
      input,
      shell: false,
    });

    return {
      exitCode: result.status ?? 1,
      stdout: result.stdout || '',
      stderr: result.stderr || '',
    };
  } finally {
    try {
      fs.rmSync(tempDir, { recursive: true, force: true });
    } catch (e) {
      // Ignore
    }
  }
}
