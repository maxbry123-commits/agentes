import React, { useMemo } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import AutoAwesomeRoundedIcon from '@mui/icons-material/AutoAwesomeRounded';
import ArrowUpwardRoundedIcon from '@mui/icons-material/ArrowUpwardRounded';
import { searchHelp, type HelpKnowledge } from './helpSearch';

interface HelpAskBoxProps {
  value: string;
  knowledge: HelpKnowledge | null;
  onChange: (v: string) => void;
  onAsk: () => void;
}

/**
 * Search first, chat second (the Raycast/Linear shape): the top questions are answered from facts
 * that shipped with the build, instantly, with no model call and no network. That also makes this
 * the one part of Help that still works when the user's provider is the thing that's broken.
 */
const HelpAskBox: React.FC<HelpAskBoxProps> = ({ value, knowledge, onChange, onAsk }) => {
  const matches = useMemo(() => searchHelp(knowledge, value), [knowledge, value]);

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mx: 1, my: 0.75, px: 1.25, py: 0.75, background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: '10px' }}>
        <AutoAwesomeRoundedIcon sx={{ fontSize: 15, color: 'rgba(255,255,255,0.5)' }} />
        <Box
          component="input"
          value={value}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => onChange(e.target.value)}
          onKeyDown={(e: React.KeyboardEvent) => { if (e.key === 'Enter') onAsk(); e.stopPropagation(); }}
          placeholder="Ask OpenSwarm anything..."
          sx={{ flex: 1, border: 'none', outline: 'none', background: 'transparent', color: 'rgba(255,255,255,0.92)', fontFamily: 'inherit', fontSize: '0.8125rem', '&::placeholder': { color: 'rgba(255,255,255,0.4)' } }}
        />
        {value.trim() && (
          <Box component="button" onClick={onAsk} sx={{ display: 'flex', border: 'none', background: 'transparent', color: 'rgba(255,255,255,0.8)', cursor: 'pointer', p: 0 }}>
            <ArrowUpwardRoundedIcon sx={{ fontSize: 16 }} />
          </Box>
        )}
      </Box>
      {matches.length > 0 && (
        <Box sx={{ mx: 1, mb: 0.75, px: 1.25, py: 0.75, background: 'rgba(255,255,255,0.035)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '10px' }}>
          <Typography sx={{ fontSize: '0.625rem', letterSpacing: '0.08em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.38)', mb: 0.5 }}>
            From the docs
          </Typography>
          {matches.map((m) => (
            <Box key={m.id} sx={{ mb: 0.75, '&:last-of-type': { mb: 0 } }}>
              <Typography sx={{ fontSize: '0.75rem', fontWeight: 600, color: 'rgba(255,255,255,0.88)' }}>{m.title}</Typography>
              <Typography sx={{ fontSize: '0.6875rem', color: 'rgba(255,255,255,0.6)', lineHeight: 1.45 }}>{m.detail}</Typography>
            </Box>
          ))}
          <Typography sx={{ fontSize: '0.625rem', color: 'rgba(255,255,255,0.35)', mt: 0.75 }}>
            Press Enter to ask the help chat instead.
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default HelpAskBox;
