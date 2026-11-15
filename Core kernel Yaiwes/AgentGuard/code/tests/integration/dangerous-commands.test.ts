/**
 * Integration tests for dangerous command handling
 *
 * IMPORTANT: These tests are designed to run inside a Docker container
 * where dangerous commands can be safely executed and validated.
 *
 * DO NOT run these tests on your host machine!
 */

import { describe, it, expect, beforeAll, beforeEach } from 'vitest';
import { execSync, spawnSync } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';

const SANDBOX_DIR = '/test-sandbox';
const SAFE_DIR = `${SANDBOX_DIR}/safe-to-delete`;

// Skip tests if not running in Docker
const isDocker = fs.existsSync('/.dockerenv') || process.env.RUNNING_IN_DOCKER === 'true';

describe.skipIf(!isDocker)('Dangerous Commands - Docker Integration', () => {

  beforeAll(() => {
    // Ensure agentguard is built
    try {
      execSync('npm run build', { cwd: path.resolve(__dirname, '../..'), stdio: 'pipe' });
    } catch (e) {
      // Build might already be done
    }
  });

  beforeEach(() => {
    // Reset sandbox directory before each test
    execSync(`rm -rf ${SAFE_DIR} && mkdir -p ${SAFE_DIR}`, { stdio: 'pipe' });
    execSync(`echo "test content" > ${SAFE_DIR}/file1.txt`, { stdio: 'pipe' });
    execSync(`echo "test content" > ${SAFE_DIR}/file2.txt`, { stdio: 'pipe' });
    execSync(`mkdir -p ${SAFE_DIR}/subdir`, { stdio: 'pipe' });
    execSync(`echo "nested" > ${SAFE_DIR}/subdir/nested.txt`, { stdio: 'pipe' });
  });

  describe('BLOCK rules - Catastrophic commands', () => {

    it('should block rm -rf /', () => {
      const result = runAgentguardCommand('rm -rf /', {
        rules: '!rm -rf /'
      });

      expect(result.exitCode).not.toBe(0);
      expect(result.stderr + result.stdout).toMatch(/block/i);
      expect(fs.existsSync('/')).toBe(true);
    });

    it('should block rm -rf /*', () => {
      const result = runAgentguardCommand('rm -rf /*', {
        rules: '!rm -rf /*'
      });

      expect(result.exitCode).not.toBe(0);
      expect(result.stderr + result.stdout).toMatch(/block/i);
    });

    it('should block mkfs commands', () => {
      const result = runAgentguardCommand('mkfs.ext4 /dev/sda1', {
        rules: '!mkfs.*'
      });

      expect(result.exitCode).not.toBe(0);
      expect(result.stderr + result.stdout).toMatch(/block/i);
    });

    it('should block dd to block devices', () => {
      const result = runAgentguardCommand('dd if=/dev/zero of=/dev/sda', {
        rules: '!dd * of=/dev/sd*'
      });

      expect(result.exitCode).not.toBe(0);
      expect(result.stderr + result.stdout).toMatch(/block/i);
    });

  });

  describe('ALLOW rules - Safe commands actually execute', () => {

    it('should allow and execute rm -rf node_modules', () => {
      const nmPath = `${SAFE_DIR}/node_modules`;
      execSync(`mkdir -p ${nmPath} && echo "pkg" > ${nmPath}/package.json`, { stdio: 'pipe' });

      expect(fs.existsSync(nmPath)).toBe(true);

      const result = runAgentguardCommand(`rm -rf ${nmPath}`, {
        rules: '+rm -rf */node_modules\n+rm -rf *'
      });

      expect(result.exitCode).toBe(0);
      expect(fs.existsSync(nmPath)).toBe(false);
    });

    it('should allow and execute safe directory cleanup', () => {
      const targetDir = `${SAFE_DIR}/dist`;
      execSync(`mkdir -p ${targetDir} && echo "built" > ${targetDir}/index.js`, { stdio: 'pipe' });

      expect(fs.existsSync(targetDir)).toBe(true);

      const result = runAgentguardCommand(`rm -rf ${targetDir}`, {
        rules: '+rm -rf */dist'
      });

      expect(result.exitCode).toBe(0);
      expect(fs.existsSync(targetDir)).toBe(false);
    });

  });

  describe('Rule precedence', () => {

    it('should block even when allow rule also matches (BLOCK > ALLOW)', () => {
      const result = runAgentguardCommand('rm -rf /', {
        rules: [
          '+rm -rf *',
          '!rm -rf /'
        ].join('\n')
      });

      expect(result.exitCode).not.toBe(0);
      expect(result.stderr + result.stdout).toMatch(/block/i);
    });

    it('should prefer more specific rules', () => {
      const targetFile = `${SAFE_DIR}/keep-this.txt`;
      execSync(`echo "important" > ${targetFile}`, { stdio: 'pipe' });

      const result = runAgentguardCommand(`rm ${targetFile}`, {
        rules: [
          '+rm *',
          `!rm ${targetFile}`
        ].join('\n')
      });

      expect(result.exitCode).not.toBe(0);
      expect(fs.existsSync(targetFile)).toBe(true);
    });

  });

  describe('Command variations', () => {

    it('should handle quoted arguments', () => {
      const testFile = `${SAFE_DIR}/file with spaces.txt`;
      execSync(`echo "content" > "${testFile}"`, { stdio: 'pipe' });

      const result = runAgentguardCommand(`rm "${testFile}"`, {
        rules: '+rm *'
      });

      expect(result.exitCode).toBe(0);
      expect(fs.existsSync(testFile)).toBe(false);
    });

    it('should handle commands with environment variables', () => {
      const result = runAgentguardCommand('rm -rf $HOME', {
        rules: '!rm -rf $HOME\n!rm -rf ~'
      });

      expect(result.exitCode).not.toBe(0);
      expect(result.stderr + result.stdout).toMatch(/block/i);
    });

  });

  describe('Chained commands (&&, ||, ;)', () => {

    it('should block if any command in && chain is blocked', () => {
      const result = runAgentguardCommand('ls && rm -rf /', {
        rules: '!rm -rf /\n+ls'
      });

      expect(result.exitCode).not.toBe(0);
      expect(result.stderr + result.stdout).toMatch(/block/i);
    });

    it('should allow && chain if all commands are allowed', () => {
      const testFile = `${SAFE_DIR}/chained.txt`;

      const result = runAgentguardCommand(`echo "test" > ${testFile} && cat ${testFile}`, {
        rules: '+echo *\n+cat *'
      });

      // Note: The command itself might fail due to redirection handling,
      // but it shouldn't be blocked by agentguard
      // For now, just verify it's not blocked
      expect(result.stderr).not.toMatch(/BLOCKED/i);
    });

    it('should block if command after || is blocked', () => {
      const result = runAgentguardCommand('false || rm -rf /', {
        rules: '!rm -rf /\n+false'
      });

      expect(result.exitCode).not.toBe(0);
      expect(result.stderr + result.stdout).toMatch(/block/i);
    });

    it('should handle semicolon-separated commands', () => {
      const result = runAgentguardCommand('ls; rm -rf /', {
        rules: '!rm -rf /\n+ls'
      });

      expect(result.exitCode).not.toBe(0);
      expect(result.stderr + result.stdout).toMatch(/block/i);
    });

  });

  describe('Piped commands', () => {

    it('should allow safe piped commands', () => {
      const testFile = `${SAFE_DIR}/pipe-test.txt`;
      execSync(`echo "hello world" > ${testFile}`, { stdio: 'pipe' });

      const result = runAgentguardCommand(`cat ${testFile} | grep hello`, {
        rules: '+cat *\n+grep *'
      });

      expect(result.exitCode).toBe(0);
      expect(result.stdout).toContain('hello');
    });

    it('should block dangerous piped patterns like curl | bash', () => {
      const result = runAgentguardCommand('echo "test" | bash', {
        rules: '!* | bash\n!* | sh'
      });

      expect(result.exitCode).not.toBe(0);
      expect(result.stderr + result.stdout).toMatch(/block/i);
    });

  });

  describe('Real dangerous scenarios (Docker only)', () => {

    it('should survive an attempt to rm -rf entire sandbox', () => {
      const result = runAgentguardCommand(`rm -rf ${SANDBOX_DIR}/*`, {
        rules: [
          `!rm -rf ${SANDBOX_DIR}/*`,
          '+rm -rf *'
        ].join('\n')
      });

      expect(result.exitCode).not.toBe(0);
      expect(fs.existsSync(SANDBOX_DIR)).toBe(true);
    });

    it('should actually delete files when allowed (proves execution works)', () => {
      for (let i = 0; i < 5; i++) {
        execSync(`echo "file ${i}" > ${SAFE_DIR}/file${i}.txt`, { stdio: 'pipe' });
      }

      expect(fs.readdirSync(SAFE_DIR).length).toBeGreaterThanOrEqual(5);

      const result = runAgentguardCommand(`rm -rf ${SAFE_DIR}/*`, {
        rules: `+rm -rf ${SAFE_DIR}/*`
      });

      expect(result.exitCode).toBe(0);
      const remaining = fs.readdirSync(SAFE_DIR);
      expect(remaining.length).toBeLessThanOrEqual(1);
    });

  });

});

