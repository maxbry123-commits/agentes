---
name: themed-ui-design
description: Use when building, designing, or modifying any frontend UI component, page, or interface for the OpenSwarm app. Covers both general design excellence principles AND the specific OpenSwarm theme system, tokens, and component conventions. Trigger this for any React/MUI component work, UI design tasks, layout creation, styling questions, or when the user asks to build something visual.
---

# Themed UI Design

Build distinctive, production-grade frontend interfaces for the OpenSwarm app that are visually striking AND perfectly aligned with the app's Apple-style design system: crisp near-white (or elevated-gray) surfaces, ink-precise type, hairline separators, one restrained blue accent.

This skill combines two concerns:
1. **Design Excellence** — Bold aesthetic thinking, anti-slop principles, creative typography/color/motion
2. **Theme Compliance** — OpenSwarm's specific tokens, MUI conventions, and component patterns

Both matter equally. A component that follows the token system but looks generic has failed. A component that looks stunning but ignores the theme system has also failed.

---

## Part 1: Design Thinking (Do This First)

Before writing any code, answer these questions:

- **Purpose**: What problem does this interface solve? Who interacts with it?
- **Tone within the brand**: The aesthetic is Apple-adjacent — luminous, precise, quietly confident — but within that envelope there's range. Is this component playful? Dense and utilitarian? Spacious and luxurious? Dramatic?
- **Differentiation**: What makes this component memorable? What's the one detail someone would notice and appreciate?
- **Hierarchy**: What's the single most important thing on screen? Everything else should defer to it.

**CRITICAL**: The brand is "an app that could ship with macOS." Every component should feel like it belongs in that world — clean surfaces, generous whitespace, hairline structure, motion with intent. But within that world, make bold choices. Asymmetric layouts. Unexpected spacing. Elegant motion. The goal is *intentional* design, not safe design.

### Anti-Slop Checklist

NEVER produce generic AI-generated aesthetics:
- ❌ Cookie-cutter card grids with no visual hierarchy
- ❌ Predictable, evenly-spaced layouts with no rhythm
- ❌ Animations that exist for no reason (bouncing icons, gratuitous fades)
- ❌ Every element getting equal visual weight
- ❌ Defaulting to the most obvious layout for every problem

ALWAYS pursue:
- ✅ Clear visual hierarchy — one thing dominates, others support
- ✅ Intentional spacing rhythm — not everything needs equal gaps
- ✅ Motion that communicates meaning (entrance = "I'm new", hover = "I'm interactive")
- ✅ Typography that creates atmosphere, not just displays text
- ✅ At least one unexpected detail that rewards attention

---

## Part 2: Tech Stack (Non-Negotiable)

| Concern | Tool | Notes |
|---------|------|-------|
| Framework | React 18 + TypeScript | Functional components only |
| UI Library | **MUI (Material UI) v7** | Use MUI components, not raw HTML |
| Styling | **MUI `sx` prop** | NO CSS files, NO styled-components, NO inline `style={}` |
| State | Redux Toolkit | `useAppDispatch()` / `useAppSelector()` typed hooks |
| Theming | `useClaudeTokens()` hook | NEVER hardcode colors |
| Animation | Framer Motion | For complex entrance/drag/spring animations |
| Icons | `@mui/icons-material` | Import individually, not barrel |
| Routing | react-router-dom v7 | `useNavigate`, `NavLink` |
| Markdown | react-markdown + remark-gfm | For rendered markdown |
| Path alias | `@/` → `src/` | Use `@/shared/...`, `@/app/...` |

---

## Part 3: The Token System

Access tokens via hook — **never hardcode colors**:
```tsx
import { useClaudeTokens } from '@/shared/styles/ThemeContext';
const c = useClaudeTokens();
```

