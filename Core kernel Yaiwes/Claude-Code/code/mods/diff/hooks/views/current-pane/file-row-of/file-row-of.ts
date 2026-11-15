import type Git from '../../../git'
import Sections from '../../sections'

/**
 * A fetched row as the list draws it: its counts, or a note in their
 * place (`untracked`, `Binary file`, `renamed`), and selection.
 *
 * @param file the row
 * @param selectedPath the selected file's path, or null
 * @returns the row model
 */
export function fileRowOf(
  file: Git.FileStat,
  selectedPath: string | null,
): Sections.FileRowModel {
  const isRenamed = file.renamedFrom !== null

  const note = file.isUntracked
    ? 'untracked'
    : file.isBinary
      ? 'Binary file'
      : isRenamed
        ? 'renamed'
        : null

  return {
    key: Sections.fileKeyOf(file.path),
    path: file.path,
    added: file.added,
    removed: file.removed,
    note,
    isSelected: file.path === selectedPath,
  }
}
