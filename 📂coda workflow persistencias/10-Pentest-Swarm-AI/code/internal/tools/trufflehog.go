package tools

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/scope"
)

// TrufflehogTool scans a repo / filesystem / artifact for leaked secrets.
// Unlike the other ProjectDiscovery-adjacent tools, trufflehog's `target`
// can be a local path, git URL, or docker image; scope enforcement is
// therefore advisory — the operator is expected to pass paths/repos they
// already control.
type TrufflehogTool struct{}

// NewTrufflehogTool constructs the adapter.
func NewTrufflehogTool() *TrufflehogTool { return &TrufflehogTool{} }

// Name implements Tool.
func (t *TrufflehogTool) Name() string { return "trufflehog" }

// IsAvailable implements Tool.
func (t *TrufflehogTool) IsAvailable() bool { return IsCommandAvailable("trufflehog") }

// Run executes trufflehog with --json so findings are NDJSON (one finding per line).
// opts["source"] picks the subcommand: "git" (default), "filesystem", "docker".
func (t *TrufflehogTool) Run(ctx context.Context, target string, opts Options) (*ToolResult, error) {
	source := opts.GetString("source", "git")
	onlyVerified := opts.GetBool("only_verified", true)
	timeout := time.Duration(opts.GetInt("timeout", 300)) * time.Second

	// Best-effort scope check for remote git URLs or hostnames in the target.
	if scopeDef := getScopeFromContext(ctx); scopeDef != nil && looksLikeURL(target) {
		if err := scope.ValidateAndLog("trufflehog", target, *scopeDef); err != nil {
			return nil, fmt.Errorf("scope violation in trufflehog: %w", err)
		}
	}

	args := []string{source, target, "--json"}
	if onlyVerified {
		args = append(args, "--only-verified")
	}
	result := RunToolCommand(ctx, t.Name(), target, timeout, "trufflehog", args...)
	if result.Error != nil {
		return result, result.Error
	}

	// NDJSON parse — one JSON object per line.
	for _, line := range strings.Split(result.RawOutput, "\n") {
		line = strings.TrimSpace(line)
		if line == "" || line[0] != '{' {
			continue
		}
		var m map[string]any
		if err := json.Unmarshal([]byte(line), &m); err != nil {
			continue
		}
		// Redact the actual secret before surfacing.
		if _, ok := m["Raw"]; ok {
			m["Raw"] = "[REDACTED]"
		}
		if _, ok := m["RawV2"]; ok {
			m["RawV2"] = "[REDACTED]"
		}
		result.ParsedFindings = append(result.ParsedFindings, m)
	}
	return result, nil
}

func looksLikeURL(s string) bool {
	return strings.HasPrefix(s, "http://") || strings.HasPrefix(s, "https://") ||
		strings.HasPrefix(s, "git@") || strings.HasPrefix(s, "git://")
}
