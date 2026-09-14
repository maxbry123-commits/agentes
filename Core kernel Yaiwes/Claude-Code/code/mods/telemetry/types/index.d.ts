/**
 * The `$.telemetry` noun as every caller sees it: the one contract for the
 * noun, its types exported here and the noun declared on `EngineInterface`.
 *
 * The telemetry mod adds the noun in the `engine.create` fold and checks its
 * return against `EngineInterface['telemetry']`; its hooks import these types
 * from this folder, a mod that calls the noun and a test that answers it read
 * them by including it in their tsconfig, and the engine's repository imports
 * the folder by path. Nothing here is imported, so it stands on its own.
 */

/**
 * A plugin's analytics, sent one event at a time through `$.telemetry`.
 *
 * Internal builds alone: the telemetry mod adds the noun in the
 * `engine.create` fold, so a plugin on an external build, or one where the
 * mod is off, finds no `$.telemetry` and its call throws.
 */
export type Telemetry = {
  /**
   * Sends one event, `tengu_plugin_<event>`, as one first-party row;
   * resolves once the ingest accepted it.
   *
   * The calling mod names itself in `event`; one already named `tengu_…` is
   * sent as named. A value is a finite number, a boolean or a
   * TelemetryChoice; free text is refused. One input, as every op on `$`
   * takes.
   *
   * @param entry the event's name, a snake_case token, and its properties by
   *   snake_case key
   * @example
   * await $.telemetry.log({
   *   event: "suggest_learning_survey_answered",
   *   props: {
   *     answer: 2,
   *     page: { value: "ready", of: ["ready", "later"] },
   *   },
   * })
   */
  log: (entry: TelemetryLogEntry) => Promise<void>

  /**
   * Marks one use of a feature as the CLI's own feature events do, one
   * `tengu_feature_<kind>` row; resolves once the ingest accepted it.
   *
   * The row carries `feature_name`, `error_code` on sad or bad (`reason`,
   * required there and refused on ok) and the entry's `props`, checked as
   * `log`'s are; it joins the product-wide feature surface, so no prefix.
   *
   * @param entry the feature, how it went, why when not ok, and the row's
   *   properties by snake_case key
   * @example
   * await $.telemetry.mark({ feature: "learn_page", kind: "ok" })
   * await $.telemetry.mark({
   *   feature: "learn_page",
   *   kind: "sad",
   *   reason: "blocked",
   * })
   */
  mark: (entry: TelemetryMarkEntry) => Promise<void>
}

/**
 * What `$.telemetry.log` takes: the event's name after the prefix, and its
 * properties by snake_case key.
 */
export type TelemetryLogEntry = {
  event: string
  props?: Readonly<Record<string, TelemetryProp>>
}

/**
 * What `$.telemetry.mark` takes: the feature, how it went, why when not
 * ok, and the properties the row carries beside them by snake_case key.
 */
export type TelemetryMarkEntry = {
  feature: string
  kind: TelemetryMarkKind
  reason?: string
  props?: Readonly<Record<string, TelemetryProp>>
}

/**
 * How a feature went, as the CLI's own feature events count it.
 *
 * `ok`: used, the person got what they asked. `sad`: degraded, a fallback
 * or a partial, the person still got something. `bad`: failed, the person
 * got nothing.
 */
export type TelemetryMarkKind = 'ok' | 'sad' | 'bad'

/**
 * A property's value: a finite number, a boolean, or a TelemetryChoice;
 * never free text.
 */
export type TelemetryProp = number | boolean | TelemetryChoice

/**
 * A string property: the value and the list it is chosen from, declared
 * beside it, so no free text reaches the row.
 *
 * Every member of `of` is a lowercase token of letters, digits, `_` and
 * `-`, which may start with a digit, at most 32 of them; `value` is one of
 * them.
 */
export type TelemetryChoice = { value: string; of: readonly string[] }

declare module 'claude-code' {
  interface EngineInterface {
    /**
     * A plugin's analytics, one first-party row per call; present only where
     * the telemetry mod is seated (internal builds), absent everywhere else.
     */
    telemetry: Telemetry
  }
}
