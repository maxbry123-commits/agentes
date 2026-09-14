import React, { useEffect, useRef, useState } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import HelpPanel from './HelpPanel';

/** Top-right desktop pill: opens the help panel (ask, report a bug, docs). Dictation lives on the composer mics + F5, not here. */
function HelpPill(): React.ReactElement {
  const [helpOpen, setHelpOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement | null>(null);

  // Outside click / Esc closes the panel; listeners only live while it's open.
  useEffect(() => {
    if (!helpOpen) return undefined;
    const onDown = (e: MouseEvent): void => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) setHelpOpen(false);
    };
    const onKey = (e: KeyboardEvent): void => { if (e.key === 'Escape') setHelpOpen(false); };
    document.addEventListener('mousedown', onDown);
    document.addEventListener('keydown', onKey);
    return () => { document.removeEventListener('mousedown', onDown); document.removeEventListener('keydown', onKey); };
  }, [helpOpen]);

  return (
    <Box ref={rootRef} sx={{ position: 'relative' }}>
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          height: 30,
          px: 1.5,
          borderRadius: 999,
          background: 'rgba(22,12,34,0.66)',
          backdropFilter: 'blur(20px) saturate(160%)',
          WebkitBackdropFilter: 'blur(20px) saturate(160%)',
          boxShadow: '0 6px 20px rgba(0,0,0,0.3)',
          cursor: 'pointer',
          userSelect: 'none',
          transition: 'background 0.2s ease',
          '&:hover': { background: 'rgba(22,12,34,0.8)' },
        }}
        onClick={() => setHelpOpen((v) => !v)}
      >
        <Typography sx={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.72)', fontWeight: 500 }}>
          Help
        </Typography>
      </Box>
      {helpOpen && <HelpPanel onClose={() => setHelpOpen(false)} />}
    </Box>
  );
}

export default HelpPill;
