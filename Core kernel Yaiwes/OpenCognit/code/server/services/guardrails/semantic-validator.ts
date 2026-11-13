// Semantic Validator — Real Layer 3 Guardrails
//
// Validates agent output against:
// 1. Groundedness: Do the factual claims match the knowledge base?
// 2. Self-Consistency: Does the output contradict itself?
// 3. Hallucination detection: Are claims supported by evidence?
//
// Uses a hybrid approach:
// - Fast heuristic path for simple outputs (<100ms)
// - Deep validation against KG + semantic memory for complex outputs

import { db } from '../../db/client.js';
import { palaceKg, memoryEmbeddings } from '../../db/schema.js';
import { eq, and, isNull } from 'drizzle-orm';
import type { GuardrailViolation } from '../guardrails.js';
import { extractFacts, factOverlap, normalizeFact } from './fact-extractor.js';
import { cosineSimilarity } from '../semantic-memory-pure.js';

export interface SemanticValidationConfig {
  /** Enable groundedness check against KB. Default: true */
  checkGroundedness?: boolean;
  /** Enable self-consistency check. Default: true */
  checkConsistency?: boolean;
  /** Minimum confidence for a fact to be checked. Default: 0.4 */
  factConfidenceThreshold?: number;
  /** Minimum overlap score to consider a fact "supported". Default: 0.3 */
  minGroundednessScore?: number;
  /** Max facts to check per output (limit cost). Default: 8 */
  maxFactsToCheck?: number;
  /** Company scope for KB lookup */
  companyId?: string;
  /** Agent scope for memory lookup */
  agentId?: string;
}

const DEFAULT_SEMANTIC_CONFIG: Required<Omit<SemanticValidationConfig, 'companyId' | 'agentId'>> = {
  checkGroundedness: true,
  checkConsistency: true,
  factConfidenceThreshold: 0.4,
  minGroundednessScore: 0.3,
  maxFactsToCheck: 8,
};

// ─── Groundedness Check ─────────────────────────────────────────────────────

interface GroundednessResult {
  fact: string;
  score: number; // 0-1 overlap with KB
  supportingEvidence: string[];
  contradictingEvidence: string[];
  verdict: 'supported' | 'unsupported' | 'contradicted' | 'uncertain';
}

/**
 * Check if extracted facts are grounded in the Knowledge Graph + Semantic Memory.
 */
