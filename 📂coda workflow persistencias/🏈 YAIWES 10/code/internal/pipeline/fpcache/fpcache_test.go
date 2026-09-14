package fpcache

import (
	"path/filepath"
	"testing"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/pipeline"
)

func TestMarkAndMatchRoundTrip(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "fp.jsonl")

	s, err := Open(path)
	if err != nil {
		t.Fatal(err)
	}
	f := pipeline.ClassifiedFinding{
		Target: "api.acme.corp", AttackCategory: "xss", Title: "Reflected XSS in /search",
	}
	if s.MatchAny(f) {
		t.Fatal("empty cache should not match")
	}
	if err := s.Mark(f, "operator confirmed not exploitable"); err != nil {
		t.Fatal(err)
	}
	// Identical finding matches.
	if !s.MatchAny(f) {
		t.Fatal("should match after Mark")
	}
	// Different target does not.
	other := f
	other.Target = "different.corp"
	if s.MatchAny(other) {
		t.Fatal("different target should not match")
	}
	// Different title does not.
	other = f
	other.Title = "Stored XSS in profile"
	if s.MatchAny(other) {
		t.Fatal("different title should not match")
	}
}

func TestPersistsAcrossReopen(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "fp.jsonl")

	// First process: mark.
	s1, _ := Open(path)
	_ = s1.Mark(pipeline.ClassifiedFinding{Target: "a.com", AttackCategory: "xss", Title: "Test"}, "fp")

	// Second process: reopen; mark should still be there.
	s2, err := Open(path)
	if err != nil {
		t.Fatal(err)
	}
	if s2.Len() != 1 {
		t.Fatalf("want 1 pattern after reopen, got %d", s2.Len())
	}
	if !s2.MatchAny(pipeline.ClassifiedFinding{Target: "a.com", AttackCategory: "xss", Title: "Test"}) {
		t.Fatal("should match persisted pattern")
	}
}

func TestFilterDropsCached(t *testing.T) {
	s, _ := Open("")
	_ = s.Mark(pipeline.ClassifiedFinding{Target: "a.com", AttackCategory: "xss", Title: "FP"}, "noisy")

	in := []pipeline.ClassifiedFinding{
		{Target: "a.com", AttackCategory: "xss", Title: "FP finding"},    // dropped
		{Target: "a.com", AttackCategory: "sqli", Title: "Real finding"}, // kept
	}
	out := s.Filter(in)
	if len(out) != 1 || out[0].Title != "Real finding" {
		t.Fatalf("want only real finding, got %+v", out)
	}
}

func TestWildcardByTargetOrCategory(t *testing.T) {
	s, _ := Open("")
	// Empty title acts as wildcard — suppress ALL xss on this target.
	_ = s.Mark(pipeline.ClassifiedFinding{Target: "a.com", AttackCategory: "xss"}, "")
	for _, title := range []string{"Reflected XSS in /a", "Stored XSS in /b"} {
		f := pipeline.ClassifiedFinding{Target: "a.com", AttackCategory: "xss", Title: title}
		if !s.MatchAny(f) {
			t.Errorf("wildcard should match %q", title)
		}
	}
}
