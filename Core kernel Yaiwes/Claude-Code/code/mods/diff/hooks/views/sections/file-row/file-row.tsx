/* @jsxRuntime classic */
/* @jsx h */
/* @jsxFrag Fragment */
import type { RenderElement } from 'claude-code'

import type { Kit } from '../../kit'
import Layout from '../../layout'
import { diffStat } from '../diff-stat'
import type { FileRowModel } from '../file-row-model'
import { POINTER } from '../pointer'
import { STAT_CELLS } from '../stat-cells'

/**
 * One file of the list (ReplDiffSidebar FileSummaryRow): a plain Button
 * with the start-truncated path, its counts or note at the right.
 *
 * The pointer marks the selected one.
 *
 * @param kit the elements, the handlers, the width
 * @param row the file
 * @param onPress selects the file
 * @returns the row element
 */
export function fileRow(
  kit: Kit,
  row: FileRowModel,
  onPress: () => void,
): RenderElement {
  const { Box, Text, Button } = kit.ui
  const room = Math.max(kit.columns - STAT_CELLS, STAT_CELLS)
  const mark = row.isSelected ? POINTER : ' '

  const note = (
    <Text dimColor italic>
      {row.note ?? ''}
    </Text>
  )

  const hasNote = row.note !== null
  const tail = hasNote ? note : diffStat(kit, row.added, row.removed)

  return (
    <Box flexDirection="row">
      <Button key={row.key} plain onPress={onPress}>
        {`${mark} ${Layout.truncateStart(Layout.sanitizeName(row.path), room)}`}
      </Button>
      <Box flexGrow={1} />
      {tail}
    </Box>
  )
}
