/**
 * CLI Interface - Main command-line interface
 */

import * as path from 'path';
import { CLIOptions } from './types';
import { RuleParser } from './rule-parser';
import { ProcessSpawner } from './process-spawner';
import { OutputFormatter } from './output-formatter';

export class CLI {
  /**
   * Main entry point for CLI
   * Requirements: 1.1
   * 
   * Parses arguments and routes to appropriate handler:
   * - init: Create default .agentguard file
   * - check: Test command validation without execution
   * - log: View audit log
   * - wrap (default): Wrap command with protection
   */
  async run(args: string[]): Promise<number> {
    try {
      // Handle help flag
      if (args.length === 0 || args[0] === '--help' || args[0] === '-h') {
        this.displayUsage();
        return args.length === 0 ? 1 : 0;
      }

      // Handle version flag
      if (args[0] === '--version' || args[0] === '-v' || args[0] === 'version') {
        const packageJson = require('../package.json');
        console.log(`ai-agentguard v${packageJson.version}`);
        return 0;
      }

      const subcommand = args[0];

      // Handle init subcommand
      if (subcommand === 'init') {
        await this.handleInit();
        return 0;
      }

      // Handle check subcommand
      if (subcommand === 'check') {
        if (args.length < 2) {
          console.error('Error: check command requires a command argument');
          console.error('Usage: agentguard check "<command>"');
          return 1;
        }
        await this.handleCheck(args[1]);
        return 0;
      }

      // Handle log subcommand
      if (subcommand === 'log') {
        await this.handleLog();
        return 0;
      }

      // Handle install subcommand
      if (subcommand === 'install') {
        const target = args[1] || 'claude';
        await this.handleInstall(target, args.includes('--global'));
        return 0;
      }

      // Handle uninstall subcommand
      if (subcommand === 'uninstall') {
        const target = args[1] || 'claude';
        await this.handleUninstall(target, args.includes('--global'));
        return 0;
      }

      // Default: wrap command
      const options = this.parseArgs(args);
      await this.handleWrap(options);
      return 0;
    } catch (error) {
      console.error('Error:', error instanceof Error ? error.message : String(error));
      return 1;
    }
  }

  /**
   * Parse command-line arguments for wrap command
   * Requirements: 1.1
   * 
   * Supports:
   * - --verbose: Enable verbose output
   * - --dry-run: Test mode, don't execute
   * - --config <path>: Override config file location
   */
  private parseArgs(args: string[]): CLIOptions {
    const options: CLIOptions = {
      command: [],
      verbose: false,
      dryRun: false
    };

    let foundSeparator = false;

    for (let i = 0; i < args.length; i++) {
      const arg = args[i];

      // After --, everything is part of the command
      if (foundSeparator) {
        options.command.push(arg);
        continue;
      }

      // -- separates agentguard flags from the command to run
      if (arg === '--') {
        foundSeparator = true;
        continue;
      }

      if (arg === '--verbose') {
        options.verbose = true;
      } else if (arg === '--dry-run') {
        options.dryRun = true;
      } else if (arg === '--config') {
        if (i + 1 >= args.length) {
          throw new Error('--config requires a path argument');
        }
        options.configPath = args[++i];
      } else if (arg.startsWith('--')) {
        throw new Error(`Unknown flag: ${arg}`);
      } else {
        // Everything else is part of the command
        options.command.push(arg);
      }
    }

    if (options.command.length === 0) {
      throw new Error('No command specified to wrap');
    }

    return options;
  }

