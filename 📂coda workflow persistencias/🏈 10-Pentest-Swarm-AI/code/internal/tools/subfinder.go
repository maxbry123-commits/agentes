package tools

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/scope"
)

// SubfinderTool wraps subfinder for passive subdomain discovery.
type SubfinderTool struct{}

func NewSubfinderTool() *SubfinderTool { return &SubfinderTool{} }

func (s *SubfinderTool) Name() string { return "subfinder" }

func (s *SubfinderTool) IsAvailable() bool {
	return IsCommandAvailable("subfinder")
}

func (s *SubfinderTool) Run(ctx context.Context, target string, opts Options) (*ToolResult, error) {
	scopeDef := getScopeFromContext(ctx)
	if scopeDef != nil {
		if err := scope.ValidateAndLog("subfinder", target, *scopeDef); err != nil {
			return nil, fmt.Errorf("scope violation in subfinder: %w", err)
		}
	}

	timeout := time.Duration(opts.GetInt("timeout", 300)) * time.Second
	args := []string{"-d", target, "-silent"}

	if opts.GetBool("recursive", false) {
		args = append(args, "-recursive")
	}

	result := RunToolCommand(ctx, "subfinder", target, timeout, "subfinder", args...)

	// Parse subdomains from output (one per line)
	if result.Error == nil && result.RawOutput != "" {
		for _, line := range splitLines(result.RawOutput) {
			result.ParsedFindings = append(result.ParsedFindings, map[string]any{
				"subdomain": line,
				"source":    "subfinder",
			})
		}
	}

	return result, result.Error
}

// getScopeFromContext extracts scope definition from context.
func getScopeFromContext(ctx context.Context) *scope.ScopeDefinition {
	if v := ctx.Value(scopeContextKey); v != nil {
		if s, ok := v.(*scope.ScopeDefinition); ok {
			return s
		}
	}
	return nil
}

type contextKeyType string

const scopeContextKey contextKeyType = "scope"

// WithScope returns a context with scope attached for tool validation.
func WithScope(ctx context.Context, s *scope.ScopeDefinition) context.Context {
	return context.WithValue(ctx, scopeContextKey, s)
}

func splitLines(s string) []string {
	var lines []string
	for _, line := range strings.Split(s, "\n") {
		line = strings.TrimSpace(line)
		if line != "" {
			lines = append(lines, line)
		}
	}
	return lines
}
