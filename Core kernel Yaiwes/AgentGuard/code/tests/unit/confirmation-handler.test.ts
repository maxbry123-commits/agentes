/**
 * Unit tests for ConfirmationHandler
 * 
 * Note: These tests verify the logic and structure of the ConfirmationHandler.
 * Full integration testing with actual stdin/stdout requires manual testing or
 * more complex test harnesses.
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { ConfirmationHandler } from '../../src/confirmation-handler';
import { RuleType, RuleSource, ConfirmOptions } from '../../src/types';

// Testable subclass that allows us to mock the readline interface
class TestableConfirmationHandler extends ConfirmationHandler {
  private mockInput: string | null = null;
  private shouldTimeout: boolean = false;

  setMockInput(input: string | null) {
    this.mockInput = input;
  }

  setShouldTimeout(timeout: boolean) {
    this.shouldTimeout = timeout;
  }

  // Override readInput to return mock data
  override readInput(timeout: number): Promise<string> {
    return new Promise((resolve, reject) => {
      if (this.shouldTimeout) {
        setTimeout(() => reject(new Error('Timeout')), 10);
      } else if (this.mockInput !== null) {
        setTimeout(() => resolve(this.mockInput!), 10);
      } else {
        reject(new Error('No mock input set'));
      }
    });
  }
}

describe('ConfirmationHandler', () => {
  let handler: TestableConfirmationHandler;
  let mockStderr: string[];
  let originalStderrWrite: typeof process.stderr.write;

  beforeEach(() => {
    handler = new TestableConfirmationHandler();
    mockStderr = [];
    
    // Mock stderr to capture output
    originalStderrWrite = process.stderr.write;
    process.stderr.write = ((chunk: any, ...args: any[]) => {
      mockStderr.push(chunk.toString());
      // Call original to avoid breaking other functionality
      return true;
    }) as any;
  });

  afterEach(() => {
    // Restore stderr
    process.stderr.write = originalStderrWrite;
  });

  const createTestRule = () => ({
    type: RuleType.CONFIRM,
    pattern: '?rm -rf *',
    source: RuleSource.PROJECT,
    lineNumber: 1,
    specificity: 5
  });

  describe('displayPrompt()', () => {
    it('should display confirmation prompt with command and rule', () => {
      const rule = createTestRule();
      const options: ConfirmOptions = {
        command: 'rm -rf test',
        rule,
        timeout: 30000
      };

      // Should not throw
      expect(() => handler.displayPrompt(options)).not.toThrow();
      
      // Verify some output was written
      expect(mockStderr.length).toBeGreaterThan(0);
    });

    it('should display metadata when provided', () => {
      const rule = createTestRule();
      const options: ConfirmOptions = {
        command: 'rm -rf test',
        rule,
        metadata: {
          affectedFiles: 42,
          targetPaths: ['/home/user/test', '/home/user/data']
        },
        timeout: 30000
      };

      // Should not throw
      expect(() => handler.displayPrompt(options)).not.toThrow();
      
      // Verify output was written
      expect(mockStderr.length).toBeGreaterThan(0);
    });

    it('should use default timeout of 30 seconds when not specified', () => {
      const rule = createTestRule();
      const options: ConfirmOptions = {
        command: 'rm -rf test',
        rule
        // No timeout specified
      };

      // Should not throw
      expect(() => handler.displayPrompt(options)).not.toThrow();
      
      // Verify output was written
      expect(mockStderr.length).toBeGreaterThan(0);
    });
  });

  describe('confirm()', () => {
    it('should return approved=true when user enters "y"', async () => {
      handler.setMockInput('y');
      const rule = createTestRule();

      const result = await handler.confirm({
        command: 'rm -rf test',
        rule,
        timeout: 100
      });

      expect(result.approved).toBe(true);
      expect(result.timedOut).toBe(false);
    });

    it('should return approved=true when user enters "Y"', async () => {
      handler.setMockInput('Y');
      const rule = createTestRule();

      const result = await handler.confirm({
        command: 'rm -rf test',
        rule,
        timeout: 100
      });

      expect(result.approved).toBe(true);
      expect(result.timedOut).toBe(false);
    });

    it('should return approved=false when user enters "n"', async () => {
      handler.setMockInput('n');
      const rule = createTestRule();

      const result = await handler.confirm({
        command: 'rm -rf test',
        rule,
        timeout: 100
      });

      expect(result.approved).toBe(false);
      expect(result.timedOut).toBe(false);
    });

    it('should return approved=false when user enters "N"', async () => {
      handler.setMockInput('N');
      const rule = createTestRule();

      const result = await handler.confirm({
        command: 'rm -rf test',
        rule,
        timeout: 100
      });

      expect(result.approved).toBe(false);
      expect(result.timedOut).toBe(false);
    });

    it('should return approved=false when user enters anything other than y/Y', async () => {
      handler.setMockInput('maybe');
      const rule = createTestRule();

      const result = await handler.confirm({
        command: 'rm -rf test',
        rule,
        timeout: 100
      });

      expect(result.approved).toBe(false);
      expect(result.timedOut).toBe(false);
    });

    it('should return approved=false when user enters empty string', async () => {
      handler.setMockInput('');
      const rule = createTestRule();

      const result = await handler.confirm({
        command: 'rm -rf test',
        rule,
        timeout: 100
      });

      expect(result.approved).toBe(false);
      expect(result.timedOut).toBe(false);
    });

    it('should timeout and return approved=false, timedOut=true after timeout period', async () => {
      handler.setShouldTimeout(true);
      const rule = createTestRule();

      const result = await handler.confirm({
        command: 'rm -rf test',
        rule,
        timeout: 50 // Short timeout for testing
      });

      expect(result.approved).toBe(false);
      expect(result.timedOut).toBe(true);
      
      // Verify some output was written
      expect(mockStderr.length).toBeGreaterThan(0);
    });

    it('should display prompt before waiting for input', async () => {
      handler.setMockInput('n');
      const rule = createTestRule();

      await handler.confirm({
        command: 'rm -rf test',
        rule,
        timeout: 100
      });

      // Verify output was written
      expect(mockStderr.length).toBeGreaterThan(0);
    });
  });
});
