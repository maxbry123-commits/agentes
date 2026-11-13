import { useEffect } from 'react';
import { useAppDispatch } from '@/shared/hooks';
import { activateSubscription, activateSignin, fetchSettings } from '@/shared/state/settingsSlice';
import { fetchModels } from '@/shared/state/modelsSlice';
import { fetchTools } from '@/shared/state/toolsSlice';
import { API_BASE } from '@/shared/config';
import { report } from '@/shared/serviceClient';

const sleep = (ms: number): Promise<void> => new Promise((r) => setTimeout(r, ms));

// Sign-in must survive a backend that is booting or mid-restart (the exact state Massimo hit
// during the update ping-pong): one failed activate POST used to lose the token forever. We retry
// with backoff AND verify the bearer actually persisted, because a backend can accept the POST then
// die before flushing settings ("landed but didn't stick"). Both are ENG-240 failure modes.
async function durableSignin(
  token: string,
  email: string | null,
  dispatch: ReturnType<typeof useAppDispatch>,
): Promise<void> {
  const DEADLINE_MS = 30000;
  const backoff = [400, 800, 1500, 3000, 3000, 4000];
  const start = Date.now();
  let attempt = 0;
  let lastError = '';
  while (Date.now() - start < DEADLINE_MS) {
    try {
      const res = await dispatch(activateSignin({ token, signin_method: 'google', email })).unwrap();
      // Verify on user_id, the exact signal the mandatory-sign-in gate reads (shouldRequireSignIn),
      // not the bearer: the bearer is a secret that may be redacted from GET /settings, and user_id
      // is what actually flips the wall down. Confirms the sign-in truly landed, not just that the POST returned.
      const settings = await dispatch(fetchSettings()).unwrap();
      if (settings?.user_id) {
        report('signin', 'activated', { method: res.signin_method, plan: res.plan, attempt: attempt + 1 });
        dispatch(fetchModels());
        return;
      }
      lastError = 'accepted but identity not persisted';
    } catch (err) {
      lastError = String((err as { message?: unknown })?.message ?? err).slice(0, 120);
    }
    await sleep(backoff[Math.min(attempt, backoff.length - 1)]);
    attempt++;
  }
  console.error('[deep-link] Sign-in did not persist after retries:', lastError);
  report('signin', 'activation_failed', { message: lastError, attempts: attempt });
}

async function claimOauth(rawUrl: string, dispatch: ReturnType<typeof useAppDispatch>): Promise<void> {
  const url = new URL(rawUrl);
  if (url.host !== 'oauth' || !url.pathname.endsWith('/complete')) {
    console.warn('[deep-link] Unexpected oauth-claim URL:', rawUrl);
    return;
  }
  const sessionId = url.searchParams.get('session_id');
  const toolId = url.searchParams.get('tool_id');
  if (!sessionId || !toolId) {
    console.warn('[deep-link] Missing session_id or tool_id in', rawUrl);
    return;
  }
  report('oauth', 'deep_link_received', { provider: url.pathname.split('/')[1] || 'unknown' });
  const resp = await fetch(`${API_BASE}/tools/oauth/claim`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, tool_id: toolId }),
  });
  if (!resp.ok) {
    console.error('[deep-link] OAuth claim failed:', resp.status, await resp.text());
    report('oauth', 'claim_failed', { status: resp.status });
    return;
  }
  report('oauth', 'claim_succeeded');
  dispatch(fetchTools());
}

/** Subscribe to openswarm:// auth/oauth deep-links from Electron main; no-op in browser. */
export function useDeepLink(): void {
  const dispatch = useAppDispatch();

  useEffect(() => {
    const api = (window as any).openswarm as OpenSwarmAPI | undefined;
    if (!api) return;

    // Same token can arrive twice (user clicked twice, or a nudge races a mount-drain); the retry
    // loop is idempotent server-side, but skip re-running it so we don't stack overlapping retries.
    const handled = new Set<string>();

    const processDeepLink = (rawUrl: string): void => {
      try {
        const url = new URL(rawUrl);
        if (url.host === 'oauth') {
          void claimOauth(rawUrl, dispatch);
          return;
        }
        if (url.host !== 'auth' && url.pathname !== '//auth' && url.pathname !== '/auth') {
          console.warn('[deep-link] Unknown openswarm:// host:', url.host);
          return;
        }
        const token = url.searchParams.get('token');
        if (!token) {
          console.warn('[deep-link] Missing token in', rawUrl);
          return;
        }
        if (handled.has(token)) return;
        handled.add(token);

        if (url.searchParams.get('signin') === 'true') {
          report('signin', 'deep_link_received', { method: 'google' });
          void durableSignin(token, url.searchParams.get('email'), dispatch);
          return;
        }
        report('subscription', 'deep_link_received', { plan: url.searchParams.get('plan') ?? 'unknown' });
        dispatch(
          activateSubscription({
            token,
            plan: url.searchParams.get('plan'),
            expires: url.searchParams.get('expires'),
          }),
        )
          .unwrap()
          .then((res) => {
            report('subscription', 'activated', { plan: res.plan });
            dispatch(fetchModels());
          })
          .catch((err) => {
            console.error('[deep-link] Activation failed:', err);
            report('subscription', 'activation_failed', { message: String(err?.message ?? err).slice(0, 120) });
          });
      } catch (e) {
        console.error('[deep-link] Failed to parse URL', rawUrl, e);
      }
    };

    // Drain the queue main holds. Called on mount (catches links delivered before this
    // subscription existed) and on every nudge (live links). Draining clears the queue in main,
    // so each link is consumed exactly once regardless of timing.
    const drain = async (): Promise<void> => {
      if (!api.drainDeeplinks) return;
      try {
        const links = await api.drainDeeplinks();
        for (const link of links) processDeepLink(link.url);
      } catch (e) {
        console.warn('[deep-link] drain failed', e);
      }
    };

    const unsubscribe = api.onDeeplinkAvailable?.(() => { void drain(); });
    void drain();

    // Legacy push channels (old main builds): still honored so a mixed-version install works.
    const unsubAuth = api.onAuthUrl?.((url) => processDeepLink(url));
    const unsubOauth = api.onOauthClaim?.((url) => processDeepLink(url));

    return () => {
      unsubscribe?.();
      unsubAuth?.();
      unsubOauth?.();
    };
  }, [dispatch]);
}
