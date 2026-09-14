/* @jsxRuntime classic */
/* @jsx h */
/* @jsxFrag Fragment */
import type { RenderElement } from 'claude-code'

import type { Kit } from '../../kit'

/**
 * The pane's close control (ReplDiffSidebar's PanelCloseButton): a `✕` at
 * the header's right edge that closes the pane as `/diff` does.
 *
 * Bold under the pointer, as the built-in's is. The built-in's rest style,
 * dim, is not a Button's to take: its label's only style is `hover`.
 *
 * @param kit the drawing's kit; its handlers close the pane
 * @returns the control, in the keyed Box its hover needs
 */
export function closeButton(kit: Kit): RenderElement {
  const { Box, Button } = kit.ui

  return (
    <Box key="close">
      <Button
        key="close"
        plain
        hover={{ bold: true }}
        onPress={kit.actions.close}
      >
        {'✕'}
      </Button>
    </Box>
  )
}
