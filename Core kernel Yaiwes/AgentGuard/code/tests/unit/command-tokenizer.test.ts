/**
 * Unit tests for CommandTokenizer
 */

import { describe, test, expect } from 'vitest';
import { CommandTokenizer } from '../../src/command-tokenizer';

describe('CommandTokenizer', () => {
  const tokenizer = new CommandTokenizer();

  describe('Basic tokenization', () => {
    test('splits simple command on spaces', () => {
      const result = tokenizer.tokenize('rm -rf file.txt');
      
      expect(result.tokens).toHaveLength(3);
      expect(result.tokens[0].type).toBe('command');
      expect(result.tokens[0].value).toBe('rm');
      expect(result.tokens[1].type).toBe('argument');
      expect(result.tokens[1].value).toBe('-rf');
      expect(result.tokens[2].type).toBe('argument');
      expect(result.tokens[2].value).toBe('file.txt');
    });

    test('preserves single-quoted strings as single tokens', () => {
      const result = tokenizer.tokenize("echo 'hello world'");
      
      expect(result.tokens).toHaveLength(2);
      expect(result.tokens[0].value).toBe('echo');
      expect(result.tokens[1].value).toBe('hello world');
    });

    test('preserves double-quoted strings as single tokens', () => {
      const result = tokenizer.tokenize('echo "hello world"');
      
      expect(result.tokens).toHaveLength(2);
      expect(result.tokens[0].value).toBe('echo');
      expect(result.tokens[1].value).toBe('hello world');
    });

    test('handles mixed quotes', () => {
      const result = tokenizer.tokenize(`echo "double" 'single' unquoted`);
      
      expect(result.tokens).toHaveLength(4);
      expect(result.tokens[1].value).toBe('double');
      expect(result.tokens[2].value).toBe('single');
      expect(result.tokens[3].value).toBe('unquoted');
    });
  });

  describe('Variable expansion', () => {
    test('expands $VAR format', () => {
      process.env.TEST_VAR = 'test_value';
      const result = tokenizer.tokenize('echo $TEST_VAR');
      
      expect(result.tokens[1].value).toBe('test_value');
      delete process.env.TEST_VAR;
    });

    test('expands ${VAR} format', () => {
      process.env.TEST_VAR = 'test_value';
      const result = tokenizer.tokenize('echo ${TEST_VAR}');
      
      expect(result.tokens[1].value).toBe('test_value');
      delete process.env.TEST_VAR;
    });

    test('leaves undefined variables as-is', () => {
      const result = tokenizer.tokenize('echo $UNDEFINED_VAR');
      
      expect(result.tokens[1].value).toBe('$UNDEFINED_VAR');
    });

    test('expands variables in double quotes', () => {
      process.env.TEST_VAR = 'test_value';
      const result = tokenizer.tokenize('echo "$TEST_VAR"');
      
      expect(result.tokens[1].value).toBe('test_value');
      delete process.env.TEST_VAR;
    });
  });

  describe('Path expansion', () => {
    test('expands tilde to home directory', () => {
      const result = tokenizer.tokenize('ls ~/documents');
      
      expect(result.tokens[1].value).toContain(process.env.HOME || '/');
      expect(result.tokens[1].value).not.toContain('~');
    });

    test('expands standalone tilde', () => {
      const result = tokenizer.tokenize('cd ~');
      
      expect(result.tokens[1].value).toBe(process.env.HOME || '/');
    });

    test('resolves relative paths to absolute', () => {
      const result = tokenizer.tokenize('cat ./file.txt');
      
      expect(result.tokens[1].value).toMatch(/^[/\\]/); // Starts with / or \
    });

    test('resolves parent directory paths', () => {
      const result = tokenizer.tokenize('cat ../file.txt');
      
      expect(result.tokens[1].value).toMatch(/^[/\\]/); // Starts with / or \
    });
  });

  describe('Escape sequence handling', () => {
    test('handles escaped backslash', () => {
      const result = tokenizer.tokenize('echo \\\\');
      
      expect(result.tokens[1].value).toBe('\\');
    });

    test('handles escaped double quote', () => {
      // \\"hello\\" becomes "hello" after escape processing, then quotes are removed
      const result = tokenizer.tokenize('echo \\"hello\\"');
      
      // After escape processing: echo "hello"
      // After quote removal: hello
      expect(result.tokens[1].value).toBe('hello');
    });

    test('handles escaped single quote', () => {
      // \\'hello\\' becomes 'hello' after escape processing, then quotes are removed
      const result = tokenizer.tokenize("echo \\'hello\\'");
      
      // After escape processing: echo 'hello'
      // After quote removal: hello
      expect(result.tokens[1].value).toBe('hello');
    });

    test('handles escaped space', () => {
      // hello\ world becomes hello world after escape processing (single token)
      const result = tokenizer.tokenize('echo hello\\ world');
      
      // After escape processing, the space is preserved and treated as part of the token
      expect(result.tokens[1].value).toBe('hello world');
    });
  });

  describe('Command segments', () => {
    test('identifies simple command segment', () => {
      const result = tokenizer.tokenize('rm file.txt');
      
      expect(result.segments).toHaveLength(1);
      expect(result.segments[0].command).toBe('rm');
      expect(result.segments[0].args).toEqual(['file.txt']);
    });

    test('splits chained commands with &&', () => {
      const result = tokenizer.tokenize('echo hello && echo world');
      
      expect(result.segments).toHaveLength(2);
      expect(result.segments[0].command).toBe('echo');
      expect(result.segments[0].args).toEqual(['hello']);
      expect(result.segments[0].operator).toBe('&&');
      expect(result.segments[1].command).toBe('echo');
      expect(result.segments[1].args).toEqual(['world']);
      expect(result.segments[1].operator).toBeUndefined();
    });

    test('splits chained commands with ||', () => {
      const result = tokenizer.tokenize('command1 || command2');
      
      expect(result.segments).toHaveLength(2);
      expect(result.segments[0].command).toBe('command1');
      expect(result.segments[0].operator).toBe('||');
      expect(result.segments[1].command).toBe('command2');
      expect(result.segments[1].operator).toBeUndefined();
    });

    test('splits chained commands with ;', () => {
      const result = tokenizer.tokenize('ls;pwd;echo done');
      
      expect(result.segments).toHaveLength(3);
      expect(result.segments[0].command).toBe('ls');
      expect(result.segments[0].operator).toBe(';');
      expect(result.segments[1].command).toBe('pwd');
      expect(result.segments[1].operator).toBe(';');
      expect(result.segments[2].command).toBe('echo');
      expect(result.segments[2].args).toEqual(['done']);
      expect(result.segments[2].operator).toBeUndefined();
    });

    test('handles mixed chain operators', () => {
      const result = tokenizer.tokenize('make && make test || echo failed');
      
      expect(result.segments).toHaveLength(3);
      expect(result.segments[0].command).toBe('make');
      expect(result.segments[0].operator).toBe('&&');
      expect(result.segments[1].command).toBe('make');
      expect(result.segments[1].args).toEqual(['test']);
      expect(result.segments[1].operator).toBe('||');
      expect(result.segments[2].command).toBe('echo');
      expect(result.segments[2].args).toEqual(['failed']);
    });

    test('handles chain operators with complex arguments', () => {
      const result = tokenizer.tokenize('rm -rf /tmp/test && echo "cleanup done"');
      
      expect(result.segments).toHaveLength(2);
      expect(result.segments[0].command).toBe('rm');
      expect(result.segments[0].args).toEqual(['-rf', expect.stringContaining('/tmp/test')]);
      expect(result.segments[0].operator).toBe('&&');
      expect(result.segments[1].command).toBe('echo');
      expect(result.segments[1].args).toEqual(['cleanup done']);
    });

    test('identifies piped commands', () => {
      const result = tokenizer.tokenize('cat file.txt | grep test');
      
      expect(result.isPiped).toBe(true);
      expect(result.segments).toHaveLength(2);
      expect(result.segments[0].command).toBe('cat');
      expect(result.segments[0].operator).toBe('|');
      expect(result.segments[1].command).toBe('grep');
    });

    test('identifies chained commands', () => {
      const result = tokenizer.tokenize('make && make test');
      
      expect(result.isChained).toBe(true);
    });

    test('distinguishes between | and ||', () => {
      const pipeResult = tokenizer.tokenize('cat file | grep test');
      const orResult = tokenizer.tokenize('command1 || command2');
      
      expect(pipeResult.segments[0].operator).toBe('|');
      expect(pipeResult.isPiped).toBe(true);
      expect(pipeResult.isChained).toBe(false);
      
      expect(orResult.segments[0].operator).toBe('||');
      expect(orResult.isChained).toBe(true);
      expect(orResult.isPiped).toBe(false);
    });
  });

  describe('Normalized output', () => {
    test('creates normalized command string', () => {
      process.env.TEST_VAR = 'value';
      const result = tokenizer.tokenize('echo $TEST_VAR');
      
      expect(result.normalized).toBe('echo value');
      delete process.env.TEST_VAR;
    });

    test('preserves original command', () => {
      const original = 'echo $HOME';
      const result = tokenizer.tokenize(original);
      
      expect(result.original).toBe(original);
    });
  });
});
