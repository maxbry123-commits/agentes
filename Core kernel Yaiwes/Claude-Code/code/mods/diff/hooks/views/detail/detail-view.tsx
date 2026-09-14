/* @jsxRuntime classic */
/* @jsx h */
/* @jsxFrag Fragment */
import type { RenderElement } from 'claude-code'

import type { Kit } from '../kit'
import Layout from '../layout'
import Sections from '../sections'
import { codeBlocksOf } from './code-blocks-of'
import type { DetailModel } from './detail-model'
import { HUNK_DIVIDER } from './hunk-divider'
import { MAX_CODE_CHARS } from './max-code-chars'
import { placeholderOf } from './placeholder-of'

/**
 * The selected file under the list: its bold path and asides, the ask
 * Button, the built-in's dim rule under them, the body.
 *
 * Each name is cut from its start to the width. The body is a placeholder,
 * or the hunks as the engine's diff `Code` blocks (codeBlocksOf), a dim
 * divider where two meet, then the footer when anything was cut.
 *
 * @param kit the elements and the width
 * @param detail the selected file
 * @param onToggleAsk arms or disarms the file for the next prompt
 * @returns the detail element
 */
export function detailView(
  kit: Kit,
  detail: DetailModel,
  onToggleAsk: () => void,
): RenderElement {
  const { Box, Text, Button, Code } = kit.ui
  const placeholder = placeholderOf(detail)
  const code = codeBlocksOf(placeholder ? [] : (detail.body?.hunks ?? []))
  const isTruncated = detail.body?.isTruncated === true || code.isTruncated
  const path = Layout.sanitizeName(detail.path).slice(-MAX_CODE_CHARS)

  const nameOf = (name: string) =>
    Layout.truncateStart(Layout.sanitizeName(name), kit.columns)

  const renamedFrom =
    detail.renamedFrom === null ? null : nameOf(detail.renamedFrom)

  const asides = [
    renamedFrom === null ? null : `renamed from ${renamedFrom}`,
    detail.isUntracked ? 'untracked' : null,
    isTruncated ? 'truncated' : null,
  ].filter(word => word !== null)

  const aside = asides.length === 0 ? '' : ` (${asides.join(', ')})`

  const ask = placeholder
    ? []
    : [
        <Button key="ask" onPress={onToggleAsk}>
          {detail.isArmed ? 'asked ✓' : 'ask'}
        </Button>,
      ]

  const footer = isTruncated
    ? [
        <Text dimColor italic>
          … diff truncated (exceeded 400 line limit)
        </Text>,
      ]
    : []

  const notes = (placeholder ?? []).map(line => (
    <Text dimColor italic wrap="wrap">
      {line}
    </Text>
  ))

  const hunks = code.blocks.flatMap(block => [
    ...(block.hasDivider ? [<Text dimColor>{HUNK_DIVIDER}</Text>] : []),
    <Code source={block.source} format="diff" path={path} />,
  ])

  return (
    <Box flexDirection="column">
      {[
        <Box flexDirection="row">
          {[
            <Text bold wrap="truncate-start">
              {nameOf(detail.path)}
            </Text>,
            <Text dimColor>{aside}</Text>,
            <Box flexGrow={1} />,
            ...ask,
          ]}
        </Box>,
        Sections.divider(kit),
        ...(placeholder ? notes : hunks),
        ...footer,
      ]}
    </Box>
  )
}
