// Lenient wire-payload validation for vendored tool-ui components: strict zod parse first, then
// mechanical repairs for the mistakes agents actually make, re-validated so a repair can flip
// fail->pass but never corrupt a valid payload.

export type Gate =
  | { state: 'pending' }
  | { state: 'ok'; parsed: Record<string, unknown> }
  | { state: 'bad'; problem: string };

function slugFor(label: unknown, i: number): string {
  const t = typeof label === 'string' ? label.trim().toLowerCase().replace(/\s+/g, '-').slice(0, 40) : '';
  return t || `item-${i + 1}`;
}

// Agents write "+12%", "1,204", "$40" where schemas want a number; strip the dressing and parse.
function numFrom(v: unknown): number | null {
  if (typeof v === 'number' && Number.isFinite(v)) return v;
  if (typeof v === 'string') {
    const n = parseFloat(v.replace(/[+,%$\s]/g, ''));
    return Number.isFinite(n) ? n : null;
  }
  return null;
}

// Mechanical repairs for the mistakes agents actually make (numeric ids, ranked priorities, nested
// row objects, bare action objects). Only ever applied when the strict parse FAILED, and the result
// is re-validated, so a repair can flip fail->pass but never corrupt a valid payload.
function repairCommonAgentShapes(props: Record<string, unknown>): Record<string, unknown> {
  let out: Record<string, unknown>;
  try {
    out = JSON.parse(JSON.stringify(props ?? {}, (_k, v) => (v === undefined ? null : v)));
  } catch {
    return props;
  }
  const fixIdLabel = (arr: unknown): unknown => {
    if (!Array.isArray(arr)) return arr;
    return arr.map((o, i) => {
      if (typeof o === 'string') return { id: slugFor(o, i), label: o };
      if (o && typeof o === 'object' && !Array.isArray(o)) {
        const obj = { ...(o as Record<string, unknown>) };
        // Agents reach for value/name/key and title/text as synonyms; honor them before inventing a slug.
        if (obj.id == null || obj.id === '') obj.id = obj.value ?? obj.key ?? obj.name ?? null;
        if (obj.id == null || obj.id === '') obj.id = slugFor(obj.label ?? obj.title ?? obj.text, i);
        else if (typeof obj.id !== 'string') obj.id = String(obj.id);
        if (typeof obj.label !== 'string' || !obj.label) obj.label = String(obj.label ?? obj.title ?? obj.text ?? obj.name ?? obj.id);
        return obj;
      }
      return o;
    });
  };
  const dedupeIds = (arr: unknown): unknown => {
    if (!Array.isArray(arr)) return arr;
    const seen = new Map<string, number>();
    return arr.map((o) => {
      if (!o || typeof o !== 'object' || Array.isArray(o)) return o;
      const obj = o as Record<string, unknown>;
      if (typeof obj.id !== 'string') return o;
      const count = (seen.get(obj.id) ?? 0) + 1;
      seen.set(obj.id, count);
      return count === 1 ? o : { ...obj, id: `${obj.id}-${count}` };
    });
  };
  const STATUS_SYNONYMS: Record<string, string> = { in_progress: 'in-progress', active: 'in-progress', running: 'in-progress', done: 'completed', complete: 'completed', error: 'failed', todo: 'pending', waiting: 'pending' };
  const fixStepStatus = (arr: unknown): unknown => {
    if (!Array.isArray(arr)) return arr;
    return arr.map((o) => {
      if (!o || typeof o !== 'object' || Array.isArray(o)) return o;
      const obj = o as Record<string, unknown>;
      const mapped = STATUS_SYNONYMS[String(obj.status ?? '').toLowerCase()];
      return mapped ? { ...obj, status: mapped } : o;
    });
  };
  if ('options' in out) out.options = fixIdLabel(out.options);
  if ('steps' in out) out.steps = fixStepStatus(dedupeIds(fixIdLabel(out.steps)));
  if ('todos' in out) out.todos = dedupeIds(fixIdLabel(out.todos));
  if (Array.isArray(out.stats)) {
    out.stats = out.stats.map((s, i) => {
      if (!s || typeof s !== 'object' || Array.isArray(s)) return s;
      const st = { ...(s as Record<string, unknown>) };
      if (typeof st.key !== 'string' || !st.key) st.key = typeof st.id === 'string' && st.id ? st.id : slugFor(st.label ?? st.name ?? st.title, i);
      if (typeof st.label !== 'string' || !st.label) st.label = String(st.name ?? st.title ?? st.key);
      if (st.diff != null && typeof st.diff !== 'object') st.diff = { value: st.diff };
      if (st.diff && typeof st.diff === 'object' && !Array.isArray(st.diff)) {
        const d = { ...(st.diff as Record<string, unknown>) };
        const n = numFrom(d.value);
        if (n === null) delete st.diff;
        else { d.value = n; st.diff = d; }
      }
      return st;
    });
  }
  const RECEIPT_OUTCOMES: Record<string, string> = { success: 'success', confirmed: 'success', ok: 'success', done: 'success', complete: 'success', completed: 'success', sent: 'success', partial: 'partial', failed: 'failed', error: 'failed', failure: 'failed', cancelled: 'cancelled', canceled: 'cancelled' };
  const receipt = out.receipt as Record<string, unknown> | null | undefined;
  if (receipt && typeof receipt === 'object' && !Array.isArray(receipt)) {
    const fixed = { ...receipt };
    const outcome = RECEIPT_OUTCOMES[String(fixed.outcome ?? '').toLowerCase()];
    if (outcome) fixed.outcome = outcome;
    const t = typeof fixed.at === 'string' ? Date.parse(fixed.at) : NaN;
    if (!Number.isNaN(t)) fixed.at = new Date(t).toISOString();
    // A receipt that still can't validate costs the optional chip, never the whole widget.
    if (!outcome || Number.isNaN(t)) delete out.receipt;
    else out.receipt = fixed;
  }
  if ('actions' in out) {
    if (out.actions && !Array.isArray(out.actions) && typeof out.actions === 'object' && 'label' in (out.actions as object)) out.actions = [out.actions];
    out.actions = fixIdLabel(out.actions);
  }
  const PRIORITY_SYNONYMS: Record<string, string> = { '1': 'primary', '2': 'secondary', '3': 'tertiary', high: 'primary', medium: 'secondary', low: 'tertiary', primary: 'primary', secondary: 'secondary', tertiary: 'tertiary' };
  if (Array.isArray(out.columns)) {
    out.columns = out.columns.map((c) => {
      if (c && typeof c === 'object' && 'priority' in (c as object)) {
        const mapped = PRIORITY_SYNONYMS[String((c as Record<string, unknown>).priority).toLowerCase()];
        const copy = { ...(c as Record<string, unknown>) };
        if (mapped) copy.priority = mapped; else delete copy.priority;
        return copy;
      }
      return c;
    });
  }
  if (Array.isArray(out.data)) {
    // Row arrays (instead of keyed objects) zip against the column keys, in order.
    const colKeys = Array.isArray(out.columns)
      ? (out.columns as Array<Record<string, unknown>>).map((c, i) => String((c && typeof c === 'object' ? (c.key ?? c.id ?? c.label) : c) ?? `col${i + 1}`))
      : null;
    out.data = out.data.map((row) => {
      if (Array.isArray(row) && colKeys && colKeys.length > 0) {
        return Object.fromEntries(row.map((v, i) => [colKeys[i] ?? `col${i + 1}`, v]));
      }
      if (!row || typeof row !== 'object' || Array.isArray(row)) return row;
      return Object.fromEntries(Object.entries(row as Record<string, unknown>).map(([k, v]) => {
        if (v !== null && typeof v === 'object' && !Array.isArray(v)) return [k, JSON.stringify(v)];
        if (Array.isArray(v)) return [k, v.map((x) => (x !== null && typeof x === 'object' ? JSON.stringify(x) : x))];
        return [k, v];
      }));
    });
  }
  return out;
}

