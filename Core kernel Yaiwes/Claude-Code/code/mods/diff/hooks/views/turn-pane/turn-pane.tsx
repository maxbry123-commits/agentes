/* @jsxRuntime classic */
/* @jsx h */
/* @jsxFrag Fragment */
import type { RenderElement } from 'claude-code'

import PaneState from '../../pane-state'
import type Turns from '../../turns'
import Detail from '../detail'
import type { Kit } from '../kit'
import Layout from '../layout'
import Sections from '../sections'

/**
 * The pane over one past turn's edits (DiffDialog's T<n> tab): the turn's
 * counts, its prompt's opening words, the pickers, its files, one body.
 *
 * @param kit the elements, the handlers, the width
 * @param model the pane's state
 * @param turn the turn picked
 * @returns the pane's tree
 */
export function turnPane(
  kit: Kit,
  model: PaneState.PaneModel,
  turn: Turns.TurnDiff,
): RenderElement {
  const { Box } = kit.ui

  const selected =
    turn.files.find(file => file.path === model.selectedPath) ??
    turn.files[0] ??
    null

  const rows = turn.files.map(file =>
    Sections.fileRow(
      kit,
      {
        key: Sections.fileKeyOf(file.path),
        path: file.path,
        added: file.added,
        removed: file.removed,
        note: null,
        isSelected: file.path === selected?.path,
      },
      () => kit.actions.selectFile(file.path),
    ),
  )

  const detail = selected
    ? [
        Sections.divider(kit),
        Detail.detailView(
          kit,
          {
            words: model.words,
            path: selected.path,
            renamedFrom: null,
            isUntracked: false,
            isBinary: false,
            body: {
              hunks: selected.hunks,
              isTruncated: selected.isTruncated,
              isLarge: false,
            },
            bodyState: 'ready',
            isArmed: model.armedPath === selected.path,
          },
          () => kit.actions.toggleAsk(selected.path),
        ),
      ]
    : []

  return (
    <Box flexDirection="column">
      {Sections.present([
        Sections.headerView(kit, PaneState.turnTotalsOf(turn)),
        Sections.dimNote(
          kit,
          `Turn ${turn.index} "${Layout.sanitizeName(turn.preview)}"`,
        ),
        Sections.controlsView(kit, model),
        ...rows,
        ...detail,
      ])}
    </Box>
  )
}
