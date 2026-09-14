// Resilience Service — Circuit Breaker, Health Monitoring, Provider Failover
//
// Provides fault tolerance for LLM provider calls:
// - Circuit Breaker per provider (Open/Half-Open/Closed)
// - Automatic health checks
// - Provider failover with fallback chain
//
// Usage:
//   import { withResilience } from './resilience/index.js';
//   const result = await withResilience('openrouter', ['anthropic', 'openai'], async (provider) => {
//     return await callLLM(provider, prompt);
//   });

export { CircuitBreaker, CircuitBreakerRegistry, circuitBreakerRegistry } from './circuit-breaker.js';
export { HealthMonitor, healthMonitor } from './health-monitor.js';
export { FailoverRouter, failoverRouter } from './failover-router.js';

export type {
  CircuitState,
  CircuitBreakerConfig,
  CircuitBreakerSnapshot,
  HealthCheckResult,
  ProviderHealth,
  FailoverDecision,
  ResilienceConfig,
} from './types.js';

import { failoverRouter } from './failover-router.js';

/**
 * Convenience wrapper: execute a function with automatic provider failover.
 */
export async function withResilience<T>(
  primaryProvider: string,
  fallbackChain: string[],
  executeFn: (providerId: string) => Promise<T>,
  options?: {
    onFailover?: (decision: import('./types.js').FailoverDecision, error: any) => void;
    onSuccess?: (decision: import('./types.js').FailoverDecision, result: T) => void;
  },
): Promise<T> {
  return failoverRouter.executeWithFailover(primaryProvider, fallbackChain, executeFn, options);
}
