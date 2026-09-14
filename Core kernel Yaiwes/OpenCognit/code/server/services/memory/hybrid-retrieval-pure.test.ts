import { describe, it, expect } from 'vitest';
import {
  tokenize,
  keywordOverlapScore,
  applyTemporalDecay,
  daysSince,
  reciprocalRankFusion,
  computeHybridScores,
  deduplicateEntries,
  formatHierarchicalContext,
} from './hybrid-retrieval-pure.js';
import type { MemoryEntry } from './types.js';

describe('tokenize', () => {
  it('splits text into lowercase tokens', () => {
    expect(tokenize('Hello World')).toEqual(['hello', 'world']);
  });

  it('filters stopwords', () => {
    expect(tokenize('the quick brown fox')).toEqual(['quick', 'brown', 'fox']);
  });

  it('handles German text', () => {
    expect(tokenize('Der schnelle braune Fuchs')).toEqual(['schnelle', 'braune', 'fuchs']);
  });

  it('removes short tokens', () => {
    expect(tokenize('a b c hello')).toEqual(['hello']);
  });
});

describe('keywordOverlapScore', () => {
  it('returns 1 for identical content', () => {
    expect(keywordOverlapScore('hello world', 'hello world')).toBe(1);
  });

  it('returns 0 for no overlap', () => {
    expect(keywordOverlapScore('hello world', 'foo bar baz')).toBe(0);
  });

  it('returns partial overlap', () => {
    expect(keywordOverlapScore('hello world foo', 'hello bar baz')).toBeCloseTo(1 / 3, 2);
  });

  it('handles empty inputs', () => {
    expect(keywordOverlapScore('', 'hello')).toBe(0);
    expect(keywordOverlapScore('hello', '')).toBe(0);
  });
});

describe('applyTemporalDecay', () => {
  it('returns original score for age 0', () => {
    expect(applyTemporalDecay(1.0, 0, 7)).toBe(1.0);
  });

  it('halves score after one half-life', () => {
    expect(applyTemporalDecay(1.0, 7, 7)).toBeCloseTo(0.5, 2);
  });

  it('quarters score after two half-lives', () => {
    expect(applyTemporalDecay(1.0, 14, 7)).toBeCloseTo(0.25, 2);
  });

  it('returns 0 for very old memories', () => {
    expect(applyTemporalDecay(1.0, 100, 7)).toBeCloseTo(0, 1);
  });
});

describe('daysSince', () => {
  it('returns 0 for current date', () => {
    const now = new Date().toISOString();
    expect(daysSince(now)).toBeCloseTo(0, 1);
  });

  it('returns ~1 for yesterday', () => {
    const yesterday = new Date(Date.now() - 86400000).toISOString();
    expect(daysSince(yesterday)).toBeCloseTo(1, 1);
  });

  it('returns Infinity for invalid date', () => {
    expect(daysSince('not-a-date')).toBe(Infinity);
  });
});

describe('reciprocalRankFusion', () => {
  it('fuses two rankings', () => {
    const r1 = ['a', 'b', 'c'];
    const r2 = ['b', 'a', 'd'];
    const scores = reciprocalRankFusion([r1, r2]);

    // a: 1/61 + 1/62 ≈ 0.0325
    // b: 1/62 + 1/61 ≈ 0.0325
    // c: 1/63 ≈ 0.0159
    // d: 1/63 ≈ 0.0159
    expect(scores.get('a')! > scores.get('c')!).toBe(true);
    expect(scores.get('b')! > scores.get('d')!).toBe(true);
    expect(Math.abs(scores.get('a')! - scores.get('b')!)).toBeLessThan(0.001);
  });

  it('handles single ranking', () => {
    const scores = reciprocalRankFusion([['x', 'y']]);
    expect(scores.get('x')! > scores.get('y')!).toBe(true);
  });

  it('handles empty rankings', () => {
    const scores = reciprocalRankFusion([]);
    expect(scores.size).toBe(0);
  });
});

