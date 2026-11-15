import type { On } from 'claude-code'
import { mock } from 'claude-code/testing'
import type { MockClock } from 'claude-code/testing'

/**
 * Answers what every /diff session asks first: its start, with its own
 * directory, the time, and each command it registers, under its name.
 *
 * @param on the test's `on`
 * @returns the clock the session reads, at 0 until the test moves it
 */
export function startsSession(on: On): MockClock {
  on('session.start', ($, e) => ({ cwd: e.cwd }))
  on('command.register', ($, e) => ({ value: { command: e.name } }))

  return mock.clock(on)
}
