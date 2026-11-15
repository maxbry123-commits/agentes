/**
 * Confirmation Handler - Handles user confirmation prompts for CONFIRM rules
 */

import * as readline from 'readline';
import { ConfirmOptions, ConfirmResult } from './types';

export class ConfirmationHandler {
  /**
   * Display confirmation prompt and get user response
   * @param options Confirmation options including command, rule, and timeout
   * @returns Promise resolving to confirmation result
   */
  async confirm(options: ConfirmOptions): Promise<ConfirmResult> {
    // Display the prompt
    this.displayPrompt(options);

    // Read user input with timeout
    const timeout = options.timeout || 30000; // Default 30 seconds
    try {
      const input = await this.readInput(timeout);
      const approved = input.toLowerCase() === 'y';
      return { approved, timedOut: false };
    } catch (error) {
      // Timeout occurred - display timeout message
      console.error(''); // New line after prompt
      console.error('⏱️  Confirmation timeout - command blocked');
      return { approved: false, timedOut: true };
    }
  }

  /**
   * Display the confirmation prompt with command details
   */
  private displayPrompt(options: ConfirmOptions): void {
    console.error(''); // Blank line for spacing
    console.error(`⚠️  CONFIRM: ${options.command}`);
    console.error(`Rule: ${options.rule.pattern}`);
    
    // Display scope information if available
    if (options.metadata) {
      if (options.metadata.affectedFiles !== undefined) {
        console.error(`Scope: Would affect ${options.metadata.affectedFiles} file(s)`);
      }
      if (options.metadata.targetPaths && options.metadata.targetPaths.length > 0) {
        console.error(`Target paths: ${options.metadata.targetPaths.join(', ')}`);
      }
    }
    
    const timeoutSeconds = Math.floor((options.timeout || 30000) / 1000);
    process.stderr.write(`Proceed? [y/N] (timeout in ${timeoutSeconds}s): `);
  }

  /**
   * Read user input from stdin with timeout
   * @param timeout Timeout in milliseconds
   * @returns Promise resolving to user input string
   * @throws Error if timeout occurs
   */
  private readInput(timeout: number): Promise<string> {
    return new Promise((resolve, reject) => {
      let resolved = false;

      const rl = readline.createInterface({
        input: process.stdin,
        output: process.stderr,
        terminal: false
      });

      // Set up timeout
      const timer = setTimeout(() => {
        if (!resolved) {
          resolved = true;
          rl.close();
          reject(new Error('Timeout'));
        }
      }, timeout);

      // Read one line of input
      rl.once('line', (line) => {
        if (!resolved) {
          resolved = true;
          clearTimeout(timer);
          rl.close();
          resolve(line.trim());
        }
      });

      // Handle stdin close/error - treat as timeout/rejection
      rl.once('close', () => {
        clearTimeout(timer);
        if (!resolved) {
          resolved = true;
          reject(new Error('Stdin closed'));
        }
      });
    });
  }
}
