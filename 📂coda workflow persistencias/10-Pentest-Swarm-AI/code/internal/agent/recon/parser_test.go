package recon

import (
	"errors"
	"strings"
	"testing"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/pipeline"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/tools"
)

// TestParseAttackSurface_StrictShape is the happy path: a frontier-API
// (Claude / GPT-4) response that honors the spec'd JSON shape end-to-end.
func TestParseAttackSurface_StrictShape(t *testing.T) {
	raw := `{
		"target": "example.com",
		"subdomains": [
			{"domain": "api.example.com", "ip": "1.2.3.4", "source": "subfinder"}
		],
		"hosts": [{"ip": "1.2.3.4", "hostnames": ["api.example.com"], "open_ports": [443]}],
		"endpoints": [{"url": "https://api.example.com/v1/users", "method": "GET"}],
		"technologies": {"nginx": "1.24", "express": "4.18"}
	}`

	s, err := ParseAttackSurface(raw)
	if err != nil {
		t.Fatalf("strict parse failed: %v", err)
	}
	if len(s.Subdomains) != 1 || s.Subdomains[0].Domain != "api.example.com" {
		t.Fatalf("subdomains not parsed strictly: %+v", s.Subdomains)
	}
	if s.Subdomains[0].Source != "subfinder" {
		t.Fatalf("source should come from input, not fallback marker; got %q", s.Subdomains[0].Source)
	}
	if s.Technologies["nginx"] != "1.24" {
		t.Fatalf("technologies map not parsed: %+v", s.Technologies)
	}
}

// TestParseAttackSurface_OllamaFlatStrings covers the #16 report: local
// Ollama models emit subdomains/hosts/endpoints as flat string arrays
// instead of object arrays. We promote each string into a record stamped
// with the fallback source marker so downstream code can see it was a
// degraded parse.
func TestParseAttackSurface_OllamaFlatStrings(t *testing.T) {
	raw := `{
		"target": "mydomain.com",
		"subdomains": ["hub.mydomain.com", "ss.mydomain.com"],
		"hosts": ["10.0.0.1", "10.0.0.2"],
		"endpoints": ["https://hub.mydomain.com/admin", "https://hub.mydomain.com/api"]
	}`

	s, err := ParseAttackSurface(raw)
	if err != nil {
		t.Fatalf("flat-string parse failed: %v", err)
	}
	if len(s.Subdomains) != 2 || s.Subdomains[0].Domain != "hub.mydomain.com" {
		t.Fatalf("flat subdomains not promoted: %+v", s.Subdomains)
	}
	if s.Subdomains[0].Source != fallbackSource {
		t.Fatalf("fallback source marker missing: %+v", s.Subdomains[0])
	}
	if len(s.Hosts) != 2 || s.Hosts[0].IP != "10.0.0.1" {
		t.Fatalf("flat hosts not promoted: %+v", s.Hosts)
	}
	if len(s.Endpoints) != 2 || s.Endpoints[0].URL != "https://hub.mydomain.com/admin" {
		t.Fatalf("flat endpoints not promoted: %+v", s.Endpoints)
	}
}

// TestParseAttackSurface_TechnologiesAsArray covers the same family as
// #7: model returns technologies as a flat list instead of a map. We
// keep the names; versions are stamped empty.
func TestParseAttackSurface_TechnologiesAsArray(t *testing.T) {
	raw := `{
		"target": "example.com",
		"technologies": ["nginx", "express", "react"]
	}`

	s, err := ParseAttackSurface(raw)
	if err != nil {
		t.Fatalf("array-technologies parse failed: %v", err)
	}
	if len(s.Technologies) != 3 {
		t.Fatalf("expected 3 technologies; got %d (%+v)", len(s.Technologies), s.Technologies)
	}
	if _, ok := s.Technologies["nginx"]; !ok {
		t.Fatalf("nginx not present in technologies map: %+v", s.Technologies)
	}
	if s.Technologies["nginx"] != "" {
		t.Fatalf("array fallback should leave versions empty; got %q", s.Technologies["nginx"])
	}
}

// TestParseAttackSurface_SingleObject covers the rarer drift where the
// model returns a single record instead of a one-element array.
func TestParseAttackSurface_SingleObject(t *testing.T) {
	raw := `{
		"target": "example.com",
		"subdomains": {"domain": "api.example.com", "source": "manual"}
	}`

	s, err := ParseAttackSurface(raw)
	if err != nil {
		t.Fatalf("single-object parse failed: %v", err)
	}
	if len(s.Subdomains) != 1 || s.Subdomains[0].Domain != "api.example.com" {
		t.Fatalf("single object not wrapped into array: %+v", s.Subdomains)
	}
}

