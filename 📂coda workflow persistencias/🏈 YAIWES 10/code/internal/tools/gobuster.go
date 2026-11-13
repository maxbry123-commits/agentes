package tools

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/scope"
)

// GobusterTool wraps gobuster for directory + DNS enumeration. gobuster
// prints findings one per line in a well-known format; we parse that
// rather than enabling JSON because older versions lack structured output.
type GobusterTool struct{}

// NewGobusterTool constructs the adapter.
func NewGobusterTool() *GobusterTool { return &GobusterTool{} }

// Name implements Tool.
func (g *GobusterTool) Name() string { return "gobuster" }

// IsAvailable implements Tool.
func (g *GobusterTool) IsAvailable() bool { return IsCommandAvailable("gobuster") }

// Run runs gobuster in the configured mode (dir by default, dns via
// opts["mode"] = "dns").
func (g *GobusterTool) Run(ctx context.Context, target string, opts Options) (*ToolResult, error) {
	if scopeDef := getScopeFromContext(ctx); scopeDef != nil {
		if err := scope.ValidateAndLog("gobuster", target, *scopeDef); err != nil {
			return nil, fmt.Errorf("scope violation in gobuster: %w", err)
		}
	}

	mode := opts.GetString("mode", "dir")
	wordlist := opts.GetString("wordlist", "/usr/share/seclists/Discovery/Web-Content/common.txt")
	threads := opts.GetInt("threads", 40)
	timeout := time.Duration(opts.GetInt("timeout", 300)) * time.Second

	args := []string{mode, "-w", wordlist, "-t", fmt.Sprintf("%d", threads), "-q", "--no-error"}
	if mode == "dir" {
		args = append(args, "-u", target)
	} else {
		args = append(args, "-d", target)
	}

	result := RunToolCommand(ctx, g.Name(), target, timeout, "gobuster", args...)
	if result.Error != nil {
		return result, result.Error
	}

	// Parse `/admin          (Status: 200) [Size: 1234]` one-per-line.
	for _, line := range strings.Split(result.RawOutput, "\n") {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		result.ParsedFindings = append(result.ParsedFindings, map[string]any{
			"mode": mode, "line": line,
		})
	}
	return result, nil
}
