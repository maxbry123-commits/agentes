/**
 * ProcessSpawner - Manages process spawning with modified environment
 * 
 * Launches target commands with modified SHELL environment variable pointing
 * to the AgentGuard wrapper, enabling command interception and validation.
 * 
 * Key responsibilities:
 * - Detect the real shell to use for executing allowed commands
 * - Build environment with AGENTGUARD_* variables
 * - Spawn target command with modified environment
 * - Display startup banner
 * - Handle process lifecycle and exit codes
 */

import { spawn, ChildProcess } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';
import { SpawnOptions } from './types';
import { Rule } from './types';
import { OutputFormatter, BannerConfig } from './output-formatter';

export class ProcessSpawner {
  private formatter: OutputFormatter;

  constructor(formatter?: OutputFormatter) {
    this.formatter = formatter || new OutputFormatter();
  }

  /**
   * Spawn a process with modified environment
   * Requirements: 1.1
   * 
   * @param options - Spawn configuration
   * @returns Promise resolving to exit code
   */
  async spawn(options: SpawnOptions): Promise<number> {
    const env = this.buildEnvironment(options);

    // Join command for shell execution
    const commandString = options.command.join(' ');

    return new Promise((resolve, reject) => {
      // Route through the guard shell wrapper so commands are validated
      const child = spawn(options.shellPath, ['-c', commandString], {
        env,
        stdio: 'inherit', // Pass through stdin/stdout/stderr
        shell: false
      });

      child.on('exit', (code, signal) => {
        if (signal) {
          // Process was killed by signal
          resolve(128 + this.signalToNumber(signal));
        } else {
          resolve(code || 0);
        }
      });

      child.on('error', (error) => {
        this.formatter.displayError(`Failed to spawn process: ${error.message}`);
        reject(error);
      });
    });
  }

  /**
   * Display startup banner
   * Requirements: 9.1
   * 
   * @param rules - Loaded rules for display
   * @param command - Command being protected
   */
  displayBanner(rules: Rule[], command: string): void {
    const config: BannerConfig = {
      version: '1.0',
      command: command,
      rulesCount: rules.length,
      mode: 'interactive'
    };

    this.formatter.displayBanner(config);
  }

  /**
   * Build environment for spawned process
   * Requirements: 1.1
   *
   * Sets up environment variables:
   * - SHELL: Points to guard shell wrapper
   * - AGENTGUARD_REAL_SHELL: Original shell for executing allowed commands
   * - AGENTGUARD_ORIGINAL_SHELL: Preserved for debugging
   * - AGENTGUARD_ACTIVE: Flag indicating AgentGuard is active
   * - AGENTGUARD_BIN: Directory containing our wrapper scripts
   * - PATH: Modified to include our wrapper directory first
   *
   * @param options - Spawn configuration
   * @returns Modified environment object
   */
  private buildEnvironment(options: SpawnOptions): Record<string, string> {
    const originalShell = this.detectRealShell();

    // Get the directory containing our wrapper scripts
    const wrapperDir = this.getWrapperDir();

    // Prepend our wrapper directory to PATH so our 'bash' is found first
    const originalPath = process.env.PATH || '/usr/bin:/bin';
    const newPath = wrapperDir ? `${wrapperDir}:${originalPath}` : originalPath;

    return {
      ...process.env,
      PATH: newPath,
      SHELL: options.shellPath,
      AGENTGUARD_REAL_SHELL: originalShell,
      AGENTGUARD_REAL_BASH: '/bin/bash',
      AGENTGUARD_ORIGINAL_SHELL: originalShell,
      AGENTGUARD_ACTIVE: '1',
      AGENTGUARD_BIN: wrapperDir || ''
    } as Record<string, string>;
  }

  /**
   * Get the directory containing wrapper scripts (bash, sh)
   * These are symlinks/scripts that intercept shell commands
   */
  private getWrapperDir(): string | null {
    // The wrapper scripts should be in dist/bin/wrappers/
    const wrapperDir = path.join(__dirname, 'bin', 'wrappers');
    if (fs.existsSync(wrapperDir)) {
      return wrapperDir;
    }
    return null;
  }

  /**
   * Detect the real shell to use for executing allowed commands
   * Requirements: 1.1
   * 
   * Priority order:
   * 1. AGENTGUARD_REAL_SHELL (if already wrapped, avoid recursion)
   * 2. SHELL environment variable (user's current shell)
   * 3. /bin/bash (system default fallback)
   * 
   * @returns Path to the real shell
   */
  detectRealShell(): string {
    // Priority 1: Already wrapped (recursive call)
    if (process.env.AGENTGUARD_REAL_SHELL) {
      return process.env.AGENTGUARD_REAL_SHELL;
    }
    
    // Priority 2: User's current shell
    if (process.env.SHELL) {
      return process.env.SHELL;
    }
    
    // Priority 3: System default
    return '/bin/bash';
  }

  /**
   * Convert signal name to exit code
   * Standard convention: 128 + signal number
   * 
   * @param signal - Signal name (e.g., 'SIGTERM', 'SIGINT')
   * @returns Exit code
   */
  private signalToNumber(signal: string): number {
    const signals: Record<string, number> = {
      'SIGHUP': 1,
      'SIGINT': 2,
      'SIGQUIT': 3,
      'SIGILL': 4,
      'SIGTRAP': 5,
      'SIGABRT': 6,
      'SIGBUS': 7,
      'SIGFPE': 8,
      'SIGKILL': 9,
      'SIGUSR1': 10,
      'SIGSEGV': 11,
      'SIGUSR2': 12,
      'SIGPIPE': 13,
      'SIGALRM': 14,
      'SIGTERM': 15
    };

    return signals[signal] || 15; // Default to SIGTERM
  }
}
