import { describe, it, expect, beforeEach, vi } from 'vitest';
import { CircuitBreakerRegistry } from './circuit-breaker.js';
import { HealthMonitor } from './health-monitor.js';
import { FailoverRouter } from './failover-router.js';

describe('FailoverRouter', () => {
  let cbRegistry: CircuitBreakerRegistry;
  let healthMonitor: HealthMonitor;
  let router: FailoverRouter;

  beforeEach(() => {
    vi.useFakeTimers();
    cbRegistry = new CircuitBreakerRegistry();
    healthMonitor = new HealthMonitor();
    router = new FailoverRouter(cbRegistry, healthMonitor);
  });

  describe('selectProvider', () => {
    it('returns primary when healthy', () => {
      healthMonitor.registerProvider('openrouter');
      const decision = router.selectProvider('openrouter', ['anthropic', 'openai']);
      expect(decision.providerId).toBe('openrouter');
      expect(decision.isFailover).toBe(false);
    });

    it('fails over when primary circuit is open', () => {
      healthMonitor.registerProvider('openrouter');
      healthMonitor.registerProvider('anthropic');

      const cb = cbRegistry.getOrCreate('openrouter', { failureThreshold: 1 });
      cb.recordFailure();
      expect(cb.currentState).toBe('open');

      const decision = router.selectProvider('openrouter', ['anthropic', 'openai']);
      expect(decision.providerId).toBe('anthropic');
      expect(decision.isFailover).toBe(true);
      expect(decision.originalProvider?.providerId).toBe('openrouter');
    });

    it('fails over when primary is unhealthy', () => {
      healthMonitor.registerProvider('openrouter');
      healthMonitor.registerProvider('anthropic');

      // Simulate unhealthy primary by injecting bad health results
      const badResult = {
        providerId: 'openrouter',
        healthy: false,
        latencyMs: 0,
        checkedAt: Date.now(),
        error: 'timeout',
      };
      // Access private method through any cast for test
      (healthMonitor as any).recordResult('openrouter', badResult);
      (healthMonitor as any).recordResult('openrouter', badResult);
      (healthMonitor as any).recordResult('openrouter', badResult);
      (healthMonitor as any).recordResult('openrouter', badResult);
      (healthMonitor as any).recordResult('openrouter', badResult);

      const decision = router.selectProvider('openrouter', ['anthropic']);
      expect(decision.providerId).toBe('anthropic');
      expect(decision.isFailover).toBe(true);
    });

    it('skips unhealthy fallbacks too', () => {
      healthMonitor.registerProvider('openrouter');
      healthMonitor.registerProvider('anthropic');
      healthMonitor.registerProvider('openai');

      const cb1 = cbRegistry.getOrCreate('openrouter', { failureThreshold: 1 });
      cb1.recordFailure();
      const cb2 = cbRegistry.getOrCreate('anthropic', { failureThreshold: 1 });
      cb2.recordFailure();

      const decision = router.selectProvider('openrouter', ['anthropic', 'openai']);
      expect(decision.providerId).toBe('openai');
      expect(decision.isFailover).toBe(true);
    });

    it('returns primary as last resort when all are bad', () => {
      healthMonitor.registerProvider('openrouter');
      healthMonitor.registerProvider('anthropic');

      const cb1 = cbRegistry.getOrCreate('openrouter', { failureThreshold: 1 });
      cb1.recordFailure();
      const cb2 = cbRegistry.getOrCreate('anthropic', { failureThreshold: 1 });
      cb2.recordFailure();

      const decision = router.selectProvider('openrouter', ['anthropic']);
      expect(decision.providerId).toBe('openrouter');
      expect(decision.isFailover).toBe(false);
      expect(decision.reason).toContain('ALL_PROVIDER_UNHEALTHY');
    });
  });

  describe('executeWithFailover', () => {
    it('executes primary successfully', async () => {
      healthMonitor.registerProvider('openrouter');
      const result = await router.executeWithFailover(
        'openrouter',
        ['anthropic'],
        async (provider) => {
          expect(provider).toBe('openrouter');
          return { ok: true, provider };
        },
      );
      expect(result).toEqual({ ok: true, provider: 'openrouter' });
    });

    it('fails over when primary throws', async () => {
      healthMonitor.registerProvider('openrouter');
      healthMonitor.registerProvider('anthropic');

      let callCount = 0;
      const result = await router.executeWithFailover(
        'openrouter',
        ['anthropic'],
        async (provider) => {
          callCount++;
          if (provider === 'openrouter') {
            throw new Error('primary down');
          }
          return { ok: true, provider };
        },
      );

      expect(callCount).toBe(2);
      expect(result).toEqual({ ok: true, provider: 'anthropic' });
    });

    it('records success on the circuit breaker', async () => {
      healthMonitor.registerProvider('openrouter');
      const cb = cbRegistry.getOrCreate('openrouter');

      await router.executeWithFailover(
        'openrouter',
        [],
        async () => 'success',
      );

      const snap = cb.snapshot();
      expect(snap.consecutiveSuccesses).toBe(1);
      expect(snap.totalRequests).toBe(1);
    });

    it('records failure on the circuit breaker', async () => {
      healthMonitor.registerProvider('openrouter');
      const cb = cbRegistry.getOrCreate('openrouter');

      await expect(
        router.executeWithFailover('openrouter', [], async () => {
          throw new Error('fail');
        }),
      ).rejects.toThrow('fail');

      const snap = cb.snapshot();
      expect(snap.consecutiveFailures).toBe(1);
      expect(snap.totalFailures).toBe(1);
    });

    it('calls onSuccess callback', async () => {
      healthMonitor.registerProvider('openrouter');
      const onSuccess = vi.fn();

      await router.executeWithFailover(
        'openrouter',
        [],
        async () => 'result',
        { onSuccess },
      );

      expect(onSuccess).toHaveBeenCalledOnce();
      expect(onSuccess.mock.calls[0][1]).toBe('result');
    });

    it('calls onFailover callback when all fail', async () => {
      healthMonitor.registerProvider('openrouter');
      const onFailover = vi.fn();

      await expect(
        router.executeWithFailover(
          'openrouter',
          [],
          async () => {
            throw new Error('fail');
          },
          { onFailover },
        ),
      ).rejects.toThrow('fail');

      expect(onFailover).toHaveBeenCalledOnce();
    });
  });
});
