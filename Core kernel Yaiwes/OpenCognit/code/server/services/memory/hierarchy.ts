// Hierarchical Memory Query Engine
// Queries Working, Episodic, and Semantic layers in parallel, then fuses results.

import { db } from '../../db/client.js';
import {
  palaceWings, palaceDrawers, palaceDiary, palaceKg, palaceSummaries,
  memoryEmbeddings, learnedSkills, agents,
} from '../../db/schema.js';
import { eq, and, desc, isNull, sql } from 'drizzle-orm';

import type {
  MemoryEntry, MemoryLayer, HierarchicalRecallParams,
  HierarchicalRecallResult, LayerStats, AutoIndexResult,
} from './types.js';
import { autoIndex } from './auto-index-pure.js';
import {
  computeHybridScores, deduplicateEntries, formatHierarchicalContext,
  daysSince, keywordOverlapScore,
} from './hybrid-retrieval-pure.js';
import { cosineSimilarity } from '../semantic-memory-pure.js';

// ── Helpers ───────────────────────────────────────────────────────────────────

function nowIso() {
  return new Date().toISOString();
}

/** Derive simple hash-based embedding for fallback (no API key). */
function hashEmbedding(text: string, dims = 384): number[] {
  const vec = new Array(dims).fill(0);
  for (let i = 0; i < text.length; i++) {
    vec[i % dims] += text.charCodeAt(i) / 1000;
  }
  const mag = Math.sqrt(vec.reduce((s, v) => s + v * v, 0));
  return mag > 0 ? vec.map(v => v / mag) : vec;
}

// ── Layer Queries ─────────────────────────────────────────────────────────────

/**
 * Query WORKING memory: recent diary entries + latest consolidated summary.
 * These are the most contextually relevant for the current task.
 */
async function queryWorkingMemory(
  agentId: string,
  companyId: string,
  query: string,
  limit: number,
): Promise<{ entries: MemoryEntry[]; durationMs: number }> {
  const start = Date.now();
  const entries: MemoryEntry[] = [];

  try {
    const wing = db.select().from(palaceWings)
      .where(eq(palaceWings.agentId, agentId)).get();

    if (wing) {
      // Latest consolidated summary (highest relevance for current context)
      const summary = db.select().from(palaceSummaries)
        .where(eq(palaceSummaries.agentId, agentId))
        .orderBy(desc(palaceSummaries.version))
        .limit(1)
        .get();

      if (summary) {
        const relevance = keywordOverlapScore(query, summary.content);
        const idx = autoIndex(summary.content);
        entries.push({
          id: summary.id,
          layer: 'working',
          source: 'palaceSummary',
          agentId,
          companyId,
          content: summary.content.slice(0, 2000),
          createdAt: summary.updatedAt,
          relevanceScore: Math.max(relevance, 0.6), // summaries are inherently relevant
          classification: idx.classification,
          entityTags: idx.entityTags,
          meta: { version: summary.version, compressedTurns: summary.komprimierteTurns },
        });
      }

      // Recent diary entries (very fresh = working memory)
      const recentDiary = db.select().from(palaceDiary)
        .where(eq(palaceDiary.wingId, wing.id))
        .orderBy(desc(palaceDiary.createdAt))
        .limit(3)
        .all();

      for (const d of recentDiary) {
        const content = [d.thought, d.action, d.knowledge].filter(Boolean).join(' | ');
        if (!content) continue;
        const relevance = keywordOverlapScore(query, content);
        const idx = autoIndex(content);
        entries.push({
          id: d.id,
          layer: 'working',
          source: 'palaceDiary',
          agentId,
          companyId,
          content: content.slice(0, 1500),
          createdAt: d.createdAt,
          relevanceScore: relevance + (daysSince(d.createdAt) < 1 ? 0.2 : 0),
          classification: idx.classification,
          entityTags: idx.entityTags,
          meta: { datum: d.datum },
        });
      }
    }
  } catch (e: any) {
    console.warn(`[hierarchy.working] query failed: ${e?.message}`);
  }

  return { entries: entries.slice(0, limit), durationMs: Date.now() - start };
}

/**
 * Query EPISODIC memory: diary entries + drawers from the agent's wing.
 * Includes temporal scoring (recency matters).
 */
