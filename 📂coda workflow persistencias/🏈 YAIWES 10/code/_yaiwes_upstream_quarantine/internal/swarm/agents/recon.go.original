package agents

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
	"time"

	reconpkg "github.com/Armur-Ai/Pentest-Swarm-AI/internal/agent/recon"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/pipeline"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/scope"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/swarm/blackboard"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/swarm/tuning"
	"github.com/google/uuid"
)

// interestingEndpointType is a virtual finding-type used only for tuning
// lookup — katana-flagged "interesting" endpoints get their own pheromone
// row so they surface to downstream agents faster. On the wire they're
// still written as blackboard.TypeHTTPEndpoint.
const interestingEndpointType blackboard.FindingType = "HTTP_ENDPOINT_INTERESTING"

// ReconAgent wakes on TARGET_REGISTERED and publishes one finding per
// discovered subdomain / port / endpoint / technology. Batched tool
// execution is retained inside the underlying recon agent — the swarm
// value is that downstream agents can react to each finding independently,
// without waiting for the full surface to be assembled.
type ReconAgent struct {
	recon      *reconpkg.ReconAgent
	scopeDef   *scope.ScopeDefinition
	campaignID uuid.UUID
	parallel   int
	tun        *tuning.Settings
}

// NewReconAgent constructs a swarm wrapper around the existing recon agent.
// Pass nil for tun to get the baked-in default pheromone tuning.
func NewReconAgent(inner *reconpkg.ReconAgent, scopeDef *scope.ScopeDefinition, campaignID uuid.UUID, parallel int, tun *tuning.Settings) *ReconAgent {
	if parallel <= 0 {
		parallel = 1
	}
	if tun == nil {
		tun = tuning.Default()
	}
	return &ReconAgent{recon: inner, scopeDef: scopeDef, campaignID: campaignID, parallel: parallel, tun: tun}
}

// Name implements swarm.Agent.
func (a *ReconAgent) Name() string { return "recon" }

// Trigger implements swarm.Agent — recon wakes on newly-registered targets.
func (a *ReconAgent) Trigger() blackboard.Predicate {
	return blackboard.Predicate{Types: []blackboard.FindingType{blackboard.TypeTargetRegistered}}
}

// MaxConcurrency implements swarm.Agent.
func (a *ReconAgent) MaxConcurrency() int { return a.parallel }

