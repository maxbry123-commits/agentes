import { useState, useCallback, useEffect, useMemo, useRef } from 'react';
import { ContextPath } from '@/app/components/editor/DirectoryBrowser';
import { API_BASE, getAuthToken } from '@/shared/config';
import { ForcedToolGroup } from '../types';
import { basename } from '../helpers';

// Only auto-shrink a file when it literally won't fit (98%+ of the window on its own). Below that, send it NATIVELY (base64 document block) the way claude.ai / OpenAI / Gemini do — the model reads the PDF server-side, instantly, no separate summarize round-trip. The old 50% trigger was force-summarizing files that fit fine, which is the entire reason our file flow felt 60s-slow vs their instant: we were doing pre-processing work the big providers simply don't do. 98% (not 100%) leaves a sliver for the prompt itself so a barely-fitting file doesn't 4xx; if the conversation later grows past the window, auto-compact handles it.
function shrinkThreshold(modelCtx: number): number {
  return Math.floor(modelCtx * 0.98);
}

export type SendBlock = null | {
  // 'compacting' = history overflow, auto-compact can fix it. 'too_long'   = this single message exceeds the window on its own; hard block.
  kind: 'compacting' | 'too_long';
  estimate: number;
  window: number;
  history: number;
  system: number;
  framework: number;
  files: number;
  prompt: number;
  largestFile?: { path: string; tokens: number };
};

