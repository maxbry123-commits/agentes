import type Git from '../../git'
import type { PaneModel } from '../pane-model'

/**
 * A requested mode's name for the base line.
 *
 * Branch mode names its base branch from the data, or says what stands in
 * while none is known. A working-tree diff names its own base (`HEAD`, a
 * short sha); anything else falls back to the backend's word for it.
 *
 * @param model the mode the person picked, and the backend's words
 * @param source what the data on screen compares
 * @param phase `pending` while the requested mode's fetch has not landed
 * @returns the label without its pending ellipsis
 */
export function modeLabelOf(
  model: Pick<PaneModel, 'requestedMode' | 'words'>,
  source: Git.DiffSource,
  phase: 'pending' | 'settled',
) {
  const base = source.kind === 'working-tree' ? source.base : model.words.base

  switch (model.requestedMode) {
    case 'session':
      return 'this session'
    case 'uncommitted':
      return `uncommitted (vs ${base})`
    case 'branch':
      if (source.kind === 'branch') {
        return `branch vs ${source.baseBranch}`
      }

      return phase === 'pending' ? 'branch diff' : `vs ${base} (no base branch)`
  }
}
