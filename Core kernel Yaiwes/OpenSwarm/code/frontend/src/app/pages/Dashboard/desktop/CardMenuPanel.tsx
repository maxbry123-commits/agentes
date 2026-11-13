import React from 'react';
import Box from '@mui/material/Box';
import CheckRoundedIcon from '@mui/icons-material/CheckRounded';
import ChevronRightRoundedIcon from '@mui/icons-material/ChevronRightRounded';
import { isMenuAction, type CardMenuRow } from './openCardContextMenu';

export const MENU_WIDTH = 236;
const ROW_RADIUS = 8;

interface CardMenuPanelProps {
  items: CardMenuRow[];
  /** Index into `items` of the keyboard-active row, or null. */
  activeIndex: number | null;
  /** Index into `items` of the row whose submenu is open, or null. */
  openIndex: number | null;
  onActivate: (index: number) => void;
  onHover: (index: number) => void;
  width?: number;
  children?: React.ReactNode;
}

const rowSx = {
  display: 'flex',
  alignItems: 'center',
  gap: '9px',
  width: '100%',
  boxSizing: 'border-box' as const,
  px: '9px',
  py: '5px',
  minHeight: 30,
  border: 'none',
  background: 'transparent',
  borderRadius: `${ROW_RADIUS}px`,
  color: 'rgba(255,255,255,0.9)',
  fontFamily: 'inherit',
  fontSize: '0.8125rem',
  lineHeight: 1.35,
  cursor: 'pointer',
  textAlign: 'left' as const,
};

// Panel radius stays 12 while rows sit at 8: the inner corner must always be the smaller one.
export const PANEL_SX = {
  width: MENU_WIDTH,
  p: '6px',
  boxSizing: 'border-box' as const,
  borderRadius: '12px',
  background: 'rgba(28,25,33,0.94)',
  backdropFilter: 'blur(24px) saturate(150%)',
  WebkitBackdropFilter: 'blur(24px) saturate(150%)',
  border: '1px solid rgba(255,255,255,0.12)',
  boxShadow: '0 18px 44px rgba(0,0,0,0.5)',
};

const CardMenuPanel = React.forwardRef<HTMLDivElement, CardMenuPanelProps>(function CardMenuPanel(
  { items, activeIndex, openIndex, onActivate, onHover, width, children },
  ref,
) {
  return (
    <Box ref={ref} sx={{ ...PANEL_SX, ...(width ? { width } : {}) }}>
      {children}
      {items.map((row, index) => {
        if (row.kind === 'separator') {
          return <Box key={`sep-${index}`} sx={{ height: '1px', mx: '7px', my: '5px', background: 'rgba(255,255,255,0.09)' }} />;
        }
        if (row.kind === 'header') {
          return (
            <Box
              key={`hdr-${index}`}
              sx={{ px: '9px', pt: '7px', pb: '3px', fontSize: '0.6875rem', fontWeight: 600, color: 'rgba(255,255,255,0.42)', letterSpacing: '0.01em' }}
            >
              {row.label}
            </Box>
          );
        }
        if (!isMenuAction(row)) return null;
        const active = activeIndex === index && !row.disabled;
        const highlighted = active || openIndex === index;
        const tone = row.danger ? '#ff7b72' : 'rgba(255,255,255,0.9)';
        const hoverBg = row.danger ? 'rgba(255,123,114,0.14)' : 'rgba(255,255,255,0.10)';
        return (
          <Box
            key={`${row.label}-${index}`}
            component="button"
            type="button"
            role="menuitem"
            aria-disabled={row.disabled || undefined}
            aria-haspopup={row.submenu ? 'menu' : undefined}
            disabled={row.disabled}
            data-menu-row={index}
            onMouseEnter={() => onHover(index)}
            onClick={() => onActivate(index)}
            sx={{
              ...rowSx,
              color: tone,
              background: highlighted ? hoverBg : 'transparent',
              '&:hover': { background: hoverBg },
              '&:disabled': { color: 'rgba(255,255,255,0.32)', cursor: 'default', background: 'transparent' },
            }}
          >
            {row.checked !== undefined && (
              <CheckRoundedIcon sx={{ fontSize: 15, flexShrink: 0, opacity: row.checked ? 1 : 0, color: 'rgba(255,255,255,0.75)' }} />
            )}
            {row.icon !== undefined && (
              <Box sx={{ display: 'flex', flexShrink: 0, color: row.danger ? tone : 'rgba(255,255,255,0.6)', '& svg': { fontSize: 16 } }}>{row.icon}</Box>
            )}
            <Box component="span" sx={{ flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {row.label}
            </Box>
            {row.shortcut && (
              <Box
                component="span"
                sx={{
                  flexShrink: 0, px: '5px', py: '1px', borderRadius: '5px',
                  background: 'rgba(255,255,255,0.08)', color: 'rgba(255,255,255,0.55)',
                  fontSize: '0.6875rem', letterSpacing: '0.02em',
                }}
              >
                {row.shortcut}
              </Box>
            )}
            {row.submenu && <ChevronRightRoundedIcon sx={{ fontSize: 16, flexShrink: 0, color: 'rgba(255,255,255,0.45)' }} />}
          </Box>
        );
      })}
    </Box>
  );
});

export default CardMenuPanel;
