import { SelectedElement } from '@/app/components/editor/ElementSelectionContext';
import { getWebview } from '@/shared/browserRegistry';
import { ContextPath } from '@/app/components/editor/DirectoryBrowser';
import { AttachedImage } from './types';
import { SendBlock } from './hooks/useContextFiles';

type OutImage = { data: string; media_type: string };

interface SendBlockInputs {
  trimmed: string;
  currentModelCtx: number;
  historyUsed: number;
  contextPaths: ContextPath[];
  sessionFrameworkOverhead: number;
}

// Pre-send dry-run guard. Sums every known component of next-turn input (history estimate from props, system prompt, framework/MCP overhead last reported by the API, attached file token estimates, and the prompt itself). If the sum exceeds 95% of the model's window, returns a block with concrete recovery actions instead of round-tripping to a doomed API call. Conservative on purpose: tokenizers differ across providers (char/4 is rough), so we leave 5% headroom plus the API's own response budget.
export function computeSendBlock({ trimmed, currentModelCtx, historyUsed, contextPaths, sessionFrameworkOverhead }: SendBlockInputs): NonNullable<SendBlock> | null {
  const win = currentModelCtx;
  const history = Math.max(0, historyUsed);
  const filesSum = contextPaths.reduce((acc, cp) => acc + (cp.tokens || 0), 0);
  const promptTokens = Math.ceil(trimmed.length / 4);
  const framework = sessionFrameworkOverhead || 0;
  const systemTokens = 0;
  const estimate = history + framework + filesSum + promptTokens + systemTokens;
  if (win > 0 && estimate > Math.floor(win * 0.95)) {
    let largest: { path: string; tokens: number } | undefined;
    for (const cp of contextPaths) {
      if ((cp.tokens || 0) > (largest?.tokens || 0)) largest = { path: cp.path, tokens: cp.tokens || 0 };
    }
    // Distinguish "history is the culprit" (compaction can fix it) from "this one message is too big on its own" (compaction can't help: dropping all prior turns still leaves framework+files+prompt over the window). The latter only happens with a giant pasted prompt, since attached files auto-shrink on attach. We surface that as a hard block instead of a doomed compact loop.
    const nonHistory = framework + filesSum + promptTokens + systemTokens;
    const kind: 'compacting' | 'too_long' =
      nonHistory > Math.floor(win * 0.95) ? 'too_long' : 'compacting';
    return {
      kind,
      estimate, window: win,
      history, system: systemTokens, framework, files: filesSum, prompt: promptTokens,
      largestFile: largest,
    };
  }
  return null;
}

/** Materialize blob-backed previews to base64 only at send; filters out empties. */
export async function materializeImages(images: AttachedImage[]): Promise<OutImage[]> {
  if (images.length === 0) return [];
  const all = await Promise.all(images.map(async (img) => {
    if (img.data) return { data: img.data, media_type: img.media_type };
    if (img._file) {
      const base64 = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
          const r = reader.result as string;
          resolve(r.split(',')[1] ?? '');
        };
        reader.onerror = () => reject(reader.error || new Error('FileReader failed'));
        reader.readAsDataURL(img._file!);
      });
      return { data: base64, media_type: img.media_type };
    }
    return { data: '', media_type: img.media_type };
  }));
  return all.filter((i) => i.data);
}

/** Appends a human-readable Selected UI Elements block to the prompt and pushes any element screenshots into allImages. */
export function appendSelectedElements(trimmed: string, selectedEls: SelectedElement[], allImages: OutImage[]): string {
  if (selectedEls.length === 0) return trimmed;
  const lines: string[] = ['\n\n---\nSelected UI Elements:\n'];
  for (let i = 0; i < selectedEls.length; i++) {
    const el = selectedEls[i];

    if (el.semanticType === 'browser-card' && el.semanticData?.selectId) {
      const wv = getWebview(el.semanticData.selectId as string);
      const url = wv ? (el.semanticData.url || wv.getURL()) : (el.semanticData.url || '');
      const title = wv ? (el.semanticData.name || wv.getTitle()) : (el.semanticLabel || '');
      lines.push(`${i + 1}. [Browser Card] ${title}`);
      lines.push(`   browser_id: ${el.semanticData.selectId}`);
      if (url) lines.push(`   URL: ${url}`);
      lines.push(`   (Use BrowserAgent with this browser_id to interact with it, or CreateBrowserAgent for a new browser)`);
    } else if (el.semanticType === 'view-card') {
      const appName = typeof el.semanticData?.name === 'string' ? el.semanticData.name : (el.semanticLabel || 'Untitled App');
      const appPath = typeof el.semanticData?.path === 'string' ? el.semanticData.path : '';
      lines.push(`${i + 1}. [App Card] ${appName}`);
      if (appPath) {
        lines.push(`   Workspace path: ${appPath}`);
        lines.push(`   (Edit this app's files in place at the path above. Don't recreate it or write files elsewhere.)`);
      } else {
        // No resolved path means the app's folder is gone or unsaved; tell the agent rather than emit a confusing opaque id.
        lines.push(`   (This app has no on-disk workspace yet; ask the user to save or reopen it before editing.)`);
      }
    } else if (el.semanticType && el.semanticData) {
      const typeLabel = {
        'agent-card': 'Agent Card',
        'message': 'Message',
        'tool-call': 'Tool Call',
        'tool-group': 'Tool Group',
        'browser-card': 'Browser Card',
        'workflow-card': 'Workflow Card',
        'workflows-hub-card': 'Workflows Hub',
        'settings-option': 'Setting',
        'dom-element': 'Element',
      }[el.semanticType] || el.semanticType;
      lines.push(`${i + 1}. [${typeLabel}] ${el.semanticLabel || ''}`);
      const { selectId, ...rest } = el.semanticData;
      if (selectId) lines.push(`   ID: ${selectId}`);
      const metaStr = Object.entries(rest)
        .filter(([, v]) => v != null)
        .map(([k, v]) => `${k}: ${typeof v === 'string' ? v : JSON.stringify(v)}`)
        .join(', ');
      if (metaStr) lines.push(`   ${metaStr}`);
      if (el.semanticType === 'agent-card' && selectId) {
        lines.push(`   (Use InvokeAgent with session_id "${selectId}" to query this agent with full conversation context)`);
      }
    } else {
      const styleStr = Object.entries(el.computedStyles)
        .map(([k, v]) => `${k}: ${v}`)
        .join('; ');
      lines.push(`${i + 1}. \`${el.selectorPath}\` (${el.tagName.toLowerCase()})`);
      lines.push(`   Selector: ${el.selectorPath}`);
      lines.push(`   HTML: ${el.outerHTML.length > 500 ? el.outerHTML.slice(0, 500) + '...' : el.outerHTML}`);
      if (styleStr) lines.push(`   Key styles: ${styleStr}`);
    }
    lines.push('');

    if (el.screenshot) {
      const base64 = el.screenshot.replace(/^data:image\/\w+;base64,/, '');
      allImages.push({ data: base64, media_type: 'image/png' });
    }
  }
  return trimmed + lines.join('\n');
}
