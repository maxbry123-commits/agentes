/**
 * What one row says of the session that sent it: its id, its model, and
 * the build's user type (`ant` or `external`) as the environment names it.
 */
export type RowSession = {
  sessionId: string
  model: string
  userType: string
}
