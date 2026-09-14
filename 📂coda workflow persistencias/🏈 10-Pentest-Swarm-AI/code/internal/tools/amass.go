package tools

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/scope"
)

// AmassTool wraps OWASP Amass for deeper OSINT / ASM than subfinder.
// Runs in passive mode by default to avoid active DNS queries against
// the target; flip `opts["active"] = true` for brute + bruteforce modes.
type AmassTool struct{}

// NewAmassTool constructs the adapter.
func NewAmassTool() *AmassTool { return &AmassTool{} }

// Name implements Tool.
func (a *AmassTool) Name() string { return "amass" }

// IsAvailable implements Tool.
func (a *AmassTool) IsAvailable() bool { return IsCommandAvailable("amass") }

// Run enumerates subdomains of target using amass `enum -d`.
func (a *AmassTool) Run(ctx context.Context, target string, opts Options) (*ToolResult, error) {
	if scopeDef := getScopeFromContext(ctx); scopeDef != nil {
		if err := scope.ValidateAndLog("amass", target, *scopeDef); err != nil {
			return nil, fmt.Errorf("scope violation in amass: %w", err)
		}
	}

	timeout := time.Duration(opts.GetInt("timeout", 600)) * time.Second
	active := opts.GetBool("active", false)

	args := []string{"enum", "-d", target, "-json", "-"}
	if !active {
		args = append(args, "-passive")
	}

	result := RunToolCommand(ctx, a.Name(), target, timeout, "amass", args...)
	if result.Error != nil && result.RawOutput == "" {
		return result, result.Error
	}

	// amass -json - prints one JSON object per line.
	for _, line := range strings.Split(result.RawOutput, "\n") {
		line = strings.TrimSpace(line)
		if line == "" || line[0] != '{' {
			continue
		}
		var m map[string]any
		if err := json.Unmarshal([]byte(line), &m); err == nil {
			result.ParsedFindings = append(result.ParsedFindings, m)
		}
	}
	return result, nil
}
