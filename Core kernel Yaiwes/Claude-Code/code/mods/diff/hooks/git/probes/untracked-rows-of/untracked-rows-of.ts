import Limits from '../../../limits'
import type Types from '../../types'
import { datingsOf } from '../datings-of'
import type { UntrackedPlace } from '../untracked-place'

/**
 * Listed untracked paths as 0/0 rows: the session's own first, then,
 * when the scope asks, the tagged pre-session ones, up to the slots.
 *
 * At most MAX_UNTRACKED_PROBES are dated; a file past that or past the
 * listing budget reads as pre-session, an undatable one as the session's
 * (the built-in panel's rule).
 *
 * @param context the fetch's stamp probe and session start
 * @param paths the untracked paths, root-relative, as the lister printed them
 * @param place the free row slots and the scope
 * @returns the rows to merge after the tracked ones
 */
export async function untrackedRowsOf(
  context: Types.DatingContext,
  paths: readonly string[],
  place: UntrackedPlace,
): Promise<readonly Types.FileStat[]> {
  const probedPaths = paths.slice(0, Limits.MAX_UNTRACKED_PROBES)
  const datings = await datingsOf(context, probedPaths)

  const probed = probedPaths.map(path => ({
    path,
    isPreSession: datings.get(path) !== 'session',
  }))

  const isWithPreSession = place.scope === 'with-pre-session'

  const earlier = isWithPreSession
    ? [
        ...probed.filter(file => file.isPreSession),
        ...paths
          .slice(Limits.MAX_UNTRACKED_PROBES)
          .map(path => ({ path, isPreSession: true })),
      ]
    : []

  const ordered = [...probed.filter(file => !file.isPreSession), ...earlier]

  return ordered.slice(0, place.slots).map(file => ({
    path: file.path,
    renamedFrom: null,
    added: 0,
    removed: 0,
    isBinary: false,
    isUntracked: true,
    isPreSession: file.isPreSession,
  }))
}
