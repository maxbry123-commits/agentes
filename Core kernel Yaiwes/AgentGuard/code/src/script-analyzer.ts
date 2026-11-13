/**
 * Script Analyzer - Analyzes script file contents for dangerous patterns
 *
 * Detects script execution commands and reads script contents to find:
 * - Shell: rm -rf, rmdir, dd, mkfs, shred
 * - Python: shutil.rmtree, os.remove, os.system('rm...')
 * - Node: fs.rmSync, fs.unlinkSync, child_process.exec('rm...')
 *
 * This addresses the Reddit feedback about AI agents writing malicious scripts
 * and then executing them to bypass direct command blocking.
 */

import * as fs from 'fs';
import * as path from 'path';
import {
  CommandSegment,
  ScriptRuntime,
  ScriptThreat,
  ScriptAnalysisResult,
  ScriptAnalyzerConfig,
  DangerousPattern,
  ThreatCategory,
  ThreatSeverity,
} from './types';

// Default configuration
const DEFAULT_CONFIG: ScriptAnalyzerConfig = {
  maxFileSize: 1024 * 1024, // 1MB
  maxLines: 10000,
  followSymlinks: false,
  customPatterns: [],
};

// Script execution detection - maps executors to their file extensions
const SCRIPT_EXECUTORS: Record<string, { extensions: string[]; skipFlags?: string[] }> = {
  python: { extensions: ['.py'], skipFlags: ['-c', '-m'] },
  python3: { extensions: ['.py'], skipFlags: ['-c', '-m'] },
  python2: { extensions: ['.py'], skipFlags: ['-c', '-m'] },
  node: { extensions: ['.js', '.mjs', '.cjs'], skipFlags: ['-e', '--eval', '-p', '--print'] },
  nodejs: { extensions: ['.js', '.mjs', '.cjs'], skipFlags: ['-e', '--eval'] },
  bash: { extensions: ['.sh', '.bash'], skipFlags: ['-c'] },
  sh: { extensions: ['.sh'], skipFlags: ['-c'] },
  zsh: { extensions: ['.zsh', '.sh'], skipFlags: ['-c'] },
  dash: { extensions: ['.sh'], skipFlags: ['-c'] },
  fish: { extensions: ['.fish'], skipFlags: ['-c'] },
  ruby: { extensions: ['.rb'], skipFlags: ['-e'] },
  perl: { extensions: ['.pl', '.pm'], skipFlags: ['-e'] },
  php: { extensions: ['.php'], skipFlags: ['-r'] },
};

// Extensions that indicate executable scripts
const SCRIPT_EXTENSIONS = new Set([
  '.py', '.sh', '.bash', '.zsh', '.fish', '.js', '.mjs', '.cjs',
  '.rb', '.pl', '.pm', '.php',
]);

// Catastrophic paths - same as in rule-engine.ts
const CATASTROPHIC_PATHS = [
  '/',
  '/home',
  '/root',
  '/etc',
  '/usr',
  '/var',
  '/bin',
  '/sbin',
  '/lib',
  '/lib64',
  '/boot',
  '/dev',
  '/proc',
  '/sys',
];

/**
 * ScriptAnalyzer - Analyzes scripts for dangerous patterns before execution
 */
export class ScriptAnalyzer {
  private config: ScriptAnalyzerConfig;
  private patterns: DangerousPattern[];
  private homeDir: string;

