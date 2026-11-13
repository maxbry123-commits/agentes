// Failover Router — Selects the best available LLM provider from a chain.
//
// Combines Circuit Breaker state + Health Monitor status to make routing decisions.
// Priority order:
// 1. Circuit must be CLOSED or HALF-OPEN
// 2. Health status must not be 'unhealthy'
// 3. Prefer lower latency
// 4. Fallback through the chain until one works

import { CircuitBreakerRegistry } from './circuit-breaker.js';
import { HealthMonitor } from './health-monitor.js';
import type { FailoverDecision, ResilienceConfig } from './types.js';

export class FailoverRouter {
  constructor(
    private cbRegistry: CircuitBreakerRegistry,
    private healthMonitor: HealthMonitor,
  ) {}

  /**
   * Select the best provider from a chain.
   * Returns the first provider in the chain whose circuit is closed AND
   * whose health is not 'unhealthy'.
   *
   * If the originally requested provider is in a failover state, the router
   * walks the chain until it finds a healthy one.
   */
  selectProvider(
    requestedProvider: string,
    fallbackChain: string[],
  ): FailoverDecision {
    const chain = [requestedProvider, ...fallbackChain.filter(p => p !== requestedProvider)];

    for (const providerId of chain) {
      const cb = this.cbRegistry.get(providerId);
      const health = this.healthMonitor.getHealth(providerId);

      // Circuit breaker check
      if (cb && !cb.canExecute()) {
        continue; // circuit is open
      }

      // Health check check
      if (health && health.status === 'unhealthy') {
        continue;
      }

      // This provider is acceptable
      const isFailover = providerId !== requestedProvider;
      let reason = `Circuit=${cb?.currentState || 'unknown'}, Health=${health?.status || 'unknown'}`;
      if (isFailover) {
        reason = `Failover from ${requestedProvider} (${this.describeWhySkipped(requestedProvider)}). ${reason}`;
      }

      return {
        providerId,
        isFailover,
        reason,
        ...(isFailover
          ? {
              originalProvider: {
                providerId: requestedProvider,
                reason: this.describeWhySkipped(requestedProvider),
              },
            }
          : {}),
      };
    }

    // Nothing healthy — return the requested one as last resort (fail-open)
    return {
      providerId: requestedProvider,
      isFailover: false,
      reason: 'ALL_PROVIDER_UNHEALTHY — attempting requested provider as last resort (fail-open)',
    };
  }

  /**
   * Execute a function with automatic failover.
   * Tries the primary provider first, then falls back through the chain.
   */
  async executeWithFailover<T>(
    requestedProvider: string,
    fallbackChain: string[],
    executeFn: (providerId: string) => Promise<T>,
    options: {
      onFailover?: (decision: FailoverDecision, error: any) => void;
      onSuccess?: (decision: FailoverDecision, result: T) => void;
    } = {},
  ): Promise<T> {
    const decision = this.selectProvider(requestedProvider, fallbackChain);
    const providersToTry = this.buildTryOrder(decision, requestedProvider, fallbackChain);

    let lastError: any;

    for (const providerId of providersToTry) {
      const cb = this.cbRegistry.getOrCreate(providerId);

      try {
        const result = await executeFn(providerId);
        cb.recordSuccess();
        options.onSuccess?.(decision, result);
        return result;
      } catch (error: any) {
        lastError = error;
        cb.recordFailure();

        const isLastProvider = providerId === providersToTry[providersToTry.length - 1];
        if (isLastProvider) {
          options.onFailover?.(decision, error);
          throw error;
        }

        // Log failover
        console.warn(
          `[FailoverRouter] ${providerId} failed (${error.message || error.status}). ` +
          `Trying next provider...`
        );
      }
    }

    throw lastError;
  }

  private buildTryOrder(
    decision: FailoverDecision,
    requestedProvider: string,
    fallbackChain: string[],
  ): string[] {
    // Build the full chain, deduplicated, with selected provider first
    const fullChain = [requestedProvider, ...fallbackChain];
    const deduped = [...new Set(fullChain)];

    // Move the selected provider to the front
    const ordered = deduped.filter(p => p !== decision.providerId);
    return [decision.providerId, ...ordered];
  }

  private describeWhySkipped(providerId: string): string {
    const cb = this.cbRegistry.get(providerId);
    const health = this.healthMonitor.getHealth(providerId);

    const reasons: string[] = [];
    if (cb?.currentState === 'open') reasons.push('circuit open');
    if (health?.status === 'unhealthy') reasons.push('health unhealthy');

    return reasons.join(', ') || 'unknown issue';
  }
}

// ── Singleton ────────────────────────────────────────────────────────────────

import { circuitBreakerRegistry } from './circuit-breaker.js';
import { healthMonitor } from './health-monitor.js';

export const failoverRouter = new FailoverRouter(circuitBreakerRegistry, healthMonitor);
