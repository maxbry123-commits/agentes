package dedup

import "testing"

func TestFindDuplicates_SimilarTitlesMatch(t *testing.T) {
	priors := []Prior{
		{ID: "1", Title: "Stored XSS in comments section"},
		{ID: "2", Title: "SQL injection in /search endpoint"},
		{ID: "3", Title: "Missing HSTS header"},
	}
	hits := FindDuplicates("SQL Injection on the search endpoint", "", priors, 0.4, 3)
	if len(hits) == 0 || hits[0].Prior.ID != "2" {
		t.Fatalf("expected match with #2; got %+v", hits)
	}
}

func TestFindDuplicates_TargetBoost(t *testing.T) {
	priors := []Prior{
		{ID: "match", Title: "XSS somewhere", Target: "acme.corp"},
		{ID: "nomatch", Title: "XSS somewhere"},
	}
	// Same token set, but only one shares the target — that one should rank higher.
	hits := FindDuplicates("XSS somewhere", "acme.corp", priors, 0.5, 2)
	if len(hits) == 0 {
		t.Fatal("expected at least one hit")
	}
	if hits[0].Prior.ID != "match" {
		t.Fatalf("target-matching prior should rank first; got %+v", hits)
	}
}

func TestFindDuplicates_BelowThresholdDropped(t *testing.T) {
	priors := []Prior{{ID: "1", Title: "Completely unrelated bug"}}
	hits := FindDuplicates("SSRF in image fetcher", "", priors, 0.5, 3)
	if len(hits) != 0 {
		t.Fatalf("unrelated titles should not match; got %+v", hits)
	}
}

func TestTokenise_DropsStopwords(t *testing.T) {
	tokens := tokenise("SQL injection in the search endpoint")
	if _, in := tokens["in"]; in {
		t.Error("'in' should be a stopword")
	}
	if _, in := tokens["the"]; in {
		t.Error("'the' should be a stopword")
	}
	for _, w := range []string{"sql", "injection", "search", "endpoint"} {
		if _, ok := tokens[w]; !ok {
			t.Errorf("expected token %q", w)
		}
	}
}