/**
 * Helper to run a command through agentguard and capture results
 */
function runAgentguardCommand(
  command: string,
  options: {
    rules?: string;
    env?: Record<string, string>;
    timeout?: number;
    input?: string;
  } = {}
): { exitCode: number; stdout: string; stderr: string } {
  const { rules = '', env = {}, timeout = 5000, input } = options;

  // Write rules to a .agentguard file in a temp directory
  const tempDir = `/tmp/agentguard-test-${Date.now()}`;
  fs.mkdirSync(tempDir, { recursive: true });
  const rulesFile = `${tempDir}/.agentguard`;
  fs.writeFileSync(rulesFile, rules);

  try {
    // Use shell: false to prevent shell from interpreting && || ; |
    // The command is passed as a single argument to agentguard
    const result = spawnSync('node', [
      '/app/dist/cli.js',
      '--',
      command
    ], {
      cwd: tempDir,  // Run from temp dir so .agentguard is found
      env: {
        ...process.env,
        ...env,
      },
      timeout,
      encoding: 'utf-8',
      input,
      shell: false,  // Don't let shell interpret && || ; |
    });

    return {
      exitCode: result.status ?? 1,
      stdout: result.stdout || '',
      stderr: result.stderr || '',
    };
  } finally {
    // Cleanup
    try {
      fs.rmSync(tempDir, { recursive: true, force: true });
    } catch (e) {
      // Ignore cleanup errors
    }
  }
}
