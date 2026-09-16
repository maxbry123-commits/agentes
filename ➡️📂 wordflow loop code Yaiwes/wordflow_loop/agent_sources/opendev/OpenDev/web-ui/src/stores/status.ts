import { create } from 'zustand';
import { wsClient } from '../api/websocket';

export interface StatusBarData {
  model: string | null;
  provider: string | null;
  inputTokens: number;
  outputTokens: number;
  maxTokens: number;
  contextUsagePct: number;
  sessionCostUsd: number;
  gitBranch: string | null;
  autonomyLevel: 'Manual' | 'Semi-Auto' | 'Auto';
  thinkingLevel: 'Off' | 'Low' | 'Medium' | 'High';
  mcpConnected: number;
  mcpTotal: number;
  fileChanges: { files: number; additions: number; deletions: number } | null;
}

interface StatusStore {
  data: StatusBarData;
  update: (partial: Partial<StatusBarData>) => void;
}

const DEFAULT_STATUS: StatusBarData = {
  model: null,
  provider: null,
  inputTokens: 0,
  outputTokens: 0,
  maxTokens: 200000,
  contextUsagePct: 0,
  sessionCostUsd: 0,
  gitBranch: null,
  autonomyLevel: 'Semi-Auto',
  thinkingLevel: 'Medium',
  mcpConnected: 0,
  mcpTotal: 0,
  fileChanges: null,
};

export const useStatusStore = create<StatusStore>((set) => ({
  data: DEFAULT_STATUS,
  update: (partial) => set((state) => ({ data: { ...state.data, ...partial } })),
}));

// Subscribe to WebSocket status events
wsClient.on('status_update', (message) => {
  const d = message.data;
  if (!d) return;

  const updates: Partial<StatusBarData> = {};
  if (d.model != null) updates.model = d.model;
  if (d.provider != null) updates.provider = d.provider;
  if (d.input_tokens != null) updates.inputTokens = d.input_tokens;
  if (d.output_tokens != null) updates.outputTokens = d.output_tokens;
  if (d.max_tokens != null) updates.maxTokens = d.max_tokens;
  if (d.context_usage_pct != null) updates.contextUsagePct = d.context_usage_pct;
  if (d.session_cost_usd != null) updates.sessionCostUsd = d.session_cost_usd;
  if (d.git_branch != null) updates.gitBranch = d.git_branch;
  if (d.autonomy_level != null) updates.autonomyLevel = d.autonomy_level;
  if (d.thinking_level != null) updates.thinkingLevel = d.thinking_level;
  if (d.mcp_connected != null) updates.mcpConnected = d.mcp_connected;
  if (d.mcp_total != null) updates.mcpTotal = d.mcp_total;
  if (d.file_changes != null) updates.fileChanges = d.file_changes;

  useStatusStore.getState().update(updates);
});