async function queryEpisodicMemory(
  agentId: string,
  companyId: string,
  query: string,
  limit: number,
): Promise<{ entries: MemoryEntry[]; durationMs: number }> {
  const start = Date.now();
  const entries: MemoryEntry[] = [];

  try {
    const wing = db.select().from(palaceWings)
      .where(eq(palaceWings.agentId, agentId)).get();

    if (wing) {
      // Diary entries beyond the most recent 3 (those go to Working)
      const diary = db.select().from(palaceDiary)
        .where(eq(palaceDiary.wingId, wing.id))
        .orderBy(desc(palaceDiary.createdAt))
        .limit(limit + 3)
        .all();

      for (let i = 3; i < diary.length; i++) {
        const d = diary[i];
        const content = [d.thought, d.action, d.knowledge].filter(Boolean).join(' | ');
        if (!content) continue;
        const relevance = keywordOverlapScore(query, content);
        const idx = autoIndex(content);
        entries.push({
          id: d.id,
          layer: 'episodic',
          source: 'palaceDiary',
          agentId,
          companyId,
          content: content.slice(0, 1500),
          createdAt: d.createdAt,
          relevanceScore: relevance,
          classification: idx.classification,
          entityTags: idx.entityTags,
          meta: { datum: d.datum },
        });
      }

      // Drawers (room-based storage)
      const drawers = db.select().from(palaceDrawers)
        .where(eq(palaceDrawers.wingId, wing.id))
        .orderBy(desc(palaceDrawers.createdAt))
        .limit(limit)
        .all();

      for (const d of drawers) {
        const relevance = keywordOverlapScore(query, d.content);
        const idx = autoIndex(d.content);
        entries.push({
          id: d.id,
          layer: 'episodic',
          source: 'palaceDrawer',
          agentId,
          companyId,
          content: d.content.slice(0, 1500),
          createdAt: d.createdAt,
          relevanceScore: relevance,
          classification: idx.classification,
          entityTags: idx.entityTags,
          meta: { room: d.room },
        });
      }
    }
  } catch (e: any) {
    console.warn(`[hierarchy.episodic] query failed: ${e?.message}`);
  }

  return { entries: entries.slice(0, limit), durationMs: Date.now() - start };
}

/**
 * Query SEMANTIC memory: vector search over memoryEmbeddings + learnedSkills.
 * Falls back to hash embeddings if no API key.
 */
async function querySemanticMemory(
  agentId: string,
  companyId: string,
  query: string,
  limit: number,
  apiKey?: string,
): Promise<{ entries: MemoryEntry[]; durationMs: number; queryEmbedding: number[] }> {
  const start = Date.now();
  const entries: MemoryEntry[] = [];

  // Generate query embedding (hash fallback if no API key)
  let queryEmbedding: number[];
  if (apiKey) {
    try {
      const resp = await fetch('https://openrouter.ai/api/v1/embeddings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiKey}`,
          'HTTP-Referer': 'https://opencognit.local',
          'X-Title': 'OpenCognit Hierarchical Memory',
        },
        body: JSON.stringify({
          model: 'openai/text-embedding-3-small',
          input: [query],
        }),
      });
      if (resp.ok) {
        const data = await resp.json() as any;
        queryEmbedding = data.data[0].embedding;
      } else {
        queryEmbedding = hashEmbedding(query);
      }
    } catch {
      queryEmbedding = hashEmbedding(query);
    }
  } else {
    queryEmbedding = hashEmbedding(query);
  }

  try {
    // ── Semantic chunks ───────────────────────────────────────────────────────
    const candidates = db.select({
      id: memoryEmbeddings.id,
      chunkText: memoryEmbeddings.chunkText,
      embeddingJson: memoryEmbeddings.embeddingJson,
      agentId: memoryEmbeddings.agentId,
      source: memoryEmbeddings.source,
      quelleId: memoryEmbeddings.quelleId,
      tags: memoryEmbeddings.tags,
      createdAt: memoryEmbeddings.createdAt,
    })
      .from(memoryEmbeddings)
      .where(eq(memoryEmbeddings.companyId, companyId))
      .all();

    const scoredChunks = candidates
      .map(c => {
        let embedding: number[];
        try {
          embedding = JSON.parse(c.embeddingJson) as number[];
        } catch {
          embedding = hashEmbedding(c.chunkText);
        }
        const similarity = cosineSimilarity(queryEmbedding, embedding);
        return { ...c, similarity };
      })
      .filter(c => c.similarity >= 0.25)
      .sort((a, b) => b.similarity - a.similarity)
      .slice(0, limit);

    for (const c of scoredChunks) {
      const idx = autoIndex(c.chunkText);
      entries.push({
        id: c.id,
        layer: 'semantic',
        source: 'semanticChunk',
        agentId: c.agentId,
        companyId,
        content: c.chunkText.slice(0, 1500),
        createdAt: c.createdAt,
        relevanceScore: c.similarity,
        classification: idx.classification,
        entityTags: idx.entityTags,
        meta: { source: c.source, quelleId: c.quelleId, tags: c.tags },
      });
    }

    // ── Learned skills ────────────────────────────────────────────────────────
    const skills = db.select().from(learnedSkills)
      .where(eq(learnedSkills.companyId, companyId))
      .orderBy(desc(learnedSkills.lastUsedAt))
      .limit(limit)
      .all();

    for (const skill of skills) {
      const skillText = `${skill.title || ''} ${skill.pattern || ''} ${skill.recipe || ''}`;
      const relevance = keywordOverlapScore(query, skillText);
      if (relevance < 0.1) continue;
      const idx = autoIndex(skillText);
      entries.push({
        id: skill.id,
        layer: 'semantic',
        source: 'learnedSkill',
        agentId: null,
        companyId,
        content: skill.recipe?.slice(0, 1500) || skill.pattern?.slice(0, 1500) || skill.title || '',
        createdAt: skill.createdAt,
        relevanceScore: relevance,
        classification: 'skill',
        entityTags: idx.entityTags,
        meta: { title: skill.title, pattern: skill.pattern, useCount: skill.useCount },
      });
    }
  } catch (e: any) {
    console.warn(`[hierarchy.semantic] query failed: ${e?.message}`);
  }

  return { entries: entries.slice(0, limit), durationMs: Date.now() - start, queryEmbedding };
}

