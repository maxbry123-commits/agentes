package tuning

import (
	"testing"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/swarm/blackboard"
)

func TestDefault_LoadsEveryType(t *testing.T) {
	s := Default()
	if s == nil || len(s.Types) == 0 {
		t.Fatal("default settings should ship with types")
	}
	// Spot-check a handful of known types.
	for _, typ := range []blackboard.FindingType{
		blackboard.TypeSubdomain,
		blackboard.TypePortOpen,
		blackboard.TypeCVEMatch,
		blackboard.TypeExploitChain,
	} {
		base, half := s.Lookup(typ)
		if base <= 0 || half <= 0 {
			t.Errorf("%s: base=%.2f half=%d — both should be positive", typ, base, half)
		}
	}
}

func TestLookup_FallsBackToDefault(t *testing.T) {
	s := Default()
	base, half := s.Lookup("SOMETHING_UNKNOWN")
	if base <= 0 || half <= 0 {
		t.Fatalf("unknown type should hit the default entry, got base=%.2f half=%d", base, half)
	}
}

func TestWithBias_ScalesBaseOnly(t *testing.T) {
	s := Default()
	base, half := s.Lookup(blackboard.TypeSubdomain)

	high := s.WithBias(BiasHigh)
	baseHigh, halfHigh := high.Lookup(blackboard.TypeSubdomain)
	if baseHigh <= base {
		t.Errorf("high bias should raise base: was %.3f, high %.3f", base, baseHigh)
	}
	if halfHigh != half {
		t.Errorf("bias must not change half-life: was %d, got %d", half, halfHigh)
	}

	low := s.WithBias(BiasLow)
	baseLow, _ := low.Lookup(blackboard.TypeSubdomain)
	if baseLow >= base {
		t.Errorf("low bias should lower base: was %.3f, low %.3f", base, baseLow)
	}
}

func TestBias_UnknownMultiplier(t *testing.T) {
	if Bias("nonsense").Multiplier() != 1.0 {
		t.Fatal("unknown bias should fall back to 1.0")
	}
}

func TestLookupFor_ReturnsReadyFinding(t *testing.T) {
	s := Default()
	f := s.LookupFor(blackboard.TypeCVEMatch)
	if f.Type != blackboard.TypeCVEMatch || f.PheromoneBase <= 0 || f.HalfLifeSec <= 0 {
		t.Fatalf("LookupFor CVE_MATCH returned %+v", f)
	}
}
