import Limits from '../limits'
import type { PaneBelief } from './pane-belief'

/**
 * What `/diff` does, the one place its toggle is decided: close only when
 * the plugin opened the pane and it still draws; otherwise open, focused.
 *
 * Narrower than the built-in panel shows on, it answers the resize line
 * (`too-narrow`). The person's close raises nothing it hooks, so a pane
 * believed open is probed with a redraw first; a width not drawn yet opens.
 *
 * @param pane the plugin's belief, the probe's answer and the width
 * @returns `close`, `open` or `too-narrow`
 */
export function paneToggleOf(
  pane: PaneBelief,
): 'open' | 'close' | 'too-narrow' {
  const isClosing = pane.isBelievedOpen && pane.wasDrawnWhenProbed

  const isTooNarrow =
    pane.columns !== null && pane.columns < Limits.OPEN_MIN_COLUMNS

  return isClosing ? 'close' : isTooNarrow ? 'too-narrow' : 'open'
}
