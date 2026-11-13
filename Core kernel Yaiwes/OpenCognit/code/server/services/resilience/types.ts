// Resilience Service Types — Circuit Breaker, Health Monitoring, Provider Failover

export type CircuitState = 'closed' | 'open' | 'half-open';

export interface CircuitBreakerConfig {
  /** Provider identifier (e.g. 'anthropic', 'openrouter', 'openai') */
  providerId: string;
  /** Number of failures before opening the circuit. Default: 5 */
  failureThreshold: number;
  /** Successes needed in half-open to close. Default: 2 */
  successThreshold: number;
  /** Milliseconds to wait before trying half-open. Default: 30000 */
  recoveryTimeoutMs: number;
  /** Percentage of requests that can fail before counting (for jittery networks). Default: 0.5 */
  errorRateThreshold: number;
}

export interface CircuitBreakerSnapshot {
  providerId: string;
  state: CircuitState;
  failures: number;
  successes: number;
  consecutiveSuccesses: number;
  consecutiveFailures: number;
  lastFailureAt: number; // timestamp
  lastSuccessAt: number; // timestamp
  openedAt: number | null; // timestamp
  totalRequests: number;
  totalFailures: number;
}

export interface HealthCheckResult {
  providerId: string;
  healthy: boolean;
  latencyMs: number;
  checkedAt: number;
  error?: string;
}

export interface ProviderHealth {
  providerId: string;
  status: 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
  lastCheck: HealthCheckResult | null;
  checkHistory: HealthCheckResult[]; // last N checks
}

export interface FailoverDecision {
  /** The provider that should be used */
  providerId: string;
  /** Whether this is a failover (not the originally requested provider) */
  isFailover: boolean;
  /** Why this provider was chosen */
  reason: string;
  /** The originally requested provider and why it was skipped */
  originalProvider?: {
    providerId: string;
    reason: string;
  };
}

export interface ResilienceConfig {
  /** Ordered list of fallback providers. First = primary, rest = backups */
  providerChain: string[];
  /** Circuit breaker config per provider (optional overrides) */
  circuitBreakerOverrides?: Partial<Record<string, Partial<CircuitBreakerConfig>>>;
  /** Enable automatic health checks. Default: true */
  healthChecksEnabled?: boolean;
  /** Health check interval in ms. Default: 60000 */
  healthCheckIntervalMs?: number;
  /** Health check timeout in ms. Default: 10000 */
  healthCheckTimeoutMs?: number;
}
