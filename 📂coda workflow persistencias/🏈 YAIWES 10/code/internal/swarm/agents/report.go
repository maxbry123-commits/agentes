package agents

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"

	reportpkg "github.com/Armur-Ai/Pentest-Swarm-AI/internal/agent/report"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/agent/report/bounty"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/agent/report/roi"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/pipeline"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/swarm/blackboard"
	"github.com/google/uuid"
)

// ReportAgent wakes on CAMPAIGN_COMPLETE, queries the blackboard for
// everything the swarm discovered, reconstructs the classical
// Campaign / Findings / Plan / Results shape, and hands it to the
// existing report agent for rendering.
type ReportAgent struct {
	reportAgent      *reportpkg.ReportAgent
	renderer         *reportpkg.Renderer
	campaign         pipeline.Campaign
	outputDir        string
	format           string
	publishThreshold float64 // findings below this pheromone are excluded from the report
	onRendered       func(paths map[string]string)
	// spendSnapshot returns the current LLM dollar spend, or 0 if no
	// metered provider is wired. Optional — when nil, the ROI footer
	// is omitted from the report.
	spendSnapshot func() float64
	// programStats is the per-program bounty stats used to refine the
	// ROI estimate. Optional — nil falls back to industry-average
	// public-market numbers in `internal/agent/report/bounty`.
	programStats *bounty.ProgramStats
}

// NewReportAgent wires the existing report agent into the swarm.
// publishThreshold gates which findings appear in the report:
//
//	0.5 (default) — 'bugbounty' mode: verified PoCs only.
//	                ConfirmationAgent's superseded findings (pheromone
//	                0.1) are automatically excluded.
//	0.1 ('aggressive') — include everything including suspected-but-
//	                not-reproduced findings (with a banner in the report).
func NewReportAgent(inner *reportpkg.ReportAgent, renderer *reportpkg.Renderer, campaign pipeline.Campaign, outputDir, format string, publishThreshold float64, onRendered func(map[string]string)) *ReportAgent {
	if outputDir == "" {
		outputDir = "./reports"
	}
	if format == "" {
		format = "md"
	}
	if publishThreshold <= 0 {
		publishThreshold = 0.5
	}
	return &ReportAgent{
		reportAgent:      inner,
		renderer:         renderer,
		campaign:         campaign,
		outputDir:        outputDir,
		format:           format,
		publishThreshold: publishThreshold,
		onRendered:       onRendered,
	}
}

// WithROI attaches a spend-snapshot closure and (optionally) per-program
// bounty stats so the agent can render an ROI footer at the bottom of
// the campaign report. Closure form means the snapshot stays fresh —
// we read it at render time, not at agent construction time.
func (a *ReportAgent) WithROI(spend func() float64, stats *bounty.ProgramStats) *ReportAgent {
	a.spendSnapshot = spend
	a.programStats = stats
	return a
}

// Name implements swarm.Agent.
func (a *ReportAgent) Name() string { return "report" }

// Trigger implements swarm.Agent.
func (a *ReportAgent) Trigger() blackboard.Predicate {
	return blackboard.Predicate{Types: []blackboard.FindingType{blackboard.TypeCampaignComplete}}
}

// MaxConcurrency implements swarm.Agent — exactly one report per campaign.
func (a *ReportAgent) MaxConcurrency() int { return 1 }

