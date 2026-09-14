import type { Telemetry } from '../../types'
import Entries from '../entries'
import { isAnalyticsOff } from '../is-analytics-off'
import type { TelemetryDeps } from '../telemetry-deps'

/**
 * Builds `$.telemetry`: `log` and `mark` check the entry, read the environment
 * and authorize afresh, build the first-party row and POST it to the ingest.
 *
 * One POST per call, rows one after another, nothing kept between them: a
 * session that has moved to a third-party provider or a gateway, or turned
 * analytics off, sends nothing more; no credential or a refusal rejects.
 *
 * @param deps the calls on the nouns beneath
 * @returns the `$.telemetry` interface, `log` and `mark`
 */
export function telemetryOf(deps: TelemetryDeps): Telemetry {
  let queue: Promise<unknown> = Promise.resolve()

  async function post(
    fields: Entries.Fields,
    method: Entries.Method,
  ): Promise<void> {
    const environment = await deps.environment()

    if (isAnalyticsOff(environment)) {
      return
    }

    const body = Entries.batchOf(fields, {
      sessionId: await deps.id(),
      model: await deps.model(),
      userType: environment.userType === 'ant' ? 'ant' : 'external',
    })

    const auth = await deps.authorize()

    if (!auth) {
      throw Entries.refusal(
        'this session has no first-party credential to authorize',
        method,
      )
    }

    const response = await deps.fetch(Entries.INGEST_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-service-name': 'claude-code',
      },
      auth: auth.handle,
      body,
    })

    if (!response.ok) {
      throw Entries.refusal(`the ingest answered ${response.status}`, method)
    }
  }

  function queued(
    fields: Entries.Fields,
    method: Entries.Method,
  ): Promise<void> {
    const turn = queue.then(() => post(fields, method))
    queue = turn.catch(() => undefined)

    return turn
  }

  return {
    log: async entry => queued(Entries.checkedFields(entry), 'log'),
    mark: async entry => queued(Entries.checkedMark(entry), 'mark'),
  }
}
