import { describe, test, expect, beforeEach } from 'vitest';
import { CommandUnwrapper } from '../../src/command-unwrapper';
import { CommandSegment } from '../../src/types';

describe('CommandUnwrapper', () => {
  let unwrapper: CommandUnwrapper;

  beforeEach(() => {
    unwrapper = new CommandUnwrapper();
  });

  describe('passthrough wrappers', () => {
    test('should unwrap sudo', () => {
      const segment: CommandSegment = {
        command: 'sudo',
        args: ['rm', '-rf', '/tmp/test']
      };

      const results = unwrapper.unwrap(segment);

      expect(results).toHaveLength(1);
      expect(results[0].command).toBe('rm');
      expect(results[0].args).toEqual(['-rf', '/tmp/test']);
      expect(results[0].wrappers).toEqual(['sudo']);
      expect(results[0].hasDynamicArgs).toBe(false);
    });

    test('should unwrap sudo with flags', () => {
      const segment: CommandSegment = {
        command: 'sudo',
        args: ['-u', 'root', 'rm', '-rf', '/tmp/test']
      };

      const results = unwrapper.unwrap(segment);

      expect(results).toHaveLength(1);
      expect(results[0].command).toBe('rm');
      expect(results[0].args).toEqual(['-rf', '/tmp/test']);
      expect(results[0].wrappers).toEqual(['sudo']);
    });

    test('should unwrap env', () => {
      const segment: CommandSegment = {
        command: 'env',
        args: ['VAR=value', 'rm', '-rf', '/tmp/test']
      };

      const results = unwrapper.unwrap(segment);

      expect(results).toHaveLength(1);
      expect(results[0].command).toBe('rm');
      expect(results[0].args).toEqual(['-rf', '/tmp/test']);
      expect(results[0].wrappers).toEqual(['env']);
    });

    test('should unwrap nice', () => {
      const segment: CommandSegment = {
        command: 'nice',
        args: ['-n', '10', 'rm', '-rf', '/tmp/test']
      };

      const results = unwrapper.unwrap(segment);

      expect(results).toHaveLength(1);
      expect(results[0].command).toBe('rm');
      expect(results[0].args).toEqual(['-rf', '/tmp/test']);
      expect(results[0].wrappers).toEqual(['nice']);
    });

    test('should unwrap timeout', () => {
      const segment: CommandSegment = {
        command: 'timeout',
        args: ['30', 'rm', '-rf', '/tmp/test']
      };

      const results = unwrapper.unwrap(segment);

      expect(results).toHaveLength(1);
      expect(results[0].command).toBe('rm');
      expect(results[0].args).toEqual(['-rf', '/tmp/test']);
      expect(results[0].wrappers).toEqual(['timeout']);
    });

    test('should unwrap nested wrappers (sudo + env)', () => {
      const segment: CommandSegment = {
        command: 'sudo',
        args: ['env', 'PATH=/bin', 'rm', '-rf', '/tmp/test']
      };

      const results = unwrapper.unwrap(segment);

      expect(results).toHaveLength(1);
      expect(results[0].command).toBe('rm');
      expect(results[0].args).toEqual(['-rf', '/tmp/test']);
      expect(results[0].wrappers).toEqual(['sudo', 'env']);
    });

    test('should unwrap doas', () => {
      const segment: CommandSegment = {
        command: 'doas',
        args: ['rm', '-rf', '/tmp/test']
      };

      const results = unwrapper.unwrap(segment);

      expect(results).toHaveLength(1);
      expect(results[0].command).toBe('rm');
      expect(results[0].args).toEqual(['-rf', '/tmp/test']);
      expect(results[0].wrappers).toEqual(['doas']);
    });

    test('should unwrap time', () => {
      const segment: CommandSegment = {
        command: 'time',
        args: ['rm', '-rf', '/tmp/test']
      };

      const results = unwrapper.unwrap(segment);

      expect(results).toHaveLength(1);
      expect(results[0].command).toBe('rm');
      expect(results[0].args).toEqual(['-rf', '/tmp/test']);
      expect(results[0].wrappers).toEqual(['time']);
    });

    test('should unwrap watch', () => {
      const segment: CommandSegment = {
        command: 'watch',
        args: ['-n', '5', 'rm', '-rf', '/tmp/test']
      };

      const results = unwrapper.unwrap(segment);

      expect(results).toHaveLength(1);
      expect(results[0].command).toBe('rm');
      expect(results[0].args).toEqual(['-rf', '/tmp/test']);
      expect(results[0].wrappers).toEqual(['watch']);
    });

    test('should unwrap strace', () => {
      const segment: CommandSegment = {
        command: 'strace',
        args: ['-f', 'rm', '-rf', '/tmp/test']
      };

      const results = unwrapper.unwrap(segment);

      expect(results).toHaveLength(1);
      expect(results[0].command).toBe('rm');
      expect(results[0].args).toEqual(['-rf', '/tmp/test']);
      expect(results[0].wrappers).toEqual(['strace']);
    });

    test('should unwrap ltrace', () => {
      const segment: CommandSegment = {
        command: 'ltrace',
        args: ['-e', 'malloc', 'rm', '-rf', '/tmp/test']
      };

      const results = unwrapper.unwrap(segment);

      expect(results).toHaveLength(1);
      expect(results[0].command).toBe('rm');
      expect(results[0].args).toEqual(['-rf', '/tmp/test']);
      expect(results[0].wrappers).toEqual(['ltrace']);
    });

    test('should unwrap ionice', () => {
      const segment: CommandSegment = {
        command: 'ionice',
        args: ['-c', '3', 'rm', '-rf', '/tmp/test']
      };

      const results = unwrapper.unwrap(segment);

      expect(results).toHaveLength(1);
      expect(results[0].command).toBe('rm');
      expect(results[0].args).toEqual(['-rf', '/tmp/test']);
      expect(results[0].wrappers).toEqual(['ionice']);
    });

    test('should unwrap chroot', () => {
      const segment: CommandSegment = {
        command: 'chroot',
        args: ['/mnt', 'rm', '-rf', '/tmp/test']
      };

      const results = unwrapper.unwrap(segment);

      expect(results).toHaveLength(1);
      expect(results[0].command).toBe('rm');
      expect(results[0].args).toEqual(['-rf', '/tmp/test']);
      expect(results[0].wrappers).toEqual(['chroot']);
    });

    test('should unwrap runuser', () => {
      const segment: CommandSegment = {
        command: 'runuser',
        args: ['-u', 'nobody', 'rm', '-rf', '/tmp/test']
      };

      const results = unwrapper.unwrap(segment);

      expect(results).toHaveLength(1);
      expect(results[0].command).toBe('rm');
      expect(results[0].args).toEqual(['-rf', '/tmp/test']);
      expect(results[0].wrappers).toEqual(['runuser']);
    });

    test('should unwrap su -c', () => {
      const segment: CommandSegment = {
        command: 'su',
        args: ['-c', 'rm -rf /tmp/test']
      };

      const results = unwrapper.unwrap(segment);

      expect(results).toHaveLength(1);
      expect(results[0].command).toBe('rm');
      expect(results[0].args).toEqual(['-rf', '/tmp/test']);
      expect(results[0].wrappers).toEqual(['su -c']);
    });

    test('should unwrap su with user and -c', () => {
      const segment: CommandSegment = {
        command: 'su',
        args: ['root', '-c', 'rm -rf /tmp/test']
      };

      const results = unwrapper.unwrap(segment);

      expect(results).toHaveLength(1);
      expect(results[0].command).toBe('rm');
      expect(results[0].args).toEqual(['-rf', '/tmp/test']);
      expect(results[0].wrappers).toEqual(['su -c']);
    });
  });

  describe('shell -c wrappers', () => {
    test('should unwrap bash -c', () => {
      const segment: CommandSegment = {
        command: 'bash',
        args: ['-c', 'rm -rf /tmp/test']
      };

      const results = unwrapper.unwrap(segment);

      expect(results).toHaveLength(1);
      expect(results[0].command).toBe('rm');
      expect(results[0].args).toEqual(['-rf', '/tmp/test']);
      expect(results[0].wrappers).toEqual(['bash -c']);
    });

    test('should unwrap sh -c', () => {
      const segment: CommandSegment = {
        command: 'sh',
        args: ['-c', 'rm -rf /']
      };

      const results = unwrapper.unwrap(segment);

      expect(results).toHaveLength(1);
      expect(results[0].command).toBe('rm');
      expect(results[0].args).toEqual(['-rf', '/']);
      expect(results[0].wrappers).toEqual(['sh -c']);
    });

    test('should unwrap zsh -c', () => {
      const segment: CommandSegment = {
        command: 'zsh',
        args: ['-c', 'rm -rf ~/important']
      };

      const results = unwrapper.unwrap(segment);

      expect(results).toHaveLength(1);
      expect(results[0].command).toBe('rm');
      expect(results[0].args).toEqual(['-rf', '~/important']);
      expect(results[0].wrappers).toEqual(['zsh -c']);
    });

    test('should unwrap bash -c with piped commands', () => {
      const segment: CommandSegment = {
        command: 'bash',
        args: ['-c', 'echo test | rm -rf /']
      };

      const results = unwrapper.unwrap(segment);

      expect(results.length).toBeGreaterThanOrEqual(2);
      // Should find both echo and rm
      const rmCommand = results.find(r => r.command === 'rm');
      expect(rmCommand).toBeDefined();
      expect(rmCommand?.args).toEqual(['-rf', '/']);
    });

    test('should unwrap bash -c with chained commands', () => {
      const segment: CommandSegment = {
        command: 'bash',
        args: ['-c', 'cd / && rm -rf *']
      };

      const results = unwrapper.unwrap(segment);

      const rmCommand = results.find(r => r.command === 'rm');
      expect(rmCommand).toBeDefined();
      expect(rmCommand?.args).toEqual(['-rf', '*']);
    });

    test('should unwrap sudo bash -c (nested)', () => {
      const segment: CommandSegment = {
        command: 'sudo',
        args: ['bash', '-c', 'rm -rf /']
      };

      const results = unwrapper.unwrap(segment);

      expect(results).toHaveLength(1);
      expect(results[0].command).toBe('rm');
      expect(results[0].args).toEqual(['-rf', '/']);
      expect(results[0].wrappers).toEqual(['sudo', 'bash -c']);
    });

    test('should unwrap dash -c', () => {
      const segment: CommandSegment = {
        command: 'dash',
        args: ['-c', 'rm -rf /tmp/test']
      };

      const results = unwrapper.unwrap(segment);

      expect(results).toHaveLength(1);
      expect(results[0].command).toBe('rm');
      expect(results[0].args).toEqual(['-rf', '/tmp/test']);
      expect(results[0].wrappers).toEqual(['dash -c']);
    });

    test('should unwrap fish -c', () => {
      const segment: CommandSegment = {
        command: 'fish',
        args: ['-c', 'rm -rf /tmp/test']
      };

      const results = unwrapper.unwrap(segment);

      expect(results).toHaveLength(1);
      expect(results[0].command).toBe('rm');
      expect(results[0].args).toEqual(['-rf', '/tmp/test']);
      expect(results[0].wrappers).toEqual(['fish -c']);
    });

    test('should unwrap ksh -c', () => {
      const segment: CommandSegment = {
        command: 'ksh',
        args: ['-c', 'rm -rf /tmp/test']
      };

      const results = unwrapper.unwrap(segment);

      expect(results).toHaveLength(1);
      expect(results[0].command).toBe('rm');
      expect(results[0].args).toEqual(['-rf', '/tmp/test']);
      expect(results[0].wrappers).toEqual(['ksh -c']);
    });

    test('should unwrap csh -c', () => {
      const segment: CommandSegment = {
        command: 'csh',
        args: ['-c', 'rm -rf /tmp/test']
      };

      const results = unwrapper.unwrap(segment);

      expect(results).toHaveLength(1);
      expect(results[0].command).toBe('rm');
      expect(results[0].args).toEqual(['-rf', '/tmp/test']);
      expect(results[0].wrappers).toEqual(['csh -c']);
    });

    test('should unwrap tcsh -c', () => {
      const segment: CommandSegment = {
        command: 'tcsh',
        args: ['-c', 'rm -rf /tmp/test']
      };

      const results = unwrapper.unwrap(segment);

      expect(results).toHaveLength(1);
      expect(results[0].command).toBe('rm');
      expect(results[0].args).toEqual(['-rf', '/tmp/test']);
      expect(results[0].wrappers).toEqual(['tcsh -c']);
    });
  });

  describe('xargs handling', () => {
    test('should identify xargs rm as dynamic', () => {
      const segment: CommandSegment = {
        command: 'xargs',
        args: ['rm', '-rf']
      };

      const results = unwrapper.unwrap(segment);

      expect(results).toHaveLength(1);
      expect(results[0].command).toBe('rm');
      expect(results[0].args).toEqual(['-rf']);
      expect(results[0].hasDynamicArgs).toBe(true);
      expect(results[0].dynamicReason).toContain('stdin');
      expect(results[0].wrappers).toEqual(['xargs']);
    });

    test('should handle xargs with flags', () => {
      const segment: CommandSegment = {
        command: 'xargs',
        args: ['-I', '{}', 'rm', '-rf', '{}']
      };

      const results = unwrapper.unwrap(segment);

      expect(results).toHaveLength(1);
      expect(results[0].command).toBe('rm');
      expect(results[0].hasDynamicArgs).toBe(true);
    });

    test('should identify parallel rm as dynamic', () => {
      const segment: CommandSegment = {
        command: 'parallel',
        args: ['rm', '-rf']
      };

      const results = unwrapper.unwrap(segment);

      expect(results).toHaveLength(1);
      expect(results[0].command).toBe('rm');
      expect(results[0].args).toEqual(['-rf']);
      expect(results[0].hasDynamicArgs).toBe(true);
      expect(results[0].dynamicReason).toContain('stdin');
      expect(results[0].wrappers).toEqual(['parallel']);
    });

    test('should handle parallel with flags', () => {
      const segment: CommandSegment = {
        command: 'parallel',
        args: ['-j', '4', 'rm', '-rf', '{}']
      };

      const results = unwrapper.unwrap(segment);

      expect(results).toHaveLength(1);
      expect(results[0].command).toBe('rm');
      expect(results[0].hasDynamicArgs).toBe(true);
      expect(results[0].wrappers).toEqual(['parallel']);
    });
  });

  describe('find -exec handling', () => {
    test('should identify find -exec rm', () => {
      const segment: CommandSegment = {
        command: 'find',
        args: ['/', '-name', '*.tmp', '-exec', 'rm', '-rf', '{}', ';']
      };

      const results = unwrapper.unwrap(segment);

      expect(results).toHaveLength(1);
      expect(results[0].command).toBe('rm');
      expect(results[0].args).toEqual(['-rf']);
      expect(results[0].hasDynamicArgs).toBe(true);
      expect(results[0].dynamicReason).toContain('find -exec');
      expect(results[0].wrappers).toEqual(['find -exec']);
    });

    test('should identify find -execdir rm', () => {
      const segment: CommandSegment = {
        command: 'find',
        args: ['.', '-type', 'f', '-execdir', 'rm', '{}', '+']
      };

      const results = unwrapper.unwrap(segment);

      expect(results).toHaveLength(1);
      expect(results[0].command).toBe('rm');
      expect(results[0].hasDynamicArgs).toBe(true);
      expect(results[0].wrappers).toEqual(['find -execdir']);
    });

    test('should identify find -delete', () => {
      const segment: CommandSegment = {
        command: 'find',
        args: ['/', '-name', '*.log', '-delete']
      };

      const results = unwrapper.unwrap(segment);

      expect(results).toHaveLength(1);
      expect(results[0].command).toBe('find');
      expect(results[0].hasDynamicArgs).toBe(true);
      expect(results[0].dynamicReason).toContain('find -delete');
    });

    test('should handle multiple -exec in find', () => {
      const segment: CommandSegment = {
        command: 'find',
        args: ['.', '-exec', 'chmod', '644', '{}', ';', '-exec', 'rm', '-f', '{}', ';']
      };

      const results = unwrapper.unwrap(segment);

      expect(results.length).toBeGreaterThanOrEqual(2);

      const chmodCmd = results.find(r => r.command === 'chmod');
      expect(chmodCmd).toBeDefined();

      const rmCmd = results.find(r => r.command === 'rm');
      expect(rmCmd).toBeDefined();
      expect(rmCmd?.hasDynamicArgs).toBe(true);
    });
  });

  describe('non-wrapper commands', () => {
    test('should return command as-is when not wrapped', () => {
      const segment: CommandSegment = {
        command: 'rm',
        args: ['-rf', '/tmp/test']
      };

      const results = unwrapper.unwrap(segment);

      expect(results).toHaveLength(1);
      expect(results[0].command).toBe('rm');
      expect(results[0].args).toEqual(['-rf', '/tmp/test']);
      expect(results[0].wrappers).toEqual([]);
      expect(results[0].hasDynamicArgs).toBe(false);
    });

    test('should handle simple commands', () => {
      const segment: CommandSegment = {
        command: 'ls',
        args: ['-la']
      };

      const results = unwrapper.unwrap(segment);

      expect(results).toHaveLength(1);
      expect(results[0].command).toBe('ls');
      expect(results[0].args).toEqual(['-la']);
      expect(results[0].wrappers).toEqual([]);
    });
  });

  describe('complex nested scenarios', () => {
    test('should unwrap sudo env bash -c rm', () => {
      const segment: CommandSegment = {
        command: 'sudo',
        args: ['env', 'PATH=/bin', 'bash', '-c', 'rm -rf /']
      };

      const results = unwrapper.unwrap(segment);

      expect(results).toHaveLength(1);
      expect(results[0].command).toBe('rm');
      expect(results[0].args).toEqual(['-rf', '/']);
      expect(results[0].wrappers).toEqual(['sudo', 'env', 'bash -c']);
    });

    test('should handle nohup sudo rm', () => {
      const segment: CommandSegment = {
        command: 'nohup',
        args: ['sudo', 'rm', '-rf', '/important']
      };

      const results = unwrapper.unwrap(segment);

      expect(results).toHaveLength(1);
      expect(results[0].command).toBe('rm');
      expect(results[0].args).toEqual(['-rf', '/important']);
      expect(results[0].wrappers).toEqual(['nohup', 'sudo']);
    });
  });
});
