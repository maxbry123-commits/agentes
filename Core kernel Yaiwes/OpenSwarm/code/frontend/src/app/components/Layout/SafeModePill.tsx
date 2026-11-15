import React, { useState } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import ShieldOutlinedIcon from '@mui/icons-material/ShieldOutlined';
import CloseIcon from '@mui/icons-material/Close';
import { useClaudeTokens } from '@/shared/styles/ThemeContext';
import { safeModeInfo } from '@/shared/safeMode';

// Shown only when the loop breaker armed (two dirty exits in ten minutes, ENG-228): tells the user
// why their browsers and apps boot paused instead of looking silently broken. Dismiss is session-only.
const SafeModePill: React.FC = () => {
  const c = useClaudeTokens();
  const [dismissed, setDismissed] = useState(false);
  const info = safeModeInfo();
  if ((!info.safeMode && !info.reducedGraphics) || dismissed) return null;
  return (
    <Box
      sx={{
        position: 'fixed', top: 34, left: '50%', transform: 'translateX(-50%)',
        zIndex: 1400, WebkitAppRegion: 'no-drag',
        display: 'flex', alignItems: 'center', gap: 1,
        px: 1.5, py: 0.75, borderRadius: '10px',
        bgcolor: c.bg.surface, border: `1px solid ${c.border.subtle}`,
        boxShadow: '0 4px 16px rgba(0,0,0,0.18)',
      }}
    >
      <ShieldOutlinedIcon sx={{ fontSize: 16, color: c.text.tertiary }} />
      <Typography sx={{ fontSize: '0.8125rem', color: c.text.primary }}>
        {info.safeMode
          ? 'Recovered after repeated crashes. Browsers and apps are paused; click one to resume it.'
          : 'Running in reduced graphics mode after repeated graphics crashes. Restart to return to full speed.'}
      </Typography>
      <Box
        role="button" aria-label="Dismiss safe mode notice" onClick={() => setDismissed(true)}
        sx={{ display: 'flex', alignItems: 'center', cursor: 'pointer', color: c.text.tertiary, '&:hover': { color: c.text.primary } }}
      >
        <CloseIcon sx={{ fontSize: 14 }} />
      </Box>
    </Box>
  );
};

export default SafeModePill;
