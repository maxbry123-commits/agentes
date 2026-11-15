import type { Fields } from './fields'
import type { RowSession } from './row-session'

/**
 * The first-party event batch for one entry, shaped as the CLI's own
 * event exporter shapes its batches.
 *
 * The ClaudeCodeInternalEvent JSON, one event per batch; the properties ride
 * as base64 JSON in `additional_metadata`, the field the exporter uses;
 * `user_type` is what the environment's USER_TYPE says of the build.
 *
 * @param fields the entry as checked
 * @param session the session's id and model, and the build's user type
 * @returns the batch's JSON text, ready to send to the exporter
 */
export function batchOf(fields: Fields, session: RowSession) {
  const metadata = JSON.stringify(fields.props)

  return JSON.stringify({
    events: [
      {
        event_type: 'ClaudeCodeInternalEvent',
        event_data: {
          event_name: fields.name,
          client_timestamp: new Date().toISOString(),
          session_id: session.sessionId,
          model: session.model,
          user_type: session.userType,
          additional_metadata: btoa(metadata),
        },
      },
    ],
  })
}
