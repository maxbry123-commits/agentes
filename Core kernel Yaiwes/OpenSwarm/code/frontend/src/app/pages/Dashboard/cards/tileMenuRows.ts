import type { CardMenuRow } from '../desktop/openCardContextMenu';
import { TILE_GROUPS, ZONE_LABELS } from './tileZones';

// The green-dot tiling grid, spelled out as words for the right-click path. Same catalog, so the two
// surfaces always offer the same zones.
export function tileMenuRows(onTile: (zone: string) => void, currentZone?: string): CardMenuRow[] {
  const rows: CardMenuRow[] = [];
  for (const group of TILE_GROUPS) {
    rows.push({ kind: 'header', label: group.label });
    for (const zone of group.zones) {
      rows.push({ label: ZONE_LABELS[zone], checked: currentZone === zone, onClick: () => onTile(zone) });
    }
  }
  return rows;
}
