import type React from 'react';

// The one right-click grammar for the whole shell (cards, tab strip, dock, minimized rail, empty
// canvas). Surfaces describe rows; CardContextMenu owns rendering, placement, and keyboard nav.

export interface CardMenuAction {
  kind?: 'action';
  label: string;
  /** Right-aligned chip. Build it with chord() so it matches the platform; never invent unbound keys. */
  shortcut?: string;
  icon?: React.ReactNode;
  danger?: boolean;
  disabled?: boolean;
  /** Renders a leading check; use for toggles that are currently on. */
  checked?: boolean;
  /** One level only. Deep nesting is a menu smell. */
  submenu?: CardMenuRow[];
  onClick?: () => void;
}

export interface CardMenuSeparator {
  kind: 'separator';
}

export interface CardMenuHeader {
  kind: 'header';
  /** Sentence case, never uppercase. */
  label: string;
}

export type CardMenuRow = CardMenuAction | CardMenuSeparator | CardMenuHeader;

export interface CardMenuRequest {
  x: number;
  y: number;
  items: CardMenuRow[];
  /** Optional inline-rename affordance: shown as the first row with an editable input. */
  rename?: { value: string; onCommit: (next: string) => void };
}

export const CARD_MENU_EVENT = 'openswarm:card-context-menu';

export function isMenuAction(row: CardMenuRow): row is CardMenuAction {
  return row.kind === undefined || row.kind === 'action';
}

/** Text fields keep the OS menu: right-clicking a URL bar or composer is how you paste. */
export function isNativeMenuTarget(e: { target: EventTarget | null }): boolean {
  const t = e.target as HTMLElement | null;
  return !!t?.closest?.('input, textarea, [contenteditable="true"]');
}

interface MenuTriggerEvent {
  clientX: number;
  clientY: number;
  preventDefault: () => void;
  stopPropagation: () => void;
}

export function openCardContextMenu(e: MenuTriggerEvent, req: Omit<CardMenuRequest, 'x' | 'y'>): void {
  e.preventDefault();
  e.stopPropagation();
  window.dispatchEvent(new CustomEvent(CARD_MENU_EVENT, { detail: { ...req, x: e.clientX, y: e.clientY } }));
}
