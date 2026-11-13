// =============================================================================
// MemoryService — unified API for agent memory.
//
// Inspired by Cognee's `remember / recall / forget / improve` shape, but
// implemented as a thin facade over our existing services (palace_*,
// learnedSkills, semantic-memory). The point isn't to introduce a new
// memory backend — it's to give consumers ONE entry point so they don't
// have to know which underlying store holds what.
// =============================================================================

// ── Recall ───────────────────────────────────────────────────────────────────

export interface RecallParams {
  /** The agent doing the recall (used for palace + per-agent skills). */
  agentId: string;
  /** Company scope (used for cross-agent learned skills + KG). */
  companyId: string;
  /**
   * Free-text query used to rank/filter memory entries. Typically the task
   * title + description, but could be any natural-language anchor.
   */
  query: string;
  /**
   * Pre-tokenized keywords. If omitted, derived from `query`. Provided for
   * the legacy palace-memory path which expects a pre-built keyword list.
   */
  keywords?: string[];
  /** Restrict which backends contribute. Defaults: all true. */
  scope?: {
    palace?: boolean;
    learnedSkills?: boolean;
    semantic?: boolean;
  };
  /** Per-source limits. */
  limits?: {
    learnedSkills?: number;
  };
}

export interface RecallResult {
  /**
   * Combined Markdown block, ready to drop into a system prompt. Empty
   * string when no source produced anything.
   */
  contextMarkdown: string;
  /** What each source contributed — useful for observability + debugging. */
  sources: {
    palaceContext: boolean;
    learnedSkills: number;
  };
}

// ── Remember ─────────────────────────────────────────────────────────────────

export interface RememberParams {
  agentId: string;
  companyId: string;
  /** Raw agent output / message — extractor decides what to keep. */
  output: string;
  /** Human-readable title for the source event (task title, meeting title…). */
  title: string;
  taskId?: string;
  runId?: string;
  /**
   * What kind of event triggered this. Affects which extractor runs:
   * - 'task_done'      → autoSaveInsights + queue learned-skill extraction
   * - 'meeting_result' → saveMeetingResult fan-out
   * - 'manual'         → just store, no extraction
   */
  kind: 'task_done' | 'meeting_result' | 'manual';
}

// ── Forget ───────────────────────────────────────────────────────────────────

export type ForgetTarget =
  | { type: 'learnedSkill'; id: string }
  | { type: 'palaceDrawer'; id: string }
  | { type: 'palaceDiary'; id: string }
  | { type: 'kgFact'; id: string };

// ── Improve ──────────────────────────────────────────────────────────────────

export interface ImproveParams {
  companyId: string;
  /** Limit the consolidation pass to specific subsystems. Defaults: all. */
  scope?: {
    wings?: boolean;
    learnedSkills?: boolean;
  };
}

export interface ImproveResult {
  consolidatedWings: number;
  /** Reserved for future learned-skill dedup pass. */
  deduplicatedSkills: number;
}

// =============================================================================
// Hierarchical Memory Engine Types (Phase 1)
// =============================================================================

/** Memory layer classification — matches cognitive architecture. */
export type MemoryLayer = 'working' | 'episodic' | 'semantic';

/** Auto-classified memory type — helps retrieval and formatting. */
export type MemoryClass = 'fact' | 'decision' | 'action' | 'observation' | 'skill' | 'relationship';

/** A single unified memory entry, normalized from any underlying store. */
export interface MemoryEntry {
  id: string;
  layer: MemoryLayer;
  source: 'palaceDiary' | 'palaceDrawer' | 'palaceKg' | 'palaceSummary' | 'semanticChunk' | 'learnedSkill';
  agentId: string | null;
  companyId: string;
  content: string;
  createdAt: string; // ISO 8601
  /** Semantic relevance score (0-1) from vector similarity or keyword overlap. */
  relevanceScore: number;
  /** Recency-boosted score after temporal decay is applied. */
  temporalScore?: number;
  /** Final fused score after RRF + hybrid ranking. */
  fusedScore?: number;
  /** Auto-extracted classification. */
  classification?: MemoryClass;
  /** Auto-extracted entity tags (subject, object names). */
  entityTags?: string[];
  /** Links to related memory IDs (cross-layer references). */
  linkedIds?: string[];
  /** Raw source metadata (room name, predicate, etc). */
  meta?: Record<string, unknown>;
}

/** Extended recall parameters for hierarchical retrieval. */
export interface HierarchicalRecallParams {
  agentId: string;
  companyId: string;
  query: string;
  /** Which layers to query. Default: all three. */
  layers?: MemoryLayer[];
  /** Max entries per layer before fusion. */
  perLayerLimit?: number;
  /** Max final entries after fusion. */
  topK?: number;
  /** Boost factor for recent memories (0 = no boost, 1 = strong boost). Default: 0.5. */
  recencyBoost?: number;
  /** Half-life in days for temporal decay. Default: 7. */
  decayHalfLifeDays?: number;
  /** Minimum fused score to include (0-1). Default: 0.15. */
  minScore?: number;
  /** Include cross-layer entity linking in output. Default: true. */
  crossLink?: boolean;
  /** Optional API key for embedding generation. */
  apiKey?: string;
}

/** Per-layer statistics for observability. */
export interface LayerStats {
  layer: MemoryLayer;
  queried: number;
  returned: number;
  durationMs: number;
}

/** Result of a hierarchical recall — structured for both prompt injection and debugging. */
export interface HierarchicalRecallResult {
  contextMarkdown: string;
  entries: MemoryEntry[];
  stats: LayerStats[];
  totalDurationMs: number;
  queryEmbedding?: number[];
}

/** Auto-indexing result — what was classified and linked. */
export interface AutoIndexResult {
  classification: MemoryClass;
  entityTags: string[];
  suggestedLinks: string[];
  confidence: number; // 0-1 heuristic confidence
}
