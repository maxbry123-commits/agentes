package ctf

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/config"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/engine"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/pipeline"
)

// Flag represents a captured CTF flag.
type Flag struct {
	Type   string `json:"type"` // user, root
	Value  string `json:"value"`
	Path   string `json:"path"`
	Method string `json:"method"`
}

// CTFResult holds the outcome of a CTF solve attempt.
type CTFResult struct {
	Flags           []Flag        `json:"flags"`
	AttackNarrative string        `json:"attack_narrative"`
	Writeup         string        `json:"writeup"`
	TimeElapsed     time.Duration `json:"time_elapsed"`
	Success         bool          `json:"success"`
	Events          []string      `json:"events"`
}

// Solver orchestrates autonomous CTF machine solving.
type Solver struct {
	platform string
	cfg      *config.Config
}

// NewSolver creates a new CTF solver.
func NewSolver(platform string, cfg *config.Config) *Solver {
	return &Solver{platform: platform, cfg: cfg}
}

// Solve attempts to capture all flags on a CTF machine.
func (s *Solver) Solve(ctx context.Context, target, machineName string) (*CTFResult, error) {
	start := time.Now()
	result := &CTFResult{}

	// Use the campaign engine with CTF-specific objective
	runner := engine.NewRunner(s.cfg)

	cc := engine.CampaignConfig{
		Target:    target,
		Scope:     []string{target},
		Objective: "CTF: Find all flags (user.txt and root.txt). Focus on privilege escalation chains, SUID binaries, cron jobs, writable scripts, kernel exploits, and password reuse. Check /home/*/user.txt and /root/root.txt.",
		Mode:      "ctf",
		Format:    "md",
		OutputDir: "./reports",
	}

	err := runner.Run(ctx, cc, func(event pipeline.CampaignEvent) {
		result.Events = append(result.Events, fmt.Sprintf("[%s] %s", event.AgentName, event.Detail))

		// Look for flags in events
		if strings.Contains(event.Detail, "flag") || strings.Contains(event.Detail, "user.txt") || strings.Contains(event.Detail, "root.txt") {
			if strings.Contains(event.Detail, "user") {
				result.Flags = append(result.Flags, Flag{
					Type:   "user",
					Method: event.Detail,
				})
			}
			if strings.Contains(event.Detail, "root") {
				result.Flags = append(result.Flags, Flag{
					Type:   "root",
					Method: event.Detail,
				})
			}
		}
	})

	result.TimeElapsed = time.Since(start)
	result.Success = len(result.Flags) > 0

	if err != nil {
		return result, fmt.Errorf("CTF solve failed: %w", err)
	}

	// Generate writeup
	result.Writeup = GenerateWriteup(machineName, s.platform, result)

	return result, nil
}

// GenerateWriteup creates a standard CTF writeup from the solve result.
func GenerateWriteup(machineName, platform string, result *CTFResult) string {
	var b strings.Builder

	b.WriteString(fmt.Sprintf("# %s — %s Writeup\n\n", machineName, strings.ToUpper(platform)))
	b.WriteString(fmt.Sprintf("**Time:** %s\n", result.TimeElapsed.Round(time.Second)))
	b.WriteString(fmt.Sprintf("**Result:** %s\n\n", map[bool]string{true: "Solved", false: "Incomplete"}[result.Success]))
	b.WriteString("---\n\n")

	// Build narrative from events
	b.WriteString("## Enumeration\n\n")
	for _, e := range result.Events {
		if strings.Contains(e, "recon") || strings.Contains(e, "subfinder") || strings.Contains(e, "naabu") || strings.Contains(e, "httpx") {
			b.WriteString(fmt.Sprintf("- %s\n", e))
		}
	}
	b.WriteString("\n")

	b.WriteString("## Exploitation\n\n")
	for _, e := range result.Events {
		if strings.Contains(e, "exploit") || strings.Contains(e, "attack") || strings.Contains(e, "chain") {
			b.WriteString(fmt.Sprintf("- %s\n", e))
		}
	}
	b.WriteString("\n")

	b.WriteString("## Flags\n\n")
	if len(result.Flags) == 0 {
		b.WriteString("No flags captured.\n")
	} else {
		for _, f := range result.Flags {
			b.WriteString(fmt.Sprintf("- **%s flag**: `%s`\n  - Path: %s\n  - Method: %s\n\n", f.Type, f.Value, f.Path, f.Method))
		}
	}

	return b.String()
}
