import type { PaneOpenArgs } from 'claude-code'

/**
 * The part of `$.ui.open`'s argument that asks the surface for the
 * person's keyboard: what `/diff` adds and the first-edit open leaves out.
 */
export const FOCUSED_PANE: Pick<PaneOpenArgs, 'focus'> = Object.freeze({
  focus: true,
})
