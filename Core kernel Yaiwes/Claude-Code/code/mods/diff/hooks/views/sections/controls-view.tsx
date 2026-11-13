/* @jsxRuntime classic */
/* @jsx h */
/* @jsxFrag Fragment */
import type { RenderElement } from 'claude-code'

import type PaneState from '../../pane-state'
import type { Kit } from '../kit'
import { present } from './present'

/**
 * The pickers under the header: the source (`Current`, then `T<n>` per
 * turn with edits, newest first) and, for the current source, the base.
 *
 * The source picker draws only when a turn exists, as DiffDialog hides its
 * tabs; the base picker is ctrl+x b's cycle as a Select over the backend's
 * modes, uncommitted naming the base as the base line does (modeLabelOf).
 *
 * @param kit the elements and the handlers
 * @param model what is picked now and the turns to pick from
 * @returns the row, or null when neither picker applies
 */
export function controlsView(
  kit: Kit,
  model: Pick<
    PaneState.PaneModel,
    'source' | 'requestedMode' | 'turns' | 'baseModes' | 'words' | 'data'
  >,
): RenderElement | null {
  const { Box, Select } = kit.ui
  const { source, turns } = model
  const hasTurns = turns.length > 0

  const sourcePicker = hasTurns ? (
    <Select
      key="source"
      label="source"
      options={[
        { value: 'current', label: 'Current' },
        ...turns.map(turn => ({
          value: String(turn.index),
          label: `T${turn.index}`,
        })),
      ]}
      value={source.kind === 'current' ? 'current' : String(source.index)}
      onSelect={value => kit.actions.chooseSource(value)}
    />
  ) : null

  const isCurrent = source.kind === 'current'
  const fetchedSource = model.data?.source
  const isWorkingTree = fetchedSource?.kind === 'working-tree'
  const base = isWorkingTree ? fetchedSource.base : model.words.base

  const basePicker = isCurrent ? (
    <Select
      key="base"
      label="base"
      options={model.baseModes.map(mode => {
        const isUncommitted = mode === 'uncommitted'
        const isSession = mode === 'session'

        const label = isUncommitted
          ? `uncommitted (vs ${base})`
          : isSession
            ? 'this session'
            : mode

        return { value: mode, label }
      })}
      value={model.requestedMode}
      onSelect={value => kit.actions.chooseBase(value)}
    />
  ) : null

  const pickers = present([sourcePicker, basePicker])

  const row = (
    <Box flexDirection="row" gap={2}>
      {pickers}
    </Box>
  )

  return pickers.length === 0 ? null : row
}
