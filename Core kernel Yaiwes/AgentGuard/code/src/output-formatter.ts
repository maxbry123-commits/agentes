/**
 * OutputFormatter - Handles console output formatting for AgentGuard
 * 
 * Provides consistent, visually clear feedback to users with:
 * - Startup banner with version and configuration info
 * - Blocked command messages with 🚫 emoji
 * - Allowed command messages with ✅ emoji
 * - Confirmation prompts with ⚠️ emoji
 * - Terminal formatting preservation (ANSI escape codes)
 */

import { Rule, ValidationAction, ConfirmOptions } from './types';

export interface BannerConfig {
  version: string;
  command: string;
  rulesCount: number;
  mode: string;
}

export class OutputFormatter {
  private colorEnabled: boolean;

  constructor(colorEnabled: boolean = true) {
    this.colorEnabled = colorEnabled;
  }

  /**
   * Display startup banner with AgentGuard configuration
   * Requirements: 9.1
   */
  displayBanner(config: BannerConfig): void {
    const banner = [
      '╔═══════════════════════════════════════════════════════════╗',
      `║  🛡️  AgentGuard v${config.version.padEnd(44)}║`,
      `║  Protecting: ${config.command.padEnd(44)}║`,
      `║  Rules: .agentguard (${config.rulesCount} rules loaded)${this.padRight(config.rulesCount)}║`,
      `║  Mode: ${config.mode.padEnd(49)}║`,
      '╚═══════════════════════════════════════════════════════════╝'
    ];

    console.log(banner.join('\n'));
  }

  /**
   * Display blocked command message
   * Requirements: 9.2
   */
  displayBlocked(command: string, rule: Rule, reason: string): void {
    const output = [
      `🚫 BLOCKED: ${command}`,
      `Rule: ${rule.pattern}`,
      `Reason: ${reason}`
    ];

    // Write to stderr for blocked commands
    console.error(output.join('\n'));
  }

  /**
   * Display allowed command message
   * Requirements: 9.3
   */
  displayAllowed(command: string, rule: Rule): void {
    const output = [
      `✅ ALLOWED: ${command}`,
      `Rule: ${rule.pattern}`
    ];

    console.log(output.join('\n'));
  }

  /**
   * Display confirmation prompt
   * Requirements: 9.4
   */
  displayConfirm(options: ConfirmOptions): void {
    const lines = [
      `⚠️  CONFIRM: ${options.command}`,
      `Rule: ${options.rule.pattern}`
    ];

    // Add scope information if available
    if (options.metadata) {
      if (options.metadata.affectedFiles !== undefined) {
        lines.push(`Scope: Would affect ${options.metadata.affectedFiles} files`);
      }
      if (options.metadata.targetPaths && options.metadata.targetPaths.length > 0) {
        lines.push(`Targets: ${options.metadata.targetPaths.join(', ')}`);
      }
    }

    const timeout = options.timeout || 30;
    lines.push(`Proceed? [y/N] (timeout in ${timeout}s):`);

    console.log(lines.join('\n'));
  }

  /**
   * Display error message
   */
  displayError(message: string): void {
    console.error(`❌ Error: ${message}`);
  }

  /**
   * Display warning message
   */
  displayWarning(message: string): void {
    console.warn(`⚠️  Warning: ${message}`);
  }

  /**
   * Display info message
   */
  displayInfo(message: string): void {
    console.log(`ℹ️  ${message}`);
  }

  /**
   * Pass through output with ANSI escape codes preserved
   * Requirements: 9.5
   * 
   * This method simply writes the output directly to stdout/stderr
   * without any modification, preserving all terminal formatting.
   */
  passThrough(output: string, useStderr: boolean = false): void {
    if (useStderr) {
      process.stderr.write(output);
    } else {
      process.stdout.write(output);
    }
  }

  /**
   * Helper to pad the rules count line correctly
   */
  private padRight(rulesCount: number): string {
    // Calculate padding needed after "rules loaded)"
    const countStr = rulesCount.toString();
    const baseText = 'Rules: .agentguard ( rules loaded)';
    const actualLength = baseText.length + countStr.length;
    const targetLength = 59; // Total width minus borders
    const padding = targetLength - actualLength;
    return ' '.repeat(Math.max(0, padding));
  }
}
