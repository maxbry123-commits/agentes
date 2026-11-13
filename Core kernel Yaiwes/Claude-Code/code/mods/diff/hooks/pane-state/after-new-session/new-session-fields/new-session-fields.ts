/**
 * What `/clear` and `/resume` reset: the pick, the source, the turns and
 * the body; the fetch itself stays.
 */
export const NEW_SESSION_FIELDS = Object.freeze({
  selectedPath: null,
  source: Object.freeze({ kind: 'current' }),
  turns: Object.freeze([]),
  body: null,
  bodyState: 'idle',
} as const)
