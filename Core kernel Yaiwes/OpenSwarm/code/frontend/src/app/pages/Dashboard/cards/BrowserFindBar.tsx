import React, { useEffect, useRef, useState, useCallback } from 'react';
import Box from '@mui/material/Box';
import InputBase from '@mui/material/InputBase';
import IconButton from '@mui/material/IconButton';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import CloseIcon from '@mui/icons-material/Close';
import { getWebview } from '@/shared/browserRegistry';
import { useClaudeTokens } from '@/shared/styles/ThemeContext';

interface BrowserFindBarProps {
  browserId: string;
  focusSignal: number;
  onClose: () => void;
}

// In-page find (Ctrl/Cmd+F): drives the active tab's webview findInPage with a Chrome-style match counter + up/down/Enter nav, clearing the highlight on close.
export default function BrowserFindBar({ browserId, focusSignal, onClose }: BrowserFindBarProps): React.ReactElement {
  const c = useClaudeTokens();
  const [query, setQuery] = useState('');
  const [result, setResult] = useState<{ active: number; total: number }>({ active: 0, total: 0 });
  const inputRef = useRef<HTMLInputElement>(null);

  // Fresh search omits findNext (passing findNext:false to a webview eats the found-in-page result, an Electron quirk); navigate=true does next/prev.
  const search = useCallback((text: string, navigate: boolean, forward: boolean) => {
    const wv = getWebview(browserId);
    if (!wv) return;
    try {
      if (!text) {
        wv.stopFindInPage('clearSelection');
        setResult({ active: 0, total: 0 });
        return;
      }
      if (navigate) wv.findInPage(text, { findNext: true, forward });
      else wv.findInPage(text);
    } catch {
      // torn-down webview; nothing to find
    }
  }, [browserId]);

  useEffect(() => {
    const wv = getWebview(browserId);
    if (!wv) return;
    const onFound = (e: any) => {
      const r = e?.result;
      if (r && typeof r.matches === 'number') {
        setResult({ active: r.activeMatchOrdinal ?? 0, total: r.matches });
      }
    };
    wv.addEventListener('found-in-page', onFound as any);
    return () => {
      try {
        wv.removeEventListener('found-in-page', onFound as any);
        wv.stopFindInPage('clearSelection');
      } catch {
        // webview already gone
      }
    };
  }, [browserId]);

  useEffect(() => {
    inputRef.current?.focus();
    inputRef.current?.select();
  }, [focusSignal]);

  const onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const text = e.target.value;
    setQuery(text);
    search(text, false, true);
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      e.preventDefault();
      onClose();
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (query) search(query, true, !e.shiftKey);
    }
  };

  return (
    <Box
      onMouseDown={(e) => e.stopPropagation()}
      sx={{
        position: 'absolute',
        top: 8,
        right: 12,
        zIndex: 30,
        display: 'flex',
        alignItems: 'center',
        gap: 0.5,
        px: 1,
        py: 0.5,
        bgcolor: c.bg.surface,
        border: `1px solid ${c.border.medium}`,
        borderRadius: `${c.radius.md}px`,
        boxShadow: c.shadow.lg,
      }}
    >
      <InputBase
        inputRef={inputRef}
        value={query}
        onChange={onChange}
        onKeyDown={onKeyDown}
        placeholder="Find in page"
        sx={{ fontSize: 13, color: c.text.primary, width: 160, '& input': { p: 0 } }}
      />
      <Box sx={{ fontSize: 12, color: c.text.tertiary, minWidth: 44, textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
        {query ? `${result.active}/${result.total}` : ''}
      </Box>
      <IconButton size="small" disabled={!query} onClick={() => search(query, true, false)} sx={{ color: c.text.secondary }}>
        <KeyboardArrowUpIcon sx={{ fontSize: 18 }} />
      </IconButton>
      <IconButton size="small" disabled={!query} onClick={() => search(query, true, true)} sx={{ color: c.text.secondary }}>
        <KeyboardArrowDownIcon sx={{ fontSize: 18 }} />
      </IconButton>
      <IconButton size="small" onClick={onClose} sx={{ color: c.text.secondary }}>
        <CloseIcon sx={{ fontSize: 16 }} />
      </IconButton>
    </Box>
  );
}
