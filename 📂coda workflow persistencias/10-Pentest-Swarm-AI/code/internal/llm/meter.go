package llm

import (
	"context"
	"sync"
)

// Meter records cumulative token + dollar spend across every LLM call in
// a campaign. It's safe for concurrent use and exposes a Snapshot() for
// the live cost meter and the final ROI footer.
//
// A Meter wraps a Provider via Wrap() — the wrapper decorator adds every
// response's Usage to the total. Agents and the rest of the codebase
// keep talking to the Provider interface; only the factory cares that
// one of the providers happens to be metered.
type Meter struct {
	pricing Pricing
	mu      sync.RWMutex
	total   Usage
}

// NewMeter builds a meter for the given model's pricing.
func NewMeter(model string) *Meter {
	return &Meter{pricing: PricingFor(model)}
}

// Record adds usage to the running total.
func (m *Meter) Record(u Usage) {
	m.mu.Lock()
	m.total.InputTokens += u.InputTokens
	m.total.OutputTokens += u.OutputTokens
	m.total.CacheCreationInputTokens += u.CacheCreationInputTokens
	m.total.CacheReadInputTokens += u.CacheReadInputTokens
	m.mu.Unlock()
}

// Snapshot returns the cumulative usage + dollar cost right now.
func (m *Meter) Snapshot() (Usage, float64) {
	m.mu.RLock()
	u := m.total
	m.mu.RUnlock()
	return u, m.pricing.CostUSD(u)
}

// Pricing is the pricing table backing this meter.
func (m *Meter) Pricing() Pricing { return m.pricing }

// meteredProvider is a transparent decorator that records every call.
type meteredProvider struct {
	inner Provider
	meter *Meter
}

// Wrap returns a Provider that records every Complete call on the meter.
// Stream is passed through but its usage is not captured — current Claude
// streaming responses don't surface Usage mid-stream.
func (m *Meter) Wrap(inner Provider) Provider {
	return &meteredProvider{inner: inner, meter: m}
}

func (mp *meteredProvider) Complete(ctx context.Context, req CompletionRequest) (*CompletionResponse, error) {
	resp, err := mp.inner.Complete(ctx, req)
	if resp != nil {
		mp.meter.Record(resp.Usage)
	}
	return resp, err
}

func (mp *meteredProvider) Stream(ctx context.Context, req CompletionRequest) (<-chan StreamChunk, error) {
	return mp.inner.Stream(ctx, req)
}

func (mp *meteredProvider) HealthCheck(ctx context.Context) error { return mp.inner.HealthCheck(ctx) }
func (mp *meteredProvider) ModelName() string                     { return mp.inner.ModelName() }
func (mp *meteredProvider) ContextWindow() int                    { return mp.inner.ContextWindow() }
func (mp *meteredProvider) SupportsToolUse() bool                 { return mp.inner.SupportsToolUse() }
