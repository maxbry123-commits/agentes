// Fact Extractor — Heuristic extraction of factual claims from agent output.
//
// Identifies sentences that make objective claims (facts, figures, names,
// dates, technical specs) that should be checked against the knowledge base.
//
// Strategy: Score each sentence. High-scoring sentences are factual claims.

export interface ExtractedFact {
  /** The original sentence */
  text: string;
  /** Start index in the original text */
  startIndex: number;
  /** End index */
  endIndex: number;
  /** Confidence that this is a factual claim (0-1) */
  confidence: number;
  /** Detected entity types in this fact */
  entityTypes: string[];
}

// ─── Heuristic Scoring ───────────────────────────────────────────────────────

/** Patterns that strongly indicate factual claims */
const FACT_INDICATORS = [
  // Numbers with units
  /\b\d+\s*(?:%|px|em|rem|ms|s|min|hr|GB|MB|KB|€|\$|°[CF])\b/i,
  // Version numbers
  /\b(?:v?\d+\.\d+(?:\.\d+)?)\b/,
  // Dates
  /\b(?:\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{4}-\d{2}-\d{2})\b/,
  // Absolute file paths
  /\/(?:[\w-]+\/)*[\w-]+(?:\.[a-z]+)?/,
  // URLs
  /https?:\/\/[^\s]+/,
  // Specific technical terms that imply facts
  /\b(?:requires|supports|uses|implements|extends|default is|equals|set to|configured as|runs on|listens on|located at|upgraded from)\b/i,
  // Keyword + number pairs (e.g. "port 3000", "timeout 5000")
  /\b(?:port|timeout|limit|count|size|version|id|key|token|page)\s+\d+\b/i,
  // Named entities (capitalized multi-word)
  /\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}\b/,
  // Code identifiers in backticks
  /`[^`]+`/,
  // Bullet points with facts
  /^\s*[-*•]\s+\w+.*[:=]/m,
];

/** Patterns that indicate opinion / speculation (negative signals) */
const OPINION_INDICATORS = [
  /\b(?:I think|I believe|maybe|perhaps|possibly|might|could be|in my opinion|I suggest|I recommend)\b/i,
  /\b(?:should|could|would|may|might want to)\b/i,
  /\?\s*$/, // questions
];

/** Entity type detection via regex heuristics */
const ENTITY_PATTERNS: Array<{ type: string; regex: RegExp }> = [
  { type: 'version', regex: /\bv?\d+\.\d+(?:\.\d+)?\b/ },
  { type: 'date', regex: /\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b/ },
  { type: 'number', regex: /\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b/ },
  { type: 'percentage', regex: /\b\d+(?:\.\d+)?%\b/ },
  { type: 'url', regex: /https?:\/\/[^\s]+/ },
  { type: 'file_path', regex: /\/(?:[\w-]+\/)*[\w-]+\.[a-z]+/ },
  { type: 'email', regex: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/ },
  { type: 'code_term', regex: /`[^`]+`/ },
  { type: 'config_value', regex: /(?:=|:)\s*["']?[^"'\s]{2,}["']?/ },
];

function scoreSentence(sentence: string): { score: number; entityTypes: string[] } {
  let score = 0.1; // baseline
  const entityTypes = new Set<string>();

  // Positive signals
  for (const pattern of FACT_INDICATORS) {
    const matches = sentence.match(pattern);
    if (matches) {
      score += 0.15 * matches.length;
    }
  }

  // Entity detection
  for (const { type, regex } of ENTITY_PATTERNS) {
    if (regex.test(sentence)) {
      entityTypes.add(type);
      score += 0.1;
    }
  }

  // Negative signals
  for (const pattern of OPINION_INDICATORS) {
    if (pattern.test(sentence)) {
      score -= 0.2;
    }
  }

  // Length penalty: very short sentences are less likely to be meaningful facts
  if (sentence.length < 20) score -= 0.1;
  // Length bonus: longer sentences with structure are more likely factual
  if (sentence.length > 60) score += 0.05;

  return { score: Math.max(0, Math.min(1, score)), entityTypes: [...entityTypes] };
}