  /**
   * Display usage information
   */
  private displayUsage(): void {
    console.log(`
AgentGuard - Command-line security tool for AI agents

Usage:
  agentguard [flags] -- <command>   Wrap command with protection
  agentguard init                   Create default .agentguard file
  agentguard check "<command>"      Test command validation
  agentguard install [target]       Install hook for AI agent (default: claude)
  agentguard uninstall [target]     Remove hook for AI agent
  agentguard log                    View audit log

Targets:
  claude                            Claude Code (hook-based, recommended)
  cursor                            Cursor (hook-based)
  kiro                              Kiro CLI (hook-based)
  opencode                          OpenCode (plugin-based)

Install Flags:
  --global                          Install globally (~/.claude/settings.json or ~/.cursor/settings.json)
                                    Default: project-local (.claude/settings.json or .cursor/settings.json)

Flags:
  --verbose                         Enable verbose output
  --dry-run                         Test mode, don't execute
  --config <path>                   Override config file location

Examples:
  agentguard init                   Create .agentguard rules in current directory
  agentguard install claude         Install Claude Code hook (project-local)
  agentguard install claude --global Install Claude Code hook (global)
  agentguard install cursor         Install Cursor hook (project-local)
  agentguard install cursor --global Install Cursor hook (global)
  agentguard install kiro           Install Kiro CLI hook (project-local)
  agentguard install kiro --global  Install Kiro CLI hook (global)
  agentguard install opencode       Install OpenCode plugin (project-local)
  agentguard install opencode --global Install OpenCode plugin (global)
  agentguard uninstall claude       Remove Claude Code hook
  agentguard uninstall cursor       Remove Cursor hook
  agentguard uninstall kiro         Remove Kiro CLI hook
  agentguard uninstall opencode     Remove OpenCode plugin
  agentguard uninstall kiro         Remove Kiro CLI hook
  agentguard -- claude              Wrap Claude with protection (legacy)
  agentguard -- kiro chat           Wrap Kiro CLI with protection (legacy)
  agentguard check "rm -rf /"       Test if command would be blocked
    `.trim());
  }

  /**
   * Handle init command - Create default .agentguard file
   * Requirements: 10.1, 10.5
   * 
   * Steps:
   * 1. Check if .agentguard exists in current directory
   * 2. If exists, prompt user for confirmation
   * 3. Copy default-rules.txt to .agentguard
   * 4. Display success message
   */
  private async handleInit(): Promise<void> {
    const fs = await import('fs');
    const readline = await import('readline');
    
    const targetPath = path.join(process.cwd(), '.agentguard');
    const templatePath = path.join(__dirname, '..', 'templates', 'default-rules.txt');

    // Check if .agentguard already exists
    if (fs.existsSync(targetPath)) {
      // Prompt user for confirmation
      const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout
      });

      const answer = await new Promise<string>((resolve) => {
        rl.question('.agentguard file already exists. Overwrite? [y/N]: ', (answer) => {
          rl.close();
          resolve(answer);
        });
      });

