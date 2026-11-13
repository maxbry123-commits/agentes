/**
 * Integration tests for init command
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { CLI } from '../../src/cli';

// Mock readline module for testing user prompts
let mockReadlineAnswer = '';
vi.mock('readline', async () => {
  const actual = await vi.importActual('readline');
  return {
    ...actual,
    createInterface: () => ({
      question: (query: string, callback: (answer: string) => void) => {
        callback(mockReadlineAnswer);
      },
      close: () => {},
    }),
  };
});

describe('Init Command', () => {
  let testDir: string;
  let originalCwd: string;

  beforeEach(() => {
    // Save original working directory
    originalCwd = process.cwd();
    
    // Create a temporary test directory
    testDir = fs.mkdtempSync(path.join(os.tmpdir(), 'agentguard-init-test-'));
    
    // Mock process.cwd() to return test directory
    vi.spyOn(process, 'cwd').mockReturnValue(testDir);
  });

  afterEach(() => {
    // Restore mocks
    vi.restoreAllMocks();
    
    // Clean up test directory
    if (fs.existsSync(testDir)) {
      fs.rmSync(testDir, { recursive: true, force: true });
    }
  });

  /**
   * Example 6: Init command creates file
   * Validates: Requirements 10.1
   * 
   * This example test verifies that executing `agentguard init` creates
   * a .agentguard file in the current directory.
   */
  it('Example 6: Init command creates file', async () => {
    const cli = new CLI();
    
    // Mock stdin to avoid hanging on prompt
    vi.spyOn(process.stdin, 'on').mockImplementation(() => process.stdin);
    
    // Verify .agentguard does not exist initially
    const agentguardPath = path.join(testDir, '.agentguard');
    expect(fs.existsSync(agentguardPath)).toBe(false);
    
    // Run init command
    const exitCode = await cli.run(['init']);
    
    // Should succeed
    expect(exitCode).toBe(0);
    
    // .agentguard file should now exist
    expect(fs.existsSync(agentguardPath)).toBe(true);
    
    // File should be readable and contain content
    const content = fs.readFileSync(agentguardPath, 'utf-8');
    expect(content.length).toBeGreaterThan(0);
    expect(content).toContain('# AgentGuard Default Rules');
  });

  /**
   * Example 7: Default rules include catastrophic blocks
   * Validates: Requirements 10.2
   * 
   * This example test verifies that the default .agentguard file created by
   * `agentguard init` includes BLOCK rules for catastrophic commands that
   * could destroy the entire system (rm -rf /, mkfs, dd to /dev).
   */
  it('Example 7: Default rules include catastrophic blocks', async () => {
    const cli = new CLI();
    await cli.run(['init']);
    
    const agentguardPath = path.join(testDir, '.agentguard');
    const content = fs.readFileSync(agentguardPath, 'utf-8');
    
    // Check for catastrophic blocks as specified in requirement 10.2
    // Should block deletion of root filesystem
    expect(content).toContain('!rm -rf /');
    expect(content).toContain('!rm -rf /*');
    
    // Should block filesystem formatting
    expect(content).toMatch(/!mkfs/);
    
    // Should block dangerous dd operations to block devices
    expect(content).toMatch(/!dd.*\/dev/);
  });

  /**
   * Example 8: Default rules include dangerous confirms
   * Validates: Requirements 10.3
   * 
   * This example test verifies that the default .agentguard file created by
   * `agentguard init` includes CONFIRM rules for dangerous commands that
   * require user approval (rm -rf *, git push --force).
   */
  it('Example 8: Default rules include dangerous confirms', async () => {
    const cli = new CLI();
    await cli.run(['init']);
    
    const agentguardPath = path.join(testDir, '.agentguard');
    const content = fs.readFileSync(agentguardPath, 'utf-8');
    
    // Check for dangerous confirms as specified in requirement 10.3
    // Should confirm before deleting everything in current directory
    expect(content).toContain('?rm -rf *');
    
    // Should confirm before force pushing to git repositories
    expect(content).toContain('?git push --force');
    expect(content).toContain('?git push -f');
  });

  /**
   * Example 9: Default rules include safe allows
   * Validates: Requirements 10.4
   * 
   * This example test verifies that the default .agentguard file created by
   * `agentguard init` includes ALLOW rules for safe cleanup commands
   * (rm -rf node_modules, rm -rf dist, rm -rf build).
   */
  it('Example 9: Default rules include safe allows', async () => {
    const cli = new CLI();
    await cli.run(['init']);
    
    const agentguardPath = path.join(testDir, '.agentguard');
    const content = fs.readFileSync(agentguardPath, 'utf-8');
    
    // Check for safe allows as specified in requirement 10.4
    // Should allow deletion of common build artifacts and dependencies
    expect(content).toContain('+rm -rf node_modules');
    expect(content).toContain('+rm -rf dist');
    expect(content).toContain('+rm -rf build');
  });

  /**
   * Edge Case 3: Init file conflict - user declines overwrite
   * Validates: Requirements 10.5
   * 
   * This edge case test verifies that when a .agentguard file already exists,
   * the init command prompts the user before overwriting. If the user declines,
   * the original file should remain unchanged.
   */
  it('Edge Case 3: Init file conflict - user declines overwrite', async () => {
    const cli = new CLI();
    const agentguardPath = path.join(testDir, '.agentguard');
    
    // Create an existing .agentguard file with custom content
    const originalContent = '# Custom rules\n!dangerous-command\n';
    fs.writeFileSync(agentguardPath, originalContent, 'utf-8');
    
    // Set mock readline to return 'n' (user declines)
    mockReadlineAnswer = 'n';
    
    // Run init command
    const exitCode = await cli.run(['init']);
    
    // Should succeed (exit code 0)
    expect(exitCode).toBe(0);
    
    // Original file should remain unchanged
    const content = fs.readFileSync(agentguardPath, 'utf-8');
    expect(content).toBe(originalContent);
  });

  /**
   * Edge Case 3: Init file conflict - user accepts overwrite
   * Validates: Requirements 10.5
   * 
   * This edge case test verifies that when a .agentguard file already exists
   * and the user confirms overwrite, the file is replaced with default rules.
   */
  it('Edge Case 3: Init file conflict - user accepts overwrite', async () => {
    const cli = new CLI();
    const agentguardPath = path.join(testDir, '.agentguard');
    
    // Create an existing .agentguard file with custom content
    const originalContent = '# Custom rules\n!dangerous-command\n';
    fs.writeFileSync(agentguardPath, originalContent, 'utf-8');
    
    // Set mock readline to return 'y' (user accepts)
    mockReadlineAnswer = 'y';
    
    // Run init command
    const exitCode = await cli.run(['init']);
    
    // Should succeed
    expect(exitCode).toBe(0);
    
    // File should be overwritten with default content
    const content = fs.readFileSync(agentguardPath, 'utf-8');
    expect(content).not.toBe(originalContent);
    expect(content).toContain('# AgentGuard Default Rules');
    expect(content).toContain('!rm -rf /');
  });
});
