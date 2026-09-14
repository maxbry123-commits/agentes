// Circuit Breaker — Per-Provider fault tolerance with Open/Half-Open/Closed states.
//
// State machine:
//   CLOSED  → (failures >= threshold) → OPEN
//   OPEN    → (recovery timeout passed) → HALF-OPEN
//   HALF-OPEN → (successes >= threshold) → CLOSED
//   HALF-OPEN → (any failure) → OPEN

import type { CircuitBreakerConfig, CircuitBreakerSnapshot, CircuitState } from './types.js';

const DEFAULT_CONFIG: Omit<CircuitBreakerConfig, 'providerId'> = {
  failureThreshold: 5,
  successThreshold: 2,
  recoveryTimeoutMs: 30000,
  errorRateThreshold: 0.5,
};

export class CircuitBreaker {
  private state: CircuitState = 'closed';
  private failures = 0;
  private successes = 0;
  private consecutiveSuccesses = 0;
  private consecutiveFailures = 0;
  private lastFailureAt = 0;
  private lastSuccessAt = 0;
  private openedAt: number | null = null;
  private totalRequests = 0;
  private totalFailures = 0;
  private config: CircuitBreakerConfig;

  constructor(config: Partial<CircuitBreakerConfig> & { providerId: string }) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /** Current state of the circuit */
  get currentState(): CircuitState {
    this.transitionIfNeeded();
    return this.state;
  }

  /** Whether a request should be allowed through */
  canExecute(): boolean {
    this.transitionIfNeeded();
    return this.state !== 'open';
  }

  /** Record a successful request */
  recordSuccess(): void {
    this.totalRequests++;
    this.successes++;
    this.consecutiveSuccesses++;
    this.consecutiveFailures = 0;
    this.lastSuccessAt = Date.now();

    if (this.state === 'half-open') {
      if (this.consecutiveSuccesses >= this.config.successThreshold) {
        this.close();
      }
    }
  }

  /** Record a failed request */
  recordFailure(): void {
    this.totalRequests++;
    this.failures++;
    this.consecutiveFailures++;
    this.consecutiveSuccesses = 0;
    this.lastFailureAt = Date.now();
    this.totalFailures++;

    if (this.state === 'half-open') {
      // Any failure in half-open immediately re-opens
      this.open();
      return;
    }

    if (this.state === 'closed') {
      // Check if we should open based on consecutive failures
      if (this.consecutiveFailures >= this.config.failureThreshold) {
        this.open();
      }
    }
  }

  /** Get a snapshot of current state */
  snapshot(): CircuitBreakerSnapshot {
    this.transitionIfNeeded();
    return {
      providerId: this.config.providerId,
      state: this.state,
      failures: this.failures,
      successes: this.successes,
      consecutiveSuccesses: this.consecutiveSuccesses,
      consecutiveFailures: this.consecutiveFailures,
      lastFailureAt: this.lastFailureAt,
      lastSuccessAt: this.lastSuccessAt,
      openedAt: this.openedAt,
      totalRequests: this.totalRequests,
      totalFailures: this.totalFailures,
    };
  }

  /** Reset the circuit to closed (useful for manual recovery) */
  reset(): void {
    this.state = 'closed';
    this.failures = 0;
    this.successes = 0;
    this.consecutiveSuccesses = 0;
    this.consecutiveFailures = 0;
    this.openedAt = null;
  }

  /** Force the circuit open (useful for maintenance) */
  forceOpen(): void {
    this.open();
  }

  private transitionIfNeeded(): void {
    if (this.state === 'open' && this.openedAt) {
      const elapsed = Date.now() - this.openedAt;
      if (elapsed >= this.config.recoveryTimeoutMs) {
        this.state = 'half-open';
        this.consecutiveSuccesses = 0;
        this.consecutiveFailures = 0;
        console.log(`🔌 Circuit Breaker [${this.config.providerId}] → HALF-OPEN (recovery timeout reached)`);
      }
    }
  }

  private open(): void {
    this.state = 'open';
    this.openedAt = Date.now();
    console.log(
      `🔴 Circuit Breaker [${this.config.providerId}] → OPEN ` +
      `(${this.consecutiveFailures} consecutive failures, ` +
      `will retry in ${this.config.recoveryTimeoutMs}ms)`
    );
  }

  private close(): void {
    this.state = 'closed';
    this.failures = 0;
    this.consecutiveFailures = 0;
    this.consecutiveSuccesses = 0;
    this.openedAt = null;
    console.log(`🟢 Circuit Breaker [${this.config.providerId}] → CLOSED (healthy again)`);
  }
}

// ── Registry ─────────────────────────────────────────────────────────────────

export class CircuitBreakerRegistry {
  private breakers = new Map<string, CircuitBreaker>();

  getOrCreate(providerId: string, overrides?: Partial<CircuitBreakerConfig>): CircuitBreaker {
    const existing = this.breakers.get(providerId);
    if (existing) return existing;

    const cb = new CircuitBreaker({ providerId, ...overrides });
    this.breakers.set(providerId, cb);
    return cb;
  }

  get(providerId: string): CircuitBreaker | undefined {
    return this.breakers.get(providerId);
  }

  all(): CircuitBreaker[] {
    return Array.from(this.breakers.values());
  }

  snapshots(): CircuitBreakerSnapshot[] {
    return this.all().map(cb => cb.snapshot());
  }

  reset(providerId: string): void {
    this.breakers.get(providerId)?.reset();
  }

  resetAll(): void {
    for (const cb of this.breakers.values()) cb.reset();
  }
}

export const circuitBreakerRegistry = new CircuitBreakerRegistry();