      if (answer.toLowerCase() !== 'y' && answer.toLowerCase() !== 'yes') {
        console.log('Init cancelled.');
        return;
      }
    }

    // Check if template exists
    if (!fs.existsSync(templatePath)) {
      throw new Error(`Template file not found at ${templatePath}`);
    }

    // Copy template to .agentguard
    fs.copyFileSync(templatePath, targetPath);

    // Display success message
    console.log('✅ Created .agentguard file in current directory');
    console.log('');
    console.log('The file contains sensible defaults for protecting your system:');
    console.log('  - BLOCK rules for catastrophic commands (rm -rf /, mkfs, dd)');
    console.log('  - CONFIRM rules for dangerous commands (rm -rf *, git push --force)');
    console.log('  - ALLOW rules for safe cleanup (rm -rf node_modules, dist, build)');
    console.log('');
    console.log('Edit .agentguard to customize rules for your project.');
  }

  /**
   * Handle check command - Test command validation without execution
   * Requirements: 11.1, 11.2, 11.3, 11.4
   * 
   * Steps:
   * 1. Load rules from all sources
   * 2. Create validator and validate command
   * 3. Display result (block/allow/confirm) and matched rule
   * 4. Do NOT execute the command
   * 5. Do NOT log to audit
   */
  private async handleCheck(command: string): Promise<void> {
    const { Validator } = await import('./validator');
    const { ValidationAction } = await import('./types');
    
    // Load rules and validate
    const validator = new Validator();
    const result = validator.validate(command);

    // Display result based on action
    const formatter = new OutputFormatter();
    
    switch (result.action) {
      case ValidationAction.BLOCK:
        console.log('🚫 WOULD BE BLOCKED');
        console.log(`Command: ${command}`);
        if (result.rule) {
          console.log(`Matched Rule: ${result.rule.pattern}`);
          console.log(`Rule Source: ${result.rule.source}`);
        }
        console.log(`Reason: ${result.reason}`);
        break;
      
      case ValidationAction.ALLOW:
        console.log('✅ WOULD BE ALLOWED');
        console.log(`Command: ${command}`);
        if (result.rule) {
          console.log(`Matched Rule: ${result.rule.pattern}`);
          console.log(`Rule Source: ${result.rule.source}`);
        } else {
          console.log('Matched Rule: (none - default allow policy)');
        }
        console.log(`Reason: ${result.reason}`);
        break;
      
      case ValidationAction.CONFIRM:
        console.log('⚠️  WOULD REQUIRE CONFIRMATION');
        console.log(`Command: ${command}`);
        if (result.rule) {
          console.log(`Matched Rule: ${result.rule.pattern}`);
          console.log(`Rule Source: ${result.rule.source}`);
        }
        console.log(`Reason: ${result.reason}`);
        console.log('');
        console.log('Note: In normal operation, you would be prompted to approve or deny this command.');
        break;
    }
  }

  private async handleLog(): Promise<void> {
    // TODO: Handle log command
    throw new Error('log command not yet implemented');
  }

  /**
   * Install Kiro hook configuration
   */
  private async installKiroHook(global: boolean): Promise<void> {
    const fs = await import('fs');
    const os = await import('os');

    // Determine config path
    const configDir = global
      ? path.join(os.homedir(), '.config', 'kiro')
      : path.join(process.cwd(), '.kiro');
    const configPath = path.join(configDir, 'agent.json');

    // Determine hook command path - always use absolute path
    const hookPath = path.join(__dirname, 'bin', 'kiro-hook.js');

    // Create directory if it doesn't exist
    if (!fs.existsSync(configDir)) {
      fs.mkdirSync(configDir, { recursive: true });
    }

    // Load existing config or create new
    let config: Record<string, unknown> = {};
    if (fs.existsSync(configPath)) {
      try {
        config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
      } catch (e) {
        console.warn('Warning: Could not parse existing agent.json, creating new one');
      }
    }

    // Add/update hooks configuration
    const hooks = config.hooks as Record<string, unknown>[] || [];
    
    // Remove existing AgentGuard hook if present
    const filteredHooks = hooks.filter((hook: any) => 
      !hook.command?.includes('agentguard') && !hook.command?.includes('kiro-hook')
    );

    // Add new AgentGuard hook
    filteredHooks.push({
      event: 'PreToolUse',
      matcher: 'execute_bash',
      command: `node ${hookPath}`,
      timeout_ms: 5000
    });

    config.hooks = filteredHooks;

    // Write updated config
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));

    // Success message
    const location = global ? 'globally' : 'for this project';
    console.log(`✅ AgentGuard hook installed ${location}`);
    console.log('');
    console.log(`Config file: ${configPath}`);
    console.log('');
    console.log('The hook will now validate all bash commands before execution.');
    console.log('Commands matching BLOCK rules in .agentguard will be prevented.');
  }

  /**
   * Install OpenCode plugin
   */
  private async installOpenCodePlugin(global: boolean): Promise<void> {
    const fs = await import('fs');
    const os = await import('os');

    // Determine plugin directory
    const pluginDir = global
      ? path.join(os.homedir(), '.config', 'opencode', 'plugin')
      : path.join(process.cwd(), '.opencode', 'plugin');

    // Create directory if it doesn't exist
    if (!fs.existsSync(pluginDir)) {
      fs.mkdirSync(pluginDir, { recursive: true });
    }

    const pluginPath = path.join(pluginDir, 'agentguard.js');
    const hookPath = path.join(__dirname, '..', 'validator.js');

    // Create the plugin file
    const pluginContent = `
const { Validator } = require('${hookPath}');

export const AgentGuardPlugin = async ({ project, client, $, directory, worktree }) => {
  return {
    "tool.execute.before": async (input, output) => {
      // Only validate bash/shell commands
      if (input.tool !== 'bash' && input.tool !== 'execute_bash') {
        return;
      }

      const command = output.args?.command;
      if (!command) {
        return;
      }

      // Validate through AgentGuard
      const validator = new Validator();
      const result = validator.validate(command);

      if (result.action === 'BLOCK') {
        throw new Error(\`🚫 AgentGuard BLOCKED: \${command}\\nRule: \${result.rule?.pattern}\\nReason: \${result.reason}\`);
      }

      if (result.action === 'CONFIRM') {
        throw new Error(\`⚠️ AgentGuard CONFIRM required: \${command}\\nThis command requires manual confirmation. Run it directly in terminal.\`);
      }
    },
  };
};
`.trim();

    fs.writeFileSync(pluginPath, pluginContent);

    // Success message
    const location = global ? 'globally' : 'for this project';
    console.log(`✅ AgentGuard plugin installed ${location}`);
    console.log('');
    console.log(`Plugin file: ${pluginPath}`);
    console.log('');
    console.log('The plugin will intercept all bash commands and validate them against');
    console.log('your .agentguard rules before execution.');
    console.log('');
    console.log('Next steps:');
    console.log('  1. Run "agentguard init" to create default rules (if not already done)');
    console.log('  2. Restart OpenCode to activate the plugin');
    console.log('  3. Edit .agentguard to customize rules for your project');
  }

  /**
   * Uninstall Kiro hook configuration
   */
  private async uninstallKiroHook(global: boolean): Promise<void> {
    const fs = await import('fs');
    const os = await import('os');

    // Determine config path
    const configDir = global
      ? path.join(os.homedir(), '.config', 'kiro')
      : path.join(process.cwd(), '.kiro');
    const configPath = path.join(configDir, 'agent.json');

    if (!fs.existsSync(configPath)) {
      console.log('No Kiro config file found. Nothing to uninstall.');
      return;
    }

    // Load existing config
    let config: Record<string, unknown>;
    try {
      config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
    } catch (e) {
      throw new Error('Could not parse agent.json');
    }

    // Remove AgentGuard hooks
    if (config.hooks) {
      const hooks = config.hooks as Record<string, unknown>[];
      const filteredHooks = hooks.filter((hook: any) => 
        !hook.command?.includes('agentguard') && !hook.command?.includes('kiro-hook')
      );

      if (filteredHooks.length < hooks.length) {
        config.hooks = filteredHooks;
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));

        const location = global ? 'globally' : 'for this project';
        console.log(`✅ AgentGuard hook uninstalled ${location}`);
        console.log('');
        console.log('Kiro will no longer validate commands through AgentGuard.');
      } else {
        console.log('No AgentGuard hook found in config. Nothing to uninstall.');
      }
    } else {
      console.log('No hooks found in config. Nothing to uninstall.');
    }
  }

  /**
   * Install Cursor hook configuration
   */
  private async installCursorHook(global: boolean): Promise<void> {
    const fs = await import('fs');
    const os = await import('os');

    // Determine settings path
    const settingsDir = global
      ? path.join(os.homedir(), '.cursor')
      : path.join(process.cwd(), '.cursor');
    const settingsPath = path.join(settingsDir, 'settings.json');

    // Determine hook command path - always use absolute path
    const hookPath = path.join(__dirname, 'bin', 'cursor-hook.js');

    // Create directory if it doesn't exist
    if (!fs.existsSync(settingsDir)) {
      fs.mkdirSync(settingsDir, { recursive: true });
    }

    // Load existing settings or create new
    let settings: Record<string, unknown> = {};
    if (fs.existsSync(settingsPath)) {
      try {
        const content = fs.readFileSync(settingsPath, 'utf8');
        settings = JSON.parse(content);
      } catch (error) {
        console.warn(`Warning: Could not parse existing settings file. Creating new one.`);
      }
    }

    // Ensure hooks structure exists
    if (!settings.hooks) {
      settings.hooks = {};
    }

    const hooks = settings.hooks as Record<string, unknown>;
    if (!hooks.PreToolUse) {
      hooks.PreToolUse = [];
    }

    const preToolUseHooks = hooks.PreToolUse as Array<unknown>;

    // Check if AgentGuard hook already exists
    const existingHookIndex = preToolUseHooks.findIndex((hook: any) => 
      hook?.hooks?.[0]?.command?.includes('cursor-hook.js')
    );

    const newHook = {
      matcher: "Bash",
      hooks: [
        {
          type: "command",
          command: `node ${hookPath}`
        }
      ]
    };

    if (existingHookIndex >= 0) {
      // Update existing hook
      preToolUseHooks[existingHookIndex] = newHook;
    } else {
      // Add new hook
      preToolUseHooks.push(newHook);
    }

    // Write settings file
    fs.writeFileSync(settingsPath, JSON.stringify(settings, null, 2));

    // Success message
    const location = global ? 'globally' : 'for this project';
    console.log(`✅ AgentGuard hook installed ${location}`);
    console.log('');
    console.log(`Settings file: ${settingsPath}`);
    console.log('');
    console.log('Restart Cursor for changes to take effect.');
    console.log('');
    console.log('AgentGuard will now validate Bash commands before Cursor executes them.');
  }

  /**
   * Uninstall Cursor hook configuration
   */
  private async uninstallCursorHook(global: boolean): Promise<void> {
    const fs = await import('fs');
    const os = await import('os');

    // Determine settings path
    const settingsDir = global
      ? path.join(os.homedir(), '.cursor')
      : path.join(process.cwd(), '.cursor');
    const settingsPath = path.join(settingsDir, 'settings.json');

    if (!fs.existsSync(settingsPath)) {
      console.log('No Cursor settings file found. Nothing to uninstall.');
      return;
    }

    // Load existing settings
    let settings: Record<string, unknown>;
    try {
      const content = fs.readFileSync(settingsPath, 'utf8');
      settings = JSON.parse(content);
    } catch (error) {
      console.log('Could not parse settings file. Nothing to uninstall.');
      return;
    }

    // Check if hooks exist
    const hooks = settings.hooks as Record<string, unknown>;
    if (hooks && hooks.PreToolUse) {
      const preToolUseHooks = hooks.PreToolUse as Array<unknown>;
      
      // Remove AgentGuard hooks
      const filteredHooks = preToolUseHooks.filter((hook: any) => 
        !hook?.hooks?.[0]?.command?.includes('cursor-hook.js')
      );

      if (filteredHooks.length !== preToolUseHooks.length) {
        hooks.PreToolUse = filteredHooks;
        
        // Write updated settings
        fs.writeFileSync(settingsPath, JSON.stringify(settings, null, 2));

        const location = global ? 'globally' : 'for this project';
        console.log(`✅ AgentGuard hook uninstalled ${location}`);
        console.log('');
        console.log('Cursor will no longer validate commands through AgentGuard.');
      } else {
        console.log('No AgentGuard hook found in settings. Nothing to uninstall.');
      }
    } else {
      console.log('No hooks found in settings. Nothing to uninstall.');
    }
  }

  /**
   * Uninstall OpenCode plugin
   */
  private async uninstallOpenCodePlugin(global: boolean): Promise<void> {
    const fs = await import('fs');
    const os = await import('os');

    // Determine plugin directory
    const pluginDir = global
      ? path.join(os.homedir(), '.config', 'opencode', 'plugin')
      : path.join(process.cwd(), '.opencode', 'plugin');
    
    const pluginPath = path.join(pluginDir, 'agentguard.js');

    if (!fs.existsSync(pluginPath)) {
      console.log('No AgentGuard plugin found. Nothing to uninstall.');
      return;
    }

    // Remove the plugin file
    fs.unlinkSync(pluginPath);

    const location = global ? 'globally' : 'for this project';
    console.log(`✅ AgentGuard plugin uninstalled ${location}`);
    console.log('');
    console.log('OpenCode will no longer validate commands through AgentGuard.');
  }

  /**
   * Handle install command - Install hook for AI agent
   *
   * @param target - The AI agent to install for (e.g., 'claude', 'kiro')
   * @param global - If true, install globally; otherwise project-local
   */
  private async handleInstall(target: string, global: boolean): Promise<void> {
    if (target === 'kiro') {
      await this.installKiroHook(global);
      return;
    }

    if (target === 'cursor') {
      await this.installCursorHook(global);
      return;
    }

    if (target === 'opencode') {
      await this.installOpenCodePlugin(global);
      return;
    }

    if (target !== 'claude') {
      throw new Error(`Unknown target: ${target}. Supported targets: claude, cursor, kiro, opencode`);
    }

    const fs = await import('fs');
    const os = await import('os');

    // Determine settings path
    const settingsDir = global
      ? path.join(os.homedir(), '.claude')
      : path.join(process.cwd(), '.claude');
    const settingsPath = path.join(settingsDir, 'settings.json');

    // Determine hook command path - always use absolute path
    const hookPath = path.join(__dirname, 'bin', 'claude-hook.js');

    // Create directory if it doesn't exist
    if (!fs.existsSync(settingsDir)) {
      fs.mkdirSync(settingsDir, { recursive: true });
    }

    // Load existing settings or create new
    let settings: Record<string, unknown> = {};
    if (fs.existsSync(settingsPath)) {
      try {
        settings = JSON.parse(fs.readFileSync(settingsPath, 'utf-8'));
      } catch (e) {
        console.warn('Warning: Could not parse existing settings.json, creating new one');
      }
    }

    // Add/update hooks configuration
    const hookConfig = {
      PreToolUse: [
        {
          matcher: 'Bash',
          hooks: [
            {
              type: 'command',
              command: `node ${hookPath}`,
              timeout: 30
            }
          ]
        }
      ]
    };

    settings.hooks = hookConfig;

    // Write settings
    fs.writeFileSync(settingsPath, JSON.stringify(settings, null, 2) + '\n');

    // Success message
    const location = global ? 'globally' : 'for this project';
    console.log(`✅ AgentGuard hook installed ${location}`);
    console.log('');
    console.log(`Settings file: ${settingsPath}`);
    console.log('');
    if (!global) {
      console.log('Note: Make sure to run "npm run build" first to compile the hook.');
      console.log('');
    }
    console.log('The hook will intercept all Bash commands and validate them against');
    console.log('your .agentguard rules before execution.');
    console.log('');
    console.log('Next steps:');
    console.log('  1. Run "agentguard init" to create default rules (if not already done)');
    console.log('  2. Restart Claude Code to activate the hook');
    console.log('  3. Edit .agentguard to customize rules for your project');
  }

  /**
   * Handle uninstall command - Remove hook for AI agent
   *
   * @param target - The AI agent to uninstall for (e.g., 'claude')
   * @param global - If true, uninstall globally; otherwise project-local
   */
  private async handleUninstall(target: string, global: boolean): Promise<void> {
    const fs = await import('fs');
    const os = await import('os');

    if (target === 'kiro') {
      await this.uninstallKiroHook(global);
      return;
    }

    if (target === 'cursor') {
      await this.uninstallCursorHook(global);
      return;
    }

    if (target === 'opencode') {
      await this.uninstallOpenCodePlugin(global);
      return;
    }

    if (target !== 'claude') {
      throw new Error(`Unknown target: ${target}. Supported targets: claude, cursor, kiro, opencode`);
    }

    // Determine settings path
    const settingsDir = global
      ? path.join(os.homedir(), '.claude')
      : path.join(process.cwd(), '.claude');
    const settingsPath = path.join(settingsDir, 'settings.json');

    if (!fs.existsSync(settingsPath)) {
      console.log('No settings file found. Nothing to uninstall.');
      return;
    }

    // Load existing settings
    let settings: Record<string, unknown>;
    try {
      settings = JSON.parse(fs.readFileSync(settingsPath, 'utf-8'));
    } catch (e) {
      throw new Error('Could not parse settings.json');
    }

    // Remove hooks configuration
    if (settings.hooks) {
      delete settings.hooks;

      // Write settings back
      fs.writeFileSync(settingsPath, JSON.stringify(settings, null, 2) + '\n');

      const location = global ? 'globally' : 'for this project';
      console.log(`✅ AgentGuard hook uninstalled ${location}`);
      console.log('');
      console.log('Restart Claude Code for changes to take effect.');
    } else {
      console.log('No AgentGuard hook found in settings. Nothing to uninstall.');
    }
  }

  /**
   * Handle wrap command - main functionality
   * Requirements: 1.1
   * 
   * Steps:
   * 1. Load rules from all sources (global, user, project)
   * 2. Initialize validator with rules
   * 3. Get path to guard shell wrapper
   * 4. Display banner with loaded rules
   * 5. Call ProcessSpawner to spawn wrapped command
   */
  private async handleWrap(options: CLIOptions): Promise<void> {
    // Load rules from all sources
    const ruleParser = new RuleParser();
    const rules = ruleParser.loadAll();

    if (options.verbose) {
      console.log(`Loaded ${rules.length} rules`);
    }

    // Get path to guard shell wrapper
    // The wrapper is compiled to dist/bin/agentguard-shell.js
    const shellPath = path.join(__dirname, 'bin', 'agentguard-shell.js');

    // Display banner
    const formatter = new OutputFormatter();
    const spawner = new ProcessSpawner(formatter);
    spawner.displayBanner(rules, options.command.join(' '));

    // Spawn the wrapped command
    const spawnOptions = {
      command: options.command,
      shellPath: shellPath,
      realShell: spawner.detectRealShell()
    };

    const exitCode = await spawner.spawn(spawnOptions);
    
    // Exit with the same code as the wrapped process
    process.exit(exitCode);
  }
}

// Run if called directly
if (require.main === module) {
  const cli = new CLI();
  cli.run(process.argv.slice(2))
    .then((exitCode) => {
      process.exit(exitCode);
    })
    .catch((error) => {
      console.error('Fatal error:', error);
      process.exit(1);
    });
}
