import { describe, it, expect } from 'vitest';
import {
  classifyMemory,
  extractEntities,
  suggestTags,
  autoIndex,
  shouldLink,
} from './auto-index-pure.js';

describe('classifyMemory', () => {
  it('classifies decisions', () => {
    const result = classifyMemory('We decided to use PostgreSQL instead of SQLite for production.');
    expect(result.classification).toBe('decision');
    expect(result.confidence).toBeGreaterThan(0);
  });

  it('classifies actions', () => {
    const result = classifyMemory('I created a new API endpoint for user authentication.');
    expect(result.classification).toBe('action');
    expect(result.confidence).toBeGreaterThan(0);
  });

  it('classifies facts', () => {
    const result = classifyMemory('The system requires Node.js 20 or higher.');
    expect(result.classification).toBe('fact');
    expect(result.confidence).toBeGreaterThan(0);
  });

  it('classifies skills', () => {
    const result = classifyMemory('Here is a step by step guide to setting up Docker.');
    expect(result.classification).toBe('skill');
    expect(result.confidence).toBeGreaterThan(0);
  });

  it('classifies relationships', () => {
    const result = classifyMemory('The Auth service depends on the Database service.');
    expect(result.classification).toBe('relationship');
    expect(result.confidence).toBeGreaterThan(0);
  });

  it('falls back to observation for short text', () => {
    const result = classifyMemory('ok');
    expect(result.classification).toBe('observation');
    expect(result.confidence).toBeLessThan(0.5);
  });

  it('handles German text', () => {
    const result = classifyMemory('Wir haben beschlossen, React zu verwenden.');
    expect(result.classification).toBe('decision');
  });
});

describe('extractEntities', () => {
  it('extracts quoted strings', () => {
    const entities = extractEntities('The project "OpenCognit" uses "React" for the frontend.');
    expect(entities).toContain('OpenCognit');
    expect(entities).toContain('React');
  });

  it('extracts capitalized phrases', () => {
    const entities = extractEntities('John Smith works at Acme Corp in New York City.');
    expect(entities.some(e => e.includes('John Smith'))).toBe(true);
    expect(entities.some(e => e.includes('Acme Corp'))).toBe(true);
  });

  it('extracts snake_case identifiers', () => {
    const entities = extractEntities('The function user_auth_handler is deprecated.');
    expect(entities).toContain('user_auth_handler');
  });

  it('extracts PascalCase identifiers', () => {
    const entities = extractEntities('Use the UserAuthHandler class for this.');
    expect(entities).toContain('UserAuthHandler');
  });

  it('extracts URLs', () => {
    const entities = extractEntities('See https://opencognit.local/docs for details.');
    expect(entities).toContain('https://opencognit.local/docs');
  });

  it('extracts backtick terms', () => {
    const entities = extractEntities('Call the `authenticateUser` method.');
    expect(entities).toContain('authenticateUser');
  });

  it('returns empty array for empty text', () => {
    expect(extractEntities('')).toEqual([]);
  });

  it('limits to 15 entities', () => {
    const text = Array.from({ length: 30 }, (_, i) => `"Entity${i}"`).join(' ');
    expect(extractEntities(text).length).toBeLessThanOrEqual(15);
  });
});

describe('suggestTags', () => {
  it('includes classification tag', () => {
    const tags = suggestTags('Some text', 'fact');
    expect(tags).toContain('type:fact');
  });

  it('includes topic tags', () => {
    const tags = suggestTags('We need to add API endpoints for user authentication.');
    expect(tags).toContain('topic:api');
    expect(tags).toContain('topic:auth');
  });

  it('includes entity tags', () => {
    const tags = suggestTags('The project "MyApp" uses React.');
    expect(tags.some(t => t.startsWith('entity:'))).toBe(true);
  });

  it('limits tag count', () => {
    const tags = suggestTags('API React Database Auth Docker Testing Design Security frontend backend');
    expect(tags.length).toBeLessThanOrEqual(12);
  });
});

describe('autoIndex', () => {
  it('returns complete index result', () => {
    const result = autoIndex('We decided to use "Docker Compose" for deployment of the OpenCognit project.');
    expect(result.classification).toBe('decision');
    expect(result.confidence).toBeGreaterThan(0);
    expect(result.entityTags.length).toBeGreaterThan(0);
    expect(result.suggestedLinks.length).toBeGreaterThan(0);
  });
});

describe('shouldLink', () => {
  it('returns true for shared entities', () => {
    const a = 'The OpenCognit project uses React for the frontend.';
    const b = 'OpenCognit requires Node.js 20 and uses Vite for building.';
    expect(shouldLink(a, b)).toBe(true);
  });

  it('returns false for unrelated texts', () => {
    const a = 'Cats are furry animals that meow.';
    const b = 'The stock market closed higher today.';
    expect(shouldLink(a, b)).toBe(false);
  });

  it('returns false when one has no entities', () => {
    const a = 'The quick brown fox jumps over the lazy dog.';
    const b = 'OpenCognit is a project.';
    expect(shouldLink(a, b)).toBe(false);
  });

  it('respects threshold', () => {
    const a = 'OpenCognit uses React and Docker.';
    const b = 'OpenCognit uses React and PostgreSQL.';
    expect(shouldLink(a, b, 0.5)).toBe(true);
    expect(shouldLink(a, b, 0.9)).toBe(false);
  });
});
