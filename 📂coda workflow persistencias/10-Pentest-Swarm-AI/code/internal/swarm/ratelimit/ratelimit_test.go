package ratelimit

import (
	"context"
	"testing"
	"time"
)

func TestLimiter_ZeroRateDoesNotBlock(t *testing.T) {
	l := New(0, 0)
	for i := 0; i < 100; i++ {
		if err := l.Take(context.Background()); err != nil {
			t.Fatalf("zero-rate Take returned %v", err)
		}
	}
}

func TestLimiter_BurstThenThrottle(t *testing.T) {
	// 10 tokens/sec, burst 3. The 4th Take should block for ~100ms.
	l := New(10, 3)
	ctx := context.Background()
	for i := 0; i < 3; i++ {
		_ = l.Take(ctx)
	}
	start := time.Now()
	_ = l.Take(ctx)
	got := time.Since(start)
	if got < 80*time.Millisecond || got > 200*time.Millisecond {
		t.Errorf("expected ~100ms wait, got %v", got)
	}
}

func TestLimiter_ContextCancelReturnsErr(t *testing.T) {
	l := New(0.1, 1) // 1 token/10s — slow
	_ = l.Take(context.Background())

	ctx, cancel := context.WithCancel(context.Background())
	go func() {
		time.Sleep(20 * time.Millisecond)
		cancel()
	}()
	if err := l.Take(ctx); err == nil {
		t.Error("expected context error")
	}
}

func TestLimiter_NilSafe(t *testing.T) {
	var l *Limiter
	if err := l.Take(context.Background()); err != nil {
		t.Errorf("nil Limiter.Take should be a no-op, got %v", err)
	}
}