describe('computeHybridScores', () => {
  const makeEntry = (id: string, layer: MemoryEntry['layer'], relevance: number, ageDays: number): MemoryEntry => ({
    id,
    layer,
    source: 'palaceDiary',
    agentId: 'agent1',
    companyId: 'comp1',
    content: `content-${id}`,
    createdAt: new Date(Date.now() - ageDays * 86400000).toISOString(),
    relevanceScore: relevance,
  });

  it('ranks higher relevance above lower', () => {
    const entries = [
      makeEntry('a', 'semantic', 0.9, 0),
      makeEntry('b', 'semantic', 0.5, 0),
    ];
    const scored = computeHybridScores(entries);
    expect(scored[0].id).toBe('a');
    expect(scored[1].id).toBe('b');
  });

  it('applies temporal decay to old entries', () => {
    const entries = [
      makeEntry('old', 'episodic', 0.9, 30),
      makeEntry('new', 'episodic', 0.5, 0),
    ];
    const scored = computeHybridScores(entries, { recencyBoost: 0.5, decayHalfLifeDays: 7 });
    // New entry should outrank old despite lower raw relevance
    expect(scored[0].id).toBe('new');
  });

  it('applies layer boosts', () => {
    const entries = [
      makeEntry('working', 'working', 0.7, 0),
      makeEntry('semantic', 'semantic', 0.7, 0),
    ];
    const scored = computeHybridScores(entries, { layerBoosts: { working: 1.2, episodic: 1.0, semantic: 1.0 } });
    expect(scored[0].id).toBe('working');
  });

  it('normalizes scores to 0-1', () => {
    const entries = [makeEntry('a', 'semantic', 0.8, 0)];
    const scored = computeHybridScores(entries);
    expect(scored[0].fusedScore).toBeCloseTo(1, 5);
  });
});

describe('deduplicateEntries', () => {
  it('removes near-duplicate entries', () => {
    const entries = [
      { id: 'a', fusedScore: 0.9, layer: 'semantic' as const, source: 'semanticChunk' as const, agentId: null, companyId: 'c', content: 'hello world foo bar', createdAt: new Date().toISOString(), relevanceScore: 0.9 },
      { id: 'b', fusedScore: 0.8, layer: 'semantic' as const, source: 'semanticChunk' as const, agentId: null, companyId: 'c', content: 'hello world foo baz', createdAt: new Date().toISOString(), relevanceScore: 0.8 },
      { id: 'c', fusedScore: 0.7, layer: 'semantic' as const, source: 'semanticChunk' as const, agentId: null, companyId: 'c', content: 'completely different', createdAt: new Date().toISOString(), relevanceScore: 0.7 },
    ];
    const result = deduplicateEntries(entries, 0.6);
    expect(result.length).toBe(2);
    expect(result.map(r => r.id)).toContain('a');
    expect(result.map(r => r.id)).toContain('c');
  });

  it('keeps all distinct entries', () => {
    const entries = [
      { id: 'a', fusedScore: 0.9, layer: 'semantic' as const, source: 'semanticChunk' as const, agentId: null, companyId: 'c', content: 'alpha beta gamma', createdAt: new Date().toISOString(), relevanceScore: 0.9 },
      { id: 'b', fusedScore: 0.8, layer: 'semantic' as const, source: 'semanticChunk' as const, agentId: null, companyId: 'c', content: 'delta epsilon zeta', createdAt: new Date().toISOString(), relevanceScore: 0.8 },
    ];
    const result = deduplicateEntries(entries);
    expect(result.length).toBe(2);
  });
});

describe('formatHierarchicalContext', () => {
  it('returns empty string for no entries', () => {
    expect(formatHierarchicalContext([])).toBe('');
  });

  it('formats entries with layer headers', () => {
    const entries = [
      { id: 'a', fusedScore: 0.9, layer: 'working' as const, source: 'palaceDiary' as const, agentId: 'x', companyId: 'c', content: 'Current task context', createdAt: new Date().toISOString(), relevanceScore: 0.9 },
      { id: 'b', fusedScore: 0.7, layer: 'semantic' as const, source: 'semanticChunk' as const, agentId: null, companyId: 'c', content: 'Some knowledge fact', createdAt: new Date().toISOString(), relevanceScore: 0.7 },
    ];
    const md = formatHierarchicalContext(entries);
    expect(md).toContain('HIERARCHICAL MEMORY RETRIEVAL');
    expect(md).toContain('Aktueller Kontext');
    expect(md).toContain('Gelerntes Wissen');
    expect(md).toContain('Current task context');
  });

  it('truncates long content', () => {
    const longContent = 'a'.repeat(500);
    const entries = [
      { id: 'a', fusedScore: 0.9, layer: 'working' as const, source: 'palaceDiary' as const, agentId: 'x', companyId: 'c', content: longContent, createdAt: new Date().toISOString(), relevanceScore: 0.9 },
    ];
    const md = formatHierarchicalContext(entries);
    expect(md).toContain('…');
    expect(md.length).toBeLessThan(longContent.length + 200);
  });

  it('respects maxChars limit', () => {
    const entries = Array.from({ length: 50 }, (_, i) => ({
      id: `e${i}`,
      fusedScore: 0.9 - i * 0.01,
      layer: 'semantic' as const,
      source: 'semanticChunk' as const,
      agentId: null,
      companyId: 'c',
      content: `This is entry number ${i} with some content text`,
      createdAt: new Date().toISOString(),
      relevanceScore: 0.9,
    }));
    const md = formatHierarchicalContext(entries, { maxChars: 500 });
    expect(md.length).toBeLessThanOrEqual(600); // buffer for truncation message
    expect(md).toContain('[…weitere Einträge gekürzt…]');
  });
});
