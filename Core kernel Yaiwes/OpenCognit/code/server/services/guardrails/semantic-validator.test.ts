import { describe, it, expect } from 'vitest';
import { runSemanticValidation } from './semantic-validator.js';

describe('runSemanticValidation', () => {
  it('detects self-contradictions with negation', () => {
    const output = 'The database is PostgreSQL. The application definitely does not use PostgreSQL. It uses SQLite instead.';
    const result = runSemanticValidation(output, { checkConsistency: true, checkGroundedness: false });

    const contradiction = result.violations.find(v => v.type === 'self_contradiction');
    expect(contradiction).toBeDefined();
    expect(['medium', 'high']).toContain(contradiction!.severity);
  });

  it('detects boolean conflicts', () => {
    const output = 'ssl_enabled = true. The server requires TLS. Later we configured ssl_enabled = false.';
    const result = runSemanticValidation(output, { checkConsistency: true, checkGroundedness: false });

    const contradiction = result.violations.find(v => v.type === 'self_contradiction');
    expect(contradiction).toBeDefined();
  });

  it('detects low confidence output', () => {
    const output = 'Maybe we should use React. Perhaps Vue is better. I think Angular might work. Possibly Svelte. Not sure about the choice.';
    const result = runSemanticValidation(output, { checkConsistency: false, checkGroundedness: false });

    const lowConf = result.violations.find(v => v.type === 'low_confidence_output');
    expect(lowConf).toBeDefined();
    expect(lowConf!.severity).toBe('medium');
  });

  it('passes consistent output', () => {
    const output = 'The API runs on Node.js 20. It uses Express 4. The database is PostgreSQL 15.';
    const result = runSemanticValidation(output, { checkConsistency: true, checkGroundedness: false });

    const contradictions = result.violations.filter(v => v.type === 'self_contradiction');
    expect(contradictions.length).toBe(0);
  });

  it('returns groundedness results with uncertain verdict when no companyId', () => {
    const output = 'The REST API server runs on port 3000 in production. It requires Node.js version 20.5.0 or higher. The database connection uses PostgreSQL 15 with SSL enabled.';
    const result = runSemanticValidation(output, {
      checkGroundedness: true,
      checkConsistency: false,
      factConfidenceThreshold: 0.3,
    });

    expect(result.groundedness.length).toBeGreaterThan(0);
    // Without companyId, all should be uncertain
    expect(result.groundedness.every(g => g.verdict === 'uncertain')).toBe(true);
  });

  it('computes hallucination score', () => {
    const output = 'The server runs on port 3000. It uses Node.js 20.';
    const result = runSemanticValidation(output, { checkGroundedness: true, checkConsistency: false });

    expect(result.hallucinationScore).toBeGreaterThanOrEqual(0);
    expect(result.hallucinationScore).toBeLessThanOrEqual(1);
  });

  it('limits facts checked to maxFactsToCheck', () => {
    const output = Array.from({ length: 20 }, (_, i) => `Fact ${i}: Server v${i}.0.0 runs on port ${3000 + i}.`).join(' ');
    const result = runSemanticValidation(output, {
      checkGroundedness: true,
      checkConsistency: false,
      maxFactsToCheck: 5,
    });

    expect(result.groundedness.length).toBeLessThanOrEqual(5);
  });

  it('is fast (< 100ms for typical output)', () => {
    const output = 'The system uses React 18.2.0 with TypeScript 5.3. The backend runs on Node.js 20.9.0 with Express 4.18.2. The database is PostgreSQL 15.4. Redis is used for caching. The frontend is deployed to Vercel.';
    const result = runSemanticValidation(output, { checkConsistency: true, checkGroundedness: true });

    expect(result.durationMs).toBeLessThan(100);
  });
});
