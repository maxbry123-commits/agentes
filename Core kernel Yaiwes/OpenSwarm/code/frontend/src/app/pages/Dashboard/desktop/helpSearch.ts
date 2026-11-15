/**
 * Ranking for the Help panel's offline answers: pure functions over the knowledge payload, no
 * imports, so the app, the tests, and any future surface all score a query identically.
 */

export interface HelpTopic {
  id: string;
  title: string;
  where: string;
  body: string;
  keywords: string[];
}

export interface HelpKnownIssue {
  id: string;
  title: string;
  status: 'known' | 'mitigated' | 'fixed';
  detail: string;
  workaround?: string | null;
}

export interface HelpShortcut {
  keys: string;
  action: string;
}

export interface HelpKnowledge {
  system_prompt: string;
  topics: HelpTopic[];
  known_issues: HelpKnownIssue[];
  shortcuts: HelpShortcut[];
  app_version: string;
}

export interface HelpMatch {
  id: string;
  title: string;
  detail: string;
}

// Words that match everything and so mean nothing; without them "change the theme" hits every entry.
const STOPWORDS = new Set([
  'the', 'a', 'an', 'and', 'or', 'of', 'in', 'on', 'for', 'to', 'is', 'are', 'was', 'be', 'it',
  'my', 'me', 'i', 'you', 'your', 'do', 'does', 'did', 'how', 'what', 'where', 'when', 'why',
  'can', 'get', 'got', 'with', 'from', 'that', 'this', 'any', 'all', 'use', 'using',
]);

function stem(word: string): string {
  return word.length > 3 && word.endsWith('s') ? word.slice(0, -1) : word;
}

// Whole-word matching on stems, so "card" still finds "cards" but "every" stops matching "everything".
function wordSet(text: string): Set<string> {
  const out = new Set<string>();
  for (const w of text.toLowerCase().split(/[^a-z0-9]+/)) {
    if (w) out.add(stem(w));
  }
  return out;
}

function hits(words: Set<string>, terms: string[]): number {
  let n = 0;
  for (const t of terms) if (words.has(t)) n += 1;
  return n;
}

/** Instant local answers: no model, no network, still works when no provider is connected. */
export function searchHelp(knowledge: HelpKnowledge | null, query: string, limit = 3): HelpMatch[] {
  if (!knowledge || query.trim().length < 2) return [];
  const terms = [...wordSet(query)].filter((t) => t.length > 1 && !STOPWORDS.has(t));
  if (terms.length === 0) return [];

  const scored: Array<{ score: number; match: HelpMatch }> = [];
  for (const topic of knowledge.topics) {
    const score =
      hits(wordSet(topic.title), terms) * 6 +
      hits(wordSet(topic.keywords.join(' ')), terms) * 4 +
      hits(wordSet(`${topic.body} ${topic.where}`), terms);
    if (score > 0) {
      scored.push({
        score,
        match: { id: topic.id, title: topic.title, detail: topic.where ? `${topic.where} ${topic.body}` : topic.body },
      });
    }
  }
  // Shortcuts rank in the same list rather than jumping the queue, so a key only leads when the
  // question is actually about that key.
  for (const s of knowledge.shortcuts) {
    const score = hits(wordSet(s.action), terms) * 5;
    if (score > 0) scored.push({ score, match: { id: `shortcut-${s.keys}`, title: s.keys, detail: s.action } });
  }

  return scored.sort((a, b) => b.score - a.score).slice(0, limit).map((s) => s.match);
}