// Handle queries the board, generates, renders, and writes the report.
func (a *ReportAgent) Handle(ctx context.Context, f blackboard.Finding, board blackboard.Board) error {
	// The report agent fires on CAMPAIGN_COMPLETE — the very signal the
	// scheduler uses to cancel the swarm's run context. Generating on that
	// context races the cancellation: the report's LLM calls (executive
	// summary, remediation, narrative) return context.Canceled and those
	// sections silently blank out, while the deterministic parts still render.
	// Detach from the campaign cancellation and give report generation its own
	// budget so it always completes.
	ctx, cancel := context.WithTimeout(context.WithoutCancel(ctx), 5*time.Minute)
	defer cancel()

	// Reconstruct findings. publishThreshold excludes low-pheromone findings
	// (those superseded by the ConfirmationAgent, or agent-error noise).
	matches, _ := board.Query(ctx, blackboard.Predicate{
		Types:        []blackboard.FindingType{blackboard.TypeCVEMatch, blackboard.TypeMisconfig},
		MinPheromone: a.publishThreshold,
		Limit:        500,
	})
	findings := make([]pipeline.ClassifiedFinding, 0, len(matches))
	for _, m := range matches {
		var cf pipeline.ClassifiedFinding
		if err := json.Unmarshal(m.Data, &cf); err == nil {
			findings = append(findings, cf)
		}
	}
	findings = collapseDuplicateFindings(findings)

	// Reconstruct plan
	var plan *pipeline.AttackPlan
	chains, _ := board.Query(ctx, blackboard.Predicate{
		Types: []blackboard.FindingType{blackboard.TypeExploitChain},
		Limit: 100,
	})
	if len(chains) > 0 {
		plan = &pipeline.AttackPlan{
			ID:         uuid.New(),
			CampaignID: a.campaign.ID,
			CreatedAt:  a.campaign.CreatedAt,
		}
		for _, c := range chains {
			var p pipeline.AttackPath
			if err := json.Unmarshal(c.Data, &p); err == nil {
				plan.Paths = append(plan.Paths, p)
			}
		}
	}

	// Reconstruct execution results
	resultFinds, _ := board.Query(ctx, blackboard.Predicate{
		Types: []blackboard.FindingType{blackboard.TypeExploitResult},
		Limit: 500,
	})
	results := make([]pipeline.ExecutionResult, 0, len(resultFinds))
	for _, r := range resultFinds {
		var wrapped struct {
			Result pipeline.ExecutionResult `json:"result"`
		}
		if err := json.Unmarshal(r.Data, &wrapped); err == nil {
			results = append(results, wrapped.Result)
		}
	}

	rep, err := a.reportAgent.Generate(ctx, a.campaign, findings, plan, results)
	if err != nil {
		return fmt.Errorf("generate report: %w", err)
	}

	// Phase 4.5.7: ROI footer. Only renders when a metered provider was
	// wired into the swarm — otherwise we'd be dividing by an unknown
	// spend and the verdict would be meaningless.
	if a.spendSnapshot != nil {
		rep.ROIFooter = roi.Calculate(a.spendSnapshot(), findings, a.programStats).Footer()
	}

	if err := os.MkdirAll(a.outputDir, 0o755); err != nil {
		return fmt.Errorf("mkdir: %w", err)
	}
	// campaign.Name embeds the raw target (e.g. "swarm-http://localhost:3000-…").
	// Left untouched, the "://" turns filepath.Join into a nested path whose
	// parent dir does not exist, so every WriteFile below silently fails and
	// the reports dir comes up empty. Sanitize the filename component so it is
	// a single safe path segment.
	name := fmt.Sprintf("%s-%s", a.campaign.Name, a.campaign.ID.String()[:8])
	base := filepath.Join(a.outputDir, sanitizeFilename(name))
	rendered := map[string]string{}

	// writeReport renders one format and writes it, surfacing the first error
	// rather than discarding it — a failed write must not look like success.
	var writeErr error
	writeReport := func(kind, ext string, render func() ([]byte, error)) {
		b, err := render()
		if err != nil {
			if writeErr == nil {
				writeErr = fmt.Errorf("render %s: %w", kind, err)
			}
			return
		}
		p := base + ext
		if err := os.WriteFile(p, b, 0o644); err != nil {
			if writeErr == nil {
				writeErr = fmt.Errorf("write %s report %q: %w", kind, p, err)
			}
			return
		}
		rendered[kind] = p
	}

	want := func(kind string) bool {
		return a.format == "all" || a.format == kind
	}
	if a.format == "" || want("md") {
		writeReport("md", ".md", func() ([]byte, error) { return a.renderer.ToMarkdown(rep) })
	}
	if want("html") {
		writeReport("html", ".html", func() ([]byte, error) { return a.renderer.ToHTML(rep) })
	}
	if want("json") {
		writeReport("json", ".json", func() ([]byte, error) { return a.renderer.ToJSON(rep) })
	}
	if want("sarif") {
		writeReport("sarif", ".sarif", func() ([]byte, error) { return a.renderer.ToSARIF(rep) })
	}

	if a.onRendered != nil {
		a.onRendered(rendered)
	}
	return writeErr
}

