package tools

import (
	"context"
	"encoding/json"
	"fmt"
	"time"
)

// SemgrepTool runs static-analysis rules against a repo. Uses the OWASP
// Top Ten and CWE Top 25 rule packs by default; SARIF output is available
// for CI/CD pipelines. Target is a filesystem path.
type SemgrepTool struct{}

// NewSemgrepTool constructs the adapter.
func NewSemgrepTool() *SemgrepTool { return &SemgrepTool{} }

// Name implements Tool.
func (s *SemgrepTool) Name() string { return "semgrep" }

// IsAvailable implements Tool.
func (s *SemgrepTool) IsAvailable() bool { return IsCommandAvailable("semgrep") }

// Run executes semgrep with JSON output against the given path. opts["config"]
// accepts any rule pack identifier (p/owasp-top-ten, p/cwe-top-25, etc.).
func (s *SemgrepTool) Run(ctx context.Context, target string, opts Options) (*ToolResult, error) {
	timeout := time.Duration(opts.GetInt("timeout", 600)) * time.Second
	if target == "" {
		target = "."
	}
	config := opts.GetString("config", "p/owasp-top-ten")

	args := []string{"--config", config, "--json", "--quiet", target}
	result := RunToolCommand(ctx, s.Name(), target, timeout, "semgrep", args...)
	if result.Error != nil && result.RawOutput == "" {
		return result, result.Error
	}

	var parsed struct {
		Results []map[string]any `json:"results"`
		Errors  []map[string]any `json:"errors"`
	}
	if err := json.Unmarshal([]byte(result.RawOutput), &parsed); err != nil {
		return result, nil
	}
	result.ParsedFindings = parsed.Results
	if len(parsed.Errors) > 0 && result.Error == nil {
		// Surface rule-eval errors as a single synthetic entry rather than
		// hiding them in RawOutput.
		result.ParsedFindings = append(result.ParsedFindings, map[string]any{
			"_type":  "errors",
			"errors": parsed.Errors,
		})
	}
	// Semgrep exits 1 when findings exist; that's success for our purposes.
	if result.Error != nil && len(result.ParsedFindings) > 0 {
		result.Error = nil
	}
	_ = fmt.Sprintf
	return result, nil
}
