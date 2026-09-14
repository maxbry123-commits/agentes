import type { RenderInput } from 'claude-code'

/**
 * The prompt's hint on a 160-column terminal: drawing it is how the plugin
 * learns how wide the terminal is.
 */
export const HINT: RenderInput<'PromptHint'> = {
  component: 'PromptHint',
  surface: 'terminal',
  requestId: 'hint',
  viewport: { columns: 160, rows: 40 },
  props: { isDraft: false, isWorking: false, hint: '' },
}
