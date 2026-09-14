package classifier

import "testing"

// TestParseClassifierFindings_StrictArray is the spec'd shape — what
// Claude / GPT-4 return when using structured output mode.
func TestParseClassifierFindings_StrictArray(t *testing.T) {
	raw := `[{"title": "SQLi in /login", "severity": "high", "cvss_score": 8.6}]`
	out, err := parseClassifierFindings(raw)
	if err != nil {
		t.Fatalf("strict array parse failed: %v", err)
	}
	if len(out) != 1 || out[0].Title != "SQLi in /login" {
		t.Fatalf("strict array not parsed: %+v", out)
	}
}

// TestParseClassifierFindings_WrappedObject covers the shape some local
// models emit: {"findings": [...]} instead of a top-level array. Common
// when the model has been fine-tuned to always wrap output in an object.
func TestParseClassifierFindings_WrappedObject(t *testing.T) {
	raw := `{"findings": [
		{"title": "XSS in search", "severity": "medium", "cvss_score": 6.1},
		{"title": "SSRF in /webhook", "severity": "high", "cvss_score": 8.2}
	]}`
	out, err := parseClassifierFindings(raw)
	if err != nil {
		t.Fatalf("wrapped object parse failed: %v", err)
	}
	if len(out) != 2 || out[0].Title != "XSS in search" || out[1].Title != "SSRF in /webhook" {
		t.Fatalf("wrapped array not extracted: %+v", out)
	}
}

// TestParseClassifierFindings_SingleObject covers #19 directly: the
// classifier was asked to classify one finding and the model returned a
// single classification object instead of a one-element array.
func TestParseClassifierFindings_SingleObject(t *testing.T) {
	raw := `{"title": "Open Redirect", "severity": "low", "cvss_score": 3.5}`
	out, err := parseClassifierFindings(raw)
	if err != nil {
		t.Fatalf("single object parse failed: %v", err)
	}
	if len(out) != 1 || out[0].Title != "Open Redirect" {
		t.Fatalf("single object not wrapped: %+v", out)
	}
}

// TestParseClassifierFindings_EmptyAndGarbageRejected — we still want a
// clear error path so genuine garbage doesn't silently produce nil.
func TestParseClassifierFindings_EmptyAndGarbageRejected(t *testing.T) {
	cases := []string{"", "  ", "not json at all", "{\"unrelated\": \"object\"}"}
	for _, c := range cases {
		if _, err := parseClassifierFindings(c); err == nil {
			t.Fatalf("expected error for input %q", c)
		}
	}
}

// TestParseClassifierFindings_ProseWrappedJSON — reasoning models (GLM, Qwen,
// DeepSeek-R1) sometimes prepend a sentence of prose before the JSON despite
// instructions. The extractFirstJSON fallback should still recover the array.
func TestParseClassifierFindings_ProseWrappedJSON(t *testing.T) {
	raw := "I'll analyze these findings now. Here is the result:\n\n" +
		`[{"title": "Exposed Metrics Endpoint", "severity": "medium", "cvss_score": 5.3}]` +
		"\n\nLet me know if you need more detail."
	out, err := parseClassifierFindings(raw)
	if err != nil {
		t.Fatalf("prose-wrapped parse failed: %v", err)
	}
	if len(out) != 1 || out[0].Title != "Exposed Metrics Endpoint" {
		t.Fatalf("prose-wrapped JSON not extracted: %+v", out)
	}
}

func TestExtractFirstJSON(t *testing.T) {
	cases := []struct{ in, want string }{
		{"prefix [1,2,3] suffix", "[1,2,3]"},
		{`text {"a": "]"} more`, `{"a": "]"}`}, // bracket inside string ignored
		{"no json here", ""},
		{`{"nested": {"x": 1}} tail`, `{"nested": {"x": 1}}`},
	}
	for _, c := range cases {
		if got := extractFirstJSON(c.in); got != c.want {
			t.Fatalf("extractFirstJSON(%q) = %q, want %q", c.in, got, c.want)
		}
	}
}
