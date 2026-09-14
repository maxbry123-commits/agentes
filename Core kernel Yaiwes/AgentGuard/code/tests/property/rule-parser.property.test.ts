/**
 * Property-Based Tests for Rule Parser
 * 
 * **Feature: agentguard, Property 5: Rule prefix parsing**
 * **Validates: Requirements 2.1**
 */

import { describe, test, expect } from 'vitest';
import * as fc from 'fast-check';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { RuleParser } from '../../src/rule-parser';
import { RuleType, RuleSource } from '../../src/types';

describe('Property 5: Rule prefix parsing', () => {
  /**
   * Property: For any valid rule file containing lines with prefixes `!`, `?`, `+`, 
   * `@protect`, or `@sandbox`, parsing should correctly identify the rule type for each line.
   */
  test('**Feature: agentguard, Property 5: Rule prefix parsing**', () => {
    // Generator for valid patterns (non-empty strings without newlines)
    const patternGenerator = fc.string({ minLength: 1, maxLength: 100 })
      .filter(s => !s.includes('\n') && s.trim().length > 0);

    // Generator for rule prefixes and their expected types
    const ruleGenerator = fc.oneof(
      fc.constant({ prefix: '!', type: RuleType.BLOCK }),
      fc.constant({ prefix: '?', type: RuleType.CONFIRM }),
      fc.constant({ prefix: '+', type: RuleType.ALLOW }),
      fc.constant({ prefix: '@protect ', type: RuleType.PROTECT }),
      fc.constant({ prefix: '@sandbox ', type: RuleType.SANDBOX })
    );

    // Generator for a single rule line
    const ruleLineGenerator = fc.tuple(ruleGenerator, patternGenerator)
      .map(([rule, pattern]) => ({
        line: `${rule.prefix}${pattern}`,
        expectedType: rule.type,
        expectedPattern: pattern
      }));

    // Generator for multiple rule lines
    const rulesGenerator = fc.array(ruleLineGenerator, { minLength: 1, maxLength: 20 });

    fc.assert(
      fc.property(rulesGenerator, (ruleData) => {
        // Create a temporary file with the generated rules
        const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'agentguard-test-'));
        const tempFile = path.join(tempDir, 'test-rules');

        try {
          // Write rules to file
          const fileContent = ruleData.map(r => r.line).join('\n');
          fs.writeFileSync(tempFile, fileContent, 'utf-8');

          // Parse the file
          const parser = new RuleParser();
          const result = parser.parse(tempFile, RuleSource.PROJECT);

          // Verify no errors occurred
          expect(result.errors).toHaveLength(0);

          // Verify correct number of rules parsed
          expect(result.rules).toHaveLength(ruleData.length);

          // Verify each rule has the correct type and pattern
          for (let i = 0; i < ruleData.length; i++) {
            const expectedData = ruleData[i];
            const actualRule = result.rules[i];

            // Check rule type
            expect(actualRule.type).toBe(expectedData.expectedType);

            // Check pattern (trimmed)
            expect(actualRule.pattern).toBe(expectedData.expectedPattern.trim());

            // Check source
            expect(actualRule.source).toBe(RuleSource.PROJECT);

            // Check line number
            expect(actualRule.lineNumber).toBe(i + 1);

            // Check specificity is calculated (should be > 0 for non-empty patterns)
            expect(actualRule.specificity).toBeGreaterThanOrEqual(0);

            // For @protect and @sandbox, check metadata
            if (actualRule.type === RuleType.PROTECT || actualRule.type === RuleType.SANDBOX) {
              expect(actualRule.metadata).toBeDefined();
              expect(actualRule.metadata?.path).toBe(expectedData.expectedPattern.trim());
            }
          }
        } finally {
          // Clean up temp file and directory
          try {
            fs.unlinkSync(tempFile);
            fs.rmdirSync(tempDir);
          } catch (e) {
            // Ignore cleanup errors
          }
        }
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Parsing should handle mixed rule types in a single file
   */
  test('parsing handles mixed rule types correctly', () => {
    const patternGenerator = fc.string({ minLength: 1, maxLength: 50 })
      .filter(s => !s.includes('\n') && s.trim().length > 0);

    const mixedRulesGenerator = fc.tuple(
      patternGenerator, // BLOCK pattern
      patternGenerator, // CONFIRM pattern
      patternGenerator, // ALLOW pattern
      patternGenerator, // PROTECT path
      patternGenerator  // SANDBOX path
    );

    fc.assert(
      fc.property(mixedRulesGenerator, ([blockPat, confirmPat, allowPat, protectPath, sandboxPath]) => {
        const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'agentguard-test-'));
        const tempFile = path.join(tempDir, 'test-rules');

        try {
          const fileContent = [
            `!${blockPat}`,
            `?${confirmPat}`,
            `+${allowPat}`,
            `@protect ${protectPath}`,
            `@sandbox ${sandboxPath}`
          ].join('\n');

          fs.writeFileSync(tempFile, fileContent, 'utf-8');

          const parser = new RuleParser();
          const result = parser.parse(tempFile, RuleSource.PROJECT);

          expect(result.errors).toHaveLength(0);
          expect(result.rules).toHaveLength(5);

          expect(result.rules[0].type).toBe(RuleType.BLOCK);
          expect(result.rules[1].type).toBe(RuleType.CONFIRM);
          expect(result.rules[2].type).toBe(RuleType.ALLOW);
          expect(result.rules[3].type).toBe(RuleType.PROTECT);
          expect(result.rules[4].type).toBe(RuleType.SANDBOX);
        } finally {
          try {
            fs.unlinkSync(tempFile);
            fs.rmdirSync(tempDir);
          } catch (e) {
            // Ignore cleanup errors
          }
        }
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Parsing should preserve pattern content exactly (after trimming)
   */
  test('parsing preserves pattern content', () => {
    // Generator for patterns with various characters
    const complexPatternGenerator = fc.string({ 
      minLength: 1, 
      maxLength: 100 
    }).filter(s => !s.includes('\n') && s.trim().length > 0);

    fc.assert(
      fc.property(complexPatternGenerator, (pattern) => {
        const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'agentguard-test-'));
        const tempFile = path.join(tempDir, 'test-rules');

        try {
          // Test with BLOCK rule
          fs.writeFileSync(tempFile, `!${pattern}`, 'utf-8');

          const parser = new RuleParser();
          const result = parser.parse(tempFile, RuleSource.PROJECT);

          expect(result.errors).toHaveLength(0);
          expect(result.rules).toHaveLength(1);
          expect(result.rules[0].pattern).toBe(pattern.trim());
        } finally {
          try {
            fs.unlinkSync(tempFile);
            fs.rmdirSync(tempDir);
          } catch (e) {
            // Ignore cleanup errors
          }
        }
      }),
      { numRuns: 100 }
    );
  });
});

/**
 * Property-Based Tests for Parse Error Recovery
 * 
 * **Feature: agentguard, Property 7: Parse error recovery**
 * **Validates: Requirements 2.4**
 */
describe('Property 7: Parse error recovery', () => {
  /**
   * Property: For any rule file containing invalid syntax on some lines,
   * parsing should report errors with line numbers for invalid lines and
   * successfully parse all valid lines.
   */
  test('**Feature: agentguard, Property 7: Parse error recovery**', () => {
    // Generator for valid patterns (non-empty strings without newlines)
    const patternGenerator = fc.string({ minLength: 1, maxLength: 100 })
      .filter(s => !s.includes('\n') && s.trim().length > 0);

    // Generator for valid rule lines
    const validRuleGenerator = fc.oneof(
      patternGenerator.map(p => ({ line: `!${p}`, type: RuleType.BLOCK, pattern: p })),
      patternGenerator.map(p => ({ line: `?${p}`, type: RuleType.CONFIRM, pattern: p })),
      patternGenerator.map(p => ({ line: `+${p}`, type: RuleType.ALLOW, pattern: p })),
      patternGenerator.map(p => ({ line: `@protect ${p}`, type: RuleType.PROTECT, pattern: p })),
      patternGenerator.map(p => ({ line: `@sandbox ${p}`, type: RuleType.SANDBOX, pattern: p }))
    );

    // Generator for invalid rule lines (various types of invalid syntax)
    const invalidRuleGenerator = fc.oneof(
      // Missing pattern after prefix
      fc.constant('!'),
      fc.constant('?'),
      fc.constant('+'),
      fc.constant('@protect'),
      fc.constant('@sandbox'),
      // Only whitespace after prefix
      fc.constant('!   '),
      fc.constant('?   '),
      fc.constant('+   '),
      fc.constant('@protect   '),
      fc.constant('@sandbox   '),
      // Invalid prefix
      fc.string({ minLength: 1, maxLength: 50 })
        .filter(s => !s.includes('\n') && s.trim().length > 0 &&
                     !s.startsWith('!') && !s.startsWith('?') &&
                     !s.startsWith('+') && !s.startsWith('@protect') &&
                     !s.startsWith('@sandbox') && !s.startsWith('#') &&
                     !s.trim().startsWith('#'))
        .map(s => s),
      // Invalid directive
      fc.constant('@invalid directive'),
      fc.constant('@unknown path')
    );

    // Generator for a mix of valid and invalid lines
    const mixedLinesGenerator = fc.array(
      fc.oneof(
        validRuleGenerator.map(r => ({ ...r, isValid: true })),
        invalidRuleGenerator.map(line => ({ line, isValid: false }))
      ),
      { minLength: 2, maxLength: 20 }
    ).filter(lines => {
      // Ensure we have at least one valid and one invalid line
      const hasValid = lines.some(l => l.isValid);
      const hasInvalid = lines.some(l => !l.isValid);
      return hasValid && hasInvalid;
    });

    fc.assert(
      fc.property(mixedLinesGenerator, (lineData) => {
        const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'agentguard-test-'));
        const tempFile = path.join(tempDir, 'test-rules');

        try {
          // Create file with mixed valid and invalid lines
          const fileContent = lineData.map(l => l.line).join('\n');
          fs.writeFileSync(tempFile, fileContent, 'utf-8');

          // Parse the file
          const parser = new RuleParser();
          const result = parser.parse(tempFile, RuleSource.PROJECT);

          // Count expected valid and invalid lines
          const expectedValidCount = lineData.filter(l => l.isValid).length;
          const expectedInvalidCount = lineData.filter(l => !l.isValid).length;

          // Verify that we got the expected number of valid rules
          expect(result.rules).toHaveLength(expectedValidCount);

          // Verify that we got errors for invalid lines
          expect(result.errors.length).toBeGreaterThan(0);
          expect(result.errors.length).toBeLessThanOrEqual(expectedInvalidCount);

          // Verify each error has a line number
          for (const error of result.errors) {
            expect(error.line).toBeGreaterThan(0);
            expect(error.line).toBeLessThanOrEqual(lineData.length);
            expect(error.message).toBeTruthy();
            expect(error.source).toBe(RuleSource.PROJECT);
          }

          // Verify that valid rules were parsed correctly
          const validLines = lineData.filter(l => l.isValid);
          for (let i = 0; i < result.rules.length; i++) {
            const rule = result.rules[i];
            const expectedData = validLines[i];

            expect(rule.type).toBe(expectedData.type);
            expect(rule.pattern).toBe(expectedData.pattern.trim());
            expect(rule.source).toBe(RuleSource.PROJECT);
          }

          // Verify that errors correspond to invalid lines
          for (const error of result.errors) {
            const lineIndex = error.line - 1;
            const lineData_at_error = lineData[lineIndex];
            expect(lineData_at_error.isValid).toBe(false);
          }
        } finally {
          // Clean up temp file and directory
          try {
            fs.unlinkSync(tempFile);
            fs.rmdirSync(tempDir);
          } catch (e) {
            // Ignore cleanup errors
          }
        }
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Parser continues after encountering errors
   */
  test('parser continues parsing after errors', () => {
    const patternGenerator = fc.string({ minLength: 1, maxLength: 50 })
      .filter(s => !s.includes('\n') && s.trim().length > 0);

    fc.assert(
      fc.property(
        patternGenerator,
        patternGenerator,
        patternGenerator,
        (pattern1, pattern2, pattern3) => {
          const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'agentguard-test-'));
          const tempFile = path.join(tempDir, 'test-rules');

          try {
            // Create file with valid-invalid-valid-invalid-valid pattern
            const fileContent = [
              `!${pattern1}`,      // valid (line 1)
              'invalid line',      // invalid (line 2)
              `?${pattern2}`,      // valid (line 3)
              '@unknown',          // invalid (line 4)
              `+${pattern3}`       // valid (line 5)
            ].join('\n');

            fs.writeFileSync(tempFile, fileContent, 'utf-8');

            const parser = new RuleParser();
            const result = parser.parse(tempFile, RuleSource.PROJECT);

            // Should have parsed 3 valid rules
            expect(result.rules).toHaveLength(3);
            expect(result.rules[0].type).toBe(RuleType.BLOCK);
            expect(result.rules[0].pattern).toBe(pattern1.trim());
            expect(result.rules[1].type).toBe(RuleType.CONFIRM);
            expect(result.rules[1].pattern).toBe(pattern2.trim());
            expect(result.rules[2].type).toBe(RuleType.ALLOW);
            expect(result.rules[2].pattern).toBe(pattern3.trim());

            // Should have 2 errors
            expect(result.errors.length).toBeGreaterThanOrEqual(2);

            // Errors should be for lines 2 and 4
            const errorLines = result.errors.map(e => e.line).sort();
            expect(errorLines).toContain(2);
            expect(errorLines).toContain(4);
          } finally {
            try {
              fs.unlinkSync(tempFile);
              fs.rmdirSync(tempDir);
            } catch (e) {
              // Ignore cleanup errors
            }
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Error messages include line numbers
   */
  test('errors include line numbers', () => {
    const invalidLineGenerator = fc.oneof(
      fc.constant('!'),
      fc.constant('invalid syntax'),
      fc.constant('@unknown directive')
    );

    fc.assert(
      fc.property(
        fc.array(invalidLineGenerator, { minLength: 1, maxLength: 10 }),
        (invalidLines) => {
          const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'agentguard-test-'));
          const tempFile = path.join(tempDir, 'test-rules');

          try {
            const fileContent = invalidLines.join('\n');
            fs.writeFileSync(tempFile, fileContent, 'utf-8');

            const parser = new RuleParser();
            const result = parser.parse(tempFile, RuleSource.PROJECT);

            // Should have no valid rules
            expect(result.rules).toHaveLength(0);

            // Should have errors for all invalid lines
            expect(result.errors.length).toBeGreaterThan(0);

            // Each error should have a valid line number
            for (const error of result.errors) {
              expect(error.line).toBeGreaterThan(0);
              expect(error.line).toBeLessThanOrEqual(invalidLines.length);
              expect(error.message).toBeTruthy();
              expect(typeof error.message).toBe('string');
            }
          } finally {
            try {
              fs.unlinkSync(tempFile);
              fs.rmdirSync(tempDir);
            } catch (e) {
              // Ignore cleanup errors
            }
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Valid rules are not affected by errors in other lines
   */
  test('valid rules unaffected by errors in other lines', () => {
    const patternGenerator = fc.string({ minLength: 1, maxLength: 50 })
      .filter(s => !s.includes('\n') && s.trim().length > 0);

    fc.assert(
      fc.property(
        fc.array(patternGenerator, { minLength: 1, maxLength: 10 }),
        fc.array(fc.constant('invalid'), { minLength: 1, maxLength: 10 }),
        (validPatterns, invalidLines) => {
          const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'agentguard-test-'));
          const tempFileWithErrors = path.join(tempDir, 'test-rules-with-errors');
          const tempFileWithoutErrors = path.join(tempDir, 'test-rules-without-errors');

          try {
            // Create file with valid rules interspersed with invalid lines
            const linesWithErrors: string[] = [];
            for (let i = 0; i < validPatterns.length; i++) {
              linesWithErrors.push(`!${validPatterns[i]}`);
              if (i < invalidLines.length) {
                linesWithErrors.push(invalidLines[i]);
              }
            }
            fs.writeFileSync(tempFileWithErrors, linesWithErrors.join('\n'), 'utf-8');

            // Create file with only valid rules
            const linesWithoutErrors = validPatterns.map(p => `!${p}`);
            fs.writeFileSync(tempFileWithoutErrors, linesWithoutErrors.join('\n'), 'utf-8');

            // Parse both files
            const parser = new RuleParser();
            const resultWithErrors = parser.parse(tempFileWithErrors, RuleSource.PROJECT);
            const resultWithoutErrors = parser.parse(tempFileWithoutErrors, RuleSource.PROJECT);

            // Both should have the same number of valid rules
            expect(resultWithErrors.rules).toHaveLength(validPatterns.length);
            expect(resultWithoutErrors.rules).toHaveLength(validPatterns.length);

            // The valid rules should be identical
            for (let i = 0; i < validPatterns.length; i++) {
              expect(resultWithErrors.rules[i].type).toBe(resultWithoutErrors.rules[i].type);
              expect(resultWithErrors.rules[i].pattern).toBe(resultWithoutErrors.rules[i].pattern);
              expect(resultWithErrors.rules[i].specificity).toBe(resultWithoutErrors.rules[i].specificity);
            }

            // File with errors should have errors reported
            expect(resultWithErrors.errors.length).toBeGreaterThan(0);

            // File without errors should have no errors
            expect(resultWithoutErrors.errors).toHaveLength(0);
          } finally {
            try {
              fs.unlinkSync(tempFileWithErrors);
              fs.unlinkSync(tempFileWithoutErrors);
              fs.rmdirSync(tempDir);
            } catch (e) {
              // Ignore cleanup errors
            }
          }
        }
      ),
      { numRuns: 100 }
    );
  });
});

/**
 * Property-Based Tests for Comment and Blank Line Handling
 * 
 * **Feature: agentguard, Property 6: Comment and blank line handling**
 * **Validates: Requirements 2.2, 2.3**
 */
describe('Property 6: Comment and blank line handling', () => {
  /**
   * Property: For any rule file containing comment lines (starting with `#`) and blank lines,
   * parsing should produce the same rule set as if those lines were removed.
   */
  test('**Feature: agentguard, Property 6: Comment and blank line handling**', () => {
    // Generator for valid patterns (non-empty strings without newlines)
    const patternGenerator = fc.string({ minLength: 1, maxLength: 100 })
      .filter(s => !s.includes('\n') && s.trim().length > 0);

    // Generator for rule prefixes
    const ruleGenerator = fc.oneof(
      fc.constant({ prefix: '!', type: RuleType.BLOCK }),
      fc.constant({ prefix: '?', type: RuleType.CONFIRM }),
      fc.constant({ prefix: '+', type: RuleType.ALLOW }),
      fc.constant({ prefix: '@protect ', type: RuleType.PROTECT }),
      fc.constant({ prefix: '@sandbox ', type: RuleType.SANDBOX })
    );

    // Generator for a single rule line
    const ruleLineGenerator = fc.tuple(ruleGenerator, patternGenerator)
      .map(([rule, pattern]) => ({
        line: `${rule.prefix}${pattern}`,
        expectedType: rule.type,
        expectedPattern: pattern
      }));

    // Generator for comment lines
    const commentGenerator = fc.string({ minLength: 0, maxLength: 100 })
      .filter(s => !s.includes('\n'))
      .map(s => `# ${s}`);

    // Generator for blank lines (empty or whitespace only)
    const blankLineGenerator = fc.oneof(
      fc.constant(''),
      fc.constant('   '),
      fc.constant('\t'),
      fc.constant('  \t  ')
    );

    // Generator for noise lines (comments or blanks)
    const noiseGenerator = fc.oneof(commentGenerator, blankLineGenerator);

    // Generator for multiple rule lines with optional noise
    const rulesWithNoiseGenerator = fc.array(ruleLineGenerator, { minLength: 1, maxLength: 10 })
      .chain(rules => {
        // For each rule, generate 0-3 noise lines to insert before it
        return fc.tuple(
          fc.constant(rules),
          fc.array(fc.array(noiseGenerator, { minLength: 0, maxLength: 3 }), { 
            minLength: rules.length, 
            maxLength: rules.length 
          }),
          fc.array(noiseGenerator, { minLength: 0, maxLength: 3 }) // trailing noise
        );
      });

    fc.assert(
      fc.property(rulesWithNoiseGenerator, ([ruleData, noiseBefore, noiseAfter]) => {
        const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'agentguard-test-'));
        const tempFileWithNoise = path.join(tempDir, 'test-rules-with-noise');
        const tempFileWithoutNoise = path.join(tempDir, 'test-rules-without-noise');

        try {
          // Create file WITH comments and blank lines
          const linesWithNoise: string[] = [];
          for (let i = 0; i < ruleData.length; i++) {
            // Add noise before this rule
            linesWithNoise.push(...noiseBefore[i]);
            // Add the rule itself
            linesWithNoise.push(ruleData[i].line);
          }
          // Add trailing noise
          linesWithNoise.push(...noiseAfter);

          const contentWithNoise = linesWithNoise.join('\n');
          fs.writeFileSync(tempFileWithNoise, contentWithNoise, 'utf-8');

          // Create file WITHOUT comments and blank lines (only rules)
          const contentWithoutNoise = ruleData.map(r => r.line).join('\n');
          fs.writeFileSync(tempFileWithoutNoise, contentWithoutNoise, 'utf-8');

          // Parse both files
          const parser = new RuleParser();
          const resultWithNoise = parser.parse(tempFileWithNoise, RuleSource.PROJECT);
          const resultWithoutNoise = parser.parse(tempFileWithoutNoise, RuleSource.PROJECT);

          // Both should have no errors
          expect(resultWithNoise.errors).toHaveLength(0);
          expect(resultWithoutNoise.errors).toHaveLength(0);

          // Both should have the same number of rules
          expect(resultWithNoise.rules).toHaveLength(resultWithoutNoise.rules.length);
          expect(resultWithNoise.rules).toHaveLength(ruleData.length);

          // Both should have the same rules (same type and pattern)
          for (let i = 0; i < ruleData.length; i++) {
            const ruleWithNoise = resultWithNoise.rules[i];
            const ruleWithoutNoise = resultWithoutNoise.rules[i];

            // Same type
            expect(ruleWithNoise.type).toBe(ruleWithoutNoise.type);
            expect(ruleWithNoise.type).toBe(ruleData[i].expectedType);

            // Same pattern
            expect(ruleWithNoise.pattern).toBe(ruleWithoutNoise.pattern);
            expect(ruleWithNoise.pattern).toBe(ruleData[i].expectedPattern.trim());

            // Same source
            expect(ruleWithNoise.source).toBe(RuleSource.PROJECT);
            expect(ruleWithoutNoise.source).toBe(RuleSource.PROJECT);

            // Same specificity
            expect(ruleWithNoise.specificity).toBe(ruleWithoutNoise.specificity);

            // For @protect and @sandbox, check metadata
            if (ruleWithNoise.type === RuleType.PROTECT || ruleWithNoise.type === RuleType.SANDBOX) {
              expect(ruleWithNoise.metadata).toBeDefined();
              expect(ruleWithoutNoise.metadata).toBeDefined();
              expect(ruleWithNoise.metadata?.path).toBe(ruleWithoutNoise.metadata?.path);
            }
          }
        } finally {
          // Clean up temp files and directory
          try {
            fs.unlinkSync(tempFileWithNoise);
            fs.unlinkSync(tempFileWithoutNoise);
            fs.rmdirSync(tempDir);
          } catch (e) {
            // Ignore cleanup errors
          }
        }
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Comments can appear anywhere and should always be ignored
   */
  test('comments are ignored regardless of position', () => {
    const patternGenerator = fc.string({ minLength: 1, maxLength: 50 })
      .filter(s => !s.includes('\n') && s.trim().length > 0);

    const commentGenerator = fc.string({ minLength: 0, maxLength: 100 })
      .filter(s => !s.includes('\n'))
      .map(s => `# ${s}`);

    fc.assert(
      fc.property(
        patternGenerator,
        fc.array(commentGenerator, { minLength: 0, maxLength: 5 }),
        fc.array(commentGenerator, { minLength: 0, maxLength: 5 }),
        (pattern, commentsBefore, commentsAfter) => {
          const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'agentguard-test-'));
          const tempFile = path.join(tempDir, 'test-rules');

          try {
            const lines = [
              ...commentsBefore,
              `!${pattern}`,
              ...commentsAfter
            ];
            const content = lines.join('\n');
            fs.writeFileSync(tempFile, content, 'utf-8');

            const parser = new RuleParser();
            const result = parser.parse(tempFile, RuleSource.PROJECT);

            // Should have exactly one rule (the BLOCK rule)
            expect(result.rules).toHaveLength(1);
            expect(result.rules[0].type).toBe(RuleType.BLOCK);
            expect(result.rules[0].pattern).toBe(pattern.trim());
            expect(result.errors).toHaveLength(0);
          } finally {
            try {
              fs.unlinkSync(tempFile);
              fs.rmdirSync(tempDir);
            } catch (e) {
              // Ignore cleanup errors
            }
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Blank lines (empty or whitespace-only) should be ignored
   */
  test('blank lines are ignored', () => {
    const patternGenerator = fc.string({ minLength: 1, maxLength: 50 })
      .filter(s => !s.includes('\n') && s.trim().length > 0);

    const blankLineGenerator = fc.oneof(
      fc.constant(''),
      fc.constant(' '),
      fc.constant('  '),
      fc.constant('\t'),
      fc.constant('  \t  '),
      fc.constant('\t\t')
    );

    fc.assert(
      fc.property(
        fc.array(patternGenerator, { minLength: 1, maxLength: 5 }),
        fc.array(blankLineGenerator, { minLength: 1, maxLength: 10 }),
        (patterns, blankLines) => {
          const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'agentguard-test-'));
          const tempFile = path.join(tempDir, 'test-rules');

          try {
            // Interleave rules with blank lines
            const lines: string[] = [];
            for (let i = 0; i < patterns.length; i++) {
              // Add some blank lines before each rule
              const numBlanks = Math.min(i + 1, blankLines.length);
              lines.push(...blankLines.slice(0, numBlanks));
              // Add the rule
              lines.push(`!${patterns[i]}`);
            }
            // Add trailing blank lines
            lines.push(...blankLines);

            const content = lines.join('\n');
            fs.writeFileSync(tempFile, content, 'utf-8');

            const parser = new RuleParser();
            const result = parser.parse(tempFile, RuleSource.PROJECT);

            // Should have exactly as many rules as patterns
            expect(result.rules).toHaveLength(patterns.length);
            expect(result.errors).toHaveLength(0);

            // Verify each rule matches the corresponding pattern
            for (let i = 0; i < patterns.length; i++) {
              expect(result.rules[i].type).toBe(RuleType.BLOCK);
              expect(result.rules[i].pattern).toBe(patterns[i].trim());
            }
          } finally {
            try {
              fs.unlinkSync(tempFile);
              fs.rmdirSync(tempDir);
            } catch (e) {
              // Ignore cleanup errors
            }
          }
        }
      ),
      { numRuns: 100 }
    );
  });
});

/**
 * Property-Based Tests for Rule Precedence Hierarchy
 * 
 * **Feature: agentguard, Property 8: Rule precedence hierarchy**
 * **Validates: Requirements 2.5, 7.5**
 */
describe('Property 8: Rule precedence hierarchy', () => {
  /**
   * Property: For any set of rules loaded from global, user, and project files,
   * when multiple rules match a command, the selected rule should follow precedence:
   * rule type (BLOCK > CONFIRM > ALLOW), then specificity, then source (project > user > global)
   */
  test('**Feature: agentguard, Property 8: Rule precedence hierarchy**', () => {
    // Generator for valid patterns (non-empty strings without newlines)
    const patternGenerator = fc.string({ minLength: 1, maxLength: 100 })
      .filter(s => !s.includes('\n') && s.trim().length > 0);

    // Generator for rule types
    const ruleTypeGenerator = fc.constantFrom(
      RuleType.BLOCK,
      RuleType.CONFIRM,
      RuleType.ALLOW
    );

    // Generator for rule sources
    const ruleSourceGenerator = fc.constantFrom(
      RuleSource.GLOBAL,
      RuleSource.USER,
      RuleSource.PROJECT
    );

    // Generator for a rule with type, pattern, and source
    const ruleGenerator = fc.tuple(
      ruleTypeGenerator,
      patternGenerator,
      ruleSourceGenerator
    ).map(([type, pattern, source]) => ({
      type,
      pattern: pattern.trim(),
      source
    }));

    // Generator for multiple rules with the same pattern but different types/sources
    const samePatternRulesGenerator = patternGenerator.chain(pattern => {
      return fc.array(
        fc.tuple(ruleTypeGenerator, ruleSourceGenerator).map(([type, source]) => ({
          type,
          pattern: pattern.trim(),
          source
        })),
        { minLength: 2, maxLength: 9 } // At most 3 types × 3 sources = 9 combinations
      ).filter(rules => {
        // Ensure we have at least 2 different rules (different type or source)
        const uniqueKeys = new Set(rules.map(r => `${r.type}:${r.source}`));
        return uniqueKeys.size >= 2;
      });
    });

    fc.assert(
      fc.property(samePatternRulesGenerator, (ruleData) => {
        const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'agentguard-test-'));
        const globalFile = path.join(tempDir, 'global-rules');
        const userFile = path.join(tempDir, 'user-rules');
        const projectFile = path.join(tempDir, 'project-rules');

        try {
          // Separate rules by source
          const globalRules = ruleData.filter(r => r.source === RuleSource.GLOBAL);
          const userRules = ruleData.filter(r => r.source === RuleSource.USER);
          const projectRules = ruleData.filter(r => r.source === RuleSource.PROJECT);

          // Helper to convert rule type to prefix
          const getPrefix = (type: RuleType): string => {
            switch (type) {
              case RuleType.BLOCK: return '!';
              case RuleType.CONFIRM: return '?';
              case RuleType.ALLOW: return '+';
              default: return '!';
            }
          };

          // Write rules to respective files
          if (globalRules.length > 0) {
            const content = globalRules.map(r => `${getPrefix(r.type)}${r.pattern}`).join('\n');
            fs.writeFileSync(globalFile, content, 'utf-8');
          }
          if (userRules.length > 0) {
            const content = userRules.map(r => `${getPrefix(r.type)}${r.pattern}`).join('\n');
            fs.writeFileSync(userFile, content, 'utf-8');
          }
          if (projectRules.length > 0) {
            const content = projectRules.map(r => `${getPrefix(r.type)}${r.pattern}`).join('\n');
            fs.writeFileSync(projectFile, content, 'utf-8');
          }

          // Parse each file
          const parser = new RuleParser();
          const globalResult = globalRules.length > 0 
            ? parser.parse(globalFile, RuleSource.GLOBAL) 
            : { rules: [], errors: [] };
          const userResult = userRules.length > 0 
            ? parser.parse(userFile, RuleSource.USER) 
            : { rules: [], errors: [] };
          const projectResult = projectRules.length > 0 
            ? parser.parse(projectFile, RuleSource.PROJECT) 
            : { rules: [], errors: [] };

          // Combine all rules
          const allRules = [
            ...globalResult.rules,
            ...userResult.rules,
            ...projectResult.rules
          ];

          // Determine expected winner based on precedence rules
          // 1. Rule type precedence: BLOCK > CONFIRM > ALLOW
          const blockRules = allRules.filter(r => r.type === RuleType.BLOCK);
          const confirmRules = allRules.filter(r => r.type === RuleType.CONFIRM);
          const allowRules = allRules.filter(r => r.type === RuleType.ALLOW);

          let expectedWinner: Rule | undefined;

          if (blockRules.length > 0) {
            // Among BLOCK rules, apply source precedence: project > user > global
            const projectBlocks = blockRules.filter(r => r.source === RuleSource.PROJECT);
            const userBlocks = blockRules.filter(r => r.source === RuleSource.USER);
            const globalBlocks = blockRules.filter(r => r.source === RuleSource.GLOBAL);

            if (projectBlocks.length > 0) {
              expectedWinner = projectBlocks[0];
            } else if (userBlocks.length > 0) {
              expectedWinner = userBlocks[0];
            } else {
              expectedWinner = globalBlocks[0];
            }
          } else if (confirmRules.length > 0) {
            // Among CONFIRM rules, apply source precedence
            const projectConfirms = confirmRules.filter(r => r.source === RuleSource.PROJECT);
            const userConfirms = confirmRules.filter(r => r.source === RuleSource.USER);
            const globalConfirms = confirmRules.filter(r => r.source === RuleSource.GLOBAL);

            if (projectConfirms.length > 0) {
              expectedWinner = projectConfirms[0];
            } else if (userConfirms.length > 0) {
              expectedWinner = userConfirms[0];
            } else {
              expectedWinner = globalConfirms[0];
            }
          } else if (allowRules.length > 0) {
            // Among ALLOW rules, apply source precedence
            const projectAllows = allowRules.filter(r => r.source === RuleSource.PROJECT);
            const userAllows = allowRules.filter(r => r.source === RuleSource.USER);
            const globalAllows = allowRules.filter(r => r.source === RuleSource.GLOBAL);

            if (projectAllows.length > 0) {
              expectedWinner = projectAllows[0];
            } else if (userAllows.length > 0) {
              expectedWinner = userAllows[0];
            } else {
              expectedWinner = globalAllows[0];
            }
          }

          // The mergeRules function should select the winner based on precedence
          // Since all rules have the same pattern, mergeRules should keep only one
          const mergedRules = (parser as any).mergeRules(allRules);

          // Should have exactly one rule (the winner)
          expect(mergedRules.length).toBe(1);

          // The merged rule should match the expected winner
          if (expectedWinner) {
            expect(mergedRules[0].type).toBe(expectedWinner.type);
            expect(mergedRules[0].source).toBe(expectedWinner.source);
            expect(mergedRules[0].pattern).toBe(expectedWinner.pattern);
          }
        } finally {
          // Clean up temp files and directory
          try {
            if (fs.existsSync(globalFile)) fs.unlinkSync(globalFile);
            if (fs.existsSync(userFile)) fs.unlinkSync(userFile);
            if (fs.existsSync(projectFile)) fs.unlinkSync(projectFile);
            fs.rmdirSync(tempDir);
          } catch (e) {
            // Ignore cleanup errors
          }
        }
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Type precedence - BLOCK always wins over CONFIRM and ALLOW
   */
  test('BLOCK rules take precedence over CONFIRM and ALLOW', () => {
    const patternGenerator = fc.string({ minLength: 1, maxLength: 50 })
      .filter(s => !s.includes('\n') && s.trim().length > 0);

    fc.assert(
      fc.property(patternGenerator, (pattern) => {
        const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'agentguard-test-'));
        const globalFile = path.join(tempDir, 'global-rules');
        const userFile = path.join(tempDir, 'user-rules');
        const projectFile = path.join(tempDir, 'project-rules');

        try {
          // Create rules with same pattern but different types
          fs.writeFileSync(globalFile, `+${pattern}`, 'utf-8'); // ALLOW in global
          fs.writeFileSync(userFile, `?${pattern}`, 'utf-8');   // CONFIRM in user
          fs.writeFileSync(projectFile, `!${pattern}`, 'utf-8'); // BLOCK in project

          const parser = new RuleParser();
          const globalResult = parser.parse(globalFile, RuleSource.GLOBAL);
          const userResult = parser.parse(userFile, RuleSource.USER);
          const projectResult = parser.parse(projectFile, RuleSource.PROJECT);

          const allRules = [
            ...globalResult.rules,
            ...userResult.rules,
            ...projectResult.rules
          ];

          const mergedRules = (parser as any).mergeRules(allRules);

          // Should have exactly one rule
          expect(mergedRules.length).toBe(1);

          // Should be the BLOCK rule
          expect(mergedRules[0].type).toBe(RuleType.BLOCK);
          expect(mergedRules[0].source).toBe(RuleSource.PROJECT);
        } finally {
          try {
            fs.unlinkSync(globalFile);
            fs.unlinkSync(userFile);
            fs.unlinkSync(projectFile);
            fs.rmdirSync(tempDir);
          } catch (e) {
            // Ignore cleanup errors
          }
        }
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Source precedence - project > user > global for same type
   */
  test('project rules take precedence over user and global for same type', () => {
    const patternGenerator = fc.string({ minLength: 1, maxLength: 50 })
      .filter(s => !s.includes('\n') && s.trim().length > 0);

    const ruleTypeGenerator = fc.constantFrom(
      RuleType.BLOCK,
      RuleType.CONFIRM,
      RuleType.ALLOW
    );

    fc.assert(
      fc.property(patternGenerator, ruleTypeGenerator, (pattern, ruleType) => {
        const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'agentguard-test-'));
        const globalFile = path.join(tempDir, 'global-rules');
        const userFile = path.join(tempDir, 'user-rules');
        const projectFile = path.join(tempDir, 'project-rules');

        try {
          const prefix = ruleType === RuleType.BLOCK ? '!' : 
                        ruleType === RuleType.CONFIRM ? '?' : '+';

          // Create same rule type in all three sources
          fs.writeFileSync(globalFile, `${prefix}${pattern}`, 'utf-8');
          fs.writeFileSync(userFile, `${prefix}${pattern}`, 'utf-8');
          fs.writeFileSync(projectFile, `${prefix}${pattern}`, 'utf-8');

          const parser = new RuleParser();
          const globalResult = parser.parse(globalFile, RuleSource.GLOBAL);
          const userResult = parser.parse(userFile, RuleSource.USER);
          const projectResult = parser.parse(projectFile, RuleSource.PROJECT);

          const allRules = [
            ...globalResult.rules,
            ...userResult.rules,
            ...projectResult.rules
          ];

          const mergedRules = (parser as any).mergeRules(allRules);

          // Should have exactly one rule
          expect(mergedRules.length).toBe(1);

          // Should be from PROJECT source
          expect(mergedRules[0].source).toBe(RuleSource.PROJECT);
          expect(mergedRules[0].type).toBe(ruleType);
        } finally {
          try {
            fs.unlinkSync(globalFile);
            fs.unlinkSync(userFile);
            fs.unlinkSync(projectFile);
            fs.rmdirSync(tempDir);
          } catch (e) {
            // Ignore cleanup errors
          }
        }
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Property: CONFIRM takes precedence over ALLOW when no BLOCK exists
   */
  test('CONFIRM rules take precedence over ALLOW when no BLOCK exists', () => {
    const patternGenerator = fc.string({ minLength: 1, maxLength: 50 })
      .filter(s => !s.includes('\n') && s.trim().length > 0);

    fc.assert(
      fc.property(patternGenerator, (pattern) => {
        const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'agentguard-test-'));
        const globalFile = path.join(tempDir, 'global-rules');
        const userFile = path.join(tempDir, 'user-rules');

        try {
          // Create ALLOW in global and CONFIRM in user
          fs.writeFileSync(globalFile, `+${pattern}`, 'utf-8');
          fs.writeFileSync(userFile, `?${pattern}`, 'utf-8');

          const parser = new RuleParser();
          const globalResult = parser.parse(globalFile, RuleSource.GLOBAL);
          const userResult = parser.parse(userFile, RuleSource.USER);

          const allRules = [
            ...globalResult.rules,
            ...userResult.rules
          ];

          const mergedRules = (parser as any).mergeRules(allRules);

          // Should have exactly one rule
          expect(mergedRules.length).toBe(1);

          // Should be the CONFIRM rule
          expect(mergedRules[0].type).toBe(RuleType.CONFIRM);
          expect(mergedRules[0].source).toBe(RuleSource.USER);
        } finally {
          try {
            fs.unlinkSync(globalFile);
            fs.unlinkSync(userFile);
            fs.rmdirSync(tempDir);
          } catch (e) {
            // Ignore cleanup errors
          }
        }
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Property: User rules override global rules for same type
   */
  test('user rules take precedence over global for same type', () => {
    const patternGenerator = fc.string({ minLength: 1, maxLength: 50 })
      .filter(s => !s.includes('\n') && s.trim().length > 0);

    const ruleTypeGenerator = fc.constantFrom(
      RuleType.BLOCK,
      RuleType.CONFIRM,
      RuleType.ALLOW
    );

    fc.assert(
      fc.property(patternGenerator, ruleTypeGenerator, (pattern, ruleType) => {
        const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'agentguard-test-'));
        const globalFile = path.join(tempDir, 'global-rules');
        const userFile = path.join(tempDir, 'user-rules');

        try {
          const prefix = ruleType === RuleType.BLOCK ? '!' : 
                        ruleType === RuleType.CONFIRM ? '?' : '+';

          // Create same rule type in global and user
          fs.writeFileSync(globalFile, `${prefix}${pattern}`, 'utf-8');
          fs.writeFileSync(userFile, `${prefix}${pattern}`, 'utf-8');

          const parser = new RuleParser();
          const globalResult = parser.parse(globalFile, RuleSource.GLOBAL);
          const userResult = parser.parse(userFile, RuleSource.USER);

          const allRules = [
            ...globalResult.rules,
            ...userResult.rules
          ];

          const mergedRules = (parser as any).mergeRules(allRules);

          // Should have exactly one rule
          expect(mergedRules.length).toBe(1);

          // Should be from USER source
          expect(mergedRules[0].source).toBe(RuleSource.USER);
          expect(mergedRules[0].type).toBe(ruleType);
        } finally {
          try {
            fs.unlinkSync(globalFile);
            fs.unlinkSync(userFile);
            fs.rmdirSync(tempDir);
          } catch (e) {
            // Ignore cleanup errors
          }
        }
      }),
      { numRuns: 100 }
    );
  });
});
