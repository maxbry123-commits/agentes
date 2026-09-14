import type { Plugin } from 'claude-code/testing'

/**
 * A plugin whose `/record <entry>` logs the entry through `$.telemetry`,
 * answering "sent", or why the row was refused.
 */
export const recording: Plugin = {
  name: 'recording',
  register(on) {
    on('command.run', { command: 'record' }, ($, e) =>
      $.telemetry.log(JSON.parse(e.args)).then(
        () => ({ text: 'sent' }),
        (error: unknown) => ({ text: String(error) }),
      ),
    )
  },
}
