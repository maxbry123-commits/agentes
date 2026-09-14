/**
 * Command Unwrapper - Recursively unwraps command wrappers to find the actual command
 *
 * Handles wrappers like:
 * - sudo rm -rf /             → rm -rf /
 * - bash -c "rm -rf /"        → rm -rf /
 * - xargs rm                  → rm (with dynamic args)
 * - find / -exec rm {} \;     → rm (with dynamic args)
 * - env VAR=val rm -rf /      → rm -rf /
 * - nice -n 10 rm -rf /       → rm -rf /
 */

import * as path from 'path';
import { CommandSegment, UnwrappedCommand } from './types';

// Commands that simply pass through to another command
const PASSTHROUGH_WRAPPERS: Record<string, { skipFlags: boolean; flagsWithArgs: string[] }> = {
  'sudo': { skipFlags: true, flagsWithArgs: ['-u', '-g', '-C', '-D', '-h', '-p', '-r', '-t', '-T', '-U'] },
  'doas': { skipFlags: true, flagsWithArgs: ['-u', '-C'] },
  'env': { skipFlags: true, flagsWithArgs: [] },  // env handles VAR=val specially
  'nice': { skipFlags: true, flagsWithArgs: ['-n', '--adjustment'] },
  'nohup': { skipFlags: false, flagsWithArgs: [] },
  'time': { skipFlags: true, flagsWithArgs: ['-f', '-o', '-a', '-p'] },
  'timeout': { skipFlags: true, flagsWithArgs: ['--signal', '-s', '-k'] },
  'watch': { skipFlags: true, flagsWithArgs: ['-n', '-d', '-t', '-g'] },
  'strace': { skipFlags: true, flagsWithArgs: ['-e', '-o', '-p', '-s', '-u'] },
  'ltrace': { skipFlags: true, flagsWithArgs: ['-e', '-o', '-p', '-s', '-u'] },
  'ionice': { skipFlags: true, flagsWithArgs: ['-c', '-n', '-p'] },
  'chroot': { skipFlags: true, flagsWithArgs: ['--userspec', '--groups'] },
  'runuser': { skipFlags: true, flagsWithArgs: ['-u', '-g', '-G'] },  // Note: -c handled specially
};

// Commands that use -c "command" like shells (su, runuser)
const SHELL_LIKE_C_WRAPPERS = ['su', 'runuser'];

// Shell commands that take -c "command" syntax
const SHELL_WRAPPERS = ['sh', 'bash', 'zsh', 'dash', 'fish', 'ksh', 'csh', 'tcsh'];

// Commands that execute other commands with dynamic arguments
const DYNAMIC_EXECUTORS = ['xargs', 'parallel'];

export class CommandUnwrapper {
  /**
   * Unwrap a command segment to find the actual command being executed.
   * Recursively handles nested wrappers.
   */
  unwrap(segment: CommandSegment): UnwrappedCommand[] {
    return this.unwrapRecursive(segment, []);
  }

  private unwrapRecursive(segment: CommandSegment, wrappers: string[]): UnwrappedCommand[] {
    const baseCommand = path.basename(segment.command);
    const results: UnwrappedCommand[] = [];

    // Check for su/runuser -c patterns (must check before passthrough)
    if (SHELL_LIKE_C_WRAPPERS.includes(baseCommand)) {
      const unwrapped = this.unwrapShellLikeC(segment, baseCommand, wrappers);
      if (unwrapped.length > 0) {
        return unwrapped;
      }
    }

    // Check for chroot (special: first non-flag arg is path, then command)
    if (baseCommand === 'chroot') {
      const unwrapped = this.unwrapChroot(segment, wrappers);
      if (unwrapped) {
        return unwrapped;
      }
    }

    // Check for passthrough wrappers (sudo, env, nice, etc.)
    if (PASSTHROUGH_WRAPPERS[baseCommand]) {
      const unwrapped = this.unwrapPassthrough(segment, baseCommand, wrappers);
      if (unwrapped) {
        return unwrapped;
      }
    }

    // Check for shell -c wrappers
    if (SHELL_WRAPPERS.includes(baseCommand)) {
      const unwrapped = this.unwrapShellC(segment, baseCommand, wrappers);
      if (unwrapped.length > 0) {
        return unwrapped;
      }
    }

    // Check for xargs/parallel
    if (DYNAMIC_EXECUTORS.includes(baseCommand)) {
      const unwrapped = this.unwrapXargs(segment, baseCommand, wrappers);
      if (unwrapped) {
        results.push(unwrapped);
        return results;
      }
    }

    // Check for find -exec/-delete
    if (baseCommand === 'find') {
      const unwrapped = this.unwrapFind(segment, wrappers);
      if (unwrapped.length > 0) {
        return unwrapped;
      }
    }

    // No wrapper detected - this is the actual command
    results.push({
      command: segment.command,
      args: segment.args,
      wrappers,
      hasDynamicArgs: false,
      originalSegment: segment
    });

    return results;
  }

