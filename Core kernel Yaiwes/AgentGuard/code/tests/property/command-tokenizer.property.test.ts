/**
 * Property-Based Tests for Command Tokenizer
 * 
 * **Feature: agentguard, Property 14: Quoted string preservation**
 * **Validates: Requirements 6.1**
 */

import { describe, test, expect } from 'vitest';
import * as fc from 'fast-check';
import { CommandTokenizer } from '../../src/command-tokenizer';

describe('Property 14: Quoted string preservation', () => {
  /**
   * Property: For any command containing quoted strings (single or double quotes),
   * tokenization should preserve the quoted content as single tokens without splitting
   * on internal spaces.
   */
  test('**Feature: agentguard, Property 14: Quoted string preservation**', () => {
    const tokenizer = new CommandTokenizer();

    // Generator for strings that contain spaces (the key thing we're testing)
    // Exclude backslashes to avoid escape sequence complications
    // Exclude $ to avoid variable expansion
    // Exclude ./ and ../ to avoid path expansion
    // Exclude ~ to avoid home directory expansion
    const stringWithSpacesGenerator = fc.string({ minLength: 3, maxLength: 50 })
      .filter(s => s.includes(' ') && !s.includes('\n') && !s.includes('"') && !s.includes("'") &&
                   !s.includes('\\') && !s.includes('$') && !s.startsWith('./') &&
                   !s.startsWith('../') && !s.startsWith('~'));

    // Generator for command names (no spaces, no quotes, no special shell characters)
    // Exclude: spaces, quotes, backslash, operators, special chars that trigger expansion
    const commandGenerator = fc.string({ minLength: 1, maxLength: 20 })
      .filter(s => !s.includes(' ') && !s.includes('\n') && !s.includes('"') && !s.includes("'") &&
                   !s.includes('\\') && !s.includes(';') && !s.includes('|') &&
                   !s.includes('&') && !s.includes('#') && !s.includes('>') &&
                   !s.includes('~') && !s.includes('$') && !s.includes('(') && !s.includes(')') &&
                   !s.startsWith('./') && !s.startsWith('../') && !s.startsWith('.') &&
                   s.trim().length > 0);

    // Generator for quote type
    const quoteTypeGenerator = fc.constantFrom('"', "'");

    // Generator for a command with a single quoted argument
    const singleQuotedArgGenerator = fc.tuple(
      commandGenerator,
      stringWithSpacesGenerator,
      quoteTypeGenerator
    ).map(([cmd, content, quote]) => ({
      command: `${cmd} ${quote}${content}${quote}`,
      expectedCommand: cmd,
      expectedArgContent: content,
      quoteType: quote
    }));

    fc.assert(
      fc.property(singleQuotedArgGenerator, (testData) => {
        const result = tokenizer.tokenize(testData.command);

        // Should have exactly 2 tokens: command and quoted argument
        expect(result.tokens).toHaveLength(2);

        // First token should be the command
        expect(result.tokens[0].type).toBe('command');
        expect(result.tokens[0].value).toBe(testData.expectedCommand);

        // Second token should be the argument with quotes removed but content preserved
        expect(result.tokens[1].type).toBe('argument');
        expect(result.tokens[1].value).toBe(testData.expectedArgContent);

        // The argument should be a single token (not split on spaces)
        // This is the key property: spaces inside quotes don't cause tokenization
        const spaceCount = testData.expectedArgContent.split(' ').length - 1;
        expect(spaceCount).toBeGreaterThan(0); // Ensure we actually tested spaces
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Multiple quoted arguments should each be preserved as single tokens
   */
  test('multiple quoted arguments are each preserved as single tokens', () => {
    const tokenizer = new CommandTokenizer();

    const stringWithSpacesGenerator = fc.string({ minLength: 3, maxLength: 30 })
      .filter(s => s.includes(' ') && !s.includes('\n') && !s.includes('"') && !s.includes("'") &&
                   !s.includes('\\') && !s.includes('$') && !s.startsWith('./') &&
                   !s.startsWith('../') && !s.startsWith('~'));

    const commandGenerator = fc.string({ minLength: 1, maxLength: 20 })
      .filter(s => !s.includes(' ') && !s.includes('\n') && !s.includes('"') && !s.includes("'") &&
                   !s.includes('\\') && !s.includes(';') && !s.includes('|') &&
                   !s.includes('&') && !s.includes('#') && !s.includes('>') &&
                   !s.includes('~') && !s.includes('$') && !s.includes('(') && !s.includes(')') &&
                   !s.startsWith('./') && !s.startsWith('../') && !s.startsWith('.') &&
                   s.trim().length > 0);

    const quoteTypeGenerator = fc.constantFrom('"', "'");

    const multipleQuotedArgsGenerator = fc.tuple(
      commandGenerator,
      fc.array(
        fc.tuple(stringWithSpacesGenerator, quoteTypeGenerator),
        { minLength: 2, maxLength: 5 }
      )
    ).map(([cmd, args]) => ({
      command: `${cmd} ${args.map(([content, quote]) => `${quote}${content}${quote}`).join(' ')}`,
      expectedCommand: cmd,
      expectedArgs: args.map(([content]) => content)
    }));

    fc.assert(
      fc.property(multipleQuotedArgsGenerator, (testData) => {
        const result = tokenizer.tokenize(testData.command);

        // Should have 1 command + N arguments
        expect(result.tokens).toHaveLength(1 + testData.expectedArgs.length);

        // First token should be the command
        expect(result.tokens[0].type).toBe('command');
        expect(result.tokens[0].value).toBe(testData.expectedCommand);

        // Each subsequent token should be an argument with preserved content
        for (let i = 0; i < testData.expectedArgs.length; i++) {
          expect(result.tokens[i + 1].type).toBe('argument');
          expect(result.tokens[i + 1].value).toBe(testData.expectedArgs[i]);
        }
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Mixed quoted and unquoted arguments should be tokenized correctly
   */
  test('mixed quoted and unquoted arguments are tokenized correctly', () => {
    const tokenizer = new CommandTokenizer();

    const quotedStringGenerator = fc.string({ minLength: 3, maxLength: 30 })
      .filter(s => s.includes(' ') && !s.includes('\n') && !s.includes('"') && !s.includes("'") &&
                   !s.includes('\\') && !s.includes('$') && !s.startsWith('./') &&
                   !s.startsWith('../') && !s.startsWith('~'));

    const unquotedStringGenerator = fc.string({ minLength: 1, maxLength: 20 })
      .filter(s => !s.includes(' ') && !s.includes('\n') && !s.includes('"') && !s.includes("'") && 
                   !s.includes('\\') && !s.includes(';') && !s.includes('|') && 
                   !s.includes('&') && !s.includes('#') && !s.includes('>') && 
                   !s.includes('~') && !s.includes('$') && !s.includes('(') && !s.includes(')') &&
                   !s.includes('.') && s.trim().length > 0);

    const commandGenerator = fc.string({ minLength: 1, maxLength: 20 })
      .filter(s => !s.includes(' ') && !s.includes('\n') && !s.includes('"') && !s.includes("'") &&
                   !s.includes('\\') && !s.includes(';') && !s.includes('|') &&
                   !s.includes('&') && !s.includes('#') && !s.includes('>') &&
                   !s.includes('~') && !s.includes('$') && !s.includes('(') && !s.includes(')') &&
                   !s.startsWith('./') && !s.startsWith('../') && !s.startsWith('.') &&
                   s.trim().length > 0);

    const quoteTypeGenerator = fc.constantFrom('"', "'");

    const mixedArgsGenerator = fc.tuple(
      commandGenerator,
      unquotedStringGenerator,
      quotedStringGenerator,
      quoteTypeGenerator,
      unquotedStringGenerator
    ).map(([cmd, unquoted1, quoted, quote, unquoted2]) => ({
      command: `${cmd} ${unquoted1} ${quote}${quoted}${quote} ${unquoted2}`,
      expectedCommand: cmd,
      expectedArgs: [unquoted1, quoted, unquoted2]
    }));

    fc.assert(
      fc.property(mixedArgsGenerator, (testData) => {
        const result = tokenizer.tokenize(testData.command);

        // Should have 1 command + 3 arguments
        expect(result.tokens).toHaveLength(4);

        // First token should be the command
        expect(result.tokens[0].type).toBe('command');
        expect(result.tokens[0].value).toBe(testData.expectedCommand);

        // Arguments should match expected values
        expect(result.tokens[1].type).toBe('argument');
        expect(result.tokens[1].value).toBe(testData.expectedArgs[0]);

        expect(result.tokens[2].type).toBe('argument');
        expect(result.tokens[2].value).toBe(testData.expectedArgs[1]);

        expect(result.tokens[3].type).toBe('argument');
        expect(result.tokens[3].value).toBe(testData.expectedArgs[2]);
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Single quotes and double quotes should both preserve content
   */
  test('both single and double quotes preserve content identically', () => {
    const tokenizer = new CommandTokenizer();

    const stringWithSpacesGenerator = fc.string({ minLength: 3, maxLength: 50 })
      .filter(s => s.includes(' ') && !s.includes('\n') && !s.includes('"') && !s.includes("'") && 
                   !s.includes('\\') && !s.includes('$'));

    const commandGenerator = fc.string({ minLength: 1, maxLength: 20 })
      .filter(s => !s.includes(' ') && !s.includes('\n') && !s.includes('"') && !s.includes("'") &&
                   !s.includes('\\') && !s.includes(';') && !s.includes('|') &&
                   !s.includes('&') && !s.includes('#') && !s.includes('>') &&
                   !s.includes('~') && !s.includes('$') && !s.includes('(') && !s.includes(')') &&
                   !s.startsWith('./') && !s.startsWith('../') && !s.startsWith('.') &&
                   s.trim().length > 0);

    fc.assert(
      fc.property(commandGenerator, stringWithSpacesGenerator, (cmd, content) => {
        // Test with single quotes
        const singleQuotedCommand = `${cmd} '${content}'`;
        const singleQuotedResult = tokenizer.tokenize(singleQuotedCommand);

        // Test with double quotes
        const doubleQuotedCommand = `${cmd} "${content}"`;
        const doubleQuotedResult = tokenizer.tokenize(doubleQuotedCommand);

        // Both should produce the same token structure
        expect(singleQuotedResult.tokens).toHaveLength(2);
        expect(doubleQuotedResult.tokens).toHaveLength(2);

        // Both should preserve the content identically
        expect(singleQuotedResult.tokens[1].value).toBe(content);
        expect(doubleQuotedResult.tokens[1].value).toBe(content);

        // Both should have the same token types
        expect(singleQuotedResult.tokens[0].type).toBe('command');
        expect(doubleQuotedResult.tokens[0].type).toBe('command');
        expect(singleQuotedResult.tokens[1].type).toBe('argument');
        expect(doubleQuotedResult.tokens[1].type).toBe('argument');
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Empty quoted strings should be preserved as empty tokens
   */
  test('empty quoted strings are preserved as empty argument tokens', () => {
    const tokenizer = new CommandTokenizer();

    const commandGenerator = fc.string({ minLength: 1, maxLength: 20 })
      .filter(s => !s.includes(' ') && !s.includes('\n') && !s.includes('"') && !s.includes("'") &&
                   !s.includes('\\') && !s.includes(';') && !s.includes('|') &&
                   !s.includes('&') && !s.includes('#') && !s.includes('>') &&
                   !s.includes('~') && !s.includes('$') && !s.includes('(') && !s.includes(')') &&
                   !s.startsWith('./') && !s.startsWith('../') && !s.startsWith('.') &&
                   s.trim().length > 0);

    const quoteTypeGenerator = fc.constantFrom('"', "'");

    fc.assert(
      fc.property(commandGenerator, quoteTypeGenerator, (cmd, quote) => {
        const command = `${cmd} ${quote}${quote}`;
        const result = tokenizer.tokenize(command);

        // Should have 2 tokens: command and empty argument
        expect(result.tokens).toHaveLength(2);

        // First token should be the command
        expect(result.tokens[0].type).toBe('command');
        expect(result.tokens[0].value).toBe(cmd);

        // Second token should be an empty argument
        expect(result.tokens[1].type).toBe('argument');
        expect(result.tokens[1].value).toBe('');
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Consecutive quoted strings should each be preserved
   */
  test('consecutive quoted strings are each preserved as separate tokens', () => {
    const tokenizer = new CommandTokenizer();

    const commandGenerator = fc.string({ minLength: 1, maxLength: 20 })
      .filter(s => !s.includes(' ') && !s.includes('\n') && !s.includes('"') && !s.includes("'") &&
                   !s.includes('\\') && !s.includes(';') && !s.includes('|') &&
                   !s.includes('&') && !s.includes('#') && !s.includes('>') &&
                   !s.includes('~') && !s.includes('$') && !s.includes('(') && !s.includes(')') &&
                   !s.startsWith('./') && !s.startsWith('../') && !s.startsWith('.') &&
                   s.trim().length > 0);

    const stringWithSpacesGenerator = fc.string({ minLength: 3, maxLength: 30 })
      .filter(s => s.includes(' ') && !s.includes('\n') && !s.includes('"') && !s.includes("'") &&
                   !s.includes('\\') && !s.includes('$') && !s.startsWith('./') &&
                   !s.startsWith('../') && !s.startsWith('~'));

    const quoteTypeGenerator = fc.constantFrom('"', "'");

    fc.assert(
      fc.property(
        commandGenerator,
        stringWithSpacesGenerator,
        stringWithSpacesGenerator,
        quoteTypeGenerator,
        (cmd, content1, content2, quote) => {
          // Test consecutive quoted strings: "content1" "content2"
          const command = `${cmd} ${quote}${content1}${quote} ${quote}${content2}${quote}`;
          const result = tokenizer.tokenize(command);

          // Should have 1 command + 2 arguments
          expect(result.tokens).toHaveLength(3);

          expect(result.tokens[0].type).toBe('command');
          expect(result.tokens[0].value).toBe(cmd);

          expect(result.tokens[1].type).toBe('argument');
          expect(result.tokens[1].value).toBe(content1);

          expect(result.tokens[2].type).toBe('argument');
          expect(result.tokens[2].value).toBe(content2);
        }
      ),
      { numRuns: 100 }
    );
  });
});
