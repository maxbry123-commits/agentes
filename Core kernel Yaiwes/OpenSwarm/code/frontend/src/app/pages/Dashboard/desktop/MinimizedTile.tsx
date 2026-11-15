import React, { useState } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import LanguageIcon from '@mui/icons-material/Language';
import GridViewRoundedIcon from '@mui/icons-material/GridViewRounded';
import EventRepeatIcon from '@mui/icons-material/EventRepeat';
import SettingsIcon from '@mui/icons-material/Settings';
import { pickIcon } from '../canvas/DashboardGlyph';
import WindowControls, { ARC_CHIP_SX } from '../cards/WindowControls';
import { getMinimizedShot } from './minimizedShots';
import type { MinimizedEntry } from './minimizedEntries';

interface MinimizedTileProps {
  entry: MinimizedEntry;
  accent: string;
  selected: boolean;
  onRestore: () => void;
  onClose: () => void;
  onTile: (zone: string) => void;
  onContextMenu: (e: React.MouseEvent) => void;
}

export const MINIMIZED_TILE_W = 132;

// Opaque interior: the rail above is the one glass layer, so stacking more alpha in here just muddies
// the text. Chromium also does a backdrop readback per blurred element, so N blurred tiles is N passes.
const TILE_BODY = '#262624';
const TILE_WELL = '#1b1b19';
const REST_EDGE = 'rgba(255,255,255,0.10)';
const HOVER_EDGE = 'rgba(255,255,255,0.16)';

/** One parked window: its own last frame, a favicon or glyph, and the title. Hover reveals the lights. */
function MinimizedTile({ entry, accent, selected, onRestore, onClose, onTile, onContextMenu }: MinimizedTileProps): React.ReactElement {
  const [faviconFailed, setFaviconFailed] = useState(false);
  const preview = getMinimizedShot(entry.id) || entry.thumbnail || null;
  const showFavicon = entry.kind === 'browser' && !!entry.faviconUrl && !faviconFailed;

  const mark = (size: number): React.ReactElement => {
    if (showFavicon) {
      return (
        <Box
          component="img"
          src={entry.faviconUrl}
          alt=""
          onError={() => setFaviconFailed(true)}
          sx={{ width: size, height: size, borderRadius: `${Math.round(size / 4)}px`, display: 'block' }}
        />
      );
    }
    if (entry.kind === 'browser') return <LanguageIcon sx={{ fontSize: size, color: 'rgba(255,255,255,0.55)', display: 'block' }} />;
    // The singleton windows never have a thumbnail, so their own app glyph is the whole identity of the tile.
    if (entry.kind === 'workflows') return <EventRepeatIcon sx={{ fontSize: size, color: 'rgba(255,255,255,0.55)', display: 'block' }} />;
    if (entry.kind === 'settings') return <SettingsIcon sx={{ fontSize: size, color: 'rgba(255,255,255,0.55)', display: 'block' }} />;
    // Never a letter here: a glyph initial reads as a bug, so an unmatched name falls back to a real symbol.
    const AppIcon = pickIcon(entry.label);
    if (AppIcon) return <AppIcon size={size} strokeWidth={1.75} color="rgba(255,255,255,0.6)" />;
    return <GridViewRoundedIcon sx={{ fontSize: size, color: 'rgba(255,255,255,0.55)', display: 'block' }} />;
  };

  return (
    <Box
      className="osw-card osw-pill-host osw-min-tile"
      onClick={onRestore}
      onContextMenu={onContextMenu}
      title={entry.label}
      sx={{
        position: 'relative',
        width: MINIMIZED_TILE_W,
        flexShrink: 0,
        p: '4px',
        display: 'flex',
        flexDirection: 'column',
        gap: '4px',
        borderRadius: '12px',
        cursor: 'pointer',
        border: `1px solid ${REST_EDGE}`,
        // Selection reads as a soft tint plus ONE accent inner edge; the outer glow is decoration only.
        background: selected ? `linear-gradient(0deg, ${accent}1f, ${accent}1f), ${TILE_BODY}` : TILE_BODY,
        boxShadow: selected ? `inset 0 0 0 1px ${accent}, 0 0 24px ${accent}26` : 'none',
        transition: 'border-color 140ms ease, background 140ms ease',
        '&:hover': { borderColor: HOVER_EDGE },
        '&:hover .osw-pill-lights': { opacity: 1, pointerEvents: 'auto' },
        '&:hover .osw-min-well': { filter: 'brightness(1.08)' },
      }}
    >
      <Box
        className="osw-min-well"
        sx={{
          position: 'relative',
          width: '100%',
          aspectRatio: '16 / 10',
          borderRadius: '8px',
          overflow: 'hidden',
          background: preview ? TILE_WELL : `linear-gradient(135deg, #302f2c, ${TILE_WELL})`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transition: 'filter 140ms ease',
        }}
      >
        {preview ? (
          <Box component="img" src={preview} alt="" sx={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: 'top center', display: 'block' }} />
        ) : (
          mark(26)
        )}
        <Box
          className="osw-pill-lights"
          onClick={(e: React.MouseEvent) => e.stopPropagation()}
          sx={{
            ...ARC_CHIP_SX,
            position: 'absolute', top: 4, left: 4, zIndex: 2, background: 'rgba(24,14,32,0.85)',
            backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)',
            opacity: 0, pointerEvents: 'none', transition: 'opacity 140ms ease',
          }}
        >
          <WindowControls onClose={onClose} onMinimize={onRestore} onTile={onTile} tiled={false} />
        </Box>
      </Box>

      <Box sx={{ display: 'flex', alignItems: 'center', gap: '6px', px: '2px', height: 22 }}>
        <Box
          sx={{
            width: 5, height: 5, borderRadius: '50%', flexShrink: 0,
            background: selected ? accent : 'rgba(255,255,255,0.26)',
            transition: 'background 140ms ease',
          }}
        />
        <Box sx={{ display: 'flex', alignItems: 'center', flexShrink: 0 }}>{mark(13)}</Box>
        <Typography
          sx={{
            fontSize: '0.6875rem',
            fontWeight: selected ? 600 : 500,
            color: selected ? '#FAF9F5' : 'rgba(255,255,255,0.62)',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            transition: 'color 140ms ease',
          }}
        >
          {entry.label}
        </Typography>
      </Box>
    </Box>
  );
}

export default MinimizedTile;
