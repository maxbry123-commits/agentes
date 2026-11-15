// Pure functions for hybrid memory retrieval.
// No DB dependencies — safe to import from tests without side-effects.

import type { MemoryEntry, MemoryLayer } from './types.js';

// ── Constants ───────────────────────────────────────────────────────────────

/** RRF constant k — prevents rank 1 from dominating. Higher = more democratic. */
const RRF_K = 60;

/** Default half-life for temporal decay in days. */
const DEFAULT_HALF_LIFE_DAYS = 7;

/** Milliseconds per day. */
const MS_PER_DAY = 24 * 60 * 60 * 1000;

// ── Tokenization ─────────────────────────────────────────────────────────────

const STOPWORDS = new Set([
  // EN
  'the', 'and', 'for', 'with', 'this', 'that', 'from', 'have', 'has', 'are', 'was',
  'were', 'will', 'would', 'should', 'could', 'into', 'task', 'tasks', 'about',
  'when', 'then', 'than', 'them', 'they', 'their', 'there', 'where', 'which',
  'while', 'after', 'before', 'over', 'such', 'some', 'each', 'also', 'just',
  'make', 'made', 'use', 'using', 'used', 'need', 'needs', 'work', 'works',
  // DE
  'der', 'die', 'das', 'den', 'dem', 'des', 'ein', 'eine', 'einen', 'einer',
  'und', 'oder', 'aber', 'auch', 'aus', 'bei', 'für', 'mit', 'von', 'zu',
  'ist', 'sind', 'war', 'waren', 'wird', 'werden', 'wurde', 'soll', 'sollte',
  'kann', 'könnte', 'muss', 'müssen', 'noch', 'nicht', 'nur', 'doch', 'sehr',
  'aufgabe', 'aufgaben', 'task', 'arbeit', 'tun', 'mache', 'machen',
]);

export function tokenize(text: string): string[] {
  if (!text) return [];
  return text
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s-]/gu, ' ')
    .split(/\s+/)
    .filter(t => t.length >= 3 && !STOPWORDS.has(t));
}

/** Compute BM25-like keyword overlap score between query and document. */
export function keywordOverlapScore(query: string, document: string): number {
  const qTokens = new Set(tokenize(query));
  if (qTokens.size === 0) return 0;
  const dTokens = tokenize(document);
  if (dTokens.length === 0) return 0;
  const dSet = new Set(dTokens);
  let hits = 0;
  for (const t of qTokens) {
    if (dSet.has(t)) hits++;
  }
  return hits / qTokens.size;
}

// ── Temporal Decay ───────────────────────────────────────────────────────────

/**
 * Apply exponential decay based on age.
 * score * 2^(-ageDays / halfLifeDays)
 */
export function applyTemporalDecay(
  score: number,
  ageDays: number,
  halfLifeDays: number = DEFAULT_HALF_LIFE_DAYS,
): number {
  if (ageDays <= 0) return score;
  if (halfLifeDays <= 0) return score;
  return score * Math.pow(2, -ageDays / halfLifeDays);
}

export function daysSince(isoDate: string, reference = new Date()): number {
  const then = new Date(isoDate);
  if (Number.isNaN(then.getTime())) return Infinity;
  const diffMs = reference.getTime() - then.getTime();
  return diffMs / MS_PER_DAY;
}

// ── Reciprocal Rank Fusion ───────────────────────────────────────────────────

/**
 * Fuse multiple ranked lists into a single ranking using RRF.
 * Each list is an array of item IDs in rank order (best first).
 */
export function reciprocalRankFusion(
  rankings: string[][],
  k: number = RRF_K,
): Map<string, number> {
  const scores = new Map<string, number>();

  for (const list of rankings) {
    for (let rank = 0; rank < list.length; rank++) {
      const id = list[rank];
      const current = scores.get(id) || 0;
      scores.set(id, current + 1 / (k + rank + 1));
    }
  }

  return scores;
}

// ── Hybrid Scoring ───────────────────────────────────────────────────────────

export interface ScoredEntry extends MemoryEntry {
  fusedScore: number;
}

/**
 * Compute hybrid scores for a collection of entries from different layers.
 *
 * Algorithm:
 * 1. Rank each layer independently by relevanceScore
 * 2. Fuse with RRF to get combined ranks
 * 3. Apply temporal decay to episodic memories
 * 4. Apply layer-specific boosts
 * 5. Normalize to 0-1 range
 */
