// The zone catalog the tiling MENUS render. The geometry itself lives in canvas/tiledGeometry.

export const ZONE_LABELS: Record<string, string> = {
  fill: 'Fill', left: 'Left half', right: 'Right half', top: 'Top half', bottom: 'Bottom half',
  tl: 'Top left', tr: 'Top right', bl: 'Bottom left', br: 'Bottom right',
};

// The one grid every tiling surface renders: the green-dot hover menu and the right-click "Tile to
// zone" submenu both map this, so they can never drift apart on which zones exist. Thirds were cut
// (Eric 2026-08-09): the geometry still restores an old t3* card fine, the menus just stop offering it.
export const TILE_GROUPS: { label: string; zones: string[] }[] = [
  { label: 'Fill and halves', zones: ['fill', 'left', 'right', 'top', 'bottom'] },
  { label: 'Quarters', zones: ['tl', 'tr', 'bl', 'br'] },
];
