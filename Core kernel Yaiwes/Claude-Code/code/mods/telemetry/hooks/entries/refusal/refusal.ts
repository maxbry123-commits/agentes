import type { Method } from '../method'

/**
 * The error a refused entry rejects with, naming the method and what was wrong.
 *
 * The text carries a key that passed TOKEN or a status code, nothing the caller
 * wrote as free text.
 *
 * @param what the refusal, as the caller reads it
 * @param method the method refusing
 * @returns the error to reject the call with, naming the method and what was
 *          wrong
 */
export const refusal = (what: string, method: Method = 'log'): Error =>
  new Error(`$.telemetry.${method}: ${what}`)
