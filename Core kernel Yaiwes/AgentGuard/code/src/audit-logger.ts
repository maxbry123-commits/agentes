/**
 * Audit Logger - Records command validation attempts
 */

import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { LogEntry, LogReadOptions } from './types';

export class AuditLogger {
  private logPath: string;
  private maxSize: number;

  constructor(logPath?: string, maxSize: number = 10 * 1024 * 1024) {
    // Default to ~/.agentguard/audit.log
    this.logPath = logPath || path.join(os.homedir(), '.agentguard', 'audit.log');
    this.maxSize = maxSize;
  }

  /**
   * Log a command validation entry
   * Requirements: 8.1, 8.2, 8.4
   */
  log(entry: LogEntry): void {
    try {
      // Ensure log directory exists
      this.ensureLogDirectory();

      // Check if rotation is needed before writing
      if (this.shouldRotate()) {
        this.rotate();
      }

      // Format entry as single-line JSON
      const logLine = JSON.stringify(entry) + '\n';

      // Append to log file
      fs.appendFileSync(this.logPath, logLine, 'utf-8');
    } catch (error) {
      // Resilient logging: log error to stderr but don't throw
      // Requirement 8.5: Continue operation if log writes fail
      console.error(`Warning: Failed to write audit log: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * Rotate log file when it exceeds maxSize
   * Requirement 8.3
   */
  rotate(): void {
    try {
      // Check if log file exists
      if (!fs.existsSync(this.logPath)) {
        return;
      }

      // Create timestamped backup filename
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const backupPath = `${this.logPath}.${timestamp}`;

      // Rename current log to backup
      fs.renameSync(this.logPath, backupPath);

      // New log file will be created on next write
    } catch (error) {
      // Log error but don't throw
      console.error(`Warning: Failed to rotate audit log: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * Read log entries from the audit log
   */
  read(options?: LogReadOptions): LogEntry[] {
    try {
      // Check if log file exists
      if (!fs.existsSync(this.logPath)) {
        return [];
      }

      // Read log file
      const content = fs.readFileSync(this.logPath, 'utf-8');
      const lines = content.trim().split('\n').filter(line => line.length > 0);

      // Parse JSON lines
      const entries: LogEntry[] = [];
      for (const line of lines) {
        try {
          const entry = JSON.parse(line) as LogEntry;
          entries.push(entry);
        } catch (parseError) {
          // Skip invalid JSON lines
          console.error(`Warning: Invalid JSON in audit log: ${line}`);
        }
      }

      // Apply filters
      let filtered = entries;

      if (options?.action) {
        filtered = filtered.filter(e => e.action === options.action);
      }

      if (options?.since) {
        filtered = filtered.filter(e => new Date(e.timestamp) >= options.since!);
      }

      // Apply limit (default 50, most recent entries)
      const limit = options?.limit ?? 50;
      if (filtered.length > limit) {
        filtered = filtered.slice(-limit);
      }

      return filtered;
    } catch (error) {
      console.error(`Warning: Failed to read audit log: ${error instanceof Error ? error.message : String(error)}`);
      return [];
    }
  }

  /**
   * Ensure the log directory exists
   */
  private ensureLogDirectory(): void {
    const logDir = path.dirname(this.logPath);
    
    if (!fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }
  }

  /**
   * Check if log file should be rotated
   */
  private shouldRotate(): boolean {
    try {
      if (!fs.existsSync(this.logPath)) {
        return false;
      }

      const stats = fs.statSync(this.logPath);
      return stats.size >= this.maxSize;
    } catch (error) {
      // If we can't check, assume no rotation needed
      return false;
    }
  }
}
