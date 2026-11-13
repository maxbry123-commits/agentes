package tools

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"time"
)

// GitleaksTool scans git history (or a plain filesystem) for committed
// secrets. Output is a JSON array written to a file we read + redact.
// target is a filesystem path; scope enforcement doesn't apply here —
// git history scanning is always local.
type GitleaksTool struct{}

// NewGitleaksTool constructs the adapter.
func NewGitleaksTool() *GitleaksTool { return &GitleaksTool{} }

// Name implements Tool.
func (g *GitleaksTool) Name() string { return "gitleaks" }

// IsAvailable implements Tool.
func (g *GitleaksTool) IsAvailable() bool { return IsCommandAvailable("gitleaks") }

// Run executes gitleaks in detect mode against target (defaults to ./).
func (g *GitleaksTool) Run(ctx context.Context, target string, opts Options) (*ToolResult, error) {
	timeout := time.Duration(opts.GetInt("timeout", 300)) * time.Second
	if target == "" {
		target = "."
	}

	outFile, err := os.CreateTemp("", "gitleaks-*.json")
	if err != nil {
		return nil, fmt.Errorf("gitleaks tmpfile: %w", err)
	}
	outFile.Close()
	defer os.Remove(outFile.Name())

	mode := opts.GetString("mode", "detect") // detect | protect
	args := []string{mode, "-s", target, "--report-format", "json", "--report-path", outFile.Name(), "--no-banner", "--redact"}
	if cfg := opts.GetString("config", ""); cfg != "" {
		args = append(args, "-c", cfg)
	}

	result := RunToolCommand(ctx, g.Name(), target, timeout, "gitleaks", args...)
	// gitleaks exits non-zero when leaks are found — that's not an error.
	data, _ := os.ReadFile(outFile.Name())
	if len(data) > 0 {
		var findings []map[string]any
		if err := json.Unmarshal(data, &findings); err == nil {
			for i := range findings {
				// --redact already scrubs Match; belt-and-braces just in case.
				if _, ok := findings[i]["Secret"]; ok {
					findings[i]["Secret"] = "[REDACTED]"
				}
			}
			result.ParsedFindings = findings
		}
	}
	// Clear error if it was purely due to leaks being detected.
	if result.Error != nil && len(result.ParsedFindings) > 0 {
		result.Error = nil
	}
	return result, nil
}
