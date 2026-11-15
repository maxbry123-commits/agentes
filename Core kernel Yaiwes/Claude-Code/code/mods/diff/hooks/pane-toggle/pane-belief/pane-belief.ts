/**
 * What the plugin knows of its pane when `/diff` runs.
 *
 * Whether it opened it and never closed it, whether it drew when a redraw
 * was asked, and the terminal's width as last drawn (null before any draw).
 */
export type PaneBelief = {
  isBelievedOpen: boolean
  wasDrawnWhenProbed: boolean
  columns: number | null
}
