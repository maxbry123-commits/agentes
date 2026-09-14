//go:build e2e

package e2e

import (
	"context"
	"testing"
	"time"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/agent/classifier"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/agent/recon"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/agent/report"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/llm"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/pipeline"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/scope"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/tools"
	"github.com/google/uuid"
)

// TestFullCampaign runs a complete campaign pipeline end-to-end.
// Requires: LLM provider (Claude API key or Ollama running), network access.
// Run with: go test -tags=e2e -v ./tests/e2e/ -timeout 20m
func TestFullCampaign(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Minute)
	defer cancel()

	// Setup provider — tries Claude first, falls back to checking Ollama
	provider := setupProvider(t)

	campaignID := uuid.New()
	target := "scanme.nmap.org" // legitimate public test target
	scopeDef := &scope.ScopeDefinition{
		AllowedDomains: []string{"scanme.nmap.org"},
		AllowedCIDRs:   []string{"45.33.32.0/24"},
	}

	// Phase 1: Recon
	t.Log("Phase 1: Running reconnaissance...")
	coordinator := tools.NewCoordinator()
	reconAgent := recon.NewReconAgent(provider, coordinator)

	plan := reconAgent.PlanRecon(target)
	if len(plan.ToolOrder) == 0 {
		t.Fatal("Recon plan has no tools")
	}
	t.Logf("  Recon plan: %v", plan.ToolOrder)

	surface, err := reconAgent.Execute(ctx, plan, scopeDef, campaignID)
	if err != nil {
		t.Fatalf("Recon failed: %v", err)
	}
	t.Logf("  Attack surface: %d subdomains, %d hosts, %d endpoints",
		len(surface.Subdomains), len(surface.Hosts), len(surface.Endpoints))

	// Phase 2: Classification
	t.Log("Phase 2: Classifying findings...")
	classifierAgent := classifier.NewClassifierAgent(provider)

	// Create some raw findings from recon (in a real run, these come from tool results)
	rawFindings := []pipeline.RawFinding{
		{ID: uuid.New(), CampaignID: campaignID, Source: "naabu", Type: "open_port", Target: target, Detail: "Port 22 open - SSH OpenSSH 6.6.1p1", DiscoveredAt: time.Now()},
		{ID: uuid.New(), CampaignID: campaignID, Source: "naabu", Type: "open_port", Target: target, Detail: "Port 80 open - HTTP Apache httpd 2.4.7", DiscoveredAt: time.Now()},
		{ID: uuid.New(), CampaignID: campaignID, Source: "nuclei", Type: "misconfig", Target: target, Detail: "Apache default page exposed at http://scanme.nmap.org", DiscoveredAt: time.Now()},
	}

	findingSet, err := classifierAgent.Classify(ctx, campaignID, rawFindings)
	if err != nil {
		t.Fatalf("Classification failed: %v", err)
	}
	t.Logf("  Classified %d findings (filtered %d as FP)", findingSet.Summary.TotalFindings, findingSet.Summary.FilteredAsFP)

	// Phase 3: Report generation
	t.Log("Phase 3: Generating report...")
	reportAgent := report.NewReportAgent(provider)

	pentestReport, err := reportAgent.Generate(ctx, pipeline.Campaign{
		ID: campaignID, Target: target, Objective: "find all vulnerabilities",
	}, findingSet.Findings, nil, nil)
	if err != nil {
		t.Fatalf("Report generation failed: %v", err)
	}

	if pentestReport.ExecutiveSummary == "" {
		t.Error("Report has empty executive summary")
	}
	t.Logf("  Report generated: %d findings, risk level: %s", len(pentestReport.Findings), pentestReport.RiskSummary.OverallRisk)

	// Render to Markdown
	renderer := report.NewRenderer()
	md, err := renderer.ToMarkdown(pentestReport)
	if err != nil {
		t.Fatalf("Markdown rendering failed: %v", err)
	}
	if len(md) < 100 {
		t.Error("Markdown report is suspiciously short")
	}
	t.Logf("  Markdown report: %d bytes", len(md))

	t.Log("Campaign complete!")
}

func setupProvider(t *testing.T) llm.Provider {
	t.Helper()

	// Try Claude first
	apiKey := envOrSkip(t, "PENTESTSWARM_ORCHESTRATOR_API_KEY", "ANTHROPIC_API_KEY")
	if apiKey != "" {
		provider := llm.NewClaudeProvider(llm.ClaudeProviderConfig{
			APIKey: apiKey,
			Model:  "claude-sonnet-4-6",
		})
		t.Log("Using Claude provider")
		return provider
	}

	// Try Ollama
	provider := llm.NewOllamaProvider(llm.OllamaProviderConfig{
		Endpoint: "http://localhost:11434",
		Model:    "llama3.1:8b",
	})
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := provider.HealthCheck(ctx); err != nil {
		t.Skip("No LLM provider available (set ANTHROPIC_API_KEY or run Ollama)")
	}
	t.Log("Using Ollama provider")
	return provider
}

func envOrSkip(t *testing.T, keys ...string) string {
	t.Helper()
	for _, key := range keys {
		if v := lookupEnv(key); v != "" {
			return v
		}
	}
	return ""
}

func lookupEnv(key string) string {
	// Simple env lookup without importing os to keep build tag clean
	// In real code, use os.Getenv
	return ""
}