### 3.1 Color Palette

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `c.bg.page` | `#F5F5F7` Apple light gray | `#1C1C1E` elevated iOS gray | Full-page background |
| `c.bg.surface` | `#FFFFFF` | `#2C2C2E` | Cards, panels, dialogs |
| `c.bg.elevated` | `#FBFBFD` | `#3A3A3C` | Hover states, raised elements |
| `c.bg.secondary` | `#F2F2F7` | `#242426` | Sidebar, secondary panels |
| `c.bg.inverse` | `#1D1D1F` | `#F5F5F7` | Tooltips, inverted elements |
| `c.text.primary` | `#1D1D1F` ink | `#F5F5F7` | Headings, body text |
| `c.text.secondary` | `#48484A` | `#D1D1D6` | Secondary labels |
| `c.text.tertiary` | `#6E6E73` | `#98989D` | Placeholders, captions |
| `c.text.muted` | `#86868B` | `#8E8E93` | De-emphasized text |
| `c.text.ghost` | `rgba(110,110,115,0.5)` | `rgba(152,152,157,0.5)` | Timestamps, hints |
| `c.accent.primary` | `#007AFF` system blue | `#0A84FF` | Primary buttons, links, active indicators |
| `c.accent.hover` | `#0071E3` | `#409CFF` | Hover on accent |
| `c.accent.pressed` | `#0062CC` | `#0070E0` | Active/pressed state |
| `c.user.bubble` | `#E9E9EB` | `#3A3A3C` | User chat bubbles |

### 3.2 Borders

Borders are extremely subtle — transparency, not solid colors:
```tsx
border: `1px solid ${c.border.subtle}`    // 6-8% opacity — default for cards
border: `1px solid ${c.border.medium}`    // 8-12% opacity — dividers
border: `1px solid ${c.border.strong}`    // 15-20% opacity — hover, emphasis
border: `0.5px solid ${c.border.medium}`  // Hairline dividers
```

### 3.3 Shadows

Very soft, low-contrast. No heavy drop shadows:
```tsx
c.shadow.sm  // "0 1px 2px rgba(0,0,0,0.05)"    — cards at rest
c.shadow.md  // "0 4px 16px rgba(0,0,0,0.06)"   — hover elevation
c.shadow.lg  // "0 12px 32px rgba(0,0,0,0.12)"  — dialogs, drag
```

### 3.4 Border Radius

```tsx
c.radius.xs   // 5px  — chips, badges
c.radius.sm   // 8px  — input fields
c.radius.md   // 10px — chips, tags
c.radius.lg   // 12px — buttons, list items
c.radius.xl   // 16px — cards, panels (the soft continuous-corner feel)
c.radius.full // 9999px — pills, avatars
```

### 3.5 Typography

**SF-first, one sans everywhere** — the type IS the Apple identity:
```
Font family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", ui-sans-serif, system-ui, "Helvetica Neue", "Inter", Arial, sans-serif
Mono font:   ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace
```
Headings get tight tracking (`letterSpacing: '-0.01em'` to `-0.02em` as sizes grow); body stays default.

| Use Case | Size | Weight |
|----------|------|--------|
| Page heading | `h6` or manual | 700 |
| Section heading | `0.95rem` | 600 |
| Body text | `0.875rem` | 400 |
| Small label | `0.8rem` | 400 |
| Caption/timestamp | `0.75rem` / `0.65rem` | 400 |
| Button text | inherited | 500 |

**Important**: `textTransform: 'none'` on ALL buttons. No uppercase anywhere.

### 3.6 Transitions

Signature easing for interactive elements:
```tsx
transition: c.transition  // "all 280ms cubic-bezier(0.32, 0.72, 0, 1)" — the macOS ease
```
For micro-interactions:
```tsx
transition: 'opacity 0.15s'
transition: 'all 0.2s ease'
```

### 3.7 Accent-Tinted Backgrounds

The signature technique for active/selected states — accent color at very low opacity:
```tsx
bgcolor: `${c.accent.primary}0F`   // ~6% — active state
bgcolor: `${c.accent.primary}08`   // ~3% — hover state
bgcolor: `${c.accent.primary}0A`   // ~4% — subtle hover
bgcolor: `${c.accent.primary}0C`   // ~5% — hover on active
bgcolor: `${c.accent.primary}18`   // ~9% — decorative fill
```

### 3.8 Spacing (MUI units = 8px)

| `sx` value | Pixels | Usage |
|------------|--------|-------|
| `p: 0.25` | 2px | Tiny icon padding |
| `gap: 0.5` | 4px | Tight button groups |
| `p: 0.75` | 6px | Compact list items |
| `gap: 1` / `p: 1` | 8px | Standard small gap |
| `gap: 1.5` | 12px | Logo + text |
| `p: 2` | 16px | Card content |
| `p: 2.5` | 20px | Header/section |

---

## Part 4: Component Structure

Every component follows this skeleton:

