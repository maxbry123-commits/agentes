// Pure functions for automatic memory classification & entity extraction.
// No DB dependencies — fully deterministic heuristics.

import type { MemoryClass, AutoIndexResult } from './types.js';

// ── Classification Heuristics ────────────────────────────────────────────────

const DECISION_MARKERS = new Set([
  'decided', 'decision', 'beschlossen', 'entschieden', 'beschluss',
  'chose', 'chosen', 'gewählt', 'ausgewählt', 'wird verwendet',
  'going with', 'settled on', 'finalized', 'approved', 'rejected',
]);

const ACTION_MARKERS = new Set([
  'created', 'updated', 'deleted', 'implemented', 'fixed', 'refactored',
  'erstellt', 'aktualisiert', 'gelöscht', 'implementiert', 'behoben',
  'wrote', 'wrote a', 'schrieb', 'gebaut', 'deployed', 'merged',
  'added', 'removed', 'configured', 'installed', 'set up',
]);

const FACT_MARKERS = new Set([
  'is a', 'are a', 'consists of', 'contains', 'supports', 'requires',
  'ist ein', 'sind', 'besteht aus', 'enthält', 'unterstützt', 'benötigt',
  'equals', 'equivalent to', 'defined as', 'the value is', 'default is',
]);

const RELATIONSHIP_MARKERS = new Set([
  'reports to', 'depends on', 'blocked by', 'parent of', 'child of',
  'related to', 'links to', 'connected to', 'references', 'uses',
  'berichtet an', 'abhängig von', 'blockiert durch', 'verwendet',
]);

const SKILL_MARKERS = new Set([
  'how to', 'recipe', 'pattern', 'template', 'best practice',
  'step by step', 'guide', 'tutorial', 'workaround', 'solution for',
  'wie man', 'schritt für schritt', 'anleitung', 'rezept', 'muster',
]);

function countMarkers(text: string, markers: Set<string>): number {
  const lower = text.toLowerCase();
  let count = 0;
  for (const m of markers) {
    if (lower.includes(m.toLowerCase())) count++;
  }
  return count;
}

/**
 * Heuristic classification of memory content.
 * Returns the most likely class + confidence score.
 */
export function classifyMemory(text: string): { classification: MemoryClass; confidence: number } {
  if (!text || text.length < 10) {
    return { classification: 'observation', confidence: 0.3 };
  }

  const scores: Record<MemoryClass, number> = {
    decision: countMarkers(text, DECISION_MARKERS),
    action: countMarkers(text, ACTION_MARKERS),
    fact: countMarkers(text, FACT_MARKERS),
    relationship: countMarkers(text, RELATIONSHIP_MARKERS),
    skill: countMarkers(text, SKILL_MARKERS),
    observation: 0,
  };

  // Normalize by text length (longer texts can accumulate more hits)
  const lengthFactor = Math.min(text.length / 500, 1);
  for (const k of Object.keys(scores) as MemoryClass[]) {
    if (k === 'observation') continue;
    scores[k] = scores[k] > 0 ? scores[k] / (1 + lengthFactor) : 0;
  }

  // Default observation gets a small baseline
  scores.observation = 0.2;

  // Find best
  let best: MemoryClass = 'observation';
  let bestScore = scores.observation;
  for (const [k, v] of Object.entries(scores) as [MemoryClass, number][]) {
    if (v > bestScore) {
      bestScore = v;
      best = k;
    }
  }

  // Confidence: how much does the winner lead?
  const runnerUp = Object.entries(scores)
    .filter(([k]) => k !== best)
    .sort((a, b) => b[1] - a[1])[0]?.[1] || 0;

  const confidence = Math.min(bestScore / (runnerUp + 0.5), 1);

  return { classification: best, confidence };
}

// ── Entity Extraction ────────────────────────────────────────────────────────

/**
 * Simple heuristic entity extraction: capitalized phrases, quoted strings,
 * and camelCase/ snake_case identifiers that look like names.
 */