  /**
   * Unwrap passthrough wrappers like sudo, env, nice, etc.
   */
  private unwrapPassthrough(
    segment: CommandSegment,
    wrapper: string,
    currentWrappers: string[]
  ): UnwrappedCommand[] | null {
    const config = PASSTHROUGH_WRAPPERS[wrapper];
    const args = segment.args;
    let cmdStart = 0;

    // Track if we've seen the duration for timeout
    let seenTimeoutDuration = false;

    // Find where the actual command starts
    while (cmdStart < args.length) {
      const arg = args[cmdStart];

      // Handle env's VAR=val syntax
      if (wrapper === 'env' && arg.includes('=') && !arg.startsWith('-')) {
        cmdStart++;
        continue;
      }

      // Handle timeout's duration argument (first non-flag argument is duration)
      if (wrapper === 'timeout' && !seenTimeoutDuration && !arg.startsWith('-')) {
        // This is the duration argument (e.g., "30", "10s", "1m")
        seenTimeoutDuration = true;
        cmdStart++;
        continue;
      }

      // Skip flags
      if (arg.startsWith('-')) {
        if (config.skipFlags) {
          // Check if this flag takes an argument
          const flagWithArg = config.flagsWithArgs.find(f =>
            arg === f || arg.startsWith(f + '=')
          );

          if (flagWithArg && !arg.includes('=')) {
            // Skip the flag and its argument
            cmdStart += 2;
          } else {
            cmdStart++;
          }
          continue;
        }
      }

      // Found the start of the actual command
      break;
    }

    if (cmdStart >= args.length) {
      return null; // No command found after wrapper
    }

    // Create new segment with the unwrapped command
    const newSegment: CommandSegment = {
      command: args[cmdStart],
      args: args.slice(cmdStart + 1),
      operator: segment.operator
    };

    // Recursively unwrap
    return this.unwrapRecursive(newSegment, [...currentWrappers, wrapper]);
  }

  /**
   * Unwrap su/runuser -c "command" patterns
   * These commands use -c to execute a shell command string
   */
  private unwrapShellLikeC(
    segment: CommandSegment,
    wrapper: string,
    currentWrappers: string[]
  ): UnwrappedCommand[] {
    const args = segment.args;

    // Look for -c flag
    for (let i = 0; i < args.length; i++) {
      if (args[i] === '-c' && i + 1 < args.length) {
        const commandString = args[i + 1];

        // Parse the command string into segments
        const innerSegments = this.parseCommandString(commandString);
        const results: UnwrappedCommand[] = [];

        for (const innerSegment of innerSegments) {
          const unwrapped = this.unwrapRecursive(
            innerSegment,
            [...currentWrappers, `${wrapper} -c`]
          );
          results.push(...unwrapped);
        }

        return results;
      }
    }

    return [];
  }

  /**
   * Unwrap chroot: first non-flag arg is the root path, then the command
   * Example: chroot /mnt rm -rf / → rm -rf /
   */
  private unwrapChroot(
    segment: CommandSegment,
    currentWrappers: string[]
  ): UnwrappedCommand[] | null {
    const config = PASSTHROUGH_WRAPPERS['chroot'];
    const args = segment.args;
    let i = 0;

    // Skip flags
    while (i < args.length) {
      const arg = args[i];
      if (arg.startsWith('-')) {
        const flagWithArg = config.flagsWithArgs.find(f =>
          arg === f || arg.startsWith(f + '=')
        );
        if (flagWithArg && !arg.includes('=')) {
          i += 2;
        } else {
          i++;
        }
      } else {
        break;
      }
    }

    // First non-flag arg is the new root path
    if (i >= args.length) return null;
    i++; // Skip the root path

    // Next arg (if any) is the command
    if (i >= args.length) return null;

    const newSegment: CommandSegment = {
      command: args[i],
      args: args.slice(i + 1),
      operator: segment.operator
    };

    return this.unwrapRecursive(newSegment, [...currentWrappers, 'chroot']);
  }

