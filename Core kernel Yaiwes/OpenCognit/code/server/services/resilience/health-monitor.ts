// Health Monitor — Periodic lightweight health checks for LLM providers.
//
// Uses a simple "ping" approach: send a minimal request to each provider's
// health/status endpoint or API root. Tracks latency and success rate over
// a sliding window.

import type { HealthCheckResult, ProviderHealth } from './types.js';

const HISTORY_SIZE = 10;

/** Map of provider IDs to their lightweight health check URLs */
const HEALTH_ENDPOINTS: Record<string, string> = {
  anthropic: 'https://api.anthropic.com/v1/health',
  openrouter: 'https://openrouter.ai/api/v1/models',
  openai: 'https://api.openai.com/v1/models',
  ollama: '', // configured per-instance
};

export class HealthMonitor {
  private providers = new Map<string, ProviderHealth>();
  private intervals: NodeJS.Timeout[] = [];
  private checkFn: (providerId: string, url: string, timeoutMs: number) => Promise<HealthCheckResult>;

  constructor(
    options: {
      customCheckFn?: (providerId: string, url: string, timeoutMs: number) => Promise<HealthCheckResult>;
    } = {},
  ) {
    this.checkFn = options.customCheckFn || defaultHealthCheck;
  }

  /**
   * Register a provider for monitoring.
   * @param providerId e.g. 'anthropic', 'openrouter'
   * @param customUrl Optional override for the health check URL
   */
  registerProvider(providerId: string, customUrl?: string): void {
    if (this.providers.has(providerId)) return;

    this.providers.set(providerId, {
      providerId,
      status: 'unknown',
      lastCheck: null,
      checkHistory: [],
    });

    // Allow custom URLs (e.g. for self-hosted Ollama)
    if (customUrl) {
      HEALTH_ENDPOINTS[providerId] = customUrl;
    }
  }

  /**
   * Unregister a provider.
   */
  unregisterProvider(providerId: string): void {
    this.providers.delete(providerId);
  }

  /**
   * Start periodic health checks.
   */
  start(intervalMs: number = 60000, timeoutMs: number = 10000): void {
    this.stop(); // clear any existing

    const tick = async () => {
      for (const [providerId] of this.providers) {
        const result = await this.checkOne(providerId, timeoutMs);
        this.recordResult(providerId, result);
      }
    };

    // Run immediately, then on interval
    tick();
    this.intervals.push(setInterval(tick, intervalMs));
  }

  /**
   * Stop all health checks.
   */
  stop(): void {
    for (const iv of this.intervals) clearInterval(iv);
    this.intervals = [];
  }

  /**
   * Run a single health check for a provider.
   */
  async checkOne(providerId: string, timeoutMs: number = 10000): Promise<HealthCheckResult> {
    const url = HEALTH_ENDPOINTS[providerId] || '';
    if (!url) {
      return {
        providerId,
        healthy: false,
        latencyMs: 0,
        checkedAt: Date.now(),
        error: 'No health endpoint configured',
      };
    }
    return this.checkFn(providerId, url, timeoutMs);
  }

  /**
   * Get current health status for a provider.
   */
  getHealth(providerId: string): ProviderHealth | undefined {
    return this.providers.get(providerId);
  }

  /**
   * Get all provider health statuses.
   */
  getAllHealth(): ProviderHealth[] {
    return Array.from(this.providers.values());
  }

  /**
   * Is a provider currently considered healthy?
   */
  isHealthy(providerId: string): boolean {
    const health = this.providers.get(providerId);
    if (!health) return false;
    return health.status === 'healthy' || health.status === 'unknown';
  }

  private recordResult(providerId: string, result: HealthCheckResult): void {
    const health = this.providers.get(providerId);
    if (!health) return;

    health.lastCheck = result;
    health.checkHistory.push(result);
    if (health.checkHistory.length > HISTORY_SIZE) {
      health.checkHistory.shift();
    }

    // Compute status from recent history
    const recent = health.checkHistory.slice(-5);
    const successRate = recent.filter(r => r.healthy).length / recent.length;
    const avgLatency = recent.reduce((s, r) => s + r.latencyMs, 0) / recent.length;

    if (recent.length < 2) {
      health.status = result.healthy ? 'healthy' : 'unhealthy';
    } else if (successRate >= 0.8 && avgLatency < 5000) {
      health.status = 'healthy';
    } else if (successRate >= 0.5) {
      health.status = 'degraded';
    } else {
      health.status = 'unhealthy';
    }
  }
}

// ── Default HTTP health check ────────────────────────────────────────────────

async function defaultHealthCheck(
  providerId: string,
  url: string,
  timeoutMs: number,
): Promise<HealthCheckResult> {
  const start = Date.now();
  try {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeoutMs);

    const res = await fetch(url, {
      method: 'GET',
      signal: controller.signal,
    });

    clearTimeout(id);
    const latencyMs = Date.now() - start;

    // Some endpoints return 401/403 for unauthenticated requests,
    // which is fine — it means the service is up.
    const isUp = res.ok || res.status === 401 || res.status === 403;

    return {
      providerId,
      healthy: isUp,
      latencyMs,
      checkedAt: start,
      error: isUp ? undefined : `HTTP ${res.status}`,
    };
  } catch (e: any) {
    return {
      providerId,
      healthy: false,
      latencyMs: Date.now() - start,
      checkedAt: start,
      error: e.message || String(e),
    };
  }
}

export const healthMonitor = new HealthMonitor();
