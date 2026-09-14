// Descs stay version-free on purpose; model versions churn monthly and stale tags read as abandonware.
export const SUBSCRIPTION_PROVIDERS = [
  { id: 'claude', name: 'Claude Pro / Max', desc: 'The latest Claude models', color: '#E8927A', preview: false },
  // "Gemini" routes through Antigravity OAuth (same Google sign-in, higher quota than Gemini CLI's free tier).
  { id: 'antigravity', name: 'Gemini Advanced', desc: 'The latest Gemini models', color: '#4285F4', preview: false },
  { id: 'codex', name: 'ChatGPT Plus / Pro', desc: 'The latest ChatGPT models', color: '#74AA9C', preview: false },
];

export type SubscriptionProvider = typeof SUBSCRIPTION_PROVIDERS[0];
