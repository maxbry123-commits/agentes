import React, { useEffect, useRef, useState } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import KeyboardIcon from '@mui/icons-material/Keyboard';
import { useClaudeTokens } from '@/shared/styles/ThemeContext';

export const IS_MAC = /Mac/.test(navigator.platform);

/** Platform default for the dictation hotkey; F5 is deliberately absent (macOS routes it to Siri before apps ever see it). */
export function dictationDefaultCombo(): string {
  // fn/Globe on mac (native watcher), Ctrl+Win on windows: the same physical bottom-corner key.
  return IS_MAC ? 'Fn' : 'Ctrl+Meta';
}

export function comboDisplay(combo: string): string {
  return combo
    .split('+')
    .map((p) => {
      if (p === 'Fn') return 'fn';
      if (p === 'Meta') return IS_MAC ? '⌘' : 'Win';
      if (p === 'Ctrl') return IS_MAC ? '⌃' : 'Ctrl';
      if (p === 'Alt') return IS_MAC ? '⌥' : 'Alt';
      if (p === 'Shift') return IS_MAC ? '⇧' : 'Shift';
      return p.length === 1 ? p.toUpperCase() : p;
    })
    .join(IS_MAC ? '' : '+');
}

/** Click-to-record shortcut chip: click arms it, the next non-modifier keydown becomes the combo
 * ("Meta+Shift+d" parts format, same as new_agent_shortcut). While armed, the WINDOW owns the
 * keyboard at capture phase and app hotkeys are suppressed: the old chip-local listener lost the
 * keys to global shortcuts (pressing the current dictation combo started a dictation, stole focus,
 * and snapped the chip back before any combo could land, ENG-183). */
const ShortcutRecorderChip: React.FC<{ value: string; onChange: (combo: string) => void }> = ({ value, onChange }) => {
  const c = useClaudeTokens();
  const [recording, setRecording] = useState(false);
  const hostRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!recording) return undefined;
    const w = window as unknown as Record<string, unknown>;
    w.__OSW_SHORTCUT_RECORDING__ = true;
    const onKey = (e: KeyboardEvent): void => {
      // Swallow EVERYTHING while armed so no app shortcut fires mid-recording.
      e.preventDefault();
      e.stopImmediatePropagation();
      if (['Meta', 'Control', 'Shift', 'Alt'].includes(e.key)) return;
      if (e.key === 'Escape') { setRecording(false); return; }
      const parts: string[] = [];
      if (e.metaKey) parts.push('Meta');
      if (e.ctrlKey) parts.push('Ctrl');
      if (e.altKey) parts.push('Alt');
      if (e.shiftKey) parts.push('Shift');
      parts.push(e.key.length === 1 ? e.key.toLowerCase() : e.key);
      onChange(parts.join('+'));
      setRecording(false);
    };
    // Click-away cancels; blur alone must not (a global hotkey stealing focus was the snap-back).
    const onPointerDown = (e: PointerEvent): void => {
      if (hostRef.current && e.target instanceof Node && hostRef.current.contains(e.target)) return;
      setRecording(false);
    };
    window.addEventListener('keydown', onKey, true);
    window.addEventListener('pointerdown', onPointerDown, true);
    return () => {
      w.__OSW_SHORTCUT_RECORDING__ = false;
      window.removeEventListener('keydown', onKey, true);
      window.removeEventListener('pointerdown', onPointerDown, true);
    };
  }, [recording, onChange]);

  return (
    <Box
      ref={hostRef}
      onClick={() => setRecording(true)}
      sx={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 0.75,
        px: 1.5,
        py: 0.75,
        borderRadius: `${c.radius.sm}px`,
        border: `1px solid ${recording ? c.accent.primary : c.border.medium}`,
        cursor: 'pointer',
        outline: 'none',
        transition: 'border-color 0.15s',
        '&:hover': { borderColor: c.accent.primary },
      }}
    >
      <KeyboardIcon sx={{ fontSize: 16, color: recording ? c.accent.primary : c.text.tertiary }} />
      {recording ? (
        <Typography sx={{ fontSize: '0.8125rem', color: c.accent.primary, fontWeight: 500 }}>
          Press shortcut…
        </Typography>
      ) : (
        <Typography sx={{ fontSize: '0.8125rem', color: c.text.primary, fontFamily: c.font.mono, fontWeight: 500 }}>
          {comboDisplay(value)}
        </Typography>
      )}
    </Box>
  );
};

export default ShortcutRecorderChip;
