/* @jsxRuntime classic */
/* @jsx h */
/* @jsxFrag Fragment */
import type { RenderElement } from 'claude-code'

import type PaneState from '../../pane-state'
import type { Kit } from '../kit'
import Layout from '../layout'
import { closeButton } from './close-button'
import { diffStat } from './diff-stat'

/**
 * The pane's first line (ReplDiffSidebar's header row): `N files changed
 * +A -R`, or nothing over an empty state.
 *
 * The close `✕` sits at the right edge either way.
 *
 * @param kit the drawing's kit; its elements draw the line
 * @param totals the header's counts, or null when there is nothing to count
 * @returns the line
 */
export function headerView(
  kit: Kit,
  totals: PaneState.HeaderTotals | null,
): RenderElement {
  const { Box, Text } = kit.ui

  return (
    <Box flexDirection="row">
      {[
        ...(totals
          ? [
              <Text wrap="truncate-end">
                <Text bold>{Layout.plural(totals.filesCount, 'file')}</Text>
                {' changed '}
                {diffStat(kit, totals.linesAdded, totals.linesRemoved)}
              </Text>,
            ]
          : []),
        <Box flexGrow={1} />,
        closeButton(kit),
      ]}
    </Box>
  )
}