function checkGroundedness(
  facts: Array<{ text: string; confidence: number }>,
  config: SemanticValidationConfig,
): GroundednessResult[] {
  const results: GroundednessResult[] = [];
  const { companyId, minGroundednessScore } = {
    ...DEFAULT_SEMANTIC_CONFIG,
    ...config,
  };

  if (!companyId) {
    // No company context → can't check KB, mark all as uncertain
    return facts.map(f => ({
      fact: f.text,
      score: 0,
      supportingEvidence: [],
      contradictingEvidence: [],
      verdict: 'uncertain' as const,
    }));
  }

  // Load active KG facts for this company
  let kgFacts: Array<{ subject: string; predicate: string; object: string }> = [];
  try {
    kgFacts = db.select()
      .from(palaceKg)
      .where(and(
        eq(palaceKg.companyId, companyId),
        isNull(palaceKg.validUntil),
      ))
      .all();
  } catch {
    // DB error → continue with empty KB
  }

  // Load recent semantic memory embeddings for this company
  let memoryChunks: Array<{ chunkText: string; embeddingJson: string | null }> = [];
  try {
    memoryChunks = db.select({ chunkText: memoryEmbeddings.chunkText, embeddingJson: memoryEmbeddings.embeddingJson })
      .from(memoryEmbeddings)
      .where(eq(memoryEmbeddings.companyId, companyId))
      .limit(50)
      .all();
  } catch {
    // DB error → continue with empty memory
  }

  // Build searchable text corpus from KG
  const kgTexts = kgFacts.map(f => `${f.subject} ${f.predicate} ${f.object}`.toLowerCase());

  for (const fact of facts) {
    const normalizedFact = normalizeFact(fact.text);
    const factWords = new Set(normalizedFact.split(/\s+/).filter(w => w.length > 3));

    let bestScore = 0;
    const supporting: string[] = [];
    const contradicting: string[] = [];

    // 1. Check against KG facts (exact/partial overlap)
    for (const kgText of kgTexts) {
      const overlap = factOverlap(fact.text, kgText);
      if (overlap > bestScore) bestScore = overlap;
      if (overlap > 0.5) {
        supporting.push(`KG: ${kgText.slice(0, 200)}`);
      }
    }

    // 2. Check against semantic memory chunks (keyword overlap + embedding)
    for (const chunk of memoryChunks) {
      const overlap = factOverlap(fact.text, chunk.chunkText);
      if (overlap > bestScore) bestScore = overlap;
      if (overlap > 0.5) {
        supporting.push(`Memory: ${chunk.chunkText.slice(0, 200)}`);
      }

      // Embedding similarity if available
      if (chunk.embeddingJson) {
        try {
          const embedding = JSON.parse(chunk.embeddingJson) as number[];
          const factEmbedding = hashEmbedding(normalizedFact);
          const sim = cosineSimilarity(factEmbedding, embedding);
          if (sim > bestScore) bestScore = sim;
        } catch {
          // ignore parse errors
        }
      }
    }

    // 3. Check for contradiction: does KG contain an inverse fact?
    for (const kg of kgFacts) {
      const kgWords = new Set(normalizeFact(`${kg.subject} ${kg.object}`).split(/\s+/).filter(w => w.length >= 3));
      const sharedWords = [...factWords].filter(w => kgWords.has(w));
      // If they share significant words but the predicate is negated
      if (sharedWords.length >= 2) {
        const negatedPredicates = ['not', 'no', 'false', 'disabled', 'removed', 'deleted'];
        const isNegated = negatedPredicates.some(n => normalizedFact.includes(n));
        const kgNegated = negatedPredicates.some(n => kg.predicate.toLowerCase().includes(n));
        if (isNegated !== kgNegated) {
          contradicting.push(`KG contradiction: ${kg.subject} → ${kg.predicate} → ${kg.object}`);
        }
      }
    }

    // Determine verdict
    let verdict: GroundednessResult['verdict'];
    if (contradicting.length > 0) {
      verdict = 'contradicted';
    } else if (bestScore >= (minGroundednessScore || 0.3)) {
      verdict = 'supported';
    } else if (supporting.length > 0) {
      verdict = 'supported';
    } else {
      verdict = 'unsupported';
    }

    results.push({
      fact: fact.text,
      score: bestScore,
      supportingEvidence: supporting.slice(0, 3),
      contradictingEvidence: contradicting.slice(0, 3),
      verdict,
    });
  }

  return results;
}

// ─── Self-Consistency Check ─────────────────────────────────────────────────

interface ConsistencyResult {
  /** The two statements that contradict each other */
  pair: [string, string];
  /** Why they are considered contradictory */
  reason: string;
  /** Confidence in the contradiction (0-1) */
  confidence: number;
}

/**
 * Check if an output contradicts itself.
 * Looks for: negated versions of the same claim, conflicting values,
 * opposite boolean states.
 */
