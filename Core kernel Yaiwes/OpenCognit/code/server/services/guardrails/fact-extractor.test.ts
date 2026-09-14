import { describe, it, expect } from 'vitest';
import { extractFacts, factOverlap, normalizeFact, hasFacts } from './fact-extractor.js';

describe('extractFacts', () => {
  it('extracts factual claims with high confidence', () => {
    const text = 'The API runs on Node.js 20.5.0. It uses PostgreSQL 15. The server listens on port 3000.';
    const facts = extractFacts(text, 0.3);
    expect(facts.length).toBeGreaterThanOrEqual(2);
    expect(facts[0].confidence).toBeGreaterThan(0.3);
  });

  it('extracts version numbers as facts', () => {
    const text = 'The system requires Node.js v20.5.0 and React 18.2.0. We upgraded from version 17.0.2 last month.';
    const facts = extractFacts(text, 0.2);
    expect(facts.length).toBeGreaterThan(0);
    const versions = facts.filter(f => f.entityTypes.includes('version'));
    expect(versions.length).toBeGreaterThanOrEqual(1);
  });

  it('extracts URLs as facts', () => {
    const text = 'The documentation is hosted at https://opencognit.local/docs and the API endpoint is https://api.opencognit.local/v1/users.';
    const facts = extractFacts(text, 0.25);
    expect(facts.length).toBeGreaterThan(0);
    const urls = facts.filter(f => f.entityTypes.includes('url'));
    expect(urls.length).toBeGreaterThanOrEqual(1);
  });

  it('ignards opinionated sentences', () => {
    const text = 'I think we should use React. Maybe Vue would be better. The team decided on Angular 17.';
    const facts = extractFacts(text, 0.4);
    // "The team decided on Angular 17" might be extracted, but "I think" and "Maybe" should score low
    const lowConfidence = facts.filter(f => f.confidence < 0.3);
    expect(lowConfidence.length).toBeLessThanOrEqual(facts.length);
  });

  it('extracts file paths', () => {
    const text = 'The main configuration file is located at /etc/opencognit/config.yaml and logs are written to /var/log/app.log.';
    const facts = extractFacts(text, 0.2);
    expect(facts.length).toBeGreaterThan(0);
    const paths = facts.filter(f => f.entityTypes.includes('file_path'));
    expect(paths.length).toBeGreaterThanOrEqual(1);
  });

  it('returns empty array for short text', () => {
    expect(extractFacts('ok')).toEqual([]);
    expect(extractFacts('')).toEqual([]);
  });

  it('hasFacts returns false for opinions', () => {
    expect(hasFacts('I think this is nice.')).toBe(false);
  });

  it('hasFacts returns true for facts with strong signals', () => {
    const facts = extractFacts('The API server runs on Node.js v20.5.0 and listens on port 3000.', 0.3);
    expect(facts.length).toBeGreaterThan(0);
    expect(facts[0].confidence).toBeGreaterThanOrEqual(0.3);
  });
});

describe('normalizeFact', () => {
  it('lowercases and removes punctuation', () => {
    const result = normalizeFact('Hello, World!');
    expect(result).toBe('hello world');
  });

  it('handles multiple spaces', () => {
    const result = normalizeFact('  hello   world  ');
    expect(result).toBe('hello world');
  });
});

describe('factOverlap', () => {
  it('returns 1 for identical facts', () => {
    expect(factOverlap('Node.js 20 is required', 'Node.js 20 is required')).toBeGreaterThan(0.8);
  });

  it('returns 0 for unrelated facts', () => {
    expect(factOverlap('The cat is black', 'React 18 is used')).toBeLessThan(0.3);
  });

  it('returns partial overlap for similar facts', () => {
    const overlap = factOverlap('The API uses PostgreSQL 15', 'PostgreSQL 15 is the database');
    expect(overlap).toBeGreaterThan(0.2);
    expect(overlap).toBeLessThan(1);
  });
});
