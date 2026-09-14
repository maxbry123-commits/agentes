import type { GitDeps } from '../git-deps'
import type { StampProbe } from '../stamp-probe'

/**
 * What dating a path against the session takes: the session's start and
 * one stamp probe over the working tree's top.
 */
export type DatingContext = {
  deps: Pick<GitDeps, 'sessionStartMs'>
  stamps: StampProbe
}
