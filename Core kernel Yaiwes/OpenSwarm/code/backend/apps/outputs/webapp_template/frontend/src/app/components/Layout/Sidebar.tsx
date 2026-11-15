import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import List from '@mui/material/List';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import HomeIcon from '@mui/icons-material/Home';
import FavoriteIcon from '@mui/icons-material/Favorite';
import LightModeIcon from '@mui/icons-material/LightMode';
import DarkModeIcon from '@mui/icons-material/DarkMode';
import { NavLink, useLocation } from 'react-router-dom';
import { useClaudeTokens, useThemeMode } from '@/shared/styles/ThemeContext';
import logoUrl from '@/assets/logo.png';

const NAV_ITEMS = [
  { path: '/', label: 'Home', icon: HomeIcon },
  { path: '/health', label: 'Health', icon: FavoriteIcon },
];

const SIDEBAR_WIDTH_EXPANDED = 240;
const SIDEBAR_WIDTH_COLLAPSED = 64;

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ collapsed, onToggle }) => {
  const c = useClaudeTokens();
  const { mode, toggleMode } = useThemeMode();
  const location = useLocation();

  const width = collapsed ? SIDEBAR_WIDTH_COLLAPSED : SIDEBAR_WIDTH_EXPANDED;

  return (
    <Box
      component="nav"
      sx={{
        width,
        minWidth: width,
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        // Soft tonal separation instead of a hard borderRight — Claude
        // Design uses background-color steps rather than 1px lines for
        // pane boundaries, which reads as airy rather than fenced-off.
        bgcolor: c.bg.secondary,
        transition: c.transition,
        overflow: 'hidden',
      }}
    >
      <Box
        onClick={onToggle}
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1.75,
          px: collapsed ? 0 : 3,
          // Looser vertical breathing — was py:2.5 → 3.5 (~+40%). The
          // sidebar logo lockup is the first thing the eye lands on;
          // tight padding reads as cramped.
          py: 3.5,
          justifyContent: collapsed ? 'center' : 'flex-start',
          minHeight: 72,
          cursor: 'pointer',
          userSelect: 'none',
        }}
      >
        <Box
          component="img"
          // Imported as an ES module so vite bundles the asset into the
          // JS chunk graph — `/logo.png` from `public/` was getting
          // 404'd during the cold-start window (vite hadn't indexed the
          // public dir yet), which produced visible broken-image
          // placeholders in the first ~1 s of every app load.
          src={logoUrl}
          alt="OpenSwarm"
          sx={{ width: 26, height: 26, objectFit: 'contain', flexShrink: 0 }}
        />
        {!collapsed && (
          <Typography
            sx={{
              fontWeight: 600,
              fontSize: '1rem',
              color: c.text.primary,
              // Unified sans across the whole template — was a mix of
              // FONT_SERIF (which falls back to Times on systems without
              // "Anthropic Sans") and FONT_SANS, which read as two
              // different apps stitched together. Inherit the body
              // font instead.
              fontFamily: 'inherit',
              letterSpacing: '-0.015em',
              whiteSpace: 'nowrap',
            }}
          >
            OpenSwarm
          </Typography>
        )}
      </Box>

      <List sx={{ flex: 1, px: collapsed ? 1 : 2, pt: 1, gap: 0.5 }}>
        {NAV_ITEMS.map(({ path, label, icon: Icon }) => {
          const isActive =
            path === '/' ? location.pathname === '/' : location.pathname.startsWith(path);

          const button = (
            <ListItemButton
              key={path}
              component={NavLink}
              to={path}
              sx={{
                // Fully pill-shaped — Claude Design's nav items are
                // capsules, not 4-8 px rounded rectangles. 999 px clamps
                // to the natural height = perfect pill.
                borderRadius: 999,
                mb: 0.5,
                py: 1,
                px: collapsed ? 0 : 1.75,
                justifyContent: collapsed ? 'center' : 'flex-start',
                // Background-fill active state instead of an underline
                // bar. The fill uses a richer accent-tinted bg so the
                // pill reads as the focal point of the sidebar.
                bgcolor: isActive ? `${c.accent.primary}1A` : 'transparent',
                '&:hover': {
                  bgcolor: isActive ? `${c.accent.primary}1A` : `${c.text.primary}08`,
                },
                transition: c.transition,
              }}
            >
              <ListItemIcon
                sx={{
                  color: isActive ? c.accent.primary : c.text.tertiary,
                  minWidth: collapsed ? 'auto' : 32,
                  justifyContent: 'center',
                }}
              >
                <Icon sx={{ fontSize: 19 }} />
              </ListItemIcon>
              {!collapsed && (
                <ListItemText
                  primary={label}
                  sx={{
                    '& .MuiListItemText-primary': {
                      color: isActive ? c.text.primary : c.text.muted,
                      fontSize: '0.9rem',
                      fontWeight: isActive ? 600 : 450,
                      fontFamily: 'inherit',
                      whiteSpace: 'nowrap',
                    },
                  }}
                />
              )}
            </ListItemButton>
          );

          return collapsed ? (
            <Tooltip key={path} title={label} placement="right">
              {button}
            </Tooltip>
          ) : (
            button
          );
        })}
      </List>

      <Box
        sx={{
          px: collapsed ? 1 : 2.5,
          py: 2,
          // Drop the hard borderTop here too — let the bg-color step
          // between the nav list and this footer do the work.
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'flex-start',
        }}
      >
        <Tooltip title={mode === 'light' ? 'Dark mode' : 'Light mode'} placement={collapsed ? 'right' : 'top'}>
          <IconButton
            onClick={toggleMode}
            size="small"
            sx={{
              color: c.text.tertiary,
              borderRadius: 999,
              '&:hover': { color: c.accent.primary, bgcolor: `${c.text.primary}08` },
              transition: c.transition,
            }}
          >
            {mode === 'light' ? (
              <DarkModeIcon sx={{ fontSize: 18 }} />
            ) : (
              <LightModeIcon sx={{ fontSize: 18 }} />
            )}
          </IconButton>
        </Tooltip>
        {!collapsed && (
          <Typography
            sx={{
              fontSize: '0.78rem',
              color: c.text.ghost,
              fontFamily: 'inherit',
              ml: 1,
            }}
          >
            {mode === 'light' ? 'Light' : 'Dark'}
          </Typography>
        )}
      </Box>
    </Box>
  );
};

export { SIDEBAR_WIDTH_EXPANDED, SIDEBAR_WIDTH_COLLAPSED };
export default Sidebar;