export function extractEntities(text: string): string[] {
  if (!text) return [];

  const entities = new Set<string>();

  // Quoted strings
  const quoted = text.match(/"([^"]{2,60})"/g) || [];
  for (const q of quoted) {
    entities.add(q.slice(1, -1).trim());
  }

  // Capitalized multi-word phrases (likely names)
  const capitalized = text.match(/\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4}\b/g) || [];
  for (const c of capitalized) {
    if (c.length > 3 && !c.startsWith('The ') && !c.startsWith('This ')) {
      entities.add(c.trim());
    }
  }

  // snake_case identifiers (likely IDs or roles)
  const snakeIds = text.match(/\b[a-z]+_[a-z_]{2,30}\b/g) || [];
  for (const s of snakeIds) {
    if (!['is_a', 'are_a', 'the_', 'and_'].some(p => s.startsWith(p))) {
      entities.add(s);
    }
  }

  // camelCase / PascalCase identifiers
  const camelIds = text.match(/\b[A-Z][a-z]+[A-Z][a-zA-Z]{2,30}\b/g) || [];
  for (const c of camelIds) {
    entities.add(c);
  }

  // URL-like patterns
  const urls = text.match(/\bhttps?:\/\/[^\s]{5,80}\b/g) || [];
  for (const u of urls) {
    entities.add(u);
  }

  // Technical terms (backtick quoted)
  const codeTerms = text.match(/`([^`]{2,40})`/g) || [];
  for (const t of codeTerms) {
    entities.add(t.slice(1, -1).trim());
  }

  return [...entities].filter(e => e.length >= 2 && e.length <= 80).slice(0, 15);
}

// ── Tag Suggestion ───────────────────────────────────────────────────────────

/**
 * Suggest tags based on content classification + entities.
 */
export function suggestTags(text: string, classification?: MemoryClass): string[] {
  const tags: string[] = [];

  if (classification) {
    tags.push(`type:${classification}`);
  }

  const entities = extractEntities(text);
  for (const e of entities.slice(0, 8)) {
    const normalized = e.toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '').slice(0, 30);
    if (normalized.length >= 3) {
      tags.push(`entity:${normalized}`);
    }
  }

  // Topic heuristics
  const lower = text.toLowerCase();
  const topicKeywords: [string, string[]][] = [
    ['api', ['api', 'endpoint', 'rest', 'graphql']],
    ['frontend', ['frontend', 'react', 'vue', 'angular', 'component', 'ui']],
    ['backend', ['backend', 'server', 'express', 'fastapi', 'database']],
    ['database', ['database', 'sql', 'sqlite', 'postgres', 'schema', 'migration']],
    ['auth', ['auth', 'login', 'jwt', 'session', 'permission']],
    ['deployment', ['deploy', 'docker', 'kubernetes', 'ci/cd', 'pipeline']],
    ['testing', ['test', 'testing', 'jest', 'vitest', 'cypress', 'playwright']],
    ['design', ['design', 'figma', 'ui/ux', 'mockup', 'prototype']],
    ['security', ['security', 'vulnerability', 'xss', 'csrf', 'sanitize']],
  ];

  for (const [topic, keywords] of topicKeywords) {
    if (keywords.some(k => lower.includes(k))) {
      tags.push(`topic:${topic}`);
    }
  }

  return [...new Set(tags)].slice(0, 12);
}

// ── Unified Auto-Index ───────────────────────────────────────────────────────

/**
 * Run the full auto-index pipeline on a piece of text.
 * Returns classification, entities, suggested tags, and confidence.
 */
export function autoIndex(text: string): AutoIndexResult {
  const { classification, confidence } = classifyMemory(text);
  const entityTags = extractEntities(text);
  const tags = suggestTags(text, classification);

  return {
    classification,
    entityTags,
    suggestedLinks: tags,
    confidence,
  };
}

/**
 * Determine if two memories should be cross-linked based on entity overlap.
 */
export function shouldLink(
  textA: string,
  textB: string,
  threshold = 0.3,
): boolean {
  const entitiesA = new Set(extractEntities(textA).map(e => e.toLowerCase()));
  const entitiesB = new Set(extractEntities(textB).map(e => e.toLowerCase()));

  if (entitiesA.size === 0 || entitiesB.size === 0) return false;

  let intersection = 0;
  for (const e of entitiesA) {
    if (entitiesB.has(e)) intersection++;
  }

  const union = new Set([...entitiesA, ...entitiesB]).size;
  return intersection / union >= threshold;
}
