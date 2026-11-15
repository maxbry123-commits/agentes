// The app-side SDK: call the OpenSwarm host (your tools, workflows, models, agents) from app
// frontend code. The auth token rides in the preview URL (?token=), injected by the host; every
// helper resolves it lazily so importing this file never throws. See SDK.md for the guide.

const HOST = 'http://localhost:8324';

function hostToken(): string {
  try {
    return new URLSearchParams(window.location.search).get('token') ?? '';
  } catch {
    return '';
  }
}

async function hostFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${hostToken()}`,
    ...(init?.headers as Record<string, string> | undefined),
  };
  const res = await fetch(`${HOST}${path}`, { ...init, headers });
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new Error(`OpenSwarm host ${path} -> ${res.status}: ${body.slice(0, 300)}`);
  }
  return res.json() as Promise<T>;
}

export interface LlmOptions {
  system?: string;
  /** Short model name (sonnet, haiku, ...). Omit for the cheap tier of the user's provider. */
  model?: string;
  maxTokens?: number;
}

/** One-shot completion through the user's own configured providers/subscription. */
export async function llm(prompt: string, opts: LlmOptions = {}): Promise<string> {
  const reply = await hostFetch<{ text: string; model: string }>('/api/apps-sdk/llm', {
    method: 'POST',
    body: JSON.stringify({
      prompt,
      system: opts.system,
      model: opts.model,
      max_tokens: opts.maxTokens ?? 1024,
    }),
  });
  return reply.text;
}

export interface WorkflowSummary {
  id: string;
  name: string;
  enabled?: boolean;
  [key: string]: unknown;
}

/** The user's saved workflows. */
export async function listWorkflows(): Promise<WorkflowSummary[]> {
  const data = await hostFetch<{ workflows?: WorkflowSummary[] }>('/api/workflows/list');
  return data.workflows ?? [];
}

/** Fire a workflow now. Returns whatever the host reports for the started run. */
export async function runWorkflow(workflowId: string): Promise<Record<string, unknown>> {
  return hostFetch<Record<string, unknown>>(`/api/workflows/${encodeURIComponent(workflowId)}/run`, {
    method: 'POST',
    body: JSON.stringify({}),
  });
}

/** All workflow runs (newest first), for reading a fired run's status/result. */
export async function listWorkflowRuns(): Promise<Record<string, unknown>[]> {
  const data = await hostFetch<{ runs?: Record<string, unknown>[] }>('/api/workflows/runs/all');
  return data.runs ?? [];
}

export interface SpawnAgentOptions {
  name?: string;
  /** Short model name; omit for the user's default. */
  model?: string;
  dashboardId?: string;
  /** Canvas position for the spawned card; give both or neither. */
  x?: number;
  y?: number;
}

/** Spawn a real agent on the canvas with a first prompt. Returns its session id. */
export async function spawnAgent(prompt: string, opts: SpawnAgentOptions = {}): Promise<string> {
  const reply = await hostFetch<{ session_id: string }>('/api/apps-sdk/agents/spawn', {
    method: 'POST',
    body: JSON.stringify({
      prompt,
      name: opts.name ?? 'Agent',
      model: opts.model,
      dashboard_id: opts.dashboardId,
      x: opts.x,
      y: opts.y,
    }),
  });
  return reply.session_id;
}

/** A spawned agent's live state: status plus its transcript so far. */
export async function agentSession(sessionId: string): Promise<Record<string, unknown>> {
  return hostFetch<Record<string, unknown>>(`/api/agents/sessions/${encodeURIComponent(sessionId)}`);
}

export interface ToolServer {
  id: string;
  name: string;
  description: string;
}

/** The user's connected tool servers (Gmail, Calendar, custom MCP connectors, ...). */
export async function listTools(): Promise<ToolServer[]> {
  const reply = await hostFetch<{ servers: ToolServer[] }>('/api/apps-sdk/tools/list', {
    method: 'POST',
    body: JSON.stringify({}),
  });
  return reply.servers;
}

/** The individual tools a server exposes (name + input schema), straight from the live server. */
export async function discoverTools(serverId: string): Promise<Record<string, unknown>[]> {
  const reply = await hostFetch<{ tools: Record<string, unknown>[] }>(`/api/tools/${encodeURIComponent(serverId)}/discover`, { method: 'POST', body: JSON.stringify({}) });
  return reply.tools ?? [];
}

/** Call one tool as `<serverId>:<ToolName>`. The FIRST call per tool shows the user an approval
 * card (Allow once / Always / Never); a deny or an unanswered card rejects with a 403. Design for
 * that: it is the user saying no, not an error to retry. */
export async function callTool(tool: string, args: Record<string, unknown> = {}): Promise<string> {
  const reply = await hostFetch<{ result: string }>('/api/apps-sdk/tools/call', {
    method: 'POST',
    body: JSON.stringify({ tool, args }),
  });
  return reply.result;
}
