import type Backend from '../../../backend'
import type Git from '../../../git'
import type PaneState from '../../../pane-state'

/**
 * The selected file as its body draws it.
 *
 * The path, what kind of row it is, its hunks once read, whether it is armed
 * for the next prompt, and the backend's words for an untracked row's note.
 */
export type DetailModel = {
  words: Pick<Backend.BackendWords, 'untrackedNoteOf'>
  path: string
  renamedFrom: string | null
  isUntracked: boolean
  isBinary: boolean
  body: Git.FileHunks | null
  bodyState: PaneState.BodyState
  isArmed: boolean
}