export function useContextFiles(
  currentModelCtx: number,
  model: string,
  contextEstimate: { used: number; limit: number } | undefined,
  sessionFrameworkOverhead: number,
) {
  const [isUploading, setIsUploading] = useState(false);
  const [contextPaths, setContextPaths] = useState<ContextPath[]>([]);
  const [forcedTools, setForcedTools] = useState<ForcedToolGroup[]>([]);
  const [copiedPathIdx, setCopiedPathIdx] = useState<number | null>(null);
  const [oversizeQueue, setOversizeQueue] = useState<Array<{ path: string; name: string; tokens: number }>>([]);
  const [summarizingPath, setSummarizingPath] = useState<string | null>(null);
  const [summarizingAll, setSummarizingAll] = useState(false);
  const [summarizeError, setSummarizeError] = useState<string | null>(null);
  const [sendBlock, setSendBlock] = useState<SendBlock>(null);
  // Set when user clicked Send but oversize popup intercepted. Once the queue drains, we trigger the send automatically so the user doesn't have to click Send a second time.
  const pendingSendRef = useRef<(() => void) | null>(null);

  const uploadAndAttachFiles = useCallback(async (files: File[]) => {
    if (files.length === 0) return;
    setIsUploading(true);
    try {
      const formData = new FormData();
      files.forEach((f) => formData.append('files', f));
      const resp = await fetch(`${API_BASE}/settings/upload-files`, {
        method: 'POST',
        body: formData,
      });
      if (!resp.ok) throw new Error('Upload failed');
      const data = await resp.json();
      const oversize: Array<{ path: string; name: string; tokens: number }> = [];
      const newPaths: ContextPath[] = (data.files || []).map((f: { path: string; name?: string; tokens?: number; kind?: 'text' | 'pdf' | 'image' | 'binary'; media_type?: string }) => {
        const t = typeof f.tokens === 'number' ? f.tokens : 0;
        if (t > shrinkThreshold(currentModelCtx)) oversize.push({ path: f.path, name: f.name || basename(f.path) || 'file', tokens: t });
        return { path: f.path, type: 'file' as const, tokens: t, kind: f.kind, media_type: f.media_type };
      });
      setContextPaths((prev) => [...prev, ...newPaths]);
      if (oversize.length > 0) setOversizeQueue((q) => [...q, ...oversize]);
    } catch (err) {
      console.error('File upload failed:', err);
    } finally {
      setIsUploading(false);
    }
  }, [currentModelCtx]);

  useEffect(() => {
    const stillOversize: Array<{ path: string; name: string; tokens: number }> = [];
    for (const cp of contextPaths) {
      const t = cp.tokens || 0;
      if (t > shrinkThreshold(currentModelCtx)) {
        const name = basename(cp.path) || cp.path;
        stillOversize.push({ path: cp.path, name, tokens: t });
      }
    }
    setOversizeQueue((q) => {
      const next = stillOversize.filter((o) => !q.find((qq) => qq.path === o.path));
      return [...q.filter((qq) => stillOversize.find((o) => o.path === qq.path)), ...next];
    });
  }, [currentModelCtx, contextPaths]);

  const detachOversize = useCallback((path: string) => {
    setContextPaths((prev) => prev.filter((cp) => cp.path !== path));
    setOversizeQueue((q) => q.filter((o) => o.path !== path));
  }, []);

  // Single-click batch: remove EVERY oversize file. The auto-retry effect below notices the queue went empty and fires the pending send (if any), so going from 5 too-big files to a sent message is 1 click instead of 6.
  const detachAllOversize = useCallback(() => {
    setOversizeQueue((q) => {
      const paths = new Set(q.map((o) => o.path));
      setContextPaths((prev) => prev.filter((cp) => !paths.has(cp.path)));
      return [];
    });
  }, []);

  const summarizeOversize = useCallback(async (path: string) => {
    if (summarizingPath) return;  // another summarize is in flight; ignore
    setSummarizingPath(path);
    try {
      const tok = (() => { try { return getAuthToken(); } catch { return ''; } })();
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (tok) headers['Authorization'] = `Bearer ${tok}`;
      const target = Math.min(8_000, Math.max(1_000, Math.floor(currentModelCtx * 0.05)));
      const resp = await fetch(`${API_BASE}/settings/summarize-file`, {
        method: 'POST', headers,
        body: JSON.stringify({ path, target_tokens: target, primary_model: model }),
      });
      if (!resp.ok) {
        let detail = `summarize failed (${resp.status})`;
        try { const j = await resp.json(); if (j?.detail) detail = String(j.detail); } catch {}
        throw new Error(detail);
      }
      const data = await resp.json();
      const newPath: string = data.path;
      const newTokens: number = data.tokens || 0;
      setContextPaths((prev) => prev.map((cp) => cp.path === path ? { ...cp, path: newPath, tokens: newTokens, kind: 'text', media_type: 'text/plain' } : cp));
      setOversizeQueue((q) => q.filter((o) => o.path !== path));
    } catch (err) {
      // Don't show backend stack traces / model error JSON to users. The raw error ("Error code: 400 - {'error': {'message': '[claude/...] prompt is too long...'}}") is logged in console for devs; users see a plain English ask.
      if (err instanceof Error) console.error('[summarize] failed:', err.message);
      setSummarizeError('Could not shrink the file. Try removing it, or pick a model with a bigger window in Settings.');
    } finally {
      setSummarizingPath(null);
    }
  }, [currentModelCtx, model, summarizingPath]);

  // Single-click batch: shrink EVERY oversize file in parallel. Server-side each call already chunks-and-merges via asyncio.gather, so N files at once is bounded by the slowest one's chunk count, not N x single-file time. Errors from any one file land in summarizeError; others continue.
  const summarizeAllOversize = useCallback(async () => {
    if (summarizingAll) return;
    const snapshot = oversizeQueue.slice();
    if (snapshot.length === 0) return;
    setSummarizingAll(true);
    try {
      const tok = (() => { try { return getAuthToken(); } catch { return ''; } })();
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (tok) headers['Authorization'] = `Bearer ${tok}`;
      const target = Math.min(8_000, Math.max(1_000, Math.floor(currentModelCtx * 0.05)));
      const results = await Promise.allSettled(snapshot.map(async (item) => {
        const resp = await fetch(`${API_BASE}/settings/summarize-file`, {
          method: 'POST', headers,
          body: JSON.stringify({ path: item.path, target_tokens: target, primary_model: model }),
        });
        if (!resp.ok) {
          let detail = `summarize failed (${resp.status})`;
          try { const j = await resp.json(); if (j?.detail) detail = String(j.detail); } catch {}
          throw new Error(detail);
        }
        const data = await resp.json();
        return { oldPath: item.path, newPath: data.path as string, newTokens: (data.tokens as number) || 0 };
      }));
      const succeeded = results.filter((r) => r.status === 'fulfilled') as PromiseFulfilledResult<{ oldPath: string; newPath: string; newTokens: number }>[];
      const failed = results.filter((r) => r.status === 'rejected') as PromiseRejectedResult[];
      if (succeeded.length > 0) {
        setContextPaths((prev) => prev.map((cp) => {
          const hit = succeeded.find((r) => r.value.oldPath === cp.path);
          return hit ? { ...cp, path: hit.value.newPath, tokens: hit.value.newTokens, kind: 'text' as const, media_type: 'text/plain' } : cp;
        }));
        const okPaths = new Set(succeeded.map((r) => r.value.oldPath));
        setOversizeQueue((q) => q.filter((o) => !okPaths.has(o.path)));
      }
      if (failed.length > 0) {
        failed.forEach((f) => { if (f.reason instanceof Error) console.error('[summarize-all] failed:', f.reason.message); });
        setSummarizeError(failed.length === snapshot.length
          ? 'Could not shrink the files. Try removing some, or pick a model with a bigger window in Settings.'
          : `Could not shrink ${failed.length} of ${snapshot.length} files. Remove or retry the ones still flagged.`);
      }
    } finally {
      setSummarizingAll(false);
    }
  }, [oversizeQueue, summarizingAll, currentModelCtx, model]);

  // Auto-shrink: as soon as a file lands oversize, fire the shrink. No "this file is too big, what do you want to do?" prompt — there's no real choice, we KNOW the only reasonable answer is "shrink it". The popup becomes a status indicator ("Shrinking X") not a question, and disappears the moment shrinking finishes. If the user wanted the original unshrunk file they'd not have attached something bigger than the model's window in the first place; we still expose detach-on-chip if they change their mind.
  const lastAutoShrinkSig = useRef('');
  useEffect(() => {
    if (oversizeQueue.length === 0) return;
    if (summarizingAll || summarizingPath) return;
    const sig = oversizeQueue.map((o) => o.path).sort().join('|');
    if (sig === lastAutoShrinkSig.current) return;
    lastAutoShrinkSig.current = sig;
    summarizeAllOversize();
  }, [oversizeQueue, summarizingAll, summarizingPath, summarizeAllOversize]);

  // Auto-retry: when the queue drains AND the user had a pending send, fire it. Zero extra clicks; user types "hi" with attached files, the shrink happens, send fires.
  useEffect(() => {
    if (oversizeQueue.length === 0 && !summarizingAll && !summarizingPath && pendingSendRef.current) {
      const send = pendingSendRef.current;
      pendingSendRef.current = null;
      send();
    }
  }, [oversizeQueue.length, summarizingAll, summarizingPath]);

  const pendingPayloadEstimate = useMemo(() => {
    const history = Math.max(0, contextEstimate?.used ?? 0);
    const filesSum = contextPaths.reduce((acc, cp) => acc + (cp.tokens || 0), 0);
    return history + (sessionFrameworkOverhead || 0) + filesSum;
  }, [contextEstimate, contextPaths, sessionFrameworkOverhead]);

  const pendingKinds = useMemo(() => {
    const set = new Set<string>();
    for (const cp of contextPaths) {
      if (cp.kind) set.add(cp.kind);
    }
    return set;
  }, [contextPaths]);

  return {
    isUploading,
    contextPaths, setContextPaths,
    forcedTools, setForcedTools,
    copiedPathIdx, setCopiedPathIdx,
    oversizeQueue,
    summarizingPath,
    summarizingAll,
    summarizeError, setSummarizeError,
    sendBlock, setSendBlock,
    uploadAndAttachFiles,
    detachOversize,
    detachAllOversize,
    summarizeOversize,
    summarizeAllOversize,
    pendingPayloadEstimate,
    pendingKinds,
    pendingSendRef,
  };
}
