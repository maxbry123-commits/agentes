package agents

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/integrations/burp"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/pipeline"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/swarm/blackboard"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/swarm/tuning"
	"github.com/google/uuid"
)

// BurpAgent triggers on high-pheromone HTTP endpoints and asks a running
// Burp Suite MCP server to do an active scan. Issues come back as
// CVE_MATCH / MISCONFIGURATION findings.
//
// Enable by passing a non-nil *burp.Client to NewBurpAgent (typically
// built in the swarm runner from config). If Burp isn't running, skip
// wiring this agent and the rest of the swarm still works.
type BurpAgent struct {
	burp       *burp.Client
	campaignID uuid.UUID
	parallel   int
	tun        *tuning.Settings
}

// NewBurpAgent wires a Burp MCP client into the swarm.
func NewBurpAgent(client *burp.Client, campaignID uuid.UUID, parallel int, tun *tuning.Settings) *BurpAgent {
	if parallel <= 0 {
		parallel = 1
	}
	if tun == nil {
		tun = tuning.Default()
	}
	return &BurpAgent{burp: client, campaignID: campaignID, parallel: parallel, tun: tun}
}

// Name implements swarm.Agent.
func (a *BurpAgent) Name() string { return "burp" }

// Trigger: fire on HTTP endpoints that look interesting enough to spend
// Burp's time on. Pheromone gate of 0.5 tracks the same threshold the
// exploit agent uses for CVE matches.
func (a *BurpAgent) Trigger() blackboard.Predicate {
	return blackboard.Predicate{
		Types:        []blackboard.FindingType{blackboard.TypeHTTPEndpoint},
		MinPheromone: 0.5,
	}
}

// MaxConcurrency implements swarm.Agent — Burp doesn't love parallel scans.
func (a *BurpAgent) MaxConcurrency() int { return a.parallel }

// Handle scans one endpoint and fans out each Burp issue as a blackboard finding.
func (a *BurpAgent) Handle(ctx context.Context, f blackboard.Finding, board blackboard.Board) error {
	// f.Target is typically the URL for HTTP_ENDPOINT findings; we still
	// check to avoid scanning a bare hostname.
	url := f.Target
	if url == "" {
		return nil
	}

	taskID, err := a.burp.StartActiveScan(ctx, url)
	if err != nil {
		return fmt.Errorf("burp active_scan: %w", err)
	}

	issues, err := a.burp.GetIssues(ctx, taskID)
	if err != nil {
		return fmt.Errorf("burp get_issues: %w", err)
	}

	for _, iss := range issues {
		severity := mapBurpSeverity(fmt.Sprintf("%v", iss["severity"]))
		// Use the tuning system for base/half-life, then scale by Burp severity.
		base, half := a.tun.Lookup(blackboard.TypeCVEMatch)
		base *= burpSeverityScale(severity)

		data, _ := json.Marshal(iss)
		_, _ = board.Write(ctx, blackboard.Finding{
			CampaignID:    a.campaignID,
			AgentName:     a.Name(),
			Type:          blackboard.TypeCVEMatch,
			Target:        url,
			Data:          data,
			PheromoneBase: base,
			HalfLifeSec:   half,
		})
	}
	return nil
}

func mapBurpSeverity(s string) pipeline.Severity {
	switch s {
	case "High":
		return pipeline.SeverityHigh
	case "Medium":
		return pipeline.SeverityMedium
	case "Low":
		return pipeline.SeverityLow
	case "Information":
		return pipeline.SeverityInformational
	}
	return pipeline.SeverityMedium
}

func burpSeverityScale(s pipeline.Severity) float64 {
	switch s {
	case pipeline.SeverityCritical:
		return 1.0
	case pipeline.SeverityHigh:
		return 0.95
	case pipeline.SeverityMedium:
		return 0.7
	case pipeline.SeverityLow:
		return 0.4
	default:
		return 0.2
	}
}
