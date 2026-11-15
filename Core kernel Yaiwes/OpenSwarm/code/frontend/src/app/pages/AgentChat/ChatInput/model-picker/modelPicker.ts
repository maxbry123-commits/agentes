// Mirrors SubscriptionCard colors in Settings.
export const PROVIDER_COLORS: Record<string, string> = {
  anthropic: '#E8927A',
  openai: '#74AA9C',
  google: '#4285F4',
  gemini: '#4285F4',
  xai: '#8B949E',
  meta: '#0866FF',
  deepseek: '#4D6BFE',
  mistral: '#FF7000',
  qwen: '#A974FF',
  cohere: '#FF7759',
  openrouter: '#64748B',
};

export const LS_RECENT_MODELS = 'openswarm.picker.recentModels';
export const LS_RECENT_SEARCHES = 'openswarm.picker.recentSearches';
export const RECENT_MODELS_MAX = 3;
export const RECENT_SEARCHES_MAX = 4;
export const OR_AUTO_COLLAPSE_THRESHOLD = 12;

export const LS_FILTERS_EXPANDED = 'openswarm.picker.filtersExpanded';
export const LS_COLLAPSED_GROUPS = 'openswarm.picker.collapsedGroups';

export const CTX_STEPS = [0, 32_000, 128_000, 200_000, 500_000, 1_000_000];
export const CTX_LABELS = ['Any', '32K+', '128K+', '200K+', '500K+', '1M+'];
export const COST_STEPS = [Infinity, 50, 15, 5, 1, 0];
export const COST_LABELS = ['Any', '≤$50/M', '≤$15/M', '≤$5/M', '≤$1/M', 'Free only'];

export function readLS<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

export function writeLS(key: string, value: unknown) {
  try { localStorage.setItem(key, JSON.stringify(value)); } catch {}
}

// Heuristic tiering for pre-load FALLBACK_MODELS only; backend provides real tiers post-load.
export type Tier = 1 | 2 | 3 | 4 | 5;
const clampTier = (n: number): Tier => Math.max(1, Math.min(5, n)) as Tier;

function _costBucket(out: number): Tier {
  if (out < 0.5) return 1;
  if (out < 2) return 2;
  if (out < 7) return 3;
  if (out < 25) return 4;
  return 5;
}

export function tierIntelligence(opt: any): Tier {
  let tier: number = _costBucket(opt.output_cost_per_1m ?? 0);
  if (opt.reasoning) tier += 1;
  return clampTier(tier);
}

export function tierSpeed(opt: any): Tier {
  let tier: number = 6 - _costBucket(opt.output_cost_per_1m ?? 0);
  if (opt.reasoning) tier -= 1;
  const lower = String(opt.label || '').toLowerCase();
  if (/\b(mini|lite|flash|haiku|nano|small|fast|turbo|micro|tiny)\b/.test(lower)) tier += 1;
  if (/\b(opus|ultra|max|xlarge|titan)\b/.test(lower)) tier -= 1;
  return clampTier(tier);
}

export function tierCost(opt: any): Tier {
  return _costBucket(opt.output_cost_per_1m ?? 0);
}

/** Extract version number from a model label; clamps to <30 to skip param counts like 70B/120B. */
function modelVersion(label: string): number {
  const matches = String(label).matchAll(/(\d+(?:\.\d+)?)/g);
  let bestVersion = 0;
  for (const m of matches) {
    const v = parseFloat(m[1]);
    if (v >= 0.5 && v < 30 && v > bestVersion) bestVersion = v;
  }
  return bestVersion;
}

/** Strip versions and route suffixes so "Claude Sonnet 4.6" and 4.5 share one key. */
function modelFamilyKey(label: string): string {
  return String(label)
    .toLowerCase()
    .replace(/\b\d+(?:\.\d+)?\b/g, '')
    .replace(/\(api key\)/gi, '')
    .replace(/\s+/g, ' ')
    .trim();
}

/** Sort: version desc FIRST (the newest release always tops its provider group), then intelligence desc, family asc, label asc. */
export function sortModelsForPicker<T extends { label: string }>(models: T[]): T[] {
  const intelOf = (opt: any): number => {
    if (Array.isArray(opt.tiers) && opt.tiers.length === 3) return opt.tiers[0];
    return tierIntelligence(opt);
  };
  return [...models].sort((a: any, b: any) => {
    const verA = modelVersion(a.label);
    const verB = modelVersion(b.label);
    if (verA !== verB) return verB - verA;
    const intelA = intelOf(a);
    const intelB = intelOf(b);
    if (intelA !== intelB) return intelB - intelA;
    const famA = modelFamilyKey(a.label);
    const famB = modelFamilyKey(b.label);
    if (famA !== famB) return famA.localeCompare(famB);
    return a.label.localeCompare(b.label);
  });
}

// The three billing tiers the picker groups by, in the order they render (Eric 2026-08-09): your
// own subscriptions first, your own API keys second, pass-through routers last, never interleaved.
export type ModelTier = 'subscription' | 'api_key' | 'router';
export const TIER_ORDER: ModelTier[] = ['subscription', 'api_key', 'router'];
export const TIER_LABELS: Record<ModelTier, string> = {
  subscription: 'Subscriptions',
  api_key: 'API keys',
  router: 'Routers',
};

/** A provider group's tier: OpenRouter/router prefixes are routers; otherwise the group's dominant
 * billing_kind (subscription rows win ties so a mixed group sorts with the subs). */
export function groupTier(prov: string, models: Array<{ billing_kind?: string }>): ModelTier {
  if (/^(openrouter|router)\b/i.test(prov) || prov.includes('·')) return 'router';
  if (models.some((m) => m.billing_kind === 'subscription' || m.billing_kind === 'free')) return 'subscription';
  return 'api_key';
}

/** Reorder group entries into subscription -> api_key -> router, keeping each provider's existing
 * order within its tier. The one place tier order is decided, so headers and list can't drift. */
export function orderGroupsByTier(
  grouped: Record<string, Array<{ billing_kind?: string }>>,
): Array<[string, Array<any>, ModelTier]> {
  const entries = Object.entries(grouped).map(
    ([prov, models]) => [prov, models, groupTier(prov, models as any[])] as [string, any[], ModelTier],
  );
  return entries.sort((a, b) => TIER_ORDER.indexOf(a[2]) - TIER_ORDER.indexOf(b[2]));
}

// Superseded generations we no longer surface in the picker; the ids still work if saved as a default.
const DEPRECATED_PATTERNS: RegExp[] = [
  /\bgpt[-_ ]?[34](\b|o|\.|-)/,
  /\bo[134](?:[-_ ]?(mini|pro|preview))?\b/,
  /claude[-_ ]?(1|2|3)(\b|\.|-)/,
  /claude[-_ ]?instant/,
  /gemini[-_ ]?1\./,
  /\bllama[-_ ]?[23]\b/,
  /\b(davinci|curie|babbage|palm|bison)\b/,
];

export function isDeprecatedModel(label: string, value: string): boolean {
  const hay = `${label} ${value}`.toLowerCase();
  return DEPRECATED_PATTERNS.some((re) => re.test(hay));
}
