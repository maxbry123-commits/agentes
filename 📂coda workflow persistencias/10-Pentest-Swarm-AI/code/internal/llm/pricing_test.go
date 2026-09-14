package llm

import "testing"

func TestPricingFor_KnownAndUnknown(t *testing.T) {
	if PricingFor("claude-haiku-4-5-20251001").OutputPerMillion != 4.0 {
		t.Fatal("haiku output price should be 4.0")
	}
	if PricingFor("unknown-model").OutputPerMillion != 15.0 {
		t.Fatal("unknown model should default to sonnet ($15 output)")
	}
}

func TestCostUSD_BreaksDownByToken(t *testing.T) {
	p := PricingFor("claude-sonnet-4-6")
	u := Usage{
		InputTokens:              100_000,
		CacheCreationInputTokens: 10_000,
		CacheReadInputTokens:     50_000,
		OutputTokens:             20_000,
	}
	got := p.CostUSD(u)
	// Expected: (110_000 * 3 + 50_000 * 0.30 + 20_000 * 15) / 1e6
	//         = (330_000 + 15_000 + 300_000) / 1e6 = 0.645
	if got < 0.64 || got > 0.65 {
		t.Fatalf("cost breakdown off: got %.4f, want ~0.645", got)
	}
}

func TestEstimate_Buckets(t *testing.T) {
	p := PricingFor("claude-sonnet-4-6")
	small, _ := p.EstimateUSD("small")
	_, largeHi := p.EstimateUSD("large")
	if small <= 0 || largeHi <= small {
		t.Fatalf("expected small=%.4f < large-hi=%.4f", small, largeHi)
	}
}

func TestUsage_CacheHitRate(t *testing.T) {
	u := Usage{InputTokens: 100, CacheReadInputTokens: 900}
	if r := u.CacheHitRate(); r < 0.89 || r > 0.91 {
		t.Fatalf("cache hit rate: want ~0.9, got %f", r)
	}
}
