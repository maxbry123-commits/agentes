import { modeLabelOf } from './mode-label-of'
import type { PaneModel } from './pane-model'

/**
 * The dim line under the header naming what the diff compares against
 * (ReplDiffSidebar diffBaseLabel), or null for none.
 *
 * Hidden in settled session mode and before any fetch; the requested mode
 * with an ellipsis while its fetch is pending; on an unborn HEAD with
 * rows, what the rows are instead.
 *
 * @param model the mode the person picked, the last good fetch, and the
 *   backend's words
 * @param filesCount the header's session file count
 * @returns the line, or null
 */
export function baseLabelOf(
  model: Pick<PaneModel, 'requestedMode' | 'data' | 'words'>,
  filesCount: number,
): string | null {
  const { requestedMode, data } = model

  if (!data) {
    return null
  }

  if (data.isUnborn) {
    const hasRows = filesCount > 0

    return hasRows ? 'no commits yet — showing staged and new files' : null
  }

  const isPending = requestedMode !== data.mode
  const isSettledSession = !isPending && requestedMode === 'session'

  if (isSettledSession) {
    return null
  }

  const phase = isPending ? 'pending' : 'settled'
  const label = modeLabelOf(model, data.source, phase)

  return isPending ? `${label}…` : label
}