export function computeHybridScores(
  entries: MemoryEntry[],
  options: {
    recencyBoost?: number;
    decayHalfLifeDays?: number;
    layerBoosts?: Partial<Record<MemoryLayer, number>>;
    now?: Date;
  } = {},
): ScoredEntry[] {
  const {
    recencyBoost = 0.5,
    decayHalfLifeDays = DEFAULT_HALF_LIFE_DAYS,
    layerBoosts = { working: 1.15, episodic: 1.05, semantic: 1.0 },
    now = new Date(),
  } = options;

  if (entries.length === 0) return [];

  // 1. Group by layer and create per-layer rankings (by relevanceScore)
  const byLayer = new Map<MemoryLayer, MemoryEntry[]>();
  for (const e of entries) {
    const list = byLayer.get(e.layer) || [];
    list.push(e);
    byLayer.set(e.layer, list);
  }

  const rankings: string[][] = [];
  for (const [, list] of byLayer) {
    const sorted = [...list].sort((a, b) => b.relevanceScore - a.relevanceScore);
    rankings.push(sorted.map(e => e.id));
  }

  // 2. RRF fusion scores
  const rrfScores = reciprocalRankFusion(rankings);

  // 3. Apply temporal decay + layer boosts
  const scored = entries.map(entry => {
    const rrf = rrfScores.get(entry.id) || 0;
    const ageDays = daysSince(entry.createdAt, now);
    const decayed = applyTemporalDecay(rrf, ageDays, decayHalfLifeDays);

    // Layer boost
    const boost = layerBoosts[entry.layer] || 1.0;

    // Episodic memories get extra recency boost
    const episodicBoost = entry.layer === 'episodic' ? (1 + recencyBoost) : 1.0;

    return {
      ...entry,
      temporalScore: decayed,
      fusedScore: decayed * boost * episodicBoost,
    };
  });

  // 4. Normalize to 0-1 (softmax-like: divide by max)
  const maxScore = Math.max(...scored.map(s => s.fusedScore), 1e-9);
  return scored
    .map(s => ({ ...s, fusedScore: s.fusedScore / maxScore }))
    .sort((a, b) => b.fusedScore - a.fusedScore);
}

// ── Deduplication ────────────────────────────────────────────────────────────

/**
 * Deduplicate entries by content similarity (simple Jaccard on token sets).
 * Keeps the highest-scored entry from each duplicate cluster.
 */
export function deduplicateEntries(
  entries: ScoredEntry[],
  threshold = 0.75,
): ScoredEntry[] {
  if (entries.length === 0) return [];

  const kept: ScoredEntry[] = [];

  for (const candidate of entries) {
    const cTokens = new Set(tokenize(candidate.content));
    if (cTokens.size === 0) {
      kept.push(candidate);
      continue;
    }

    let isDuplicate = false;
    for (const existing of kept) {
      const eTokens = new Set(tokenize(existing.content));
      if (eTokens.size === 0) continue;

      const intersection = new Set([...cTokens].filter(t => eTokens.has(t)));
      const union = new Set([...cTokens, ...eTokens]);
      const jaccard = intersection.size / union.size;

      if (jaccard >= threshold) {
        isDuplicate = true;
        break;
      }
    }

    if (!isDuplicate) {
      kept.push(candidate);
    }
  }

  return kept;
}

// ── Formatting ───────────────────────────────────────────────────────────────

/**
 * Format entries into a structured markdown block for prompt injection.
 * Groups by layer and includes relevance indicators.
 */
export function formatHierarchicalContext(
  entries: ScoredEntry[],
  options: { maxChars?: number; includeScores?: boolean } = {},
): string {
  const { maxChars = 12000, includeScores = false } = options;

  if (entries.length === 0) return '';

  const layerNames: Record<MemoryLayer, string> = {
    working: 'Aktueller Kontext',
    episodic: 'Letzte Erfahrungen',
    semantic: 'Gelerntes Wissen',
  };

  // Group by layer in priority order
  const layerOrder: MemoryLayer[] = ['working', 'episodic', 'semantic'];
  const byLayer = new Map<MemoryLayer, ScoredEntry[]>();
  for (const e of entries) {
    const list = byLayer.get(e.layer) || [];
    list.push(e);
    byLayer.set(e.layer, list);
  }

  const parts: string[] = ['--- HIERARCHICAL MEMORY RETRIEVAL ---'];
  let charCount = parts[0].length;

  for (const layer of layerOrder) {
    const layerEntries = byLayer.get(layer);
    if (!layerEntries || layerEntries.length === 0) continue;

    const header = `\n## ${layerNames[layer]} (${layerEntries.length})\n`;
    parts.push(header);
    charCount += header.length;

    for (const entry of layerEntries) {
      const scoreTag = includeScores ? ` [${(entry.fusedScore * 100).toFixed(0)}%]` : '';
      const metaTag = entry.classification ? ` (${entry.classification})` : '';
      const entityTag = entry.entityTags?.length ? ` [${entry.entityTags.join(', ')}]` : '';

      let line = `- ${entry.content.slice(0, 400)}${entry.content.length > 400 ? '…' : ''}${scoreTag}${metaTag}${entityTag}`;

      // Hard char limit
      if (charCount + line.length + 2 > maxChars) {
        parts.push('\n[…weitere Einträge gekürzt…]');
        return parts.join('');
      }

      parts.push(line);
      charCount += line.length + 1;
    }
  }

  parts.push('\n--- END MEMORY ---');
  return parts.join('\n');
}
