import { useCallback } from 'react';
import type React from 'react';
import type { AppDispatch } from '@/shared/state/store';
import { openCardContextMenu } from '../desktop/openCardContextMenu';
import { pasteClipboardCards } from '../hooks/interaction/pasteClipboardCards';
import { canvasMenuRows } from './canvasMenuRows';
import type { useDashboardSelection } from '../hooks/state/useDashboardSelection';

interface CanvasContextMenuArgs {
  dispatch: AppDispatch;
  dashboardId: string;
  expandedSessionIds: string[];
  selection: ReturnType<typeof useDashboardSelection>;
  canvasEmpty: boolean;
  viewportRef: React.RefObject<HTMLDivElement>;
  getCamera: () => { panX: number; panY: number; zoom: number };
  onNewAgent: () => void;
  onAddBrowser: () => void;
  onApplications: () => void;
  onTidy: () => void;
  onFitToView: () => void;
}

export function useCanvasContextMenu(args: CanvasContextMenuArgs): (e: React.MouseEvent) => void {
  const { dispatch, dashboardId, expandedSessionIds, selection, canvasEmpty, viewportRef, getCamera } = args;
  const { onNewAgent, onAddBrowser, onApplications, onTidy, onFitToView } = args;
  // Fired from the viewport's mouseUP (never contextmenu): the right button starts the marquee, so the
  // menu may only appear once the release proves the gesture was a click.
  return useCallback((e: React.MouseEvent) => {
    // Bare canvas only; cards own their own menus and inputs/webviews keep the native one.
    const t = e.target as HTMLElement;
    if (t.closest('[data-select-id]') || t.closest('input, textarea, [contenteditable]')) return;
    const rect = viewportRef.current?.getBoundingClientRect();
    const cam = getCamera();
    const at = rect
      ? { x: (e.clientX - rect.left - cam.panX) / cam.zoom, y: (e.clientY - rect.top - cam.panY) / cam.zoom }
      : undefined;
    openCardContextMenu(e, {
      items: canvasMenuRows({
        dispatch,
        hasCards: !canvasEmpty,
        onNewAgent,
        onAddBrowser,
        onApplications,
        onPaste: () => { void pasteClipboardCards({ dispatch, dashboardId, expandedSessionIds, selection, at }); },
        onSelectAll: selection.selectAll,
        onTidy,
        onFitToView,
      }),
    });
  }, [dispatch, dashboardId, expandedSessionIds, selection, canvasEmpty, viewportRef, getCamera, onNewAgent, onAddBrowser, onApplications, onTidy, onFitToView]);
}
