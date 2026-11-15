import Argv from '../argv'
import { EMPTY_FILE_HUNKS } from '../empty-file-hunks'
import Parse from '../parse'
import type Types from '../types'

/**
 * One file's hunks against the base its row was read against, so body and
 * counts agree, by literal pathspec, as the built-in panel reads hunks.
 *
 * A rename passes both its paths so git pairs them; an untracked or binary
 * row, or on an unborn HEAD a file edited after staging, has no honest
 * body and answers no hunks.
 *
 * @param run runs git against the pinned repository
 * @param data the fetch the row belongs to
 * @param file the row
 * @returns the parsed body, or null when git failed
 */
export async function fetchFileHunks(
  run: Types.GitRun,
  data: Types.DiffData,
  file: Types.FileStat,
): Promise<Types.FileHunks | null> {
  const hasNoBody =
    file.isUntracked || file.isBinary || data.stalePaths.includes(file.path)

  if (hasNoBody) {
    return EMPTY_FILE_HUNKS
  }

  const { exitCode, stdout } = await run([
    '--literal-pathspecs',
    ...Argv.DIFF_LEADING_ARGS,
    data.baseRef,
    '--',
    ...(file.renamedFrom === null ? [] : [file.renamedFrom]),
    file.path,
  ])

  return exitCode === 0 ? Parse.parseFileDiff(stdout) : null
}
