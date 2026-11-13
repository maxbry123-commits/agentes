import type { CommandRunInput } from 'claude-code'

/**
 * The command as the person types it, with no arguments.
 */
export const DIFF: CommandRunInput = {
  command: 'diff',
  args: '',
  origin: { kind: 'composer' },
}