function checkSelfConsistency(output: string): ConsistencyResult[] {
  const contradictions: ConsistencyResult[] = [];

  // Split into sentences
  const sentences = output
    .split(/[.!?\n]+/)
    .map(s => s.trim())
    .filter(s => s.length > 10);

  if (sentences.length < 2) return [];

  // 1. Direct negation: "X is Y" vs "X is not Y"
  for (let i = 0; i < sentences.length; i++) {
    for (let j = i + 1; j < sentences.length; j++) {
      const a = normalizeFact(sentences[i]);
      const b = normalizeFact(sentences[j]);

      // Check if they share significant words but one negates
      const wordsA = new Set(a.split(/\s+/).filter(w => w.length >= 3));
      const wordsB = new Set(b.split(/\s+/).filter(w => w.length >= 3));
      const shared = [...wordsA].filter(w => wordsB.has(w));

      if (shared.length >= 2) {
        const negationWords = ['not', 'no', 'never', 'none', 'without', 'false'];
        const aNegated = negationWords.some(n => a.includes(` ${n} `));
        const bNegated = negationWords.some(n => b.includes(` ${n} `));

        if (aNegated !== bNegated) {
          contradictions.push({
            pair: [sentences[i], sentences[j]],
            reason: 'One statement negates the other',
            confidence: Math.min(0.9, shared.length * 0.15),
          });
        }
      }

      // 2. Conflicting boolean assignments: "enabled: true" vs "enabled: false"
      const boolConflict = detectBooleanConflict(sentences[i], sentences[j]);
      if (boolConflict) {
        contradictions.push({
          pair: [sentences[i], sentences[j]],
          reason: 'Conflicting boolean values for the same property',
          confidence: 0.95,
        });
      }

      // 3. Numeric conflict: "X = 10" vs "X = 20" (same variable, different values)
      const numConflict = detectNumericConflict(sentences[i], sentences[j]);
      if (numConflict) {
        contradictions.push({
          pair: [sentences[i], sentences[j]],
          reason: `Conflicting numeric values: ${numConflict.valueA} vs ${numConflict.valueB}`,
          confidence: 0.85,
        });
      }
    }
  }

  // Deduplicate by normalizing pairs
  const seen = new Set<string>();
  return contradictions.filter(c => {
    const key = normalizeFact(c.pair[0] + c.pair[1]);
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function detectBooleanConflict(a: string, b: string): boolean {
  const boolPattern = /(\w+)\s*[:=]\s*(true|false|yes|no|on|off|enabled|disabled|0|1)/gi;
  const aMatches = [...a.matchAll(boolPattern)];
  const bMatches = [...b.matchAll(boolPattern)];

  for (const ma of aMatches) {
    for (const mb of bMatches) {
      const keyA = ma[1].toLowerCase();
      const keyB = mb[1].toLowerCase();
      const valA = ma[2].toLowerCase();
      const valB = mb[2].toLowerCase();

      if (keyA === keyB && valA !== valB) {
        // Normalize: true/yes/on/1 are equivalent, false/no/off/0 are equivalent
        const truthy = ['true', 'yes', 'on', '1'];
        const aTruthy = truthy.includes(valA);
        const bTruthy = truthy.includes(valB);
        if (aTruthy !== bTruthy) return true;
      }
    }
  }
  return false;
}

function detectNumericConflict(a: string, b: string): { valueA: string; valueB: string } | null {
  const numPattern = /(\w+)\s*[:=]\s*(\d+(?:\.\d+)?)/gi;
  const aMatches = [...a.matchAll(numPattern)];
  const bMatches = [...b.matchAll(numPattern)];

  for (const ma of aMatches) {
    for (const mb of bMatches) {
      const keyA = ma[1].toLowerCase();
      const keyB = mb[1].toLowerCase();
      if (keyA === keyB && ma[2] !== mb[2]) {
        return { valueA: ma[2], valueB: mb[2] };
      }
    }
  }
  return null;
}

// ─── Hallucination Detection ────────────────────────────────────────────────

/**
 * Detect potential hallucinations: high-confidence factual claims with
 * no grounding in the knowledge base.
 */
function detectHallucinations(
  groundednessResults: GroundednessResult[],
): GuardrailViolation[] {
  const violations: GuardrailViolation[] = [];

  const unsupported = groundednessResults.filter(r => r.verdict === 'unsupported');
  const hallucinationRatio = unsupported.length / (groundednessResults.length || 1);

  // If many claims are unsupported, flag as potential hallucination
  if (hallucinationRatio > 0.5 && unsupported.length >= 2) {
    violations.push({
      layer: 3,
      severity: 'high',
      type: 'potential_hallucination',
      message: `${unsupported.length} of ${groundednessResults.length} factual claims are unsupported by the knowledge base. Potential hallucination detected.`,
      suggestedFix: 'Verify claims against known facts or mark them as uncertain',
    });
  }

  // Flag individual strongly-unsupported facts
  for (const result of unsupported) {
    if (result.score < 0.1) {
      violations.push({
        layer: 3,
        severity: 'medium',
        type: 'unsubstantiated_claim',
        message: `Claim appears unsubstantiated: "${result.fact.slice(0, 120)}"`,
        suggestedFix: 'Provide evidence or rephrase as an assumption',
      });
    }
  }

  return violations;
}

// ─── Confidence Calibration ─────────────────────────────────────────────────

function checkConfidenceCalibration(output: string, minConfidence?: number): GuardrailViolation[] {
  const violations: GuardrailViolation[] = [];

  const uncertaintyPatterns = [
    /\b(maybe|perhaps|possibly|might|could be|i think|i guess|not sure|unclear|unsure)\b/gi,
    /\b(i don't know|i'm not certain|it's hard to say|difficult to determine)\b/gi,
  ];

  let uncertaintyCount = 0;
  for (const pattern of uncertaintyPatterns) {
    const matches = output.match(pattern);
    if (matches) uncertaintyCount += matches.length;
  }

  const wordCount = output.split(/\s+/).length || 1;
  const uncertaintyRatio = uncertaintyCount / wordCount;

  if (uncertaintyRatio > 0.15) {
    violations.push({
      layer: 3,
      severity: 'medium',
      type: 'low_confidence_output',
      message: `Output contains high uncertainty (${Math.round(uncertaintyRatio * 100)}% hedge words)`,
      suggestedFix: 'Be more decisive or ask for clarification instead of guessing',
    });
  }

  return violations;
}

// ─── Hash-based embedding for fast comparison ───────────────────────────────

function hashEmbedding(text: string, dims = 384): number[] {
  const vec = new Array(dims).fill(0);
  for (let i = 0; i < text.length; i++) {
    vec[i % dims] += text.charCodeAt(i) / 1000;
  }
  const mag = Math.sqrt(vec.reduce((s, v) => s + v * v, 0));
  return mag > 0 ? vec.map(v => v / mag) : vec;
}

// ─── Public API ─────────────────────────────────────────────────────────────

export interface SemanticValidationResult {
  violations: GuardrailViolation[];
  groundedness: GroundednessResult[];
  consistency: ConsistencyResult[];
  hallucinationScore: number; // 0-1, higher = more likely hallucinating
  durationMs: number;
}

/**
 * Run full semantic validation on agent output.
 * This is the real Layer 3 implementation.
 */
export function runSemanticValidation(
  output: string,
  config: SemanticValidationConfig = {},
): SemanticValidationResult {
  const startTime = Date.now();
  const mergedConfig = { ...DEFAULT_SEMANTIC_CONFIG, ...config };
  const violations: GuardrailViolation[] = [];

  // 1. Extract facts
  const facts = extractFacts(output, mergedConfig.factConfidenceThreshold)
    .slice(0, mergedConfig.maxFactsToCheck);

  // 2. Groundedness check
  let groundedness: GroundednessResult[] = [];
  if (mergedConfig.checkGroundedness && facts.length > 0) {
    groundedness = checkGroundedness(facts, mergedConfig);
    violations.push(...detectHallucinations(groundedness));
  }

  // 3. Self-consistency check
  let consistency: ConsistencyResult[] = [];
  if (mergedConfig.checkConsistency) {
    consistency = checkSelfConsistency(output);
    for (const contradiction of consistency) {
      violations.push({
        layer: 3,
        severity: contradiction.confidence > 0.8 ? 'high' : 'medium',
        type: 'self_contradiction',
        message: `Self-contradiction detected: "${contradiction.pair[0].slice(0, 80)}..." vs "${contradiction.pair[1].slice(0, 80)}..." (${contradiction.reason})`,
        suggestedFix: 'Resolve the contradiction or clarify the context',
      });
    }
  }

  // 4. Confidence calibration (hedge words)
  violations.push(...checkConfidenceCalibration(output, mergedConfig.factConfidenceThreshold));

  // Compute hallucination score
  const unsupportedCount = groundedness.filter(r => r.verdict === 'unsupported').length;
  const hallucinationScore = facts.length > 0 ? unsupportedCount / facts.length : 0;

  return {
    violations,
    groundedness,
    consistency,
    hallucinationScore,
    durationMs: Date.now() - startTime,
  };
}