// TestParseAttackSurface_MarkdownFenced covers the common case where the
// LLM wraps its JSON in a ```json fence.
func TestParseAttackSurface_MarkdownFenced(t *testing.T) {
	raw := "```json\n{\"target\": \"example.com\", \"subdomains\": [\"a.example.com\"]}\n```"
	s, err := ParseAttackSurface(raw)
	if err != nil {
		t.Fatalf("fenced parse failed: %v", err)
	}
	if s.Target != "example.com" {
		t.Fatalf("target lost in fence stripping: %q", s.Target)
	}
}

// TestParseAttackSurface_EmptyRejects ensures we still return a clear
// error on empty / whitespace-only input rather than a confusing nil.
func TestParseAttackSurface_EmptyRejects(t *testing.T) {
	if _, err := ParseAttackSurface(""); err == nil {
		t.Fatal("expected error on empty input")
	}
	if _, err := ParseAttackSurface("   \n  "); err == nil {
		t.Fatal("expected error on whitespace-only input")
	}
}

// TestParseAttackSurface_MissingFieldsAreNil — partial responses should
// not crash. The fields the model didn't include just come back nil.
func TestParseAttackSurface_MissingFieldsAreNil(t *testing.T) {
	raw := `{"target": "example.com"}`
	s, err := ParseAttackSurface(raw)
	if err != nil {
		t.Fatalf("minimal parse failed: %v", err)
	}
	if s.Subdomains != nil || s.Hosts != nil || s.Endpoints != nil || s.Technologies != nil {
		t.Fatalf("missing fields should be nil; got s=%+v", s)
	}
}

func TestMergeToolResults_NormalizesAndDeduplicatesFindings(t *testing.T) {
	results := []*tools.ToolResult{
		nil,
		{
			ToolName: "katana",
			ParsedFindings: []map[string]any{
				{"request": map[string]any{"endpoint": "https://example.com/a"}},
				{"request": map[string]any{"endpoint": "https://example.com/a"}},
				{"request": map[string]any{"endpoint": "  "}},
				{"request": map[string]any{"endpoint": 42}},
				{"request": "malformed"},
			},
		},
		{
			ToolName: "mixed",
			ParsedFindings: []map[string]any{
				{"url": " https://example.com/b ", "host": "192.0.2.10", "subdomain": "api.example.com"},
				{"url": "", "host": " ", "subdomain": ""},
			},
		},
		{
			ToolName:       "failed",
			Error:          errors.New("tool failed"),
			ParsedFindings: []map[string]any{{"url": "https://ignored.example.com"}},
		},
	}

	merged := MergeToolResults(results)
	if len(merged.Endpoints) != 2 || !merged.Endpoints["https://example.com/a"] || !merged.Endpoints["https://example.com/b"] {
		t.Fatalf("endpoints = %+v, want two normalized unique URLs", merged.Endpoints)
	}
	if len(merged.Hosts) != 1 || !merged.Hosts["192.0.2.10"] {
		t.Fatalf("hosts = %+v, want one non-empty host", merged.Hosts)
	}
	if len(merged.Subdomains) != 1 || !merged.Subdomains["api.example.com"] {
		t.Fatalf("subdomains = %+v, want one non-empty subdomain", merged.Subdomains)
	}
}

func TestReconcileToolResults_SupplementsWithoutOverwritingLLMMetadata(t *testing.T) {
	surface := &pipeline.AttackSurface{
		Subdomains: []pipeline.SubdomainRecord{{Domain: "api.example.com", IP: "192.0.2.10", Source: "llm"}},
		Hosts: []pipeline.HostRecord{{
			IP:        "192.0.2.10",
			Hostnames: []string{"api.example.com"},
			OpenPorts: []int{443},
			OS:        "Linux",
		}},
		Endpoints: []pipeline.EndpointRecord{{
			URL:         "https://api.example.com/admin",
			Method:      "POST",
			StatusCode:  403,
			Interesting: true,
			Notes:       "authentication required",
		}},
	}
	results := []*tools.ToolResult{{
		ToolName: "recon",
		ParsedFindings: []map[string]any{
			{"subdomain": "api.example.com", "host": "192.0.2.10", "url": "https://api.example.com/admin"},
			{"subdomain": "cdn.example.com", "host": "192.0.2.11", "url": "https://cdn.example.com/app.js"},
		},
	}}

	recovered := reconcileToolResults(surface, results)
	if !recovered {
		t.Fatal("expected deterministic findings to supplement the surface")
	}
	if len(surface.Subdomains) != 2 || len(surface.Hosts) != 2 || len(surface.Endpoints) != 2 {
		t.Fatalf("reconciled surface contains duplicates or omissions: %+v", surface)
	}
	if got := surface.Subdomains[0]; got.IP != "192.0.2.10" || got.Source != "llm" {
		t.Fatalf("matching subdomain metadata was overwritten: %+v", got)
	}
	if got := surface.Hosts[0]; got.OS != "Linux" || len(got.OpenPorts) != 1 || got.OpenPorts[0] != 443 {
		t.Fatalf("matching host metadata was overwritten: %+v", got)
	}
	if got := surface.Endpoints[0]; got.Method != "POST" || got.StatusCode != 403 || !got.Interesting || got.Notes == "" {
		t.Fatalf("matching endpoint metadata was overwritten: %+v", got)
	}
	if reconcileToolResults(surface, results) {
		t.Fatal("reconciling the same findings twice should not report another recovery")
	}
	if len(surface.Subdomains) != 2 || len(surface.Hosts) != 2 || len(surface.Endpoints) != 2 {
		t.Fatalf("second reconciliation introduced duplicates: %+v", surface)
	}
}