  /**
   * Unwrap shell -c "command" patterns
   */
  private unwrapShellC(
    segment: CommandSegment,
    shell: string,
    currentWrappers: string[]
  ): UnwrappedCommand[] {
    const args = segment.args;

    // Look for -c flag
    for (let i = 0; i < args.length; i++) {
      if (args[i] === '-c' && i + 1 < args.length) {
        const commandString = args[i + 1];

        // Parse the command string into segments
        const innerSegments = this.parseCommandString(commandString);
        const results: UnwrappedCommand[] = [];

        for (const innerSegment of innerSegments) {
          const unwrapped = this.unwrapRecursive(
            innerSegment,
            [...currentWrappers, `${shell} -c`]
          );
          results.push(...unwrapped);
        }

        return results;
      }
    }

    return [];
  }

  /**
   * Unwrap xargs/parallel commands
   */
  private unwrapXargs(
    segment: CommandSegment,
    executor: string,
    currentWrappers: string[]
  ): UnwrappedCommand | null {
    const args = segment.args;
    let cmdStart = 0;

    // Skip xargs/parallel flags
    while (cmdStart < args.length && args[cmdStart].startsWith('-')) {
      const arg = args[cmdStart];
      // Flags that take arguments (xargs and parallel)
      if (['-I', '-L', '-n', '-P', '-s', '-E', '-d', '--delimiter',
           '-j', '--jobs', '-S', '--sshlogin', '--retries'].some(f => arg === f)) {
        cmdStart += 2;
      } else {
        cmdStart++;
      }
    }

    if (cmdStart >= args.length) {
      return null;
    }

    // The command after xargs flags
    const targetCommand = args[cmdStart];
    const targetArgs = args.slice(cmdStart + 1);

    return {
      command: targetCommand,
      args: targetArgs,
      wrappers: [...currentWrappers, executor],
      hasDynamicArgs: true,
      dynamicReason: `${executor} - arguments come from stdin/pipeline`,
      originalSegment: segment
    };
  }

  /**
   * Unwrap find -exec and -delete patterns
   */
  private unwrapFind(segment: CommandSegment, currentWrappers: string[]): UnwrappedCommand[] {
    const args = segment.args;
    const results: UnwrappedCommand[] = [];

    for (let i = 0; i < args.length; i++) {
      const arg = args[i];

      // Handle -delete (find itself is destructive)
      if (arg === '-delete') {
        results.push({
          command: 'find',
          args: segment.args,
          wrappers: currentWrappers,
          hasDynamicArgs: true,
          dynamicReason: 'find -delete - targets are dynamically matched',
          originalSegment: segment
        });
      }

      // Handle -exec and variants
      if (['-exec', '-execdir', '-ok', '-okdir'].includes(arg)) {
        // Find the command and arguments until \; or +
        const execStart = i + 1;
        let execEnd = execStart;

        while (execEnd < args.length) {
          if (args[execEnd] === ';' || args[execEnd] === '\\;' || args[execEnd] === '+') {
            break;
          }
          execEnd++;
        }

        if (execStart < execEnd) {
          const execCommand = args[execStart];
          const execArgs = args.slice(execStart + 1, execEnd)
            .filter(a => a !== '{}'); // Remove placeholder

          results.push({
            command: execCommand,
            args: execArgs,
            wrappers: [...currentWrappers, `find ${arg}`],
            hasDynamicArgs: true,
            dynamicReason: `find ${arg} - targets are dynamically matched files`,
            originalSegment: segment
          });
        }

        // Skip past this -exec block
        i = execEnd;
      }
    }

    return results;
  }

  /**
   * Parse a command string into segments (handles pipes, chains, etc.)
   * Simplified version - for complex parsing, use the full tokenizer
   */
  private parseCommandString(commandString: string): CommandSegment[] {
    const segments: CommandSegment[] = [];

    // Split on shell operators (simplified - doesn't handle all edge cases)
    const parts = commandString.split(/\s*(?:&&|\|\||\||;)\s*/);

    for (const part of parts) {
      const trimmed = part.trim();
      if (!trimmed) continue;

      // Simple tokenization by spaces (doesn't handle quotes perfectly)
      const tokens = this.simpleTokenize(trimmed);
      if (tokens.length > 0) {
        segments.push({
          command: tokens[0],
          args: tokens.slice(1)
        });
      }
    }

    return segments;
  }

  /**
   * Simple tokenization that handles basic quoting
   */
  private simpleTokenize(str: string): string[] {
    const tokens: string[] = [];
    let current = '';
    let inSingle = false;
    let inDouble = false;

    for (let i = 0; i < str.length; i++) {
      const char = str[i];

      if (char === "'" && !inDouble) {
        inSingle = !inSingle;
      } else if (char === '"' && !inSingle) {
        inDouble = !inDouble;
      } else if (char === ' ' && !inSingle && !inDouble) {
        if (current) {
          tokens.push(current);
          current = '';
        }
      } else {
        current += char;
      }
    }

    if (current) {
      tokens.push(current);
    }

    return tokens;
  }
}
