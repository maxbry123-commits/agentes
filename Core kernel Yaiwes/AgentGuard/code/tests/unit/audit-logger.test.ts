/**
 * Unit tests for AuditLogger
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { AuditLogger } from '../../src/audit-logger';
import { ValidationAction } from '../../src/types';

describe('AuditLogger', () => {
  let tempDir: string;
  let logPath: string;
  let logger: AuditLogger;

  beforeEach(() => {
    // Create temporary directory for test logs
    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'agentguard-test-'));
    logPath = path.join(tempDir, 'audit.log');
    logger = new AuditLogger(logPath);
  });

  afterEach(() => {
    // Clean up temporary directory
    if (fs.existsSync(tempDir)) {
      fs.rmSync(tempDir, { recursive: true, force: true });
    }
  });

  describe('log()', () => {
    it('should create log directory if it does not exist', () => {
      const nestedLogPath = path.join(tempDir, 'nested', 'dir', 'audit.log');
      const nestedLogger = new AuditLogger(nestedLogPath);

      nestedLogger.log({
        timestamp: new Date().toISOString(),
        command: 'test command',
        action: ValidationAction.ALLOW,
        reason: 'test'
      });

      expect(fs.existsSync(path.dirname(nestedLogPath))).toBe(true);
    });

    it('should write log entry as single-line JSON', () => {
      const entry = {
        timestamp: '2025-12-02T10:30:45.123Z',
        command: 'rm -rf /',
        action: ValidationAction.BLOCK,
        rule: '!rm -rf /',
        reason: 'Catastrophic'
      };

      logger.log(entry);

      const content = fs.readFileSync(logPath, 'utf-8');
      const lines = content.trim().split('\n');
      
      expect(lines).toHaveLength(1);
      expect(JSON.parse(lines[0])).toEqual(entry);
    });

    it('should append multiple entries', () => {
      logger.log({
        timestamp: '2025-12-02T10:30:45.123Z',
        command: 'rm -rf /',
        action: ValidationAction.BLOCK,
        reason: 'test1'
      });

      logger.log({
        timestamp: '2025-12-02T10:31:00.456Z',
        command: 'echo hello',
        action: ValidationAction.ALLOW,
        reason: 'test2'
      });

      const content = fs.readFileSync(logPath, 'utf-8');
      const lines = content.trim().split('\n');
      
      expect(lines).toHaveLength(2);
    });

    it('should continue operation if log write fails', () => {
      // Create logger with invalid path (read-only directory)
      const invalidPath = '/invalid/path/audit.log';
      const invalidLogger = new AuditLogger(invalidPath);

      // Should not throw
      expect(() => {
        invalidLogger.log({
          timestamp: new Date().toISOString(),
          command: 'test',
          action: ValidationAction.ALLOW,
          reason: 'test'
        });
      }).not.toThrow();
    });
  });

  describe('rotate()', () => {
    it('should rotate log file when it exceeds maxSize', () => {
      // Create logger with small maxSize (100 bytes)
      const smallLogger = new AuditLogger(logPath, 100);

      // Write entries until rotation is needed
      for (let i = 0; i < 10; i++) {
        smallLogger.log({
          timestamp: new Date().toISOString(),
          command: `test command ${i}`,
          action: ValidationAction.ALLOW,
          reason: 'test'
        });
      }

      // Check that backup file was created
      const files = fs.readdirSync(tempDir);
      const backupFiles = files.filter(f => f.startsWith('audit.log.'));
      
      expect(backupFiles.length).toBeGreaterThan(0);
    });

    it('should create timestamped backup files', () => {
      // Write some data
      logger.log({
        timestamp: new Date().toISOString(),
        command: 'test',
        action: ValidationAction.ALLOW,
        reason: 'test'
      });

      // Manually trigger rotation
      logger.rotate();

      // Check backup file exists with timestamp
      const files = fs.readdirSync(tempDir);
      const backupFiles = files.filter(f => f.startsWith('audit.log.'));
      
      expect(backupFiles).toHaveLength(1);
      expect(backupFiles[0]).toMatch(/audit\.log\.\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}/);
    });

    it('should handle rotation errors gracefully', () => {
      // Try to rotate non-existent file
      expect(() => logger.rotate()).not.toThrow();
    });
  });

  describe('read()', () => {
    beforeEach(() => {
      // Write some test entries
      logger.log({
        timestamp: '2025-12-02T10:30:00.000Z',
        command: 'rm -rf /',
        action: ValidationAction.BLOCK,
        reason: 'test1'
      });

      logger.log({
        timestamp: '2025-12-02T10:31:00.000Z',
        command: 'echo hello',
        action: ValidationAction.ALLOW,
        reason: 'test2'
      });

      logger.log({
        timestamp: '2025-12-02T10:32:00.000Z',
        command: 'rm -rf node_modules',
        action: ValidationAction.ALLOW,
        reason: 'test3'
      });
    });

    it('should read all entries', () => {
      const entries = logger.read();
      expect(entries).toHaveLength(3);
    });

    it('should filter by action', () => {
      const entries = logger.read({ action: ValidationAction.ALLOW });
      expect(entries).toHaveLength(2);
      expect(entries.every(e => e.action === ValidationAction.ALLOW)).toBe(true);
    });

    it('should filter by date', () => {
      const since = new Date('2025-12-02T10:31:30.000Z');
      const entries = logger.read({ since });
      expect(entries).toHaveLength(1);
      expect(entries[0].command).toBe('rm -rf node_modules');
    });

    it('should limit results to most recent entries', () => {
      const entries = logger.read({ limit: 2 });
      expect(entries).toHaveLength(2);
      expect(entries[0].command).toBe('echo hello');
      expect(entries[1].command).toBe('rm -rf node_modules');
    });

    it('should return empty array for non-existent log', () => {
      const emptyLogger = new AuditLogger(path.join(tempDir, 'nonexistent.log'));
      const entries = emptyLogger.read();
      expect(entries).toEqual([]);
    });

    it('should skip invalid JSON lines', () => {
      // Append invalid JSON
      fs.appendFileSync(logPath, 'invalid json line\n', 'utf-8');

      const entries = logger.read();
      expect(entries).toHaveLength(3); // Should still read valid entries
    });
  });
});
