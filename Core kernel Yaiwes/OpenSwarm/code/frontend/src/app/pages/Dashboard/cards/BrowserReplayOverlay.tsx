/**
 * PROTOTYPE (not wired yet): the "fast data mode" overlay for shadow-API replay.
 *
 * Shown over a BrowserCard for the brief moment the agent reads bulk data via the
 * page's own JSON feed instead of scroll-scraping. It's an HONEST visualization,
 * the rows are the real extracted records, revealed at once (one API call returns
 * them all), not a fake cursor and not a faked progress counter.
 *
 * Built deliberately cheap, OpenSwarm is memory/compute-sensitive and the webview
 * compositor is fragile:
 *   - NO backdrop-blur. The overlay is OPAQUE, so it fully covers the <webview>
 *     and the compositor can stop painting it while covered. Blur over a webview
 *     is paint-heavy and risky here.
 *   - Animations are opacity/transform ONLY (compositor-only; no layout/paint).
 *   - Rows reveal via a SINGLE reused @keyframes + per-row animation-delay, pure
 *     CSS, zero per-row JS, state, timers, or WS messages.
 *   - No shimmer loops. The only infinite animation is one tiny opacity-pulse dot.
 *   - Renders at most MAX_VISIBLE rows (the full set goes to the agent, not here).
 *   - unmountOnExit => literally zero cost when not replaying.
 */
import React from 'react';
import Box from '@mui/material/Box';
import Fade from '@mui/material/Fade';
import { useClaudeTokens } from '@/shared/styles/ThemeContext';

export interface ReplayRow {
  title: string;
  subtitle?: string;
}

export interface BrowserReplayOverlayProps {
  active: boolean;
  site: string;                          // plain name, e.g. "LinkedIn"
  rows: ReplayRow[];                     // real extracted records (one payload)
  total: number;
  status: 'reading' | 'done' | 'empty';
  elapsedMs?: number;
}

const MAX_VISIBLE = 6;                    // cap the DOM; the count conveys the rest

function BrowserReplayOverlay({
  active, site, rows, total, status, elapsedMs,
}: BrowserReplayOverlayProps) {
  const c = useClaudeTokens();
  const shown = rows.length > MAX_VISIBLE ? rows.slice(0, MAX_VISIBLE) : rows;

  const header =
    status === 'done'
      ? `✓ ${total} result${total === 1 ? '' : 's'}${elapsedMs != null ? ` · ${(elapsedMs / 1000).toFixed(1)}s` : ''}`
      : status === 'empty'
        ? `${site}'s feed came back empty, browsing instead`
        : `Reading ${site}'s data feed`;

  return (
    <Fade in={active} timeout={{ enter: 200, exit: 220 }} unmountOnExit>
      <Box
        aria-label="fast data read"
        sx={{
          position: 'absolute', inset: 0, zIndex: 5,
          bgcolor: c.bg.surface,             // opaque on purpose (see file header)
          display: 'flex', flexDirection: 'column', gap: 0.75,
          p: 1.25, overflow: 'hidden',
          fontFamily: c.font.sans,
          '@keyframes os-replay-row': {
            from: { opacity: 0, transform: 'translateY(6px)' },
            to: { opacity: 1, transform: 'translateY(0)' },
          },
          '@keyframes os-replay-dot': {
            '0%, 100%': { opacity: 0.3 },
            '50%': { opacity: 1 },
          },
        }}
      >
        <Box sx={{
          display: 'flex', alignItems: 'center', gap: 0.5,
          fontSize: 12, fontWeight: 600,
          color: status === 'done' ? c.accent.primary : c.text.secondary,
          minWidth: 0,
        }}>
          {status === 'reading' && (
            <Box component="span" sx={{
              flex: '0 0 auto', width: 6, height: 6, borderRadius: '50%',
              bgcolor: c.accent.primary,
              animation: 'os-replay-dot 1.2s ease-in-out infinite',
            }} />
          )}
          <Box component="span" sx={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {header}
          </Box>
        </Box>

        {status !== 'empty' && (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.4, minHeight: 0 }}>
            {shown.map((r, i) => (
              <Box
                key={`${i}-${r.title}`}
                sx={{
                  animation: 'os-replay-row 180ms ease-out both',
                  animationDelay: `${i * 45}ms`,
                  display: 'flex', alignItems: 'baseline', gap: 0.75,
                  fontSize: 12.5, color: c.text.primary,
                  whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                }}
              >
                <Box component="span" aria-hidden sx={{ flex: '0 0 auto', color: c.text.tertiary }}>{'▸'}</Box>
                <Box component="span" sx={{ fontWeight: 500, flex: '0 0 auto' }}>{r.title}</Box>
                {r.subtitle && (
                  <Box component="span" sx={{ color: c.text.tertiary, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {r.subtitle}
                  </Box>
                )}
              </Box>
            ))}
          </Box>
        )}

        <Box sx={{ mt: 'auto', fontSize: 11, color: c.text.tertiary }}>
          via the page&apos;s own data feed
        </Box>
      </Box>
    </Fade>
  );
}

// memo: re-render only when the inputs actually change (cheap, but free insurance against parent BrowserCard re-renders during an agent run).
export default React.memo(BrowserReplayOverlay);
