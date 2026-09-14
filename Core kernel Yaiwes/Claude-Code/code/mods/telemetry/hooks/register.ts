import type { EngineInterface, On } from 'claude-code'

import { telemetryOf } from './telemetry-of'

/**
 * Registers the plugin's one hook: its engine.create step adds
 * `$.telemetry` over the nouns beneath, the plugin's own `$` as core built.
 *
 * `log` runs after the fold, reaching `$.session` and `$.http` through the
 * nouns beneath; each is one call on them.
 *
 * @param on the engine's registrar
 */
export function register(on: On) {
  on('engine.create', async ($, e, next) => {
    const beneath = await next(e)

    const telemetry: EngineInterface['telemetry'] = telemetryOf({
      authorize: () => beneath.session.authorize(),
      id: () => beneath.session.id(),
      model: () => beneath.session.model(),
      environment: async () => ({
        userType: await beneath.env.get('USER_TYPE'),
        disableTelemetry: await beneath.env.get('DISABLE_TELEMETRY'),
        disableNonessentialTraffic: await beneath.env.get(
          'CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC',
        ),
        doNotTrack: await beneath.env.get('DO_NOT_TRACK'),
        customOauthUrl: await beneath.env.get('CLAUDE_CODE_CUSTOM_OAUTH_URL'),
        useBedrock: await beneath.env.get('CLAUDE_CODE_USE_BEDROCK'),
        useVertex: await beneath.env.get('CLAUDE_CODE_USE_VERTEX'),
        useFoundry: await beneath.env.get('CLAUDE_CODE_USE_FOUNDRY'),
        useAnthropicAws: await beneath.env.get('CLAUDE_CODE_USE_ANTHROPIC_AWS'),
        useAnthropicGoogleCloud: await beneath.env.get(
          'CLAUDE_CODE_USE_ANTHROPIC_GOOGLE_CLOUD',
        ),
        useMantle: await beneath.env.get('CLAUDE_CODE_USE_MANTLE'),
      }),
      fetch: (url, init) => beneath.http.fetch(url, init),
    })

    return { ...beneath, telemetry }
  })
}
