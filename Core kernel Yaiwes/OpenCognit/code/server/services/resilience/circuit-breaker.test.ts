import { describe, it, expect, beforeEach, vi } from 'vitest';
import { CircuitBreaker, CircuitBreakerRegistry } from './circuit-breaker.js';

describe('CircuitBreaker', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  it('starts in closed state', () => {
    const cb = new CircuitBreaker({ providerId: 'test' });
    expect(cb.currentState).toBe('closed');
    expect(cb.canExecute()).toBe(true);
  });

  it('opens after threshold consecutive failures', () => {
    const cb = new CircuitBreaker({ providerId: 'test', failureThreshold: 3 });

    cb.recordFailure();
    expect(cb.currentState).toBe('closed');
    cb.recordFailure();
    expect(cb.currentState).toBe('closed');
    cb.recordFailure();
    expect(cb.currentState).toBe('open');
    expect(cb.canExecute()).toBe(false);
  });

  it('resets consecutive failures on success', () => {
    const cb = new CircuitBreaker({ providerId: 'test', failureThreshold: 3 });

    cb.recordFailure();
    cb.recordFailure();
    cb.recordSuccess();
    cb.recordFailure();
    cb.recordFailure();
    // Still closed because consecutive failures reset after success
    expect(cb.currentState).toBe('closed');
  });

  it('transitions from open to half-open after recovery timeout', () => {
    const cb = new CircuitBreaker({
      providerId: 'test',
      failureThreshold: 1,
      recoveryTimeoutMs: 30000,
    });

    cb.recordFailure();
    expect(cb.currentState).toBe('open');

    vi.advanceTimersByTime(30001);
    expect(cb.currentState).toBe('half-open');
    expect(cb.canExecute()).toBe(true);
  });

  it('closes from half-open after enough successes', () => {
    const cb = new CircuitBreaker({
      providerId: 'test',
      failureThreshold: 1,
      successThreshold: 2,
      recoveryTimeoutMs: 30000,
    });

    cb.recordFailure();
    vi.advanceTimersByTime(30001);
    expect(cb.currentState).toBe('half-open');

    cb.recordSuccess();
    expect(cb.currentState).toBe('half-open');
    cb.recordSuccess();
    expect(cb.currentState).toBe('closed');
  });

  it('re-opens from half-open on any failure', () => {
    const cb = new CircuitBreaker({
      providerId: 'test',
      failureThreshold: 1,
      successThreshold: 3,
      recoveryTimeoutMs: 30000,
    });

    cb.recordFailure();
    vi.advanceTimersByTime(30001);
    expect(cb.currentState).toBe('half-open');

    cb.recordSuccess();
    cb.recordFailure(); // immediately re-opens
    expect(cb.currentState).toBe('open');
  });

  it('snapshot reflects current state', () => {
    const cb = new CircuitBreaker({ providerId: 'test', failureThreshold: 2 });
    cb.recordFailure();
    cb.recordFailure();

    const snap = cb.snapshot();
    expect(snap.providerId).toBe('test');
    expect(snap.state).toBe('open');
    expect(snap.consecutiveFailures).toBe(2);
    expect(snap.totalFailures).toBe(2);
    expect(snap.openedAt).not.toBeNull();
  });

  it('reset forces closed state', () => {
    const cb = new CircuitBreaker({ providerId: 'test', failureThreshold: 1 });
    cb.recordFailure();
    expect(cb.currentState).toBe('open');

    cb.reset();
    expect(cb.currentState).toBe('closed');
    expect(cb.canExecute()).toBe(true);
  });

  it('forceOpen forces open state', () => {
    const cb = new CircuitBreaker({ providerId: 'test' });
    expect(cb.currentState).toBe('closed');

    cb.forceOpen();
    expect(cb.currentState).toBe('open');
    expect(cb.canExecute()).toBe(false);
  });

  it('tracks total requests and failures', () => {
    const cb = new CircuitBreaker({ providerId: 'test' });
    cb.recordSuccess();
    cb.recordSuccess();
    cb.recordFailure();

    const snap = cb.snapshot();
    expect(snap.totalRequests).toBe(3);
    expect(snap.totalFailures).toBe(1);
  });
});

describe('CircuitBreakerRegistry', () => {
  it('creates and reuses breakers', () => {
    const registry = new CircuitBreakerRegistry();
    const cb1 = registry.getOrCreate('anthropic');
    const cb2 = registry.getOrCreate('anthropic');
    expect(cb1).toBe(cb2);
  });

  it('returns snapshots for all breakers', () => {
    const registry = new CircuitBreakerRegistry();
    registry.getOrCreate('a');
    registry.getOrCreate('b');
    expect(registry.snapshots()).toHaveLength(2);
  });

  it('resets a specific breaker', () => {
    const registry = new CircuitBreakerRegistry();
    const cb = registry.getOrCreate('test', { failureThreshold: 1 });
    cb.recordFailure();
    expect(cb.currentState).toBe('open');

    registry.reset('test');
    expect(cb.currentState).toBe('closed');
  });

  it('resets all breakers', () => {
    const registry = new CircuitBreakerRegistry();
    const a = registry.getOrCreate('a', { failureThreshold: 1 });
    const b = registry.getOrCreate('b', { failureThreshold: 1 });
    a.recordFailure();
    b.recordFailure();

    registry.resetAll();
    expect(a.currentState).toBe('closed');
    expect(b.currentState).toBe('closed');
  });
});