// collapseDuplicateFindings merges findings that describe the same issue on
// the same target — most visibly the several nuclei templates that all flag a
// single readable /.env (generic-env, laravel-env, codeigniter-env), which
// would otherwise render as three separate HIGH findings and read as padding.
//
// Two findings collapse when they share the same target URL, severity, and
// attack category (the tool/class). The kept entry kills the highest CVSS and
// gains a one-line note listing the other detectors, so no signal is lost.
// Findings with no target are never collapsed — an empty target is not an
// identity — so distinct business-logic findings stay separate.
func collapseDuplicateFindings(in []pipeline.ClassifiedFinding) []pipeline.ClassifiedFinding {
	type key struct{ target, sev, cat string }
	idx := make(map[key]int)        // key -> position in out
	extras := make(map[key][]string) // key -> merged finding titles
	out := make([]pipeline.ClassifiedFinding, 0, len(in))

	for _, f := range in {
		if strings.TrimSpace(f.Target) == "" {
			out = append(out, f) // no identity to dedup on
			continue
		}
		k := key{
			target: normalizeFindingTarget(f.Target),
			sev:    string(f.Severity),
			cat:    strings.ToLower(f.AttackCategory),
		}
		pos, seen := idx[k]
		if !seen {
			idx[k] = len(out)
			out = append(out, f)
			continue
		}
		// Duplicate: keep the higher-CVSS representative, record the other's title.
		extras[k] = append(extras[k], f.Title)
		if f.CVSSScore > out[pos].CVSSScore {
			title := out[pos].Title
			out[pos] = f
			extras[k] = append(extras[k], title)
		}
	}

	// Fold the merged-detector note into each collapsed finding's description.
	for k, titles := range extras {
		if len(titles) == 0 {
			continue
		}
		pos := idx[k]
		uniq := dedupeStrings(titles, out[pos].Title)
		if len(uniq) > 0 {
			out[pos].Description += "\n\nAlso reported by: " + strings.Join(uniq, ", ") + "."
		}
	}
	return out
}

// idSegmentRe matches a path segment that's an object id — a UUID, a 2+ digit
// number, or a template placeholder ({id} / {{var}}) — so the same endpoint
// addressed with different ids collapses in the dedup key. This makes the
// deterministic BOLA playbook and an adaptive BOLA hit on the same endpoint
// (one targets …/vehicle/{{victim}}/location, the other …/vehicle/<uuid>/…)
// read as one finding instead of two.
var idSegmentRe = regexp.MustCompile(`(?i)(/)([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|\d{2,}|\{\{[^}]+\}\}|\{[^}]+\})(/|$)`)

// normalizeFindingTarget lowercases/trims a finding target and collapses its
// object-id path segments to ":id" for dedup keying.
func normalizeFindingTarget(target string) string {
	t := strings.ToLower(strings.TrimSpace(target))
	// Apply twice to catch adjacent id segments separated by a shared slash.
	for i := 0; i < 2; i++ {
		t = idSegmentRe.ReplaceAllString(t, "$1:id$3")
	}
	return t
}

// dedupeStrings returns the unique entries of in, excluding `exclude` and
// preserving first-seen order.
func dedupeStrings(in []string, exclude string) []string {
	seen := map[string]struct{}{strings.ToLower(exclude): {}}
	var out []string
	for _, s := range in {
		l := strings.ToLower(s)
		if _, dup := seen[l]; dup {
			continue
		}
		seen[l] = struct{}{}
		out = append(out, s)
	}
	return out
}

// unsafeFilenameChars matches every character that is not safe in a single
// path segment across the platforms we support (path separators, the Windows
// reserved set, and control chars). Runs of them collapse to one dash.
var unsafeFilenameChars = regexp.MustCompile(`[^A-Za-z0-9._-]+`)

// sanitizeFilename turns an arbitrary label (which may contain a URL scheme,
// slashes, or colons) into a single safe filename segment.
func sanitizeFilename(s string) string {
	out := unsafeFilenameChars.ReplaceAllString(s, "-")
	out = strings.Trim(out, "-.")
	if out == "" {
		return "report"
	}
	return out
}
