import { useStatusStore } from '../../stores/status';
import { useChatStore } from '../../stores/chat';

function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return String(n);
}

function contextColor(pct: number): string {
  if (pct >= 90) return 'text-red-400';
  if (pct >= 70) return 'text-yellow-400';
  return 'text-text-300';
}

export function StatusBar() {
  const data = useStatusStore((s) => s.data);
  const status = useChatStore((s) => s.status);
  const currentSessionId = useChatStore((s) => s.currentSessionId);
  const runningSessions = useChatStore((s) => s.runningSessions);

  if (!currentSessionId) return null;

  const runningCount = runningSessions.size;

  const model = data.model || status?.model || '—';
  const branch = data.gitBranch || status?.git_branch || null;
  const autonomy = data.autonomyLevel || status?.autonomy_level || 'Semi-Auto';
  const totalTokens = data.inputTokens + data.outputTokens;
  const cost = data.sessionCostUsd || status?.session_cost || 0;
  const contextPct = data.contextUsagePct || status?.context_usage_pct || 0;

  return (
    <div className="flex items-center gap-4 px-4 py-1.5 bg-bg-100 border-t border-border-300/30 text-xs font-mono text-text-400 select-none shrink-0">
      {/* Model */}
      <span className="text-text-200 font-medium truncate max-w-[180px]" title={model}>
        {model}
      </span>

      {/* Autonomy */}
      <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wide ${
        autonomy === 'Auto' ? 'bg-green-900/40 text-green-400' :
        autonomy === 'Semi-Auto' ? 'bg-yellow-900/40 text-yellow-400' :
        'bg-zinc-800 text-text-400'
      }`}>
        {autonomy}
      </span>

      {/* Git branch */}
      {branch && (
        <span className="text-text-300 truncate max-w-[120px]" title={branch}>
          <span className="text-text-400 mr-1">⎇</span>{branch}
        </span>
      )}

      <div className="flex-1" />

      {/* Tokens */}
      <span className="text-text-300">
        {formatTokens(totalTokens)}/{formatTokens(data.maxTokens)}
      </span>

      {/* Context usage */}
      <span className={contextColor(contextPct)}>
        {contextPct.toFixed(0)}%
      </span>

      {/* MCP */}
      {data.mcpTotal > 0 && (
        <span className={data.mcpConnected === data.mcpTotal ? 'text-green-400' : 'text-yellow-400'}>
          MCP {data.mcpConnected}/{data.mcpTotal}
        </span>
      )}

      {/* Cost */}
      {cost > 0 && (
        <span className="text-text-300">${cost.toFixed(2)}</span>
      )}

      {/* Running sessions (background tasks) */}
      {runningCount > 0 && (
        <span className="text-blue-400 flex items-center gap-1">
          <span className="inline-block w-2 h-2 bg-blue-400 rounded-full animate-pulse" />
          {runningCount} running
        </span>
      )}

      {/* File changes */}
      {data.fileChanges && data.fileChanges.files > 0 && (
        <span className="text-text-300">
          {data.fileChanges.files} files
          <span className="text-green-400 ml-1">+{data.fileChanges.additions}</span>
          <span className="text-red-400 ml-1">-{data.fileChanges.deletions}</span>
        </span>
      )}
    </div>
  );
}
