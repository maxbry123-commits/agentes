import type Backend from '../../backend'
import type Git from '../../git'
import type Todos from '../../todos'
import type Turns from '../../turns'
import type { BodyState } from '../body-state'
import type { Source } from '../source'

/**
 * Everything one drawing of the pane reads.
 *
 * The last good fetch, what the person picked, the selected file's body,
 * the transcript's turns and todos, and the pinned backend's words and
 * base modes (git's until one is pinned).
 */
export type PaneModel = {
  words: Backend.BackendWords
  baseModes: readonly Git.BaseMode[]
  isLoading: boolean
  hasSettled: boolean
  isOutsideRepository: boolean
  data: Git.DiffData | null
  requestedMode: Git.BaseMode
  selectedPath: string | null
  isNoiseShown: boolean
  isPreSessionShown: boolean
  source: Source
  turns: readonly Turns.TurnDiff[]
  body: Git.FileHunks | null
  bodyState: BodyState
  todos: Todos.TodoProgress
  armedPath: string | null
  isFocused: boolean
}
