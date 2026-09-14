import type Git from '../git'
import type { Partition } from './partition'

/**
 * The rows a person can pick from right now: the session's shown rows,
 * then the pre-session rows while that section is open.
 *
 * @param partition the fetch's rows, grouped
 * @param preSession whether the pre-session section is open
 * @returns the pickable rows in drawing order
 */
export function listedOf(
  partition: Partition,
  preSession: 'shown' | 'hidden',
): readonly Git.FileStat[] {
  const isOpen = preSession === 'shown'

  return isOpen
    ? [...partition.shown, ...partition.preSession]
    : partition.shown
}
