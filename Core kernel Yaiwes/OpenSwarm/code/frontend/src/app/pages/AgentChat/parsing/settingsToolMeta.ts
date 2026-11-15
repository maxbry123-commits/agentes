// Render an agent's SettingsWrite/SettingsRead so the transcript shows WHAT it touched at a glance, with secrets masked. The agent's raw `changes` input can carry a key it's trying to set, and the generic MCP renderer would paint it; a settings value is the one new place a secret could land on screen, so it's the one place we mask. Mirrors the backend's name rule (redaction.is_secret_field).

const SECRET_NAME_RE = /_(key|token|secret)$/i;
// Narrow, prefix-anchored so it can't mask a long path or system prompt (those have slashes/spaces); it only catches a real key pasted into a non-secret field.
const KEYISH_VALUE_RE = /^(sk-|sk-ant-|AIza|ghp_|gho_|github_pat_|xox[baprs]-)/;

export function isSettingsWriteTool(toolName: string): boolean {
  return /__SettingsWrite$/.test(toolName);
}
export function isSettingsReadTool(toolName: string): boolean {
  return /__SettingsRead$/.test(toolName);
}

function isSecretField(name: string): boolean {
  return SECRET_NAME_RE.test(name) || name === 'installation_id';
}

function maskValue(key: string, value: unknown, cap: number): string {
  if (isSecretField(key)) return '••••';
  if (typeof value === 'string') {
    if (KEYISH_VALUE_RE.test(value.trim())) return '••••';
    return value.length > cap ? value.slice(0, cap) + '…' : value;
  }
  if (value === null || value === undefined) return 'none';
  return JSON.stringify(value);
}

const LABELS: Record<string, string> = {
  default_model: 'Default model',
  default_mode: 'Default mode',
  default_system_prompt: 'System prompt',
  default_thinking_level: 'Thinking level',
  default_max_turns: 'Max turns',
  default_folder: 'Default folder',
  theme: 'Theme',
  browser_homepage: 'Browser homepage',
  new_agent_shortcut: 'New-agent shortcut',
  zoom_sensitivity: 'Zoom sensitivity',
};

function humanizeKey(key: string): string {
  return LABELS[key] || key.replace(/_/g, ' ').replace(/^\w/, (ch) => ch.toUpperCase());
}

interface SettingsChangeRow {
  label: string;
  value: string;
}

function settingsChangeRows(input: unknown, cap: number): SettingsChangeRow[] {
  const changes = (input as { changes?: unknown })?.changes;
  if (!changes || typeof changes !== 'object') return [];
  return Object.entries(changes as Record<string, unknown>)
    // some models tack a free-form 'reason' onto the args; it isn't a setting.
    .filter(([k]) => k !== 'reason')
    .map(([k, v]) => ({ label: humanizeKey(k), value: maskValue(k, v, cap) }));
}

/** One-line header preview, e.g. "Theme → Light · Default model → Sonnet". */
export function settingsWriteSummary(input: unknown): string {
  return settingsChangeRows(input, 40).map((r) => `${r.label} → ${r.value}`).join(' · ');
}

/** Expanded body: one masked change per line. Replaces the raw-JSON render. */
export function settingsWriteDisplay(input: unknown): string {
  const rows = settingsChangeRows(input, 200);
  return rows.length === 0 ? 'No changes.' : rows.map((r) => `${r.label}: ${r.value}`).join('\n');
}
