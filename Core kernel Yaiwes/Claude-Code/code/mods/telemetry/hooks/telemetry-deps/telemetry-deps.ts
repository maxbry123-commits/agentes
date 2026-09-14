import type { HttpInit, HttpResponse, SessionAuthorization } from 'claude-code'

import type { Environment } from '../environment'

/**
 * What `telemetryOf` reaches on the nouns beneath: the session's authorize
 * and reads, and one fetch. Each is a call on the plugin's own `$`.
 */
export type TelemetryDeps = {
  /**
   * Resolves the session's held credential, or null.
   */
  authorize: () => Promise<SessionAuthorization>

  /**
   * The session's id, for the row.
   */
  id: () => Promise<string>

  /**
   * The session's model, for the row.
   */
  model: () => Promise<string>

  /**
   * Reads, at each call, what the row and the off switch need of the
   * environment: the build's user type and every analytics-off variable.
   */
  environment: () => Promise<Environment>

  /**
   * Posts the batch to the ingest with the credential handle.
   */
  fetch: (url: string, init: HttpInit) => Promise<HttpResponse>
}
