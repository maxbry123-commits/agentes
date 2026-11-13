import React from 'react';
import Box from '@mui/material/Box';
import Tooltip from '@mui/material/Tooltip';
import { formatTokenCount } from '../helpers';

export const ContextRing: React.FC<{ used: number; limit: number; accentColor: string; trackColor: string }> = ({ used, limit, accentColor, trackColor }) => {
  // Track the previous fill so a DROP (compaction freed space) can play a brief "settle" cue: the ring eases down AND flashes once toward the track color, signaling "we just made room" without a loud banner. A rise just eases up.
  const prevUsed = React.useRef(used);
  const [justCompacted, setJustCompacted] = React.useState(false);
  React.useEffect(() => {
    if (used < prevUsed.current - 1) {
      setJustCompacted(true);
      const t = setTimeout(() => setJustCompacted(false), 700);
      prevUsed.current = used;
      return () => clearTimeout(t);
    }
    prevUsed.current = used;
  }, [used]);

  if (used === 0) return null;
  const pct = Math.min((used / limit) * 100, 100);
  const size = 20;
  const strokeWidth = 2;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const dashOffset = circumference * (1 - pct / 100);
  const tooltip = `${pct.toFixed(1)}% · ${formatTokenCount(used)} / ${formatTokenCount(limit)} context used`;

  return (
    <Tooltip title={tooltip}>
      <Box sx={{ display: 'inline-flex', alignItems: 'center', cursor: 'default', p: 0.5 }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke={trackColor} strokeWidth={strokeWidth} />
          <circle
            cx={size / 2} cy={size / 2} r={radius}
            fill="none" stroke={accentColor} strokeWidth={strokeWidth}
            strokeDasharray={circumference} strokeDashoffset={dashOffset}
            strokeLinecap="round"
            transform={`rotate(-90 ${size / 2} ${size / 2})`}
            style={{
              // 600ms cubic-bezier ease on the fill: a rise glides up, a compaction glides down. The one-shot opacity dip is the "settle" flash on drop.
              transition: 'stroke-dashoffset 0.6s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.35s ease',
              opacity: justCompacted ? 0.35 : 1,
            }}
          />
        </svg>
      </Box>
    </Tooltip>
  );
};
