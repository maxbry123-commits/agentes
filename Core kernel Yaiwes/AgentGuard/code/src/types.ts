/**
 * Core type definitions for AgentGuard
 */

// ============================================================================
// Rule Types
// ============================================================================

export enum RuleType {
  BLOCK = 'block',
  CONFIRM = 'confirm',
  ALLOW = 'allow',
  PROTECT = 'protect',
  SANDBOX = 'sandbox'
}

export enum RuleSource {
  GLOBAL = 'global',    // /etc/agentguard/rules
  USER = 'user',        // ~/.config/agentguard/rules
  PROJECT = 'project'   // ./.agentguard
}

export interface Rule {
  type: RuleType;
  pattern: string;
  source: RuleSource;
  lineNumber: number;
  specificity: number;  // Calculated based on pattern complexity
  metadata?: {
    path?: string;  // For @protect and @sandbox
  };
}

export interface ParseResult {
  rules: Rule[];
  errors: ParseError[];
}

export interface ParseError {
  line: number;
  message: string;
  source: RuleSource;
}

// ============================================================================
// Command Parsing Types
// ============================================================================

export interface Token {
  type: 'command' | 'argument' | 'operator' | 'redirect';
  value: string;
  originalValue: string;  // Before expansion
  position: number;
}

export interface CommandSegment {
  command: string;
  args: string[];
  operator?: '&&' | '||' | ';' | '|';
}

/**
 * Unwrapped command - the actual command being executed after
 * stripping wrapper commands like sudo, bash -c, xargs, etc.
 */
export interface UnwrappedCommand {
  /** The base command being executed (e.g., 'rm', 'chmod') */
  command: string;
  /** Arguments to the command */
  args: string[];
  /** Chain of wrappers that were unwrapped (e.g., ['sudo', 'bash -c']) */
  wrappers: string[];
  /** Whether the command has dynamic/unresolvable arguments */
  hasDynamicArgs: boolean;
  /** Reason if args are dynamic (e.g., 'xargs - paths from stdin') */
  dynamicReason?: string;
  /** Original segment this was unwrapped from */
  originalSegment: CommandSegment;
}

export interface ParsedCommand {
  original: string;
  normalized: string;
  tokens: Token[];
  segments: CommandSegment[];
  isChained: boolean;
  isPiped: boolean;
}

// ============================================================================
// Validation Types
// ============================================================================

export enum ValidationAction {
  ALLOW = 'allow',
  BLOCK = 'block',
  CONFIRM = 'confirm'
}

export interface ValidationResult {
  action: ValidationAction;
  rule?: Rule;
  reason: string;
  metadata?: {
    affectedFiles?: number;
    targetPaths?: string[];
    estimatedImpact?: 'low' | 'medium' | 'high' | 'catastrophic';
  };
}

export interface MatchResult {
  matched: boolean;
  rule?: Rule;
  confidence: number;  // 0-1, based on specificity
}

// ============================================================================
// CLI Types
// ============================================================================

export interface CLIOptions {
  command: string[];        // Command to wrap (e.g., ['claude'])
  configPath?: string;      // Override config file location
  verbose?: boolean;        // Enable verbose output
  dryRun?: boolean;        // Test mode, don't execute
}

// ============================================================================
// Process Spawning Types
// ============================================================================

export interface SpawnOptions {
  command: string[];
  shellPath: string;      // Path to guard shell wrapper
  realShell: string;      // Original shell (bash/zsh)
  env?: Record<string, string>;
}

// ============================================================================
// Confirmation Types
// ============================================================================

export interface ConfirmOptions {
  command: string;
  rule: Rule;
  metadata?: {
    affectedFiles?: number;
    targetPaths?: string[];
  };
  timeout?: number;  // Default: 30 seconds
}

export interface ConfirmResult {
  approved: boolean;
  timedOut: boolean;
}

// ============================================================================
// Audit Logging Types
// ============================================================================

export interface LogEntry {
  timestamp: string;      // ISO 8601
  command: string;
  action: ValidationAction;
  rule?: string;
  reason: string;
  exitCode?: number;
}

export interface LogReadOptions {
  limit?: number;         // Default: 50
  action?: ValidationAction;
  since?: Date;
}

// ============================================================================
// Configuration Types
// ============================================================================

export interface AgentGuardConfig {
  rules: {
    globalPath: string;
    userPath: string;
    projectPath: string;
  };
  audit: {
    enabled: boolean;
    path: string;
    maxSize: number;
    maxFiles: number;
  };
  confirmation: {
    timeout: number;
    defaultAction: 'allow' | 'block';
  };
  output: {
    verbose: boolean;
    color: boolean;
  };
}

// ============================================================================
// Script Analysis Types
// ============================================================================

/** Languages/runtimes that can execute scripts */
export type ScriptRuntime = 'shell' | 'python' | 'node' | 'ruby' | 'perl' | 'unknown';

/** Category of threat found in script */
export type ThreatCategory = 'deletion' | 'system_modification' | 'data_exfiltration' | 'shell_execution';

/** Severity level of a threat */
export type ThreatSeverity = 'low' | 'medium' | 'high' | 'catastrophic';

/** A dangerous pattern found in script content */
export interface ScriptThreat {
  /** The dangerous pattern/function that was matched */
  pattern: string;
  /** Line number in the script where found (1-indexed) */
  lineNumber: number;
  /** The actual line content (truncated if too long) */
  lineContent: string;
  /** Category of threat */
  category: ThreatCategory;
  /** Severity level */
  severity: ThreatSeverity;
  /** Paths extracted from the pattern (if any) */
  targetPaths?: string[];
}

/** Result of analyzing a script file */
export interface ScriptAnalysisResult {
  /** Path to the script that was analyzed */
  scriptPath: string;
  /** Whether analysis was successfully completed */
  analyzed: boolean;
  /** If analysis failed, the reason why */
  analysisError?: string;
  /** Detected runtime/language of the script */
  runtime: ScriptRuntime;
  /** Threats found in the script */
  threats: ScriptThreat[];
  /** Should the command be blocked based on script content? */
  shouldBlock: boolean;
  /** Human-readable reason for blocking */
  blockReason?: string;
}

/** Configuration for script analysis */
export interface ScriptAnalyzerConfig {
  /** Maximum file size to analyze in bytes (default: 1MB) */
  maxFileSize: number;
  /** Maximum lines to analyze (default: 10000) */
  maxLines: number;
  /** Whether to follow symlinks (default: false for security) */
  followSymlinks: boolean;
  /** Custom patterns to detect in addition to built-ins */
  customPatterns?: DangerousPattern[];
}

/** Definition of a dangerous pattern to detect in scripts */
export interface DangerousPattern {
  /** Unique identifier for the pattern */
  id: string;
  /** Runtime this pattern applies to (or 'all' for universal) */
  runtime: ScriptRuntime | 'all';
  /** Regex pattern to match */
  regex: RegExp;
  /** Category of threat */
  category: ThreatCategory;
  /** Severity level */
  severity: ThreatSeverity;
  /** Group indices in regex that contain paths (for catastrophic path checking) */
  pathGroups?: number[];
  /** Human-readable description of what this pattern detects */
  description: string;
}
