package agents

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	classifierpkg "github.com/Armur-Ai/Pentest-Swarm-AI/internal/agent/classifier"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/pipeline"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/swarm/blackboard"
	"github.com/google/uuid"
)

// ClassifierAgent triggers on raw recon findings and publishes CVE_MATCH /
// MISCONFIGURATION findings back to the blackboard. One-at-a-time processing
// is simple and lets high-pheromone findings get an LLM call immediately;
// the existing fpFilter still drops obvious noise before hitting the model.
type ClassifierAgent struct {
	classifier *classifierpkg.ClassifierAgent
	campaignID uuid.UUID
	parallel   int
}

// NewClassifierAgent wraps the existing classifier for the swarm.
func NewClassifierAgent(inner *classifierpkg.ClassifierAgent, campaignID uuid.UUID, parallel int) *ClassifierAgent {
	if parallel <= 0 {
		parallel = 3
	}
	return &ClassifierAgent{classifier: inner, campaignID: campaignID, parallel: parallel}
}

// Name implements swarm.Agent.
func (a *ClassifierAgent) Name() string { return "classifier" }

// Trigger implements swarm.Agent.
func (a *ClassifierAgent) Trigger() blackboard.Predicate {
	return blackboard.Predicate{
		Types: []blackboard.FindingType{
			blackboard.TypeSubdomain,
			blackboard.TypePortOpen,
			blackboard.TypeService,
			// NOTE: HTTP_ENDPOINT and TECHNOLOGY are deliberately NOT classified.
			// They are attack-surface context, not vulnerabilities — classifying
			// every crawled URL (styles.css, main.js) or tech fingerprint turned
			// the report into raw-JSON noise. Real vulnerabilities now come from
			// the recon agent's tool-vuln extraction (nuclei/dalfox/sqlmap/nikto),
			// written directly as report-ready findings.
		},
		// Don't spend LLM on findings whose recency has already decayed.
		MinPheromone: 0.2,
	}
}

// MaxConcurrency implements swarm.Agent.
func (a *ClassifierAgent) MaxConcurrency() int { return a.parallel }

// Handle classifies a single finding and publishes any CVE matches.
func (a *ClassifierAgent) Handle(ctx context.Context, f blackboard.Finding, board blackboard.Board) error {
	raw := pipeline.RawFinding{
		ID:           uuid.New(),
		CampaignID:   a.campaignID,
		Source:       f.AgentName,
		Type:         string(f.Type),
		Target:       f.Target,
		Detail:       string(f.Data),
		DiscoveredAt: f.CreatedAt,
	}

	set, err := a.classifier.Classify(ctx, a.campaignID, []pipeline.RawFinding{raw})
	if err != nil {
		return fmt.Errorf("classify: %w", err)
	}

	for _, c := range set.Findings {
		// Pheromone follows severity: critical findings stay hot longer.
		pheromone, halfLife := pheromoneForSeverity(c.Severity)
		data, _ := json.Marshal(c)
		t := blackboard.TypeCVEMatch
		if len(c.CVEIDs) == 0 {
			t = blackboard.TypeMisconfig
		}
		_, _ = board.Write(ctx, blackboard.Finding{
			CampaignID:    a.campaignID,
			AgentName:     a.Name(),
			Type:          t,
			Target:        c.Target,
			Data:          data,
			PheromoneBase: pheromone,
			HalfLifeSec:   halfLife,
		})
	}
	return nil
}

// pheromoneForSeverity returns an initial pheromone and half-life appropriate
// to the finding's severity — critical findings stay attractive to the exploit
// agent for hours; low findings decay inside an hour.
func pheromoneForSeverity(s pipeline.Severity) (float64, int) {
	switch s {
	case pipeline.SeverityCritical:
		return 1.0, int((6 * time.Hour).Seconds())
	case pipeline.SeverityHigh:
		return 0.9, int((3 * time.Hour).Seconds())
	case pipeline.SeverityMedium:
		return 0.6, int((1 * time.Hour).Seconds())
	case pipeline.SeverityLow:
		return 0.4, int((30 * time.Minute).Seconds())
	default:
		return 0.2, int((10 * time.Minute).Seconds())
	}
}
