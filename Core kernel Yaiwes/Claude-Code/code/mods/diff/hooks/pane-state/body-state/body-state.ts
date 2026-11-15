/**
 * Where the selected file's body stands: nothing selected, being read, git
 * could not read it, or in hand.
 */
export type BodyState = 'idle' | 'loading' | 'failed' | 'ready'
