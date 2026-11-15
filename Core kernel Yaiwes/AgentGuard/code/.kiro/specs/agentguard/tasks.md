# Implementation Plan

- [x] 1. Set up project structure and core types
  - Create package.json with Node.js 18+ requirement and TypeScript dependencies
  - Set up tsconfig.json with strict mode and ES2022 target
  - Create src/ directory structure with placeholder files
  - Define core TypeScript interfaces in types.ts (Rule, ParsedCommand, ValidationResult, etc.)
  - _Requirements: 19.1, 19.4_

- [x] 1.1 Write property test for Node.js version check
  - **Property 0: Node.js version requirement**
  - **Validates: Requirements 19.2**

- [-] 2. Implement rule parser
  - [x] 2.1 Create RuleParser class with file reading and line parsing
    - Implement parse() method to read rule files
    - Parse rule prefixes (!, ?, +, @protect, @sandbox)
    - Handle comments (#) and blank lines
    - Calculate rule specificity based on pattern complexity
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 2.2 Write property test for rule prefix parsing
    - **Property 5: Rule prefix parsing**
    - **Validates: Requirements 2.1**

  - [x] 2.3 Write property test for comment and blank line handling
    - **Property 6: Comment and blank line handling**
    - **Validates: Requirements 2.2, 2.3**

  - [x] 2.4 Implement error handling and recovery for invalid syntax
    - Report errors with line numbers
    - Continue parsing after errors
    - _Requirements: 2.4_

  - [x] 2.5 Write property test for parse error recovery
    - **Property 7: Parse error recovery**
    - **Validates: Requirements 2.4**

  - [x] 2.6 Implement multi-file loading with precedence
    - Load from global (/etc/agentguard/rules), user (~/.config/agentguard/rules), project (./.agentguard)
    - Merge rules with project > user > global precedence
    - _Requirements: 2.5_

  - [x] 2.7 Write property test for rule precedence hierarchy
    - **Property 8: Rule precedence hierarchy**
    - **Validates: Requirements 2.5, 7.5**

- [x] 3. Implement command tokenizer
  - [x] 3.1 Create CommandTokenizer class with basic tokenization
    - Split commands on spaces while respecting quotes
    - Handle single and double quotes
    - Preserve quoted content as single tokens
    - _Requirements: 6.1_

  - [x] 3.2 Write property test for quoted string preservation
    - **Property 14: Quoted string preservation**
    - **Validates: Requirements 6.1**

  - [x] 3.3 Implement variable and path expansion
    - Expand environment variables ($VAR, ${VAR})
    - Expand tilde (~) to home directory
    - Resolve relative paths to absolute paths
    - _Requirements: 6.2, 6.3, 6.4_

  - [ ]* 3.4 Write property test for variable and path expansion
    - **Property 15: Variable and path expansion**
    - **Validates: Requirements 6.2, 6.3, 6.4**

  - [x] 3.5 Implement escape sequence handling
    - Handle backslash escapes (\, \", \')
    - Interpret escape sequences correctly
    - _Requirements: 6.5_

  - [ ]* 3.6 Write property test for escape sequence interpretation
    - **Property 16: Escape sequence interpretation**
    - **Validates: Requirements 6.5**

- [x] 4. Implement pattern matcher
  - [x] 4.1 Create PatternMatcher class with glob matching
    - Implement matchPattern() for * and ? wildcards
    - Convert glob patterns to regex for matching
    - Match patterns against full command strings
    - _Requirements: 7.1, 7.2, 7.3_

  - [ ]* 4.2 Write property test for wildcard pattern matching
    - **Property 17: Wildcard pattern matching**
    - **Validates: Requirements 7.1, 7.2**

  - [ ]* 4.3 Write example test for wildcard pattern
    - **Example 4: Wildcard pattern matching example**
    - **Validates: Requirements 7.3**

  - [x] 4.4 Implement path normalization
    - Resolve symlinks
    - Remove trailing slashes
    - Normalize before comparison
    - _Requirements: 7.4_

  - [ ]* 4.5 Write property test for path normalization
    - **Property 18: Path normalization before matching**
    - **Validates: Requirements 7.4**

  - [x] 4.6 Implement best match selection with precedence
    - Apply type precedence (BLOCK > CONFIRM > ALLOW)
    - Apply specificity precedence
    - Apply source precedence (project > user > global)
    - _Requirements: 7.5_

- [-] 5. Implement rule engine and validator
  - [x] 5.1 Create RuleEngine class with validation logic
    - Implement validate() method
    - Match commands against rules using PatternMatcher
    - Apply rule precedence
    - Return ValidationResult with action and reason
    - _Requirements: 1.3, 5.3, 5.4_

  - [ ]* 5.2 Write property test for block precedence over allow
    - **Property 12: Block precedence over allow**
    - **Validates: Requirements 5.3**

  - [ ]* 5.3 Write property test for default allow policy
    - **Property 13: Default allow policy**
    - **Validates: Requirements 5.4**

  - [x] 5.2 Implement block rule handling
    - Detect BLOCK rules
    - Prevent execution without prompting
    - Generate block messages with matched rule
    - Return non-zero exit code
    - _Requirements: 3.1, 3.2, 3.3_

  - [ ]* 5.4 Write property test for blocked command prevention
    - **Property 4: Blocked command prevention**
    - **Validates: Requirements 1.5, 3.1, 3.2, 3.3**

  - [x] 5.5 Write example test for catastrophic rm -rf /
    - **Example 1: Block catastrophic rm -rf /**
    - **Validates: Requirements 3.4**

  - [ ]* 5.6 Write example test for catastrophic rm -rf /*
    - **Example 2: Block catastrophic rm -rf /***
    - **Validates: Requirements 3.5**

  - [x] 5.7 Implement allow rule handling
    - Detect ALLOW rules
    - Execute without prompting
    - Generate allow messages with matched rule
    - _Requirements: 5.1, 5.5_

  - [ ]* 5.8 Write property test for allow rule execution
    - **Property 11: Allow rule precedence over default**
    - **Validates: Requirements 5.1, 5.5**

  - [ ]* 5.9 Write example test for safe cleanup
    - **Example 3: Allow safe cleanup**
    - **Validates: Requirements 5.2**

- [x] 6. Implement output formatter
  - [x] 6.1 Create OutputFormatter class with message formatting
    - Implement displayBanner() with version, command, rules count
    - Implement displayBlocked() with 🚫 emoji
    - Implement displayAllowed() with ✅ emoji
    - Format messages consistently
    - _Requirements: 9.1, 9.2, 9.3_

  - [ ]* 6.2 Write example test for startup banner
    - **Example 5: Startup banner display**
    - **Validates: Requirements 9.1**

  - [ ]* 6.3 Write property test for output format consistency
    - **Property 22: Output format consistency**
    - **Validates: Requirements 9.2, 9.3, 9.4**

  - [x] 6.4 Implement terminal formatting preservation
    - Pass through ANSI escape codes
    - Preserve colors and formatting from wrapped commands
    - _Requirements: 9.5_

  - [ ]* 6.5 Write property test for terminal formatting preservation
    - **Property 23: Terminal formatting preservation**
    - **Validates: Requirements 9.5**

- [x] 7. Implement audit logger
  - [x] 7.1 Create AuditLogger class with log writing
    - Implement log() method to write entries
    - Format entries as single-line JSON
    - Persist to ~/.agentguard/audit.log
    - Create log directory if needed
    - _Requirements: 8.1, 8.2, 8.4_

  - [ ]* 7.2 Write property test for audit logging completeness
    - **Property 19: Audit logging completeness**
    - **Validates: Requirements 8.1, 8.2**

  - [ ]* 7.3 Write property test for single-line log format
    - **Property 20: Single-line log format**
    - **Validates: Requirements 8.4**

  - [x] 7.4 Implement resilient logging with error handling
    - Continue operation if log writes fail
    - Log errors to stderr
    - Don't block command execution on log failures
    - _Requirements: 8.5_

  - [ ]* 7.5 Write property test for resilient logging
    - **Property 21: Resilient logging**
    - **Validates: Requirements 8.5**

  - [x] 7.6 Implement log rotation
    - Check file size before writing
    - Rotate when exceeds 10MB
    - Create timestamped backup files
    - _Requirements: 8.3_

  - [ ]* 7.7 Write edge case test for log rotation
    - **Edge Case 2: Log rotation threshold**
    - **Validates: Requirements 8.3**

- [x] 8. Implement process spawner
  - [x] 8.1 Create ProcessSpawner class with environment setup
    - Implement detectRealShell() with priority order
    - Build environment with SHELL, AGENTGUARD_REAL_SHELL, AGENTGUARD_ACTIVE
    - Store original shell in AGENTGUARD_ORIGINAL_SHELL
    - _Requirements: 1.1_

  - [ ]* 8.2 Write property test for environment injection
    - **Property 1: Environment injection for wrapped processes**
    - **Validates: Requirements 1.1**

  - [x] 8.3 Implement process spawning with child_process
    - Spawn target command with modified environment
    - Pass through stdio
    - Handle process exit codes
    - _Requirements: 1.1_

  - [x] 8.4 Implement banner display on startup
    - Show version, protected command, rules count, mode
    - Display before spawning wrapped process
    - _Requirements: 9.1_

- [x] 9. Implement guard shell wrapper
  - [x] 9.1 Create agentguard-shell Node.js script
    - Add shebang (#!/usr/bin/env node)
    - Receive command as argv[2]
    - Import and call Validator
    - Handle validation result (allow/block)
    - _Requirements: 1.2, 1.3_

  - [ ]* 9.2 Write property test for command validation pipeline
    - **Property 2: Command validation pipeline**
    - **Validates: Requirements 1.2, 1.3**

  - [x] 9.3 Implement command execution for allowed commands
    - Use child_process.spawn with AGENTGUARD_REAL_SHELL
    - Pass command with -c flag
    - Inherit stdio for output
    - Forward exit codes
    - _Requirements: 1.4_

  - [ ]* 9.4 Write property test for allowed command execution
    - **Property 3: Allowed command execution**
    - **Validates: Requirements 1.4**

  - [x] 9.5 Implement blocking for blocked commands
    - Display block message to stderr
    - Exit with code 1
    - Don't execute command
    - _Requirements: 1.5_

  - [x] 9.6 Make wrapper executable
    - Set executable permissions (chmod +x)
    - Test wrapper can be invoked as shell
    - _Requirements: 1.1_

- [x] 10. Implement CLI interface
  - [x] 10.1 Create CLI class with argument parsing
    - Parse command-line arguments
    - Identify subcommands (wrap, init, check, log)
    - Handle flags (--verbose, --dry-run)
    - _Requirements: 1.1_

  - [x] 10.2 Implement wrap command (main functionality)
    - Load rules from all sources
    - Initialize validator with rules
    - Get path to guard shell wrapper
    - Call ProcessSpawner to spawn wrapped command
    - _Requirements: 1.1_

  - [x] 10.3 Create main entry point (index.ts)
    - Import CLI class
    - Call CLI.run() with process.argv
    - Handle top-level errors
    - Exit with appropriate code
    - _Requirements: 1.1_

  - [x] 10.4 Create bin/agentguard executable
    - Add shebang
    - Import and run main entry point
    - Make executable
    - _Requirements: 1.1_

- [x] 11. Create default rules template
  - [x] 11.1 Create templates/default-rules.txt
    - Include catastrophic BLOCK rules (rm -rf /, mkfs.*, dd to /dev)
    - Include dangerous CONFIRM rules (rm -rf *, git push --force)
    - Include safe ALLOW rules (rm -rf node_modules, dist, build)
    - Add comments explaining each section
    - _Requirements: 10.2, 10.3, 10.4_

- [x] 12. Checkpoint - Ensure all P0 tests pass
  - Run all unit tests and property tests
  - Verify core functionality works end-to-end
  - Test with simple commands (rm, echo, ls)
  - Ensure all tests pass, ask the user if questions arise

- [x] 13. Implement init command [P1]
  - [x] 13.1 Add init subcommand to CLI
    - Check if .agentguard exists
    - Prompt user if file exists
    - Copy default-rules.txt to .agentguard
    - Display success message
    - _Requirements: 10.1, 10.5_

  - [x] 13.2 Write example test for init command
    - **Example 6: Init command creates file**
    - **Validates: Requirements 10.1**

  - [x] 13.3 Write example tests for default rules content
    - **Example 7: Default rules include catastrophic blocks**
    - **Example 8: Default rules include dangerous confirms**
    - **Example 9: Default rules include safe allows**
    - **Validates: Requirements 10.2, 10.3, 10.4**

  - [x] 13.4 Write edge case test for init file conflict
    - **Edge Case 3: Init file conflict**
    - **Validates: Requirements 10.5**

- [x] 14. Implement check command [P1]
  - [x] 14.1 Add check subcommand to CLI
    - Parse command argument
    - Load rules
    - Validate command without executing
    - Display result (block/allow/confirm) and matched rule
    - Don't log to audit
    - _Requirements: 11.1, 11.2, 11.3, 11.4_

  - [ ]* 14.2 Write property test for check command dry-run
    - **Property 24: Check command dry-run**
    - **Validates: Requirements 11.1, 11.2, 11.3, 11.4**

  - [ ]* 14.3 Write property test for check command no-prompt
    - **Property 25: Check command no-prompt**
    - **Validates: Requirements 11.5**

- [x] 15. Implement confirmation handler [P1]
  - [x] 15.1 Create ConfirmationHandler class
    - Implement confirm() method with prompt display
    - Show command, rule, and scope with ⚠️ emoji
    - Read user input from stdin
    - Handle y/Y as approve, anything else as deny
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [ ]* 15.2 Write property test for confirmation prompt display
    - **Property 9: Confirmation prompt display**
    - **Validates: Requirements 4.1, 4.2**

  - [ ]* 15.3 Write property test for confirmation approval
    - **Property 10: Confirmation approval**
    - **Validates: Requirements 4.3, 4.4**

  - [x] 15.4 Implement timeout handling
    - Set 30-second timeout
    - Default to block on timeout
    - Display timeout message
    - _Requirements: 4.5_

  - [ ]* 15.5 Write edge case test for confirmation timeout
    - **Edge Case 1: Confirmation timeout**
    - **Validates: Requirements 4.5**

  - [x] 15.6 Integrate confirmation into guard shell wrapper
    - Handle 'confirm' action from validator
    - Call ConfirmationHandler
    - Execute or block based on user response
    - _Requirements: 4.1_

- [x] 16. Implement chained command support [P1]
  - [x] 16.1 Extend CommandTokenizer for chain operators
    - Parse && (sequential on success)
    - Parse || (sequential on failure)
    - Parse ; (sequential regardless)
    - Split into command segments
    - _Requirements: 14.1, 14.2, 14.3_

  - [ ]* 16.2 Write property test for chained command parsing
    - **Property 29: Chained command parsing**
    - **Validates: Requirements 14.1, 14.2, 14.3**

  - [x] 16.3 Extend RuleEngine for chained validation
    - Validate each segment independently
    - Block entire chain if any segment blocked
    - _Requirements: 14.4, 14.5_

  - [ ]* 16.4 Write property test for chained command validation
    - **Property 30: Chained command validation**
    - **Validates: Requirements 14.4, 14.5**

- [x] 17. Implement piped command support [P1]
  - [x] 17.1 Extend CommandTokenizer for pipe operator
    - Parse | (pipe between commands)
    - Split into command segments
    - _Requirements: 15.1_

  - [ ]* 17.2 Write property test for piped command parsing
    - **Property 31: Piped command parsing**
    - **Validates: Requirements 15.1**

  - [x] 17.3 Extend RuleEngine for piped validation
    - Validate each segment independently
    - Block entire pipeline if any segment blocked
    - Execute full pipeline if all allowed
    - _Requirements: 15.2, 15.4, 15.5_

  - [ ]* 17.4 Write property test for piped command validation
    - **Property 32: Piped command validation**
    - **Validates: Requirements 15.2, 15.4, 15.5**

  - [ ]* 17.5 Write example test for dangerous pipe
    - **Example 13: Dangerous pipe blocking**
    - **Validates: Requirements 15.3**

- [x] 17a. Implement Claude Code hook integration [P1]
  - [x] 17a.1 Create claude-hook script
    - Read JSON input from stdin
    - Parse HookInput interface
    - Validate only Bash tool uses
    - Call Validator to check command
    - Exit with code 0 (allow) or 2 (block)
    - Handle CONFIRM as BLOCK in hook context
    - _Requirements: 22.1, 22.2, 22.3, 22.4, 22.5_

  - [ ]* 17a.2 Write example test for Claude hook blocking
    - **Example 15: Claude hook blocks dangerous command**
    - **Validates: Requirements 22.3**

  - [ ]* 17a.3 Write example test for Claude hook allowing
    - **Example 16: Claude hook allows safe command**
    - **Validates: Requirements 22.5**

  - [ ]* 17a.4 Write property test for Claude hook validation
    - **Property 38: Claude hook validation**
    - **Validates: Requirements 22.2, 22.3, 22.5**

- [x] 17b. Implement install/uninstall commands [P1]
  - [x] 17b.1 Add install subcommand to CLI
    - Parse target (claude, kiro) and --global flag
    - Route to appropriate handler
    - _Requirements: 20.1_

  - [x] 17b.2 Implement handleInstall for Claude
    - Determine settings path (project vs global)
    - Create settings directory if needed
    - Load or create settings object
    - Add PreToolUse hook configuration
    - Write settings file
    - Display success message
    - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5_

  - [x] 17b.3 Implement showKiroInstructions
    - Display wrapper usage instructions
    - Provide examples for common Kiro commands
    - Suggest alias for convenience
    - _Requirements: 23.1, 23.2, 23.3, 23.4_

  - [x] 17b.4 Add uninstall subcommand to CLI
    - Parse target and --global flag
    - Route to appropriate handler
    - _Requirements: 21.1_

  - [x] 17b.5 Implement handleUninstall for Claude
    - Determine settings path
    - Load existing settings
    - Remove hooks configuration
    - Write settings back
    - Display success message
    - _Requirements: 21.1, 21.2, 21.3, 21.4, 21.5_

  - [ ]* 17b.6 Write example test for Claude hook installation
    - **Example 14: Claude hook installation creates settings file**
    - **Validates: Requirements 20.1, 20.2**

  - [ ]* 17b.7 Write example test for Kiro instructions
    - **Example 17: Kiro instructions display**
    - **Validates: Requirements 23.1, 23.2**

  - [ ]* 17b.8 Write property test for hook installation
    - **Property 37: Claude hook installation**
    - **Validates: Requirements 20.1, 20.2, 20.3, 20.4**

  - [ ]* 17b.9 Write property test for hook uninstallation
    - **Property 39: Hook uninstallation**
    - **Validates: Requirements 21.1, 21.2, 21.3**

- [x] 17c. Implement bash wrapper (alternative integration) [P1]
  - [x] 17c.1 Create bash-wrapper script
    - Detect real bash location
    - Check for -c flag (command execution mode)
    - Validate commands through AgentGuard
    - Handle ALLOW, BLOCK, and CONFIRM actions
    - Pass through to real bash for allowed commands
    - Support interactive and script modes
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [x] 17c.2 Create wrapper shell scripts
    - Create bash wrapper (src/bin/wrappers/bash)
    - Create sh wrapper (src/bin/wrappers/sh)
    - Make wrappers executable
    - Copy to dist during build
    - _Requirements: 1.1_

- [x] 17d. Implement recursive command unwrapping [P0]
  - [x] 17d.1 Create CommandUnwrapper class
    - Implement unwrap() method to recursively find actual commands
    - Handle passthrough wrappers (sudo, doas, env, nice, nohup, timeout, time, watch, strace, ltrace, ionice, chroot, runuser, su)
    - Handle shell -c wrappers (bash, sh, zsh, dash, fish, ksh, csh, tcsh)
    - Handle dynamic executors (xargs, parallel)
    - Handle find patterns (-exec, -execdir, -ok, -okdir, -delete)
    - Track wrapper chain for context
    - Mark dynamic argument commands appropriately
    - _Requirements: 1.3 (validation must unwrap commands to find actual operation)_

  - [x] 17d.2 Add UnwrappedCommand interface to types.ts
    - command: string (actual command being executed)
    - args: string[] (arguments to the command)
    - wrappers: string[] (chain of wrappers)
    - hasDynamicArgs: boolean (true if args come from external source)
    - dynamicReason?: string (explanation for dynamic args)
    - originalSegment: CommandSegment (original segment before unwrapping)

  - [x] 17d.3 Integrate CommandUnwrapper into RuleEngine
    - Use unwrapper in checkCatastrophicPaths()
    - Unwrap each segment to find actual commands
    - Check if unwrapped command is destructive (rm, rmdir, unlink, shred)
    - Block destructive commands with dynamic args and recursive flags
    - Block destructive commands targeting catastrophic paths
    - Include wrapper context in error messages

  - [x] 17d.4 Write comprehensive unit tests for CommandUnwrapper
    - Test passthrough wrapper unwrapping (sudo, env, nice, timeout)
    - Test shell -c unwrapping (bash, sh, zsh)
    - Test nested wrapper unwrapping (sudo + env + bash -c)
    - Test xargs handling with dynamic args flag
    - Test find -exec/-delete handling
    - Test piped commands in bash -c
    - Test chained commands in bash -c
    - Test non-wrapper commands pass through unchanged

  - [x] 17d.5 Export CommandUnwrapper from index.ts
    - Add export for CommandUnwrapper class

- [x] 17e. Implement inherently dangerous commands detection [P0]
  - [x] 17e.1 Add inherently dangerous commands list to RuleEngine
    - Define INHERENTLY_DANGEROUS_COMMANDS constant array
    - Include filesystem formatting commands (mkfs, mkfs.ext2, mkfs.ext3, mkfs.ext4, mkfs.xfs, mkfs.btrfs, mkfs.vfat, mke2fs, mkswap)
    - Include disk partitioning tools (fdisk, parted, gdisk, cfdisk, sfdisk)
    - _Requirements: Requirement 24 (Inherently Dangerous Commands)_

  - [x] 17e.2 Add dd block device patterns to RuleEngine
    - Define DANGEROUS_DD_PATTERNS constant array
    - Match dd writing to SATA/SCSI drives (of=/dev/sd*)
    - Match dd writing to NVMe drives (of=/dev/nvme*)
    - Match dd writing to virtual drives (of=/dev/vd*, of=/dev/xvd*)
    - Match dd writing to SD cards/eMMC (of=/dev/mmcblk*)
    - _Requirements: Requirement 24 (Inherently Dangerous Commands)_

  - [x] 17e.3 Implement checkInherentlyDangerousCommands() method
    - Check if base command is in INHERENTLY_DANGEROUS_COMMANDS list
    - For 'dd' command, check if any args match DANGEROUS_DD_PATTERNS
    - Return BLOCK action with clear explanation
    - Apply to unwrapped commands (detects hidden dangerous commands)
    - _Requirements: Requirement 24 (Inherently Dangerous Commands)_

  - [x] 17e.4 Integrate into validation pipeline
    - Call checkInherentlyDangerousCommands() after command unwrapping
    - Call before checkCatastrophicPaths() for early detection
    - Include wrapper context in error messages
    - _Requirements: Validation pipeline ordering_

  - [x] 17e.5 Write unit tests for inherently dangerous commands
    - Test all mkfs variants are blocked
    - Test all disk partitioning tools are blocked
    - Test dd to block devices is blocked
    - Test dd to regular files is allowed
    - Test dangerous commands behind wrappers (sudo mkfs.ext4)
    - _Requirements: Comprehensive test coverage_

- [x] 18. Checkpoint - Ensure all P1 tests pass
  - Run all unit tests and property tests
  - Verify init, check, confirmation, chained, and piped commands work
  - Test with complex command scenarios
  - Ensure all tests pass, ask the user if questions arise

- [x] 18a. Implement script content analysis [P1]
  - [x] 18a.1 Add script analysis types to types.ts
    - Define ScriptRuntime type ('shell' | 'python' | 'node' | 'ruby' | 'perl' | 'unknown')
    - Define ScriptThreat interface (pattern, lineNumber, lineContent, category, severity, targetPaths)
    - Define ScriptAnalysisResult interface (scriptPath, analyzed, runtime, threats, shouldBlock, blockReason)
    - _Requirements: Defense in depth for script execution_

  - [x] 18a.2 Create ScriptAnalyzer class
    - Implement detectScriptExecution() to identify script execution commands
    - Implement analyze() to scan script contents for dangerous patterns
    - Implement detectRuntime() to determine script language from shebang/extension
    - Implement readScriptSafe() with 1MB file size limit
    - Implement extractThreats() with runtime-specific patterns
    - _Requirements: Pre-execution script scanning_

  - [x] 18a.3 Define dangerous patterns for each runtime
    - Shell patterns: rm -rf, rmdir, dd of=, mkfs, shred
    - Python patterns: shutil.rmtree, os.remove, os.system with rm
    - Node patterns: fs.rmSync, fs.rm recursive, rimraf
    - Include patterns for both literal paths and variable usage
    - _Requirements: Multi-runtime threat detection_

  - [x] 18a.4 Implement catastrophic path detection in scripts
    - Scan script content for dangerous paths (/, /home, /etc, /var, /usr, ~)
    - Block scripts that have deletion threats AND catastrophic paths
    - Handle path normalization edge cases (path.normalize('/') returns '.')
    - _Requirements: Prevent accidental system damage_

  - [x] 18a.5 Integrate ScriptAnalyzer with RuleEngine
    - Add checkScriptContent() method to RuleEngine
    - Call after checkCatastrophicPaths() in validation pipeline
    - Implement fail-open behavior (allow if script can't be read)
    - _Requirements: Validation pipeline integration_

  - [x] 18a.6 Write unit tests for ScriptAnalyzer
    - Test script execution detection for various runtimes
    - Test dangerous pattern detection (53 tests total)
    - Test catastrophic path detection
    - Test fail-open behavior for missing/binary/large files
    - _Requirements: Comprehensive test coverage_

  - [x] 18a.7 Write integration tests for script analysis
    - Test through full validation pipeline (21 tests)
    - Test with wrappers (sudo python, env python)
    - Test real-world attack scenarios (AI cleanup scripts)
    - Test rule interaction with script analysis
    - _Requirements: End-to-end validation_

  - [x] 18a.8 Update README with limitations section
    - Document what AgentGuard does and doesn't do
    - Explain defense-in-depth philosophy
    - Note script analysis limitations (no binary inspection)
    - _Requirements: User documentation_

- [ ] 19. Implement log viewing command [P2]
  - [ ] 19.1 Add log subcommand to CLI
    - Read audit log file
    - Parse JSON lines
    - Format as human-readable table
    - Show most recent 50 entries by default
    - Handle empty log
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

  - [ ]* 19.2 Write example test for log command
    - **Example 11: Log command displays entries**
    - **Validates: Requirements 13.1**

  - [ ]* 19.3 Write property test for log display formatting
    - **Property 28: Log display formatting**
    - **Validates: Requirements 13.2, 13.3**

  - [ ]* 19.4 Write edge case test for empty log
    - **Edge Case 4: Empty audit log**
    - **Validates: Requirements 13.4**

  - [ ]* 19.5 Write example test for log default limit
    - **Example 12: Log default limit**
    - **Validates: Requirements 13.5**

- [ ] 20. Implement protected paths [P2]
  - [ ] 20.1 Extend RuleEngine for @protect directives
    - Detect write operations (rm, mv, cp, touch, mkdir, etc.)
    - Extract target paths from commands
    - Check if targets are within protected paths
    - Block writes to protected paths
    - _Requirements: 12.1, 12.2, 12.4, 12.5_

  - [ ]* 20.2 Write property test for protected path write blocking
    - **Property 26: Protected path write blocking**
    - **Validates: Requirements 12.1, 12.2, 12.4**

  - [ ]* 20.3 Write property test for protected path resolution
    - **Property 27: Protected path resolution**
    - **Validates: Requirements 12.5**

  - [ ]* 20.4 Write example test for protected path
    - **Example 10: Protected path example**
    - **Validates: Requirements 12.3**

- [ ] 21. Implement sandbox paths [P2]
  - [ ] 21.1 Extend RuleEngine for @sandbox directives
    - Detect write operations
    - Check if targets are within any sandbox path
    - Block writes outside sandbox when sandboxes defined
    - Allow writes anywhere when no sandboxes defined
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5_

  - [ ]* 21.2 Write property test for sandbox write restriction
    - **Property 34: Sandbox write restriction**
    - **Validates: Requirements 18.1, 18.2, 18.4**

  - [ ]* 21.3 Write property test for multi-sandbox allowance
    - **Property 35: Multi-sandbox allowance**
    - **Validates: Requirements 18.3**

  - [ ]* 21.4 Write property test for sandbox opt-in behavior
    - **Property 36: Sandbox opt-in behavior**
    - **Validates: Requirements 18.5**

- [ ] 22. Implement platform-specific path handling [P2]
  - [ ] 22.1 Add platform detection and path utilities
    - Detect platform (macOS, Linux, Windows WSL)
    - Use appropriate path separators
    - Handle platform-specific path conventions
    - _Requirements: 17.4_

  - [ ]* 22.2 Write property test for platform-appropriate path handling
    - **Property 33: Platform-appropriate path handling**
    - **Validates: Requirements 17.4**

- [ ] 23. Final checkpoint - Ensure all tests pass
  - Run complete test suite (unit, property, integration)
  - Verify all P0, P1, and P2 features work
  - Test on macOS and Linux if possible
  - Fix any remaining bugs
  - Ensure all tests pass, ask the user if questions arise

- [ ] 24. Prepare demo and documentation
  - Create README with installation and usage instructions
  - Document rule file syntax with examples
  - Prepare demo script and test environment
  - Create demo project with sample .agentguard file
  - Test full demo flow end-to-end
  - _Requirements: 19.5_
