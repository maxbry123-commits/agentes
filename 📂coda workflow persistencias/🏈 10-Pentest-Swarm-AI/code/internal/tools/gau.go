package tools

import (
	"context"
	"fmt"
	"time"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/scope"
)

// GauTool wraps gau for fetching known URLs from Wayback Machine, Common Crawl, etc.
type GauTool struct{}

func NewGauTool() *GauTool { return &GauTool{} }

func (g *GauTool) Name() string { return "gau" }

func (g *GauTool) IsAvailable() bool { return IsCommandAvailable("gau") }

func (g *GauTool) Run(ctx context.Context, target string, opts Options) (*ToolResult, error) {
	scopeDef := getScopeFromContext(ctx)
	if scopeDef != nil {
		if err := scope.ValidateAndLog("gau", target, *scopeDef); err != nil {
			return nil, fmt.Errorf("scope violation in gau: %w", err)
		}
	}

	timeout := time.Duration(opts.GetInt("timeout", 60)) * time.Second

	args := []string{target, "--json"}

	result := RunToolCommand(ctx, "gau", target, timeout, "gau", args...)
	return result, result.Error
}
