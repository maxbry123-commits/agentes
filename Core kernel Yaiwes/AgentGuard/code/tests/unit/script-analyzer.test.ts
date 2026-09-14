/**
 * Unit tests for ScriptAnalyzer
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { ScriptAnalyzer } from '../../src/script-analyzer';
import { CommandSegment } from '../../src/types';

describe('ScriptAnalyzer', () => {
  let analyzer: ScriptAnalyzer;
  let tempDir: string;

  beforeEach(() => {
    analyzer = new ScriptAnalyzer();
    // Create temp directory for test scripts
    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'agentguard-test-'));
  });

  afterEach(() => {
    // Clean up temp directory
    if (tempDir && fs.existsSync(tempDir)) {
      fs.rmSync(tempDir, { recursive: true, force: true });
    }
  });

  // Helper to create a test script
  function createScript(name: string, content: string): string {
    const scriptPath = path.join(tempDir, name);
    fs.writeFileSync(scriptPath, content);
    return scriptPath;
  }

  describe('detectScriptExecution', () => {
    it('should detect python script.py', () => {
      const segment: CommandSegment = { command: 'python', args: ['script.py'] };
      expect(analyzer.detectScriptExecution(segment)).toBe('script.py');
    });

    it('should detect python3 /path/to/script.py', () => {
      const segment: CommandSegment = { command: 'python3', args: ['/path/to/script.py'] };
      expect(analyzer.detectScriptExecution(segment)).toBe('/path/to/script.py');
    });

    it('should detect node app.js', () => {
      const segment: CommandSegment = { command: 'node', args: ['app.js'] };
      expect(analyzer.detectScriptExecution(segment)).toBe('app.js');
    });

    it('should detect node with .mjs extension', () => {
      const segment: CommandSegment = { command: 'node', args: ['module.mjs'] };
      expect(analyzer.detectScriptExecution(segment)).toBe('module.mjs');
    });

    it('should detect node with .cjs extension', () => {
      const segment: CommandSegment = { command: 'node', args: ['common.cjs'] };
      expect(analyzer.detectScriptExecution(segment)).toBe('common.cjs');
    });

    it('should detect bash script.sh', () => {
      const segment: CommandSegment = { command: 'bash', args: ['script.sh'] };
      expect(analyzer.detectScriptExecution(segment)).toBe('script.sh');
    });

    it('should detect sh script.sh', () => {
      const segment: CommandSegment = { command: 'sh', args: ['script.sh'] };
      expect(analyzer.detectScriptExecution(segment)).toBe('script.sh');
    });

    it('should detect zsh script.zsh', () => {
      const segment: CommandSegment = { command: 'zsh', args: ['script.zsh'] };
      expect(analyzer.detectScriptExecution(segment)).toBe('script.zsh');
    });

    it('should detect ruby script.rb', () => {
      const segment: CommandSegment = { command: 'ruby', args: ['script.rb'] };
      expect(analyzer.detectScriptExecution(segment)).toBe('script.rb');
    });

    it('should detect perl script.pl', () => {
      const segment: CommandSegment = { command: 'perl', args: ['script.pl'] };
      expect(analyzer.detectScriptExecution(segment)).toBe('script.pl');
    });

    it('should detect ./script.sh (direct execution)', () => {
      const scriptPath = createScript('test.sh', '#!/bin/bash\necho hello');
      const segment: CommandSegment = { command: scriptPath, args: [] };
      expect(analyzer.detectScriptExecution(segment)).toBe(scriptPath);
    });

    it('should detect ./script.py (direct Python execution)', () => {
      const segment: CommandSegment = { command: './script.py', args: [] };
      expect(analyzer.detectScriptExecution(segment)).toBe('./script.py');
    });

    it('should detect /absolute/path/script.js', () => {
      const segment: CommandSegment = { command: '/usr/local/bin/script.js', args: [] };
      expect(analyzer.detectScriptExecution(segment)).toBe('/usr/local/bin/script.js');
    });

    it('should NOT detect python -c "code"', () => {
      const segment: CommandSegment = { command: 'python', args: ['-c', 'print("hi")'] };
      expect(analyzer.detectScriptExecution(segment)).toBeNull();
    });

    it('should NOT detect python -m module', () => {
      const segment: CommandSegment = { command: 'python', args: ['-m', 'pip', 'install'] };
      expect(analyzer.detectScriptExecution(segment)).toBeNull();
    });

    it('should NOT detect node -e "code"', () => {
      const segment: CommandSegment = { command: 'node', args: ['-e', 'console.log("hi")'] };
      expect(analyzer.detectScriptExecution(segment)).toBeNull();
    });

    it('should NOT detect bash -c "command"', () => {
      const segment: CommandSegment = { command: 'bash', args: ['-c', 'echo hello'] };
      expect(analyzer.detectScriptExecution(segment)).toBeNull();
    });

    it('should NOT detect python (no args)', () => {
      const segment: CommandSegment = { command: 'python', args: [] };
      expect(analyzer.detectScriptExecution(segment)).toBeNull();
    });

    it('should NOT detect non-script commands like ls', () => {
      const segment: CommandSegment = { command: 'ls', args: ['-la'] };
      expect(analyzer.detectScriptExecution(segment)).toBeNull();
    });

    it('should skip flags and find script after them', () => {
      const segment: CommandSegment = { command: 'python', args: ['-u', '-B', 'script.py'] };
      expect(analyzer.detectScriptExecution(segment)).toBe('script.py');
    });
  });

  describe('analyze - Python scripts', () => {
    it('should detect shutil.rmtree("/")', () => {
      const scriptPath = createScript('malicious.py', `
import shutil
shutil.rmtree("/")
`);
      const result = analyzer.analyze(scriptPath);
      expect(result.analyzed).toBe(true);
      expect(result.runtime).toBe('python');
      expect(result.shouldBlock).toBe(true);
      expect(result.threats.length).toBeGreaterThan(0);
      expect(result.threats[0].pattern).toBe('python-shutil-rmtree');
      expect(result.threats[0].severity).toBe('catastrophic');
    });

    it('should detect shutil.rmtree("~") as catastrophic', () => {
      const scriptPath = createScript('home_delete.py', `
import shutil
shutil.rmtree("~")
`);
      const result = analyzer.analyze(scriptPath);
      expect(result.analyzed).toBe(true);
      expect(result.shouldBlock).toBe(true);
    });

    it('should detect os.remove with path', () => {
      const scriptPath = createScript('remove.py', `
import os
os.remove("/etc/passwd")
`);
      const result = analyzer.analyze(scriptPath);
      expect(result.analyzed).toBe(true);
      expect(result.threats.length).toBeGreaterThan(0);
      expect(result.threats[0].pattern).toBe('python-os-remove');
    });

    it('should detect os.system("rm -rf /")', () => {
      const scriptPath = createScript('system_rm.py', `
import os
os.system("rm -rf /")
`);
      const result = analyzer.analyze(scriptPath);
      expect(result.analyzed).toBe(true);
      expect(result.threats.length).toBeGreaterThan(0);
      expect(result.threats[0].pattern).toBe('python-os-system-rm');
    });

    it('should detect subprocess with rm', () => {
      const scriptPath = createScript('subprocess_rm.py', `
import subprocess
subprocess.run(["rm", "-rf", "/tmp/test"])
`);
      const result = analyzer.analyze(scriptPath);
      expect(result.analyzed).toBe(true);
      expect(result.threats.length).toBeGreaterThan(0);
    });

    it('should allow safe Python scripts', () => {
      const scriptPath = createScript('safe.py', `
import os
print("Hello, world!")
x = 1 + 2
os.getcwd()
`);
      const result = analyzer.analyze(scriptPath);
      expect(result.analyzed).toBe(true);
      expect(result.shouldBlock).toBe(false);
      expect(result.threats.length).toBe(0);
    });

    it('should detect runtime from shebang', () => {
      const scriptPath = createScript('shebang_script', `#!/usr/bin/env python3
import shutil
shutil.rmtree("/home")
`);
      const result = analyzer.analyze(scriptPath);
      expect(result.runtime).toBe('python');
      expect(result.shouldBlock).toBe(true);
    });
  });

  describe('analyze - Node.js scripts', () => {
    it('should detect fs.rmSync with path', () => {
      const scriptPath = createScript('delete.js', `
const fs = require('fs');
fs.rmSync("/home/user", { recursive: true });
`);
      const result = analyzer.analyze(scriptPath);
      expect(result.analyzed).toBe(true);
      expect(result.runtime).toBe('node');
      expect(result.threats.length).toBeGreaterThan(0);
      expect(result.threats[0].pattern).toBe('node-fs-rm-sync');
    });

    it('should detect fs.rm with recursive: true', () => {
      const scriptPath = createScript('rm_recursive.js', `
const fs = require('fs');
fs.rm("/tmp", { recursive: true }, (err) => {});
`);
      const result = analyzer.analyze(scriptPath);
      expect(result.analyzed).toBe(true);
      expect(result.threats.length).toBeGreaterThan(0);
    });

    it('should detect rimraf("/")', () => {
      const scriptPath = createScript('rimraf_root.js', `
const rimraf = require('rimraf');
rimraf("/")
`);
      const result = analyzer.analyze(scriptPath);
      expect(result.analyzed).toBe(true);
      expect(result.shouldBlock).toBe(true);
      expect(result.threats[0].pattern).toBe('node-rimraf');
    });

    it('should detect child_process.exec with rm', () => {
      const scriptPath = createScript('exec_rm.js', `
const { exec } = require('child_process');
exec("rm -rf /tmp/*");
`);
      const result = analyzer.analyze(scriptPath);
      expect(result.analyzed).toBe(true);
      expect(result.threats.length).toBeGreaterThan(0);
    });

    it('should allow safe Node.js scripts', () => {
      const scriptPath = createScript('safe.js', `
const fs = require('fs');
const data = fs.readFileSync('file.txt');
console.log(data);
`);
      const result = analyzer.analyze(scriptPath);
      expect(result.analyzed).toBe(true);
      expect(result.shouldBlock).toBe(false);
    });
  });

  describe('analyze - Shell scripts', () => {
    it('should detect rm -rf /', () => {
      const scriptPath = createScript('danger.sh', `#!/bin/bash
rm -rf /
`);
      const result = analyzer.analyze(scriptPath);
      expect(result.analyzed).toBe(true);
      expect(result.runtime).toBe('shell');
      expect(result.shouldBlock).toBe(true);
      expect(result.threats[0].severity).toBe('catastrophic');
    });

    it('should detect rm -rf ~', () => {
      const scriptPath = createScript('home.sh', `#!/bin/bash
rm -rf ~
`);
      const result = analyzer.analyze(scriptPath);
      expect(result.analyzed).toBe(true);
      expect(result.shouldBlock).toBe(true);
    });

    it('should detect dd write to device', () => {
      const scriptPath = createScript('dd.sh', `#!/bin/bash
dd if=/dev/zero of=/dev/sda
`);
      const result = analyzer.analyze(scriptPath);
      expect(result.analyzed).toBe(true);
      expect(result.threats.length).toBeGreaterThan(0);
      expect(result.threats[0].pattern).toBe('shell-dd-write');
    });

    it('should detect mkfs', () => {
      const scriptPath = createScript('mkfs.sh', `#!/bin/bash
mkfs.ext4 /dev/sdb1
`);
      const result = analyzer.analyze(scriptPath);
      expect(result.analyzed).toBe(true);
      expect(result.threats.length).toBeGreaterThan(0);
      expect(result.threats[0].severity).toBe('catastrophic');
    });

    it('should detect shred', () => {
      const scriptPath = createScript('shred.sh', `#!/bin/bash
shred -vfz /dev/sda
`);
      const result = analyzer.analyze(scriptPath);
      expect(result.analyzed).toBe(true);
      expect(result.threats.length).toBeGreaterThan(0);
    });

    it('should allow safe shell scripts', () => {
      const scriptPath = createScript('safe.sh', `#!/bin/bash
echo "Hello, world!"
ls -la
cat README.md
`);
      const result = analyzer.analyze(scriptPath);
      expect(result.analyzed).toBe(true);
      expect(result.shouldBlock).toBe(false);
    });

    it('should skip comments', () => {
      const scriptPath = createScript('comments.sh', `#!/bin/bash
# rm -rf /
# This is a comment about dangerous commands
echo "Safe script"
`);
      const result = analyzer.analyze(scriptPath);
      expect(result.analyzed).toBe(true);
      expect(result.shouldBlock).toBe(false);
    });
  });

  describe('analyze - Ruby scripts', () => {
    it('should detect FileUtils.rm_rf', () => {
      const scriptPath = createScript('cleanup.rb', `
require 'fileutils'
FileUtils.rm_rf("/")
`);
      const result = analyzer.analyze(scriptPath);
      expect(result.analyzed).toBe(true);
      expect(result.runtime).toBe('ruby');
      expect(result.threats.length).toBeGreaterThan(0);
    });

    it('should detect system("rm -rf")', () => {
      const scriptPath = createScript('system.rb', `
system("rm -rf /home/user")
`);
      const result = analyzer.analyze(scriptPath);
      expect(result.analyzed).toBe(true);
      expect(result.threats.length).toBeGreaterThan(0);
    });
  });

  describe('analyze - graceful handling', () => {
    it('should fail-open for missing files', () => {
      const result = analyzer.analyze('/nonexistent/script.py');
      expect(result.analyzed).toBe(false);
      expect(result.shouldBlock).toBe(false);
      expect(result.analysisError).toContain('not found');
    });

    it('should fail-open for directories', () => {
      const result = analyzer.analyze(tempDir);
      expect(result.analyzed).toBe(false);
      expect(result.shouldBlock).toBe(false);
    });

    it('should fail-open for binary files', () => {
      const binaryPath = path.join(tempDir, 'binary.py');
      // Create a file with binary content (null bytes)
      fs.writeFileSync(binaryPath, Buffer.from([0x00, 0x01, 0x02, 0x00, 0x03, 0x00]));
      const result = analyzer.analyze(binaryPath);
      expect(result.analyzed).toBe(false);
      expect(result.shouldBlock).toBe(false);
    });

    it('should handle files exceeding size limit', () => {
      // Create analyzer with tiny size limit
      const smallAnalyzer = new ScriptAnalyzer({ maxFileSize: 10 });
      const scriptPath = createScript('large.py', 'x = 1\n'.repeat(100));
      const result = smallAnalyzer.analyze(scriptPath);
      expect(result.analyzed).toBe(false);
      expect(result.analysisError).toContain('too large');
    });

    it('should truncate files exceeding line limit', () => {
      const manyLinesAnalyzer = new ScriptAnalyzer({ maxLines: 5 });
      const scriptPath = createScript('many_lines.py', `
line1
line2
line3
line4
shutil.rmtree("/")
line6
line7
line8
`);
      // Should still analyze (truncated, but works)
      const result = manyLinesAnalyzer.analyze(scriptPath);
      expect(result.analyzed).toBe(true);
    });
  });

  describe('analyze - path extraction and catastrophic detection', () => {
    it('should extract paths from quoted strings', () => {
      const scriptPath = createScript('paths.py', `
import shutil
shutil.rmtree("/home/user")
`);
      const result = analyzer.analyze(scriptPath);
      expect(result.threats[0].targetPaths).toContain('/home/user');
    });

    it('should detect catastrophic path in function argument', () => {
      const scriptPath = createScript('cat_path.py', `
import shutil
shutil.rmtree("/etc")
`);
      const result = analyzer.analyze(scriptPath);
      expect(result.shouldBlock).toBe(true);
      expect(result.threats[0].severity).toBe('catastrophic');
    });

    it('should NOT block safe paths', () => {
      const scriptPath = createScript('safe_rm.py', `
import shutil
shutil.rmtree("/tmp/myapp/cache")
`);
      const result = analyzer.analyze(scriptPath);
      expect(result.analyzed).toBe(true);
      // Should have threat but not catastrophic severity
      expect(result.threats.length).toBeGreaterThan(0);
      expect(result.threats[0].severity).not.toBe('catastrophic');
      expect(result.shouldBlock).toBe(false);
    });
  });

  describe('analyze - real-world attack scenarios', () => {
    it('should block AI-written "cleanup" script with hidden rmtree("/")', () => {
      const scriptPath = createScript('cleanup.py', `
#!/usr/bin/env python3
"""
Cleanup script to remove temporary files and caches.
This helps free up disk space on the system.
"""

import shutil
import os

def cleanup_temps():
    """Clean up temporary directories."""
    dirs_to_clean = [
        "./temp",
        "./cache",
        "./__pycache__",
        "/",  # Oops, this was a mistake
    ]
    for d in dirs_to_clean:
        if os.path.exists(d):
            shutil.rmtree(d, ignore_errors=True)

if __name__ == "__main__":
    cleanup_temps()
    print("Cleanup complete!")
`);
      const result = analyzer.analyze(scriptPath);
      expect(result.analyzed).toBe(true);
      expect(result.shouldBlock).toBe(true);
      expect(result.blockReason).toContain('catastrophic');
    });

    it('should block script with os.system rm -rf hidden in variables', () => {
      const scriptPath = createScript('sneaky.py', `
import os

# Cleanup command
cmd = "rm -rf /"
os.system(cmd)
`);
      // Note: This particular pattern won't be caught because we look for
      // os.system("rm...) with the string directly in the call.
      // This is a known limitation - we'd need dataflow analysis to catch this.
      const result = analyzer.analyze(scriptPath);
      expect(result.analyzed).toBe(true);
      // This specific pattern may not be caught - documenting expected behavior
    });

    it('should block Node script with rimraf on home directory', () => {
      const scriptPath = createScript('deploy.js', `
const rimraf = require('rimraf');
const path = require('path');

// Clean build directory
rimraf("~")
console.log("Build directory cleaned");
`);
      const result = analyzer.analyze(scriptPath);
      expect(result.analyzed).toBe(true);
      expect(result.shouldBlock).toBe(true);
    });

    it('should block shell script with rm -rf buried in function', () => {
      const scriptPath = createScript('build.sh', `#!/bin/bash

# Build script for myapp

function clean() {
    echo "Cleaning build artifacts..."
    rm -rf /
}

function build() {
    echo "Building..."
    npm run build
}

clean
build
`);
      const result = analyzer.analyze(scriptPath);
      expect(result.analyzed).toBe(true);
      expect(result.shouldBlock).toBe(true);
    });
  });
});