```tsx
import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import SomeIcon from '@mui/icons-material/SomeIcon';
import { useAppDispatch, useAppSelector } from '@/shared/hooks';
import { useClaudeTokens } from '@/shared/styles/ThemeContext';

interface Props {
  // Explicit interface, not inline types
}

const MyComponent: React.FC<Props> = ({ prop1, prop2 }) => {
  const c = useClaudeTokens();
  const dispatch = useAppDispatch();

  return (
    <Box sx={{ /* styling */ }}>
      {/* content */}
    </Box>
  );
};

export default MyComponent;
```

**Rules:**
- `export default` the component
- Destructure props in the signature
- `const c = useClaudeTokens()` as the first line
- `Box` for containers (not `div`), `Typography` for text (not `p`/`span`/`h1`)
- All styling via `sx={{}}` — never `style={{}}`
- Import MUI components from individual paths, not barrel

---

## Part 5: Pattern Library

### 5.1 Card
```tsx
<Box sx={{
  cursor: 'pointer',
  borderRadius: 3,
  border: `1px solid ${c.border.subtle}`,
  bgcolor: c.bg.surface,
  overflow: 'hidden',
  transition: 'all 0.2s ease',
  '&:hover': {
    borderColor: c.border.strong,
    boxShadow: c.shadow.md,
    transform: 'translateY(-2px)',
  },
  '&:hover .card-actions': { opacity: 1 },
}}>
```

### 5.2 Hover-Reveal Actions
```tsx
<Box className="card-actions" sx={{
  position: 'absolute',
  top: 8, right: 8,
  display: 'flex',
  gap: 0.5,
  opacity: 0,
  transition: 'opacity 0.15s',
}}>
  <Tooltip title="Run">
    <IconButton size="small" sx={{
      bgcolor: c.bg.surface,
      color: c.accent.primary,
      boxShadow: c.shadow.sm,
      '&:hover': { bgcolor: c.bg.elevated },
    }}>
      <PlayArrowIcon sx={{ fontSize: 16 }} />
    </IconButton>
  </Tooltip>
</Box>
```

### 5.3 Sidebar Nav Item
```tsx
<ListItemButton sx={{
  borderRadius: 2,
  mb: 1,
  bgcolor: isActive ? `${c.accent.primary}0F` : 'transparent',
  '&:hover': { bgcolor: `${c.accent.primary}08` },
}}>
  <ListItemIcon sx={{
    color: isActive ? c.text.primary : c.text.tertiary,
    minWidth: 40,
  }}>
    <SomeIcon />
  </ListItemIcon>
  <ListItemText primary="Label" sx={{
    '& .MuiListItemText-primary': {
      color: isActive ? c.text.primary : c.text.muted,
      fontSize: '0.875rem',
      fontWeight: isActive ? 500 : 400,
    },
  }} />
</ListItemButton>
```

### 5.4 Icon Buttons (Always in Tooltip)
```tsx
<Tooltip title="Settings">
  <IconButton size="small" sx={{
    color: c.text.tertiary,
    '&:hover': { color: c.accent.primary, bgcolor: `${c.accent.primary}0A` },
    transition: c.transition,
  }}>
    <SettingsIcon sx={{ fontSize: 18 }} />
  </IconButton>
</Tooltip>
```

### 5.5 Dialog/Modal
```tsx
<Dialog
  open={open}
  onClose={handleClose}
  PaperProps={{
    sx: {
      borderRadius: 4,
      bgcolor: c.bg.surface,
      border: `1px solid ${c.border.subtle}`,
      boxShadow: c.shadow.lg,
      maxWidth: 600,
      width: '100%',
    },
  }}
  slotProps={{
    backdrop: { sx: { backdropFilter: 'blur(4px)' } },
  }}
>
```

### 5.6 Status Chips
```tsx
<Chip label="Active" size="small" sx={{
  bgcolor: c.status.successBg,
  color: c.status.success,
  fontWeight: 500,
  fontSize: '0.75rem',
}} />
```

### 5.7 Destructive Actions
```tsx
<IconButton sx={{
  color: c.text.ghost,
  '&:hover': { color: c.status.error },
}}>
  <DeleteOutlineIcon sx={{ fontSize: 14 }} />
</IconButton>
```

### 5.8 Custom Scrollbar
```tsx
sx={{
  overflow: 'auto',
  '&::-webkit-scrollbar': { width: 4 },
  '&::-webkit-scrollbar-track': { background: 'transparent' },
  '&::-webkit-scrollbar-thumb': { background: c.border.medium, borderRadius: 2 },
  scrollbarWidth: 'thin',
  scrollbarColor: `${c.border.medium} transparent`,
}}
```