func TestExtractVulnerabilities_Nuclei(t *testing.T) {
	r := &tools.ToolResult{ToolName: "nuclei", ParsedFindings: []map[string]any{
		{"template-id": "http-missing-security-headers", "matched-at": "http://t/",
			"info": map[string]any{"name": "HTTP Missing Security Headers", "severity": "info"}},
		{"template-id": "CVE-2021-1234", "matched-at": "http://t/x",
			"info": map[string]any{"name": "Some RCE", "severity": "critical"}},
	}}
	v := ExtractVulnerabilities([]*tools.ToolResult{r})
	if len(v) != 2 {
		t.Fatalf("want 2 vulns, got %d", len(v))
	}
	if v[0].Title != "HTTP Missing Security Headers" || v[0].Severity != "info" {
		t.Errorf("nuclei vuln 0 = %+v", v[0])
	}
	if v[1].Severity != "critical" || v[1].Reference != "CVE-2021-1234" {
		t.Errorf("nuclei vuln 1 = %+v", v[1])
	}
}

func TestExtractVulnerabilities_Dalfox(t *testing.T) {
	r := &tools.ToolResult{ToolName: "dalfox", ParsedFindings: []map[string]any{
		{"type": "V", "param": "q", "severity": "H", "data": "http://t/?q=x", "evidence": "<script>"},
	}}
	v := ExtractVulnerabilities([]*tools.ToolResult{r})
	if len(v) != 1 || v[0].Severity != "high" {
		t.Fatalf("dalfox = %+v", v)
	}
	if !strings.Contains(v[0].Title, "XSS") || !strings.Contains(v[0].Title, "q") {
		t.Errorf("dalfox title = %q", v[0].Title)
	}
}

func TestExtractVulnerabilities_NiktoAndSqlmap(t *testing.T) {
	nikto := &tools.ToolResult{ToolName: "nikto", ParsedFindings: []map[string]any{
		{"title": "X-Content-Type-Options header not set", "url": "/", "severity": "low", "id": "999103"},
	}}
	sqlmap := &tools.ToolResult{ToolName: "sqlmap", Target: "http://t/login", ParsedFindings: []map[string]any{
		{"type": 1, "value": "injectable"},
	}}
	v := ExtractVulnerabilities([]*tools.ToolResult{nikto, sqlmap})
	if len(v) != 2 {
		t.Fatalf("want 2, got %d: %+v", len(v), v)
	}
	if v[0].Tool != "nikto" || v[0].Severity != "low" {
		t.Errorf("nikto = %+v", v[0])
	}
	if v[1].Tool != "sqlmap" || v[1].Title != "SQL Injection" || v[1].Severity != "critical" {
		t.Errorf("sqlmap = %+v", v[1])
	}
}

func TestExtractVulnerabilities_CRLFuzz(t *testing.T) {
	r := &tools.ToolResult{ToolName: "crlfuzz", ParsedFindings: []map[string]any{
		{"url": "http://t/%0d%0aSet-Cookie:x", "severity": "high", "category": "crlf_injection"},
		{"url": ""}, // missing url is skipped
	}}
	v := ExtractVulnerabilities([]*tools.ToolResult{r})
	if len(v) != 1 {
		t.Fatalf("want 1, got %d: %+v", len(v), v)
	}
	if v[0].Tool != "crlfuzz" || v[0].Severity != "high" || !strings.Contains(v[0].Title, "CRLF") {
		t.Errorf("crlfuzz = %+v", v[0])
	}
}

func TestExtractVulnerabilities_GXSS(t *testing.T) {
	// gxss reports "medium" for a reflection, but we downgrade to low because
	// reflection is a lead, not a confirmed exploit — keep the report honest.
	r := &tools.ToolResult{ToolName: "gxss", ParsedFindings: []map[string]any{
		{"url": "http://t/?q=x", "severity": "medium", "category": "reflected_input"},
	}}
	v := ExtractVulnerabilities([]*tools.ToolResult{r})
	if len(v) != 1 || v[0].Tool != "gxss" || v[0].Severity != "low" {
		t.Fatalf("gxss = %+v", v)
	}
	if !strings.Contains(v[0].Title, "XSS") {
		t.Errorf("gxss title = %q", v[0].Title)
	}
}