/**
 * Query KNOWLEDGE GRAPH: temporal facts related to the agent or company.
 */
async function queryKnowledgeGraph(
  agentId: string,
  companyId: string,
  query: string,
  limit: number,
): Promise<{ entries: MemoryEntry[]; durationMs: number }> {
  const start = Date.now();
  const entries: MemoryEntry[] = [];

  try {
    const agent = db.select({ name: agents.name }).from(agents)
      .where(eq(agents.id, agentId)).get();
    const agentName = agent?.name?.toLowerCase() || '';

    const facts = db.select().from(palaceKg)
      .where(and(
        eq(palaceKg.companyId, companyId),
        isNull(palaceKg.validUntil),
      ))
      .all();

    // Score by keyword overlap with query AND agent name
    const scored = facts.map(f => {
      const content = `${f.subject} → ${f.predicate} → ${f.object}`;
      let relevance = keywordOverlapScore(query, content);
      if (agentName && f.subject.toLowerCase().includes(agentName)) {
        relevance += 0.15;
      }
      return { fact: f, relevance, content };
    })
      .filter(s => s.relevance > 0.05)
      .sort((a, b) => b.relevance - a.relevance)
      .slice(0, limit);

    for (const s of scored) {
      const idx = autoIndex(s.content);
      entries.push({
        id: s.fact.id,
        layer: 'semantic',
        source: 'palaceKg',
        agentId: null,
        companyId,
        content: s.content,
        createdAt: s.fact.createdAt,
        relevanceScore: s.relevance,
        classification: idx.classification === 'observation' ? 'relationship' : idx.classification,
        entityTags: [s.fact.subject, s.fact.object].filter(Boolean),
        meta: { predicate: s.fact.predicate, validFrom: s.fact.validFrom },
      });
    }
  } catch (e: any) {
    console.warn(`[hierarchy.kg] query failed: ${e?.message}`);
  }

  return { entries: entries.slice(0, limit), durationMs: Date.now() - start };
}

// ── Public API ────────────────────────────────────────────────────────────────

/**
 * Hierarchical recall — queries all memory layers, fuses with RRF + temporal decay,
 * deduplicates, and formats as structured markdown.
 */