function splitIntoSentences(text: string): Array<{ text: string; start: number; end: number }> {
  // Mask entities that contain periods to prevent false sentence splits
  const masks: Array<{ start: number; end: number }> = [];
  const entityRegexes = [
    /https?:\/\/[^\s]+/g,               // URLs
    /\bv?\d+\.\d+(?:\.\d+)?\b/g,        // Versions
    /\/(?:[\w-]+\/)*[\w-]+(?:\.[a-z]+)?/g, // File paths
    /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g, // Emails
  ];

  for (const regex of entityRegexes) {
    let m;
    while ((m = regex.exec(text)) !== null) {
      masks.push({ start: m.index, end: m.index + m[0].length });
    }
  }
  masks.sort((a, b) => a.start - b.start);

  // Replace '.' inside masked entity ranges with null char so they don't
  // trigger false sentence boundaries. Length is preserved so indices stay valid.
  let maskedText = text;
  for (const mask of masks) {
    const segment = text.slice(mask.start, mask.end);
    const maskedSegment = segment.replace(/\./g, '\u0000');
    maskedText = maskedText.slice(0, mask.start) + maskedSegment + maskedText.slice(mask.end);
  }

  const sentences: Array<{ text: string; start: number; end: number }> = [];
  const regex = /[^.!?\n]+[.!?\n]+/g;
  let match;
  while ((match = regex.exec(maskedText)) !== null) {
    const raw = match[0].trim();
    if (raw.length > 5) {
      // Unmask periods and compute bounds in original text
      const sentenceText = raw.replace(/\u0000/g, '.');
      sentences.push({ text: sentenceText, start: match.index, end: match.index + match[0].length });
    }
  }

  // Catch any trailing text without terminator
  const lastEnd = sentences.length > 0 ? sentences[sentences.length - 1].end : 0;
  const trailing = maskedText.slice(lastEnd).trim();
  if (trailing.length > 5) {
    sentences.push({ text: trailing.replace(/\u0000/g, '.'), start: lastEnd, end: text.length });
  }

  return sentences;
}

// ─── Public API ──────────────────────────────────────────────────────────────

/**
 * Extract factual claims from agent output.
 * Returns sentences that appear to state objective facts.
 */
export function extractFacts(text: string, minConfidence = 0.35): ExtractedFact[] {
  if (!text || text.length < 10) return [];

  const sentences = splitIntoSentences(text);
  const facts: ExtractedFact[] = [];

  for (const sent of sentences) {
    const { score, entityTypes } = scoreSentence(sent.text);
    if (score >= minConfidence) {
      facts.push({
        text: sent.text,
        startIndex: sent.start,
        endIndex: sent.end,
        confidence: score,
        entityTypes,
      });
    }
  }

  // Sort by confidence descending, keep top N
  return facts.sort((a, b) => b.confidence - a.confidence);
}

/**
 * Quick check: does the text contain any high-confidence factual claims?
 */
export function hasFacts(text: string): boolean {
  return extractFacts(text, 0.5).length > 0;
}

/**
 * Normalize a fact for comparison (lowercase, remove punctuation, sort words).
 */
export function normalizeFact(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s]/gu, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

/**
 * Compute simple overlap between two facts (0-1).
 */
export function factOverlap(a: string, b: string): number {
  const normA = normalizeFact(a);
  const normB = normalizeFact(b);

  const tokensA = new Set(normA.split(/\s+/).filter(t => t.length > 2));
  const tokensB = new Set(normB.split(/\s+/).filter(t => t.length > 2));

  if (tokensA.size === 0 || tokensB.size === 0) return 0;

  const intersection = new Set([...tokensA].filter(t => tokensB.has(t)));
  const union = new Set([...tokensA, ...tokensB]);

  return intersection.size / union.size;
}