  constructor(config?: Partial<ScriptAnalyzerConfig>) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.patterns = this.getBuiltInPatterns();
    if (this.config.customPatterns) {
      this.patterns = [...this.patterns, ...this.config.customPatterns];
    }
    this.homeDir = process.env.HOME || process.env.USERPROFILE || '/home/user';
  }

  /**
   * Check if a command segment is executing a script file.
   * Returns the script path if detected, null otherwise.
   */
  detectScriptExecution(segment: CommandSegment): string | null {
    const { command, args } = segment;
    const baseCommand = path.basename(command);

    // Check if it's a known script executor
    const executor = SCRIPT_EXECUTORS[baseCommand];
    if (executor) {
      // Skip if using inline code flags (-c, -e, etc.)
      if (executor.skipFlags?.some(flag => args.includes(flag))) {
        return null;
      }

      // Find the first argument that looks like a script file
      for (const arg of args) {
        // Skip flags
        if (arg.startsWith('-')) continue;

        // Check if it has a matching extension
        const ext = path.extname(arg).toLowerCase();
        if (executor.extensions.includes(ext)) {
          return arg;
        }

        // Check if file exists and has matching extension (for extensionless files)
        if (!ext && this.fileExists(arg)) {
          return arg;
        }
      }

      return null;
    }

    // Check for direct script execution: ./script.sh, /path/to/script.py
    if (command.startsWith('./') || command.startsWith('/') || command.startsWith('../')) {
      const ext = path.extname(command).toLowerCase();
      if (SCRIPT_EXTENSIONS.has(ext)) {
        return command;
      }

      // Check shebang for extensionless files
      if (!ext && this.fileExists(command)) {
        const runtime = this.detectRuntimeFromShebang(command);
        if (runtime !== 'unknown') {
          return command;
        }
      }
    }

    return null;
  }

  /**
   * Analyze a script file for dangerous patterns.
   * Returns analysis result with any threats found.
   */
  analyze(scriptPath: string): ScriptAnalysisResult {
    const result: ScriptAnalysisResult = {
      scriptPath,
      analyzed: false,
      runtime: 'unknown',
      threats: [],
      shouldBlock: false,
    };

    // Read the script safely
    const { content, error } = this.readScriptSafe(scriptPath);
    if (error) {
      result.analysisError = error;
      return result; // Fail-open
    }

    result.analyzed = true;

    // Detect runtime from shebang or extension
    result.runtime = this.detectRuntime(scriptPath, content);

    // Extract threats
    result.threats = this.extractThreats(content, result.runtime);

    // Determine if we should block
    if (result.threats.length > 0) {
      const catastrophicThreats = result.threats.filter(t => t.severity === 'catastrophic');
      const highThreats = result.threats.filter(t => t.severity === 'high');

      if (catastrophicThreats.length > 0) {
        result.shouldBlock = true;
        result.blockReason = `Script contains catastrophic operations: ${
          catastrophicThreats.map(t => t.pattern).join(', ')
        }`;
      } else if (highThreats.length > 0) {
        // Check if any high-severity threats target catastrophic paths
        const hasCatastrophicPaths = highThreats.some(t =>
          t.targetPaths?.some(p => this.isCatastrophicPath(p))
        );
        if (hasCatastrophicPaths) {
          result.shouldBlock = true;
          result.blockReason = `Script targets critical system paths: ${
            highThreats.flatMap(t => t.targetPaths || []).filter(p => this.isCatastrophicPath(p)).join(', ')
          }`;
        } else {
          // Additional check: If script has high-severity deletion threats AND
          // contains catastrophic paths anywhere in the content (even in variables/lists),
          // block it. This catches attacks like defining "/" in a list then passing to rmtree.
          const deletionThreats = highThreats.filter(t => t.category === 'deletion');
          if (deletionThreats.length > 0) {
            const allPaths = this.extractAllPathsFromContent(content);
            const catastrophicPathsInScript = allPaths.filter(p => this.isCatastrophicPath(p));
            if (catastrophicPathsInScript.length > 0) {
              result.shouldBlock = true;
              result.blockReason = `Script contains deletion operations and catastrophic paths: ${
                catastrophicPathsInScript.join(', ')
              }`;
              // Upgrade all deletion threats to catastrophic
              for (const threat of deletionThreats) {
                threat.severity = 'catastrophic';
                if (!threat.targetPaths) {
                  threat.targetPaths = [];
                }
                threat.targetPaths.push(...catastrophicPathsInScript);
              }
            }
          }
        }
      }
    }

    return result;
  }

  /**
   * Extract all path-like strings from the entire script content.
   * This catches paths defined in variables, lists, etc.
   */
  private extractAllPathsFromContent(content: string): string[] {
    const paths: string[] = [];
    const lines = content.split('\n');

    for (const line of lines) {
      // Skip comments
      const trimmed = line.trim();
      if (trimmed.startsWith('#') || trimmed.startsWith('//') || trimmed.startsWith('/*')) {
        continue;
      }

      // Extract paths from this line
      const linePaths = this.extractPathsFromLine(line);
      paths.push(...linePaths);
    }

    return [...new Set(paths)];
  }

  /**
   * Detect runtime from shebang line or file extension.
   */
  private detectRuntime(scriptPath: string, content?: string): ScriptRuntime {
    // Try shebang first
    if (content) {
      const runtime = this.detectRuntimeFromContent(content);
      if (runtime !== 'unknown') {
        return runtime;
      }
    }

    // Fall back to extension
    const ext = path.extname(scriptPath).toLowerCase();
    switch (ext) {
      case '.py':
        return 'python';
      case '.js':
      case '.mjs':
      case '.cjs':
        return 'node';
      case '.sh':
      case '.bash':
      case '.zsh':
      case '.fish':
        return 'shell';
      case '.rb':
        return 'ruby';
      case '.pl':
      case '.pm':
        return 'perl';
      default:
        return 'unknown';
    }
  }

  /**
   * Detect runtime from shebang in file content.
   */
  private detectRuntimeFromContent(content: string): ScriptRuntime {
    const firstLine = content.split('\n')[0];
    if (!firstLine.startsWith('#!')) {
      return 'unknown';
    }

    const shebang = firstLine.toLowerCase();

    if (shebang.includes('python')) return 'python';
    if (shebang.includes('node') || shebang.includes('nodejs')) return 'node';
    if (shebang.includes('bash') || shebang.includes('/sh') || shebang.includes('zsh') ||
        shebang.includes('dash') || shebang.includes('fish')) return 'shell';
    if (shebang.includes('ruby')) return 'ruby';
    if (shebang.includes('perl')) return 'perl';

    return 'unknown';
  }

  /**
   * Detect runtime from shebang by reading just the first line.
   */
  private detectRuntimeFromShebang(scriptPath: string): ScriptRuntime {
    try {
      const fd = fs.openSync(scriptPath, 'r');
      const buffer = Buffer.alloc(256);
      fs.readSync(fd, buffer, 0, 256, 0);
      fs.closeSync(fd);
      const firstLine = buffer.toString('utf8').split('\n')[0];
      return this.detectRuntimeFromContent(firstLine);
    } catch {
      return 'unknown';
    }
  }

  /**
   * Read script file safely with size and line limits.
   */
  private readScriptSafe(scriptPath: string): { content: string; error?: string } {
    try {
      // Resolve path
      const resolvedPath = path.resolve(scriptPath);

      // Check if file exists
      if (!fs.existsSync(resolvedPath)) {
        return { content: '', error: `File not found: ${scriptPath}` };
      }

      // Get file stats
      const stats = this.config.followSymlinks
        ? fs.statSync(resolvedPath)
        : fs.lstatSync(resolvedPath);

      // Check if it's a symlink and we're not following
      if (!this.config.followSymlinks && stats.isSymbolicLink()) {
        return { content: '', error: 'Symlink not followed (security policy)' };
      }

      // Check file size
      if (stats.size > this.config.maxFileSize) {
        return { content: '', error: `File too large: ${stats.size} bytes (max: ${this.config.maxFileSize})` };
      }

      // Check if it's a regular file
      if (!stats.isFile()) {
        return { content: '', error: 'Not a regular file' };
      }

      // Read the file
      const content = fs.readFileSync(resolvedPath, 'utf8');

      // Check line count
      const lineCount = content.split('\n').length;
      if (lineCount > this.config.maxLines) {
        // Only analyze first N lines
        const lines = content.split('\n').slice(0, this.config.maxLines);
        return { content: lines.join('\n') };
      }

      // Check if it looks like a binary file
      if (this.isBinaryContent(content)) {
        return { content: '', error: 'Binary file detected' };
      }

      return { content };
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      return { content: '', error: `Failed to read file: ${message}` };
    }
  }

  /**
   * Check if content appears to be binary.
   */
  private isBinaryContent(content: string): boolean {
    // Check for null bytes or high concentration of non-printable characters
    const sample = content.slice(0, 1000);
    let nonPrintable = 0;
    for (let i = 0; i < sample.length; i++) {
      const code = sample.charCodeAt(i);
      if (code === 0 || (code < 32 && code !== 9 && code !== 10 && code !== 13)) {
        nonPrintable++;
      }
    }
    return nonPrintable / sample.length > 0.1;
  }

  /**
   * Check if a file exists.
   */
  private fileExists(filePath: string): boolean {
    try {
      return fs.existsSync(filePath);
    } catch {
      return false;
    }
  }

  /**
   * Extract dangerous patterns from script content.
   */
  private extractThreats(content: string, runtime: ScriptRuntime): ScriptThreat[] {
    const threats: ScriptThreat[] = [];
    const lines = content.split('\n');

    // Get patterns applicable to this runtime
    const applicablePatterns = this.patterns.filter(
      p => p.runtime === 'all' || p.runtime === runtime
    );

    for (let lineNum = 0; lineNum < lines.length; lineNum++) {
      const line = lines[lineNum];

      // Skip empty lines and comments
      if (!line.trim() || this.isComment(line, runtime)) {
        continue;
      }

      for (const pattern of applicablePatterns) {
        const match = pattern.regex.exec(line);
        if (match) {
          const threat: ScriptThreat = {
            pattern: pattern.id,
            lineNumber: lineNum + 1,
            lineContent: line.length > 100 ? line.slice(0, 100) + '...' : line,
            category: pattern.category,
            severity: pattern.severity,
          };

          // Extract paths if pattern has pathGroups defined
          if (pattern.pathGroups && pattern.pathGroups.length > 0) {
            const paths: string[] = [];
            for (const groupIndex of pattern.pathGroups) {
              if (match[groupIndex]) {
                paths.push(this.normalizePath(match[groupIndex]));
              }
            }
            if (paths.length > 0) {
              threat.targetPaths = paths;
              // Upgrade severity if targeting catastrophic paths
              if (paths.some(p => this.isCatastrophicPath(p))) {
                threat.severity = 'catastrophic';
              }
            }
          }

          // Try to extract paths from the line even without explicit pathGroups
          if (!threat.targetPaths) {
            const extractedPaths = this.extractPathsFromLine(line);
            if (extractedPaths.length > 0) {
              threat.targetPaths = extractedPaths;
              if (extractedPaths.some(p => this.isCatastrophicPath(p))) {
                threat.severity = 'catastrophic';
              }
            }
          }

          threats.push(threat);
        }
      }
    }

    return threats;
  }

  /**
   * Check if a line is a comment based on runtime.
   */
  private isComment(line: string, runtime: ScriptRuntime): boolean {
    const trimmed = line.trim();
    switch (runtime) {
      case 'python':
      case 'shell':
      case 'ruby':
      case 'perl':
        return trimmed.startsWith('#');
      case 'node':
        return trimmed.startsWith('//') || trimmed.startsWith('/*');
      default:
        return trimmed.startsWith('#') || trimmed.startsWith('//');
    }
  }

  /**
   * Extract path-like strings from a line.
   */
  private extractPathsFromLine(line: string): string[] {
    const paths: string[] = [];

    // Match quoted strings that look like paths
    const quotedPaths = line.match(/['"]([\/~][^'"]*)['"]/g);
    if (quotedPaths) {
      for (const quoted of quotedPaths) {
        const p = quoted.slice(1, -1);
        paths.push(this.normalizePath(p));
      }
    }

    // Match unquoted paths starting with / or ~
    const unquotedPaths = line.match(/(?:^|[\s,\(])([\/~][^\s'")\],]+)/g);
    if (unquotedPaths) {
      for (const match of unquotedPaths) {
        const p = match.trim().replace(/^[,\(\s]/, '');
        if (p.startsWith('/') || p.startsWith('~')) {
          paths.push(this.normalizePath(p));
        }
      }
    }

    return [...new Set(paths)];
  }

  /**
   * Normalize a path for comparison.
   */
  private normalizePath(p: string): string {
    // Handle empty string
    if (!p) {
      return '/';
    }

    // Expand ~
    if (p.startsWith('~')) {
      p = p.replace(/^~/, this.homeDir);
    }

    // Special case: root path - path.normalize('/') returns '.' which is wrong
    if (p === '/') {
      return '/';
    }

    // Remove trailing slashes (but not for root)
    p = p.replace(/\/+$/, '');

    // Resolve .. and . (but preserve leading /)
    try {
      p = path.normalize(p);
    } catch {
      // Keep original if normalize fails
    }

    // Ensure we return '/' if everything was stripped
    return p || '/';
  }

  /**
   * Check if a path is catastrophic.
   */
  private isCatastrophicPath(p: string): boolean {
    const normalized = this.normalizePath(p);

    // Exact matches
    if (CATASTROPHIC_PATHS.includes(normalized)) {
      return true;
    }

    // Home directory
    if (normalized === this.homeDir) {
      return true;
    }

    // Check if it's a parent of or equal to catastrophic paths
    for (const catPath of CATASTROPHIC_PATHS) {
      if (normalized === catPath || catPath.startsWith(normalized + '/')) {
        return true;
      }
    }

    // Wildcards at dangerous locations
    if (normalized === '/*' || normalized === `${this.homeDir}/*`) {
      return true;
    }

    return false;
  }

  /**
   * Get built-in dangerous patterns for all runtimes.
   */
  private getBuiltInPatterns(): DangerousPattern[] {
    return [
      // ========== Shell patterns ==========
      {
        id: 'shell-rm-rf',
        runtime: 'shell',
        regex: /\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*|-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*|--recursive\s+--force|--force\s+--recursive)\s+(\S+)/,
        category: 'deletion',
        severity: 'high',
        pathGroups: [2],
        description: 'Recursive forced removal (rm -rf)',
      },
      {
        id: 'shell-rm-recursive',
        runtime: 'shell',
        regex: /\brm\s+(-[a-zA-Z]*r[a-zA-Z]*|--recursive)\s+(\S+)/,
        category: 'deletion',
        severity: 'medium',
        pathGroups: [2],
        description: 'Recursive removal (rm -r)',
      },
      {
        id: 'shell-rmdir',
        runtime: 'shell',
        regex: /\brmdir\s+(\S+)/,
        category: 'deletion',
        severity: 'medium',
        pathGroups: [1],
        description: 'Directory removal',
      },
      {
        id: 'shell-dd-write',
        runtime: 'shell',
        regex: /\bdd\s+.*\bof=(\S+)/,
        category: 'system_modification',
        severity: 'high',
        pathGroups: [1],
        description: 'Low-level disk write (dd)',
      },
      {
        id: 'shell-mkfs',
        runtime: 'shell',
        regex: /\bmkfs(\.[a-z0-9]+)?\s+(\S+)/,
        category: 'system_modification',
        severity: 'catastrophic',
        pathGroups: [2],
        description: 'Filesystem format (mkfs)',
      },
      {
        id: 'shell-shred',
        runtime: 'shell',
        regex: /\bshred\s+.*(\S+)/,
        category: 'deletion',
        severity: 'high',
        pathGroups: [1],
        description: 'Secure file deletion (shred)',
      },

      // ========== Python patterns ==========
      {
        id: 'python-shutil-rmtree',
        runtime: 'python',
        regex: /\bshutil\.rmtree\s*\(\s*['"]([^'"]+)['"]/,
        category: 'deletion',
        severity: 'high',
        pathGroups: [1],
        description: 'Recursive directory removal (shutil.rmtree)',
      },
      {
        id: 'python-shutil-rmtree-var',
        runtime: 'python',
        regex: /\bshutil\.rmtree\s*\([^)]+\)/,
        category: 'deletion',
        severity: 'high',
        description: 'Recursive directory removal with variable (shutil.rmtree)',
      },
      {
        id: 'python-os-remove',
        runtime: 'python',
        regex: /\bos\.(remove|unlink)\s*\(\s*['"]([^'"]+)['"]/,
        category: 'deletion',
        severity: 'medium',
        pathGroups: [2],
        description: 'File deletion (os.remove/unlink)',
      },
      {
        id: 'python-os-rmdir',
        runtime: 'python',
        regex: /\bos\.rmdir\s*\(\s*['"]([^'"]+)['"]/,
        category: 'deletion',
        severity: 'medium',
        pathGroups: [1],
        description: 'Directory removal (os.rmdir)',
      },
      {
        id: 'python-os-system-rm',
        runtime: 'python',
        regex: /\bos\.system\s*\(\s*['"](.*rm\s+.*)['"]/,
        category: 'shell_execution',
        severity: 'high',
        pathGroups: [1],
        description: 'Shell command execution with rm (os.system)',
      },
      {
        id: 'python-subprocess-rm',
        runtime: 'python',
        regex: /\bsubprocess\.(run|call|Popen)\s*\(\s*\[?\s*['"](.*rm.*)['"]/,
        category: 'shell_execution',
        severity: 'high',
        description: 'Subprocess execution with rm',
      },
      {
        id: 'python-pathlib-rmtree',
        runtime: 'python',
        regex: /\.rmtree\s*\(\s*\)/,
        category: 'deletion',
        severity: 'high',
        description: 'Pathlib recursive removal',
      },

      // ========== Node.js patterns ==========
      {
        id: 'node-fs-rm-sync',
        runtime: 'node',
        regex: /\bfs\.(rmSync|unlinkSync|rmdirSync)\s*\(\s*['"]([^'"]+)['"]/,
        category: 'deletion',
        severity: 'high',
        pathGroups: [2],
        description: 'Synchronous file/directory deletion',
      },
      {
        id: 'node-fs-rm-recursive',
        runtime: 'node',
        regex: /\bfs\.rm\s*\([^)]*recursive\s*:\s*true/,
        category: 'deletion',
        severity: 'high',
        description: 'Recursive file removal (fs.rm with recursive)',
      },
      {
        id: 'node-fs-promises-rm',
        runtime: 'node',
        regex: /\bfs\.promises\.(rm|rmdir|unlink)\s*\(\s*['"]([^'"]+)['"]/,
        category: 'deletion',
        severity: 'high',
        pathGroups: [2],
        description: 'Promise-based file deletion',
      },
      {
        id: 'node-rimraf',
        runtime: 'node',
        regex: /\brimraf\s*\(\s*['"]([^'"]+)['"]/,
        category: 'deletion',
        severity: 'high',
        pathGroups: [1],
        description: 'rimraf package deletion',
      },
      {
        id: 'node-child-process-rm',
        runtime: 'node',
        regex: /\bchild_process\.(exec|execSync|spawn|spawnSync)\s*\(\s*['"]([^'"]*rm\s+[^'"]*)['"]/,
        category: 'shell_execution',
        severity: 'high',
        pathGroups: [2],
        description: 'Child process with rm command',
      },
      {
        id: 'node-exec-rm',
        runtime: 'node',
        regex: /\bexec\s*\(\s*['"]([^'"]*rm\s+[^'"]*)['"]/,
        category: 'shell_execution',
        severity: 'high',
        pathGroups: [1],
        description: 'exec() with rm command',
      },

      // ========== Ruby patterns ==========
      {
        id: 'ruby-fileutils-rm-rf',
        runtime: 'ruby',
        regex: /\bFileUtils\.(rm_rf|remove_dir|remove_entry_secure)\s*\(\s*['"]([^'"]+)['"]/,
        category: 'deletion',
        severity: 'high',
        pathGroups: [2],
        description: 'FileUtils recursive deletion',
      },
      {
        id: 'ruby-file-delete',
        runtime: 'ruby',
        regex: /\bFile\.delete\s*\(\s*['"]([^'"]+)['"]/,
        category: 'deletion',
        severity: 'medium',
        pathGroups: [1],
        description: 'File deletion',
      },
      {
        id: 'ruby-system-rm',
        runtime: 'ruby',
        regex: /\bsystem\s*\(\s*['"]([^'"]*rm\s+[^'"]*)['"]/,
        category: 'shell_execution',
        severity: 'high',
        pathGroups: [1],
        description: 'System call with rm',
      },

      // ========== Perl patterns ==========
      {
        id: 'perl-unlink',
        runtime: 'perl',
        regex: /\bunlink\s*\(\s*['"]([^'"]+)['"]/,
        category: 'deletion',
        severity: 'medium',
        pathGroups: [1],
        description: 'File deletion (unlink)',
      },
      {
        id: 'perl-rmtree',
        runtime: 'perl',
        regex: /\brmtree\s*\(\s*['"]([^'"]+)['"]/,
        category: 'deletion',
        severity: 'high',
        pathGroups: [1],
        description: 'Recursive directory removal (rmtree)',
      },
      {
        id: 'perl-system-rm',
        runtime: 'perl',
        regex: /\bsystem\s*\(\s*['"]([^'"]*rm\s+[^'"]*)['"]/,
        category: 'shell_execution',
        severity: 'high',
        pathGroups: [1],
        description: 'System call with rm',
      },

      // ========== Universal patterns (all runtimes) ==========
      {
        id: 'any-eval-rm',
        runtime: 'all',
        regex: /\beval\s*\(\s*['"]([^'"]*rm\s+-rf[^'"]*)['"]/,
        category: 'shell_execution',
        severity: 'catastrophic',
        pathGroups: [1],
        description: 'Eval with rm -rf',
      },
    ];
  }
}