export async function hierarchicalRecall(
  params: HierarchicalRecallParams,
): Promise<HierarchicalRecallResult> {
  const {
    agentId, companyId, query,
    layers = ['working', 'episodic', 'semantic'],
    perLayerLimit = 8,
    topK = 10,
    recencyBoost = 0.5,
    decayHalfLifeDays = 7,
    minScore = 0.15,
    crossLink = true,
    apiKey,
  } = params;

  const overallStart = Date.now();
  const stats: LayerStats[] = [];
  let allEntries: MemoryEntry[] = [];
  let queryEmbedding: number[] | undefined;

  // Query layers in parallel
  const promises: Promise<void>[] = [];

  if (layers.includes('working')) {
    promises.push(
      queryWorkingMemory(agentId, companyId, query, perLayerLimit).then(r => {
        stats.push({ layer: 'working', queried: perLayerLimit, returned: r.entries.length, durationMs: r.durationMs });
        allEntries = allEntries.concat(r.entries);
      }),
    );
  }

  if (layers.includes('episodic')) {
    promises.push(
      queryEpisodicMemory(agentId, companyId, query, perLayerLimit).then(r => {
        stats.push({ layer: 'episodic', queried: perLayerLimit, returned: r.entries.length, durationMs: r.durationMs });
        allEntries = allEntries.concat(r.entries);
      }),
    );
  }

  if (layers.includes('semantic')) {
    promises.push(
      querySemanticMemory(agentId, companyId, query, perLayerLimit, apiKey).then(r => {
        stats.push({ layer: 'semantic', queried: perLayerLimit, returned: r.entries.length, durationMs: r.durationMs });
        allEntries = allEntries.concat(r.entries);
        queryEmbedding = r.queryEmbedding;
      }),
    );
    // Also include KG in semantic layer
    promises.push(
      queryKnowledgeGraph(agentId, companyId, query, perLayerLimit).then(r => {
        stats.push({ layer: 'semantic', queried: perLayerLimit, returned: r.entries.length, durationMs: r.durationMs });
        allEntries = allEntries.concat(r.entries);
      }),
    );
  }

  await Promise.all(promises);

  // Fusion + ranking
  const scored = computeHybridScores(allEntries, { recencyBoost, decayHalfLifeDays });
  const filtered = scored.filter(s => s.fusedScore >= minScore);
  const deduped = deduplicateEntries(filtered);
  const topEntries = deduped.slice(0, topK);

  // Cross-linking
  if (crossLink && topEntries.length > 1) {
    for (let i = 0; i < topEntries.length; i++) {
      const entry = topEntries[i];
      const linked: string[] = [];
      for (let j = 0; j < topEntries.length; j++) {
        if (i === j) continue;
        const other = topEntries[j];
        // Link if same entity tag overlap
        if (entry.entityTags?.some(t => other.entityTags?.includes(t))) {
          linked.push(other.id);
        }
      }
      if (linked.length > 0) {
        entry.linkedIds = [...new Set(linked)].slice(0, 5);
      }
    }
  }

  const totalDurationMs = Date.now() - overallStart;

  // Log summary
  const layerCounts = new Map<MemoryLayer, number>();
  for (const e of topEntries) {
    layerCounts.set(e.layer, (layerCounts.get(e.layer) || 0) + 1);
  }
  console.log(
    `[HierarchicalMemory] query="${query.slice(0, 40)}…" ` +
    `layers=[${layers.join(',')}] total=${allEntries.length} ` +
    `fused=${topEntries.length} ` +
    `(${[...layerCounts.entries()].map(([l, c]) => `${l}:${c}`).join(',')}) ` +
    `in ${totalDurationMs}ms`
  );

  return {
    contextMarkdown: formatHierarchicalContext(topEntries),
    entries: topEntries,
    stats,
    totalDurationMs,
    queryEmbedding,
  };
}

// ── Store with auto-indexing ─────────────────────────────────────────────────

/**
 * Store a memory entry with automatic classification and entity extraction.
 * Currently stores into palaceDrawers (episodic layer) with indexed metadata.
 */
export async function storeWithAutoIndex(
  agentId: string,
  companyId: string,
  content: string,
  room = 'auto_indexed',
): Promise<{ drawerId: string; index: AutoIndexResult }> {
  const wing = db.select().from(palaceWings)
    .where(eq(palaceWings.agentId, agentId)).get();

  if (!wing) {
    throw new Error(`No wing found for agent ${agentId}`);
  }

  const index = autoIndex(content);

  const { v4: uuid } = await import('uuid');
  const id = uuid();
  const now = nowIso();

  db.insert(palaceDrawers).values({
    id,
    wingId: wing.id,
    room,
    content,
    createdAt: now,
  }).run();

  db.update(palaceWings).set({ updatedAt: now }).where(eq(palaceWings.id, wing.id)).run();

  console.log(`[AutoIndex] stored drawer ${id.slice(0, 8)} ` +
    `class=${index.classification} conf=${(index.confidence * 100).toFixed(0)}% ` +
    `entities=[${index.entityTags.slice(0, 5).join(',')}]`);

  return { drawerId: id, index };
}