// Drop top-level keys the schema rejects (models pad payloads with invented ones) and reparse.
// Runs even when OTHER issues coexist, so a payload with extra keys AND a repairable shape can
// still be saved by the repair pass instead of failing on the first problem it happens to hit.
function stripUnrecognizedKeys(props: Record<string, unknown>, issues: Array<{ code: string; keys?: string[] }>): Record<string, unknown> | null {
  const unrecognized = issues.filter((i) => i.code === 'unrecognized_keys');
  if (unrecognized.length === 0) return null;
  const cleaned: Record<string, unknown> = { ...props };
  for (const issue of unrecognized) {
    for (const key of issue.keys || []) delete cleaned[key];
  }
  return cleaned;
}

export function parseLeniently(schema: { safeParse: (v: unknown) => any }, props: Record<string, unknown>): Gate {
  let result = schema.safeParse(props);
  let base: Record<string, unknown> = props;
  if (!result.success) {
    const cleaned = stripUnrecognizedKeys(props, result.error.issues);
    if (cleaned) {
      base = cleaned;
      result = schema.safeParse(cleaned);
    }
  }
  if (!result.success) {
    const repairedBase = repairCommonAgentShapes(base);
    let repaired = schema.safeParse(repairedBase);
    if (!repaired.success) {
      const cleaned = stripUnrecognizedKeys(repairedBase, repaired.error.issues);
      if (cleaned) repaired = schema.safeParse(cleaned);
    }
    if (repaired.success) return { state: 'ok', parsed: repaired.data as Record<string, unknown> };
  }
  if (result.success) return { state: 'ok', parsed: result.data as Record<string, unknown> };
  const issues = result.error.issues.slice(0, 2).map((i: { path: Array<string | number>; message: string }) => `${i.path.join('.')}: ${i.message}`).join('; ');
  return { state: 'bad', problem: issues };
}
