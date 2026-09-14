import type Git from '../../git'

/**
 * The file whose body the pane shows: the one the person picked while it is
 * still listed, else the first listed one, else none.
 *
 * @param listed the rows on screen, in order (session rows, then the
 *   pre-session rows while that section is open)
 * @param selectedPath the person's pick, or null
 * @returns the selected row, or null for an empty list
 */
export const selectionOf = (
  listed: readonly Git.FileStat[],
  selectedPath: string | null,
): Git.FileStat | null =>
  listed.find(file => file.path === selectedPath) ?? listed[0] ?? null
