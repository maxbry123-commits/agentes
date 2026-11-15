import type Types from '../types'
import { datingsOf } from './datings-of'

/**
 * The tracked rows, `isPreSession` set on each whose file was modified
 * before the session began, by mtime alone as the built-in panel tags them.
 *
 * A file that cannot be dated (deleted this session, a symbolic link, past
 * the listing budget) stays session work, so nothing real is hidden.
 *
 * @param context the fetch: its stamp probe and the session's start
 * @param files the tracked rows
 * @returns the rows, tagged
 */
export async function tagPreSession(
  context: Types.DatingContext,
  files: readonly Types.FileStat[],
): Promise<readonly Types.FileStat[]> {
  const datings = await datingsOf(
    context,
    files.map(file => file.path),
  )

  return files.map(file => ({
    ...file,
    isPreSession: datings.get(file.path) === 'pre-session',
  }))
}
