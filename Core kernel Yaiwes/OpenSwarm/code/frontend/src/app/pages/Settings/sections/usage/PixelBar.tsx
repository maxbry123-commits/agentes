import React from 'react';
import Box from '@mui/material/Box';

export const PIXEL_SALMON = ['#C46B57', '#D4795F', '#E8927A', '#F0A088', '#F5B49E'];
export const PIXEL_BLUE = ['#445588', '#5577AA', '#6688BB', '#7799CC', '#88AADD'];

export const PixelBarOuter: React.FC<{ value: number; max: number; width?: number; palette?: string[]; tokens: any }> = ({ value, max, width = 16, palette = PIXEL_SALMON, tokens: c }) => {
  // A continuous rounded bar reads professional where the old 5px pixel blocks read "vibey".
  const pct = max > 0 ? Math.max(value > 0 ? 4 : 0, Math.round((value / max) * 100)) : 0;
  const fill = palette[Math.floor(palette.length / 2)];
  return (
    <Box sx={{ width: width * 6, maxWidth: '100%', height: 4, borderRadius: 2, bgcolor: c.border.subtle, mt: 0.5, overflow: 'hidden' }}>
      <Box sx={{ width: `${pct}%`, height: '100%', borderRadius: 2, bgcolor: fill }} />
    </Box>
  );
};
