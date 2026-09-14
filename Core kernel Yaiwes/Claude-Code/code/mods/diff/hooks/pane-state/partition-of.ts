import Classify from '../classify'
import type Git from '../git'
import type { Partition } from './partition'

/**
 * A fetch's rows split the way ReplDiffSidebar splits them: pre-session
 * rows apart, tests and generated files counted and hidden unless shown.
 *
 * No read-deny bucket: the pane feeds nothing to the model on its own.
 *
 * @param files the fetched rows
 * @param noise `shown` keeps tests and generated files in the list
 * @returns the groups
 */
export function partitionOf(
  files: readonly Git.FileStat[],
  noise: 'shown' | 'hidden',
): Partition {
  const preSession = files.filter(file => file.isPreSession)
  const session = files.filter(file => !file.isPreSession)
  const quiet = session.filter(file => !Classify.isNoiseFile(file.path))

  return {
    shown: noise === 'shown' ? session : quiet,
    preSession,
    noiseCount: session.length - quiet.length,
  }
}