### 5.9 Text Truncation
```tsx
// Single line:
sx={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}

// Multi-line clamp (2 lines):
sx={{
  display: '-webkit-box',
  WebkitLineClamp: 2,
  WebkitBoxOrient: 'vertical',
  overflow: 'hidden',
}}
```

---

## Part 6: Animation Conventions

### Framer Motion (entrance, drag, springs)
```tsx
import { motion } from 'framer-motion';

<motion.div
  initial={{ opacity: 0, scale: 0.3 }}
  animate={{ opacity: 1, scale: 1 }}
  transition={{ type: 'spring', stiffness: 400, damping: 28, mass: 0.6 }}
/>
```

### CSS Keyframes (via sx)
```tsx
// Pulsing dot:
sx={{
  '@keyframes pulse': {
    '0%, 100%': { opacity: 0.4, transform: 'scale(0.8)' },
    '50%': { opacity: 1, transform: 'scale(1.2)' },
  },
  animation: 'pulse 1.5s ease-in-out infinite',
}}
```

### Motion Philosophy
- **Entrance**: Staggered reveals with `animation-delay` create delight
- **Hover**: Cards lift (`translateY(-2px)`), borders sharpen, shadows deepen
- **Active**: `transform: 'scale(0.98)'` on press
- **Reveal**: Actions fade in on parent hover (opacity 0 → 1)
- **Scroll**: Use scroll-triggered animations sparingly but memorably
- One well-orchestrated page load > scattered micro-interactions

---

## Part 7: Hard Rules (Don'ts)

- ❌ Hardcode any color value — use `c.xxx` tokens
- ❌ CSS files, CSS modules, styled-components, emotion `css` prop
- ❌ Raw HTML (`div`, `span`, `p`, `button`) — use MUI equivalents
- ❌ `style={{}}` — use `sx={{}}`
- ❌ Uppercase text transforms on buttons or labels
- ❌ Heavy/solid borders — always transparent/opacity-based
- ❌ Bright/saturated colors outside the token palette
- ❌ Sharp corners (0 radius) on interactive elements
- ❌ Icon buttons without `<Tooltip>` wrapper
- ❌ Barrel imports from `@mui/material` — import each component from its path
- ❌ `React.memo` unless measured performance need
- ❌ Separate type files — keep interfaces colocated unless shared

---

## Part 8: File & Folder Conventions

Routes use **file-based routing** via `vite-plugin-pages`. Any `.tsx` file in `src/pages/` automatically becomes a route (e.g. `src/pages/health.tsx` → `/health`, `src/pages/index.tsx` → `/`).

```
src/pages/                    # File-based routes (auto-registered)
  index.tsx                   # Home page → /
  health.tsx                  # Health page → /health
  settings.tsx                # Example → /settings

src/app/
  Main.tsx                    # Root: providers + BrowserRouter + AppShell
  components/
    Layout/
      AppShell.tsx            # Sidebar + content area shell
      Sidebar.tsx             # Navigation rail, theme toggle
    SharedComponent.tsx       # Truly shared/reusable

src/shared/
  hooks.ts                    # useAppDispatch, useAppSelector
  state/                      # Redux slices
  styles/                     # Theme tokens, context
  modals/                     # Modal components
```

---

## Part 9: Quality Checklist

Before delivering any component, verify:

1. ☐ `useClaudeTokens()` is the first hook call
2. ☐ Zero hardcoded colors — every color references a token
3. ☐ All styling via `sx={{}}` — no `style`, no CSS files
4. ☐ Every `IconButton` wrapped in `Tooltip`
5. ☐ `textTransform: 'none'` on all buttons
6. ☐ Borders use `c.border.*` tokens (opacity-based)
7. ☐ Interactive elements have `transition: c.transition`
8. ☐ Active states use accent-tinted backgrounds (`${c.accent.primary}0F`)
9. ☐ Cards have subtle border + shadow + hover lift pattern
10. ☐ Component has clear visual hierarchy — not everything equal weight
11. ☐ At least one thoughtful design detail that elevates beyond generic
12. ☐ Dark mode works correctly (tokens handle this automatically if used properly)
13. ☐ MUI imports are from individual paths, not barrel
14. ☐ `export default` at the bottom
