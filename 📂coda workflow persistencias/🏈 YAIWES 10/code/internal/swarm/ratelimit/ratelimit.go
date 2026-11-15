// Package ratelimit caps the rate at which an agent processes findings
// off the blackboard. Belt-and-braces against pathological feedback
// loops: an agent that wakes itself (via its own writes) without
// rate-limiting can saturate the LLM provider in seconds.
//
// Limiter is a tiny token bucket — fills at `rate` tokens/second up to
// `burst` tokens, blocks Take() when empty. No external dependency
// (we intentionally avoid pulling in golang.org/x/time just for this).
package ratelimit

import (
	"context"
	"sync"
	"time"
)

// Limiter is a per-agent rate cap.
type Limiter struct {
	rate   float64 // tokens added per second
	burst  float64 // bucket capacity
	tokens float64
	last   time.Time
	mu     sync.Mutex
}

// New builds a limiter that fills at perSecond tokens/second, with a
// bucket cap of burst tokens (default = perSecond if burst<=0). A
// rate of 0 means no limit (Take returns instantly).
func New(perSecond, burst float64) *Limiter {
	if burst <= 0 {
		burst = perSecond
	}
	return &Limiter{
		rate:   perSecond,
		burst:  burst,
		tokens: burst,
		last:   time.Now(),
	}
}

// Take blocks until one token is available (or ctx is done). Returns
// ctx.Err() on cancellation; nil on a successful take. Rate <= 0
// short-circuits — no waiting.
func (l *Limiter) Take(ctx context.Context) error {
	if l == nil || l.rate <= 0 {
		return nil
	}
	for {
		l.mu.Lock()
		now := time.Now()
		// Refill bucket based on elapsed time.
		elapsed := now.Sub(l.last).Seconds()
		l.tokens += elapsed * l.rate
		if l.tokens > l.burst {
			l.tokens = l.burst
		}
		l.last = now

		if l.tokens >= 1 {
			l.tokens--
			l.mu.Unlock()
			return nil
		}
		// Compute the smallest wait that yields a token.
		need := 1 - l.tokens
		wait := time.Duration(need / l.rate * float64(time.Second))
		l.mu.Unlock()

		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(wait):
			// loop and retry
		}
	}
}
