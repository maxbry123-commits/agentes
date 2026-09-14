import type Backend from '../backend'
import type Git from '../git'
import Names from '../names'
import type { EmptyState } from './empty-state'

/**
 * The headline that replaces the count when nothing is listed, worded as
 * ReplDiffSidebar words it, keyed on the mode the data was FETCHED in.
 *
 * Null while there are files to count. No data after a settled fetch is
 * "Diff unavailable"; no tracked rows while the untracked listing was
 * withheld claims nothing about new files.
 *
 * @param data the last good fetch, or null when none ever settled
 * @param filesCount the header's session file count
 * @param words the backend's words
 * @returns the empty state, or null
 */
export function emptyStateOf(
  data: Git.DiffData | null,
  filesCount: number,
  words: Backend.BackendWords,
): EmptyState | null {
  if (!data) {
    return {
      headline: 'Diff unavailable',
      hint:
        `Couldn't read the ${words.diffCommand} — it will retry on the ` +
        'next change',
    }
  }

  if (filesCount > 0) {
    return null
  }

  if (data.isUntrackedWithheld) {
    return {
      headline: 'No tracked changes',
      hint: Names.untrackedWithheldTextOf(words),
    }
  }

  if (data.isUnborn) {
    return {
      headline: 'No commits yet',
      hint: "Nothing to diff against until the repo's first commit",
    }
  }

  switch (data.mode) {
    case 'uncommitted':
      return { headline: 'No uncommitted changes', hint: null }
    case 'branch':
      if (data.source.kind === 'branch') {
        return {
          headline: `No changes vs ${data.source.baseBranch}`,
          hint: null,
        }
      }

      return {
        headline: `No changes vs ${data.source.base}`,
        hint:
          'No base branch to compare against — showing changes vs ' +
          data.source.base,
      }
    case 'session':
      return { headline: 'No changes this session', hint: null }
  }
}
