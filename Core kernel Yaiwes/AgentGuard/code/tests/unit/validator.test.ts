/**
 * Unit tests for Validator integration
 * 
 * Note: These tests verify the validator orchestrates the pipeline correctly.
 * Detailed validation logic is tested in rule-engine.test.ts
 */

import { describe, it, expect } from 'vitest';
import { Validator } from '../../src/validator';
import { ValidationAction } from '../../src/types';

describe('Validator', () => {
  const validator = new Validator();

  describe('validate', () => {
    it('should ALLOW safe commands', () => {
      // Simple echo command should be allowed (either by explicit rule or default policy)
      const result = validator.validate('echo hello');

      expect(result.action).toBe(ValidationAction.ALLOW);
      // Reason should indicate why it was allowed
      expect(result.reason).toBeDefined();
    });

    it('should tokenize and validate commands through the pipeline', () => {
      // This test verifies the validator orchestrates the components
      // The actual validation logic is tested in rule-engine.test.ts
      const result = validator.validate('rm -rf /tmp');

      // Should return a valid ValidationResult
      expect(result).toBeDefined();
      expect(result.action).toBeDefined();
      expect(result.reason).toBeDefined();
      expect([ValidationAction.ALLOW, ValidationAction.BLOCK, ValidationAction.CONFIRM]).toContain(result.action);
    });

    it('should handle empty commands', () => {
      const result = validator.validate('');

      expect(result).toBeDefined();
      expect(result.action).toBeDefined();
    });

    it('should handle commands with special characters', () => {
      const result = validator.validate('echo "hello world"');

      expect(result).toBeDefined();
      expect(result.action).toBeDefined();
    });

    it('should handle chained commands', () => {
      const result = validator.validate('echo hello && echo world');

      expect(result).toBeDefined();
      expect(result.action).toBeDefined();
      expect([ValidationAction.ALLOW, ValidationAction.BLOCK, ValidationAction.CONFIRM]).toContain(result.action);
    });

    it('should handle piped commands', () => {
      const result = validator.validate('cat file.txt | grep test');

      expect(result).toBeDefined();
      expect(result.action).toBeDefined();
      expect([ValidationAction.ALLOW, ValidationAction.BLOCK, ValidationAction.CONFIRM]).toContain(result.action);
    });
  });
});
