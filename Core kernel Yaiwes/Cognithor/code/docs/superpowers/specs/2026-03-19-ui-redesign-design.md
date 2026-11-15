# Cognithor UI Redesign — Design Specification

**Date:** 2026-03-19
**Status:** Approved
**Target:** v0.47.0+

---

## Problem Statement

The current Flutter UI is functional but visually dull. Young, tech-affine users expect a premium, futuristic experience. The UI lacks visual identity, wow-factor, and modern design patterns.

## Design Goals

1. **Sci-Fi Command Center** aesthetic with Cyberpunk-Neon, Glassmorphism, and Gaming-Community feel
2. **Never boring** — animations, glow effects, living elements everywhere
3. **High contrast** — readability must not suffer despite visual effects
4. **Complexity stays** — the app is powerful, but organization improves

---

## 1. Color System

### Primary Palette
- **Neon Violett**: `#8B5CF6` (primary accent)
- **Gold**: `#FFD700` (secondary accent, branding)
- **Matrix Green**: `#00FF41` (tertiary, data/code accent)

### Section Colors (each screen has its own neon identity)
| Section | Color | Hex |
|---------|-------|-----|
| Chat | Electric Cyan | `#00E5FF` |
| Dashboard | Neon Green | `#00FF41` |
| Admin/Config | Neon Violett | `#8B5CF6` |
| Identity | Gold | `#FFD700` |
| Skills | Neon Pink | `#FF1493` |

### Surfaces
- **Background**: Deep space black `#050510`
- **Surface**: Dark navy with subtle blue tint `#0A0F24`
- **Glass panels**: `rgba(255,255,255,0.04)` with `BackdropFilter` blur(16)
- **Borders**: Section-color at 15% opacity, glow on hover at 30%

---

## 2. Navigation — Morphing Sidebar

### Behavior
- **Chat screen**: Sidebar collapses to 64px (icon-only), maximizes chat space
- **Admin screen**: Sidebar expands to 260px with sub-navigation
- **Dashboard**: Sidebar minimizes to 48px or hides completely
- Animated transitions (300ms easeOutQuart)

### Visual Style
- Active item: Neon-glow pill background (section color at 20%), icon pulses
- Hover: Icon scales 1.1x, subtle glow appears
- Section indicator: Thin vertical neon line on left edge of active item
- Logo at top with subtle breathing animation

### Command Bar (Top)
- Slim 40px bar across top
- Left: Current screen breadcrumb with section-color icon
- Center: Quick search (Ctrl+K trigger)
- Right: Backend status dot (green=running), active model name, token count badge

---

## 3. Chat Screen — Immersive + Split View

### Chat Bubbles
- User: Right-aligned, gradient from section-cyan to darker shade, subtle glow border
- Assistant: Left-aligned, glassmorphism panel with blur, section-color left accent bar
- Messages slide in with fade+translateY animation (200ms stagger)
- Code blocks: Dark surface with syntax highlighting, neon-bordered, copy button with glow

### Typing Indicator
- Holographic waveform visualizer (3 animated sine waves in section color)
- Replaces the boring bouncing dots

### Context Side Panel
- Appears on the right (350px) when relevant
- Web search: Shows source cards with favicons and snippets
- Code execution: Live preview/output
- Tool execution: Animated progress with tool name and phase
- Glassmorphism panel with blur background

### Hacker Mode (Toggle)
- Switch icon in chat AppBar
- Activates: Monospace font (JetBrains Mono), green-on-black color scheme
- Shows raw API calls, JSON responses, tool parameters
- Matrix-style falling characters as subtle background effect
- All messages rendered as terminal output with timestamps

---

## 4. Dashboard — Command Center

### Layout
- **Hero**: Robot Office (50-60% of viewport height) — the living visualization
- **Overlays IN the scene**: Real data displayed as elements in the office
  - Server rack LEDs: Map to actual CPU/memory usage
  - Kanban board sticky notes: Map to real PGE pipeline phases
  - Monitor screens: Show actual recent chat snippets
  - Ceiling light intensity: Maps to system load
- **Below the scene**: Radial gauge widgets for key metrics
  - CPU Usage (radial gauge with neon arc)
  - Memory Usage (radial gauge)
  - Token consumption (animated ring with daily/monthly)
  - Response time (speedometer-style)
- **Bottom ticker**: Scrolling event log with severity-colored entries

### Metric Cards
- Glassmorphism cards with section-color accent
- Numbers animate up when values change (AnimatedCounter)
- Subtle particle effects on significant changes

---

## 5. Config/Admin — 5 Categories

### Category Structure

| Category | Icon | Sub-pages |
|----------|------|-----------|
| **AI Engine** | 🧠 | Providers, Models, Planner, Executor, Prompts |
| **Channels** | 📡 | All 17 channels, Voice Config |
| **Knowledge** | 💾 | Memory, Agents, Bindings, Web Search |
| **Security** | 🛡️ | Security, Gatekeeper, Sandbox, Database |
| **System** | ⚙️ | General, Language, Logging, Cron, MCP, System |

### Visual Style
- Category tabs across the top with section-color underline
- Each category has a neon-colored header banner with icon
- Sub-pages as vertical list within the category (current sidebar style)
- Save bar: Glassmorphism floating bar at bottom with glow when dirty

### First-Run Wizard
- 3-step guided setup: Provider → Model → First Test
- Full-screen overlay with step indicator
- Animated transitions between steps
- Success celebration with confetti/particles

---

## 6. Global Effects

### Glassmorphism
- All cards/panels use `BackdropFilter` with `ImageFilter.blur(sigmaX: 16, sigmaY: 16)`
- Background: Semi-transparent with section-color tint
- Border: 1px with section-color at 15% opacity
- Must maintain readability — text always high contrast

### Animations
- Page transitions: Fade + slide (250ms easeOutQuart)
- List items: Staggered entrance (50ms per item)
- Numbers: AnimatedCounter for all metric values
- Hover: Scale 1.02x + glow increase on all interactive elements
- Loading: ShimmerLoading with section-color gradient

### Particles/Effects
- Subtle floating particles in background (very low density)
- Neon glow on focus states
- Confetti on celebrations (task completion, first setup)

---

## 7. Responsive Behavior

- **Desktop (>1024px)**: Full sidebar + content + side panel
- **Tablet (600-1024px)**: Collapsed sidebar + content
- **Mobile (<600px)**: Bottom navigation + full content, no side panel

---

## 8. Typography

- **Primary**: Inter (already in use via Google Fonts)
- **Monospace**: JetBrains Mono for code/hacker mode
- **Headings**: Semi-bold, tight letter-spacing (-0.3px)
- **Section titles**: Section-color with subtle text-shadow glow

---

## Implementation Priority

1. Color system + Glassmorphism foundation
2. Morphing sidebar + Command bar
3. Chat screen redesign (immersive + split view)
4. Dashboard Command Center with real data overlays
5. Config reorganization (5 categories)
6. Hacker Mode toggle
7. First-run wizard
8. Polish + particle effects
