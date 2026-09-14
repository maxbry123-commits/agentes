import type Backend from '../../backend'

/**
 * The pane's word for a fetch whose untracked listing the backend did not
 * give whole: the tracked rows stand, the new files are not counted.
 *
 * @param words the backend's words, naming the program that lists them
 * @returns the note
 */
export const untrackedWithheldTextOf = (
  words: Pick<Backend.BackendWords, 'lister'>,
) =>
  `Untracked files unavailable (${words.lister} could not list them); ` +
  'not counted'