// Handle runs recon against the target and fans out findings to the blackboard.
func (a *ReconAgent) Handle(ctx context.Context, f blackboard.Finding, board blackboard.Board) error {
	plan := a.recon.PlanRecon(f.Target)
	surface, err := a.recon.Execute(ctx, plan, a.scopeDef, a.campaignID)
	if err != nil {
		return fmt.Errorf("recon execute: %w", err)
	}

	// Every write pulls its pheromone from the tuning table so operators
	// can steer the swarm via config/pheromones.yaml + --exploration-bias.
	write := func(t blackboard.FindingType, onWire blackboard.FindingType, target string, payload any) {
		if onWire == "" {
			onWire = t
		}
		base, half := a.tun.Lookup(t)
		data, _ := json.Marshal(payload)
		_, _ = board.Write(ctx, blackboard.Finding{
			CampaignID:    a.campaignID,
			AgentName:     a.Name(),
			Type:          onWire,
			Target:        target,
			Data:          data,
			PheromoneBase: base,
			HalfLifeSec:   half,
		})
	}

	for _, sd := range surface.Subdomains {
		write(blackboard.TypeSubdomain, "", sd.Domain, sd)
	}
	for _, host := range surface.Hosts {
		for _, port := range host.OpenPorts {
			write(blackboard.TypePortOpen, "", fmt.Sprintf("%s:%d", host.IP, port),
				map[string]any{"ip": host.IP, "port": port, "service": host.Services[port]})
			if svc, ok := host.Services[port]; ok && svc.Name != "" {
				write(blackboard.TypeService, "", fmt.Sprintf("%s:%d/%s", host.IP, port, svc.Name), svc)
			}
		}
	}
	for _, ep := range surface.Endpoints {
		tuneKey := blackboard.TypeHTTPEndpoint
		if ep.Interesting {
			tuneKey = interestingEndpointType
		}
		write(tuneKey, blackboard.TypeHTTPEndpoint, ep.URL, ep)
	}
	for tech, version := range surface.Technologies {
		write(blackboard.TypeTechnology, "", tech,
			map[string]string{"technology": tech, "version": version})
	}

	// Verified attack playbooks (e.g. crAPI's BOLA chain). These are published
	// at a high fixed pheromone so the exploit agent picks them up promptly and
	// runs them deterministically — the reliable path to a known high-value
	// finding, independent of the LLM planner.
	for _, pb := range surface.Playbooks {
		data, _ := json.Marshal(pb)
		_, _ = board.Write(ctx, blackboard.Finding{
			CampaignID:    a.campaignID,
			AgentName:     a.Name(),
			Type:          blackboard.TypeExploitPlaybook,
			Target:        f.Target,
			Data:          data,
			PheromoneBase: 0.95,
			HalfLifeSec:   3600,
		})
	}

	// The actual vulnerabilities the tools reported. These are written as
	// report-ready classified findings with clean titles and tool-reported
	// severities — NOT raw endpoint/tech context. Pheromone tracks severity so
	// the publish threshold naturally filters info/low noise unless the
	// operator opts into --publish-unverified.
	for _, v := range surface.Vulnerabilities {
		cf := vulnToClassifiedFinding(a.campaignID, v)
		data, _ := json.Marshal(cf)
		ftype := blackboard.TypeMisconfig
		if len(cf.CVEIDs) > 0 {
			ftype = blackboard.TypeCVEMatch
		}
		pher, half := pheromoneForSeverity(cf.Severity)
		_, _ = board.Write(ctx, blackboard.Finding{
			CampaignID:    a.campaignID,
			AgentName:     a.Name(),
			Type:          ftype,
			Target:        cf.Target,
			Data:          data,
			PheromoneBase: pher,
			HalfLifeSec:   half,
		})
	}

	return nil
}

// vulnToClassifiedFinding converts a tool-reported vulnerability into a
// report-ready ClassifiedFinding with a clean title and an approximate CVSS
// score derived from the tool-reported severity. Findings flow to the report
// directly (recon → report), so their quality does not depend on the LLM
// classifier succeeding.
func vulnToClassifiedFinding(campaignID uuid.UUID, v pipeline.VulnerabilityRecord) pipeline.ClassifiedFinding {
	sev := pipeline.Severity(strings.ToLower(v.Severity))
	switch sev {
	case "informational", "": // normalize tool "info" spelling to the pipeline value
		sev = pipeline.SeverityInformational
	case "info":
		sev = pipeline.SeverityInformational
	}
	var cves []string
	if strings.HasPrefix(strings.ToUpper(v.Reference), "CVE-") {
		cves = []string{strings.ToUpper(v.Reference)}
	}
	desc := v.Description
	if desc == "" {
		desc = v.Title
	}
	if v.Reference != "" {
		desc = fmt.Sprintf("%s\n\nReported by %s (ref: %s).", desc, v.Tool, v.Reference)
	} else {
		desc = fmt.Sprintf("%s\n\nReported by %s.", desc, v.Tool)
	}
	return pipeline.ClassifiedFinding{
		ID:             uuid.New(),
		CampaignID:     campaignID,
		Title:          v.Title,
		Description:    desc,
		CVEIDs:         cves,
		CVSSScore:      cvssForSeverity(sev),
		Severity:       sev,
		AttackCategory: v.Tool,
		Confidence:     pipeline.Confidence("medium"),
		Target:         firstNonEmpty(v.URL, ""),
		ClassifiedAt:   time.Now(),
	}
}

// cvssForSeverity returns a representative CVSS base score for a severity band,
// used when a tool reports severity but no numeric score.
func cvssForSeverity(s pipeline.Severity) float64 {
	switch s {
	case pipeline.SeverityCritical:
		return 9.5
	case pipeline.SeverityHigh:
		return 8.0
	case pipeline.SeverityMedium:
		return 5.5
	case pipeline.SeverityLow:
		return 3.0
	default:
		return 0.0
	}
}

func firstNonEmpty(vals ...string) string {
	for _, v := range vals {
		if v != "" {
			return v
		}
	}
	return ""
}
