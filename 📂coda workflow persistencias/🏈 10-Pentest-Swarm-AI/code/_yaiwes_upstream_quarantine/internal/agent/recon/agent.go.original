package recon

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/llm"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/pipeline"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/scope"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/tools"
	"github.com/google/uuid"
)

// ReconAgent orchestrates security tools and analyzes output to build an AttackSurface.
type ReconAgent struct {
	provider       llm.Provider
	coordinator    *tools.Coordinator
	strict         bool
	onErr          func(error)
	nucleiSeverity []string
	activeScan     bool
}

// Option customises ReconAgent construction.
type Option func(*ReconAgent)

// WithStrict makes LLM failures fatal instead of returning a partial surface.
func WithStrict() Option {
	return func(r *ReconAgent) { r.strict = true }
}

// WithNucleiSeverity sets the nuclei severity filter for the recon scan.
// Empty leaves nuclei on its own default (critical,high,medium). Widening it
// to include low,info surfaces configuration-level findings (missing security
// headers, exposed docs, etc.) at the cost of a longer scan.
func WithNucleiSeverity(sev []string) Option {
	return func(r *ReconAgent) { r.nucleiSeverity = sev }
}

// WithActiveScan enables the active web-app attack tools (dalfox, sqlmap,
// nikto, ffuf) for URL targets. These actively probe the application for
// exploitable vulnerabilities (XSS, SQLi) rather than passively fingerprinting,
// so they take longer and are more intrusive — opt in per engagement.
func WithActiveScan(on bool) Option {
	return func(r *ReconAgent) { r.activeScan = on }
}

// WithErrorSink installs a callback for LLM / parse errors. Useful for
// emitting degraded-mode warnings to the event stream.
func WithErrorSink(fn func(error)) Option {
	return func(r *ReconAgent) { r.onErr = fn }
}

// NewReconAgent creates a new recon agent.
func NewReconAgent(provider llm.Provider, coordinator *tools.Coordinator, opts ...Option) *ReconAgent {
	r := &ReconAgent{
		provider:    provider,
		coordinator: coordinator,
	}
	for _, opt := range opts {
		opt(r)
	}
	return r
}

// ReconPlan defines which tools to run based on target type.
type ReconPlan struct {
	Target    string   `json:"target"`
	ToolOrder []string `json:"tool_order"`
}

// PlanRecon determines which tools to run based on the target type.
func (r *ReconAgent) PlanRecon(target string) ReconPlan {
	plan := ReconPlan{Target: target}

	if isIPTarget(target) {
		// IP target: port scan → probe → scan
		plan.ToolOrder = []string{"naabu", "httpx", "nuclei"}
	} else if isURLTarget(target) {
		// URL target: probe → crawl → history → passive scan.
		plan.ToolOrder = []string{"httpx", "katana", "gau", "nuclei"}
		// Active web-app arsenal: dalfox (XSS), sqlmap (SQLi), nikto (server
		// misconfig), ffuf (content discovery). These are what actually catch
		// app-level vulns (the passive tools above only fingerprint + template-
		// match). The coordinator runs the whole set concurrently and skips any
		// tool whose binary is absent, so this degrades gracefully.
		if r.activeScan {
			// dalfox (XSS), sqlmap (SQLi), nikto (server misconfig), ffuf
			// (content discovery), plus crlfuzz (CRLF/response splitting) and
			// gxss (fast reflected-input triage). The coordinator runs the
			// whole set concurrently and skips any tool whose binary is absent.
			plan.ToolOrder = append(plan.ToolOrder, "dalfox", "sqlmap", "nikto", "ffuf", "crlfuzz", "gxss")
		}
	} else {
		// Domain target: full recon pipeline
		plan.ToolOrder = []string{"subfinder", "dnsx", "naabu", "httpx", "katana", "gau", "nuclei"}
	}

	return plan
}

// Execute runs the recon plan and produces an AttackSurface.
func (r *ReconAgent) Execute(ctx context.Context, plan ReconPlan, scopeDef *scope.ScopeDefinition, campaignID uuid.UUID) (*pipeline.AttackSurface, error) {
	// Run tools. A non-empty nuclei severity filter is forwarded via Options;
	// the nuclei adapter reads opts["severity"] and otherwise keeps its own
	// default. Other tools ignore the key.
	opts := tools.Options{}
	if len(r.nucleiSeverity) > 0 {
		opts["severity"] = r.nucleiSeverity
	}
	_, resultCh := r.coordinator.RunSelected(ctx, plan.ToolOrder, plan.Target, scopeDef, opts)

	// Collect results as they stream in
	var results []*tools.ToolResult
	for result := range resultCh {
		results = append(results, result)
	}

	// Analyze results with LLM (extracts endpoints/hosts/tech into the surface).
	surface, err := r.Analyze(ctx, results, campaignID)
	if err != nil {
		return nil, fmt.Errorf("analyzing recon results: %w", err)
	}

	// Extract the actual vulnerabilities the tools reported. This is separate
	// from Analyze (which only builds the attack-surface map) — without it the
	// vuln output from nuclei/dalfox/sqlmap/nikto is discarded entirely.
	surface.Vulnerabilities = ExtractVulnerabilities(results)

	// Actively discover API endpoints a passive crawl can't reach (SPA back-end
	// routes expose no crawlable links). These are the endpoints where API
	// business-logic flaws — BOLA/IDOR, mass assignment — live, and where the
	// exploit agent's authenticated httpreq chains do their work.
	if isURLTarget(plan.Target) {
		discovered := DiscoverAPISurface(ctx, plan.Target, scopeDef)
		surface.Endpoints = mergeEndpoints(surface.Endpoints, discovered)
		// Verified attack chains for any fingerprinted app (run deterministically
		// by the exploit agent, not improvised by the LLM).
		surface.Playbooks = DiscoverPlaybooks(ctx, plan.Target, scopeDef)
	}

	return surface, nil
}

// mergeEndpoints appends discovered endpoints to existing ones, skipping
// duplicates keyed on method+URL so an actively-probed route the crawler also
// found isn't listed twice. Existing entries win (they carry the crawler's
// status code); a new entry contributes its attack-hint notes.
func mergeEndpoints(existing, discovered []pipeline.EndpointRecord) []pipeline.EndpointRecord {
	seen := make(map[string]struct{}, len(existing))
	key := func(e pipeline.EndpointRecord) string {
		m := strings.ToUpper(e.Method)
		if m == "" {
			m = "GET"
		}
		return m + " " + e.URL
	}
	for _, e := range existing {
		seen[key(e)] = struct{}{}
	}
	for _, e := range discovered {
		if _, dup := seen[key(e)]; dup {
			continue
		}
		seen[key(e)] = struct{}{}
		existing = append(existing, e)
	}
	return existing
}

// Analyze sends tool results to the LLM for structured analysis.
func (r *ReconAgent) Analyze(ctx context.Context, results []*tools.ToolResult, campaignID uuid.UUID) (*pipeline.AttackSurface, error) {
	// Build a size-bounded context from tool results. A verbose crawler
	// (katana on a large SPA) or a full nuclei run can emit output far larger
	// than any model's context window — feeding it raw makes the LLM call fail
	// with context_length_exceeded and the whole recon phase collapses. We
	// budget per-tool so no single noisy tool crowds out high-signal output
	// (e.g. nuclei findings), and cap the total to fit the provider window.
	toolContext := r.buildAnalysisContext(results)

	req := llm.CompletionRequest{
		SystemPrompt: reconSystemPrompt,
		Messages: []llm.Message{
			{
				Role: "user",
				Content: fmt.Sprintf(
					"Analyze the following security tool outputs and produce a structured AttackSurface JSON object.\n\n%s\n\nRespond ONLY with valid JSON matching the AttackSurface schema.",
					toolContext,
				),
			},
		},
		MaxTokens:         8192,
		Temperature:       0.1,
		CacheSystemPrompt: true,
	}

	resp, err := r.provider.Complete(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("LLM analysis failed: %w", err)
	}

	// Parse the response
	surface, err := ParseAttackSurface(resp.Content)
	if err != nil {
		// Retry with simplified prompt
		retryReq := llm.CompletionRequest{
			SystemPrompt: "You are a JSON parser. Extract structured data from security tool output. Respond ONLY with valid JSON.",
			Messages: []llm.Message{
				{
					Role: "user",
					Content: fmt.Sprintf(
						"Parse this into an AttackSurface JSON with fields: target, subdomains, hosts, endpoints, technologies.\n\n%s",
						toolContext,
					),
				},
			},
			MaxTokens:   8192,
			Temperature: 0,
		}

		retryResp, retryErr := r.provider.Complete(ctx, retryReq)
		if retryErr != nil {
			return nil, fmt.Errorf("retry analysis also failed: %w", retryErr)
		}

		surface, err = ParseAttackSurface(retryResp.Content)
		if err != nil {
			if r.strict {
				return nil, fmt.Errorf("recon parse failed after retry: %w", err)
			}
			if r.onErr != nil {
				r.onErr(fmt.Errorf("recon analysis returned empty surface: %w", err))
			}
			// Return deterministic partial results rather than error (degraded mode).
			surface = &pipeline.AttackSurface{}
		}
	}

	if recovered := reconcileToolResults(surface, results); recovered && err == nil && r.onErr != nil {
		r.onErr(fmt.Errorf("recon analysis omitted discoveries parsed from tool output; recovered deterministic findings"))
	}

	surface.CampaignID = campaignID
	surface.CreatedAt = time.Now()

	return surface, nil
}

// analysisContextFloor is the minimum total budget (in bytes) for the recon
// analysis prompt, used when the provider reports a small or unknown window.
const analysisContextFloor = 24_000

// analysisContextCeiling caps the total budget regardless of how large the
// provider window is. Attack-surface extraction needs the structured signal
// (hosts, endpoints, tech, nuclei findings), not megabytes of raw crawl text;
// this keeps requests well clear of tokenizer expansion blowing the window.
const analysisContextCeiling = 400_000

// buildAnalysisContext concatenates tool outputs into a single prompt context
// that is guaranteed to fit the provider's window. The total byte budget is
// derived from the provider's context window (reserving room for the system
// prompt and the model's response) and clamped to [floor, ceiling]. The budget
// is shared fairly across tools so one high-volume tool cannot starve the
// others; each tool's output is truncated to its share with an explicit marker
// so the LLM knows the data was clipped.
func (r *ReconAgent) buildAnalysisContext(results []*tools.ToolResult) string {
	budget := analysisContextCeiling
	if r.provider != nil {
		if cw := r.provider.ContextWindow(); cw > 0 {
			// Reserve ~24k tokens for the system prompt + max response, then
			// assume a conservative ~3 bytes/token for the remainder.
			if avail := (cw - 24_000) * 3; avail < budget {
				budget = avail
			}
		}
	}
	if budget < analysisContextFloor {
		budget = analysisContextFloor
	}

	perTool := budget
	if len(results) > 0 {
		perTool = budget / len(results)
	}
	if perTool < 1_000 {
		perTool = 1_000 // never truncate so hard that a tool contributes nothing
	}

	var b strings.Builder
	for _, result := range results {
		if result.Error != nil {
			fmt.Fprintf(&b, "Tool: %s (FAILED: %s)\n\n", result.ToolName, result.Error)
			continue
		}
		out := result.RawOutput
		if len(out) > perTool {
			out = out[:perTool] + fmt.Sprintf("\n… [truncated %d of %d bytes]", len(result.RawOutput)-perTool, len(result.RawOutput))
		}
		fmt.Fprintf(&b, "Tool: %s\nOutput:\n%s\n\n", result.ToolName, out)
	}
	return b.String()
}

const reconSystemPrompt = `You are a specialized security reconnaissance analyst. Your job is to analyze output from security scanning tools and produce a structured attack surface model.

Given the raw output from tools like subfinder, httpx, nuclei, naabu, katana, dnsx, and gau, you must:

1. Identify all discovered subdomains with their IP addresses and sources
2. Map all hosts with their open ports and running services
3. Catalog all discovered web endpoints with parameters
4. Detect technologies and their versions
5. Note any interesting findings or anomalies

Output your analysis as a valid JSON object matching this schema:
{
  "target": "string",
  "subdomains": [{"domain": "string", "ip": "string", "source": "string"}],
  "hosts": [{"ip": "string", "hostnames": ["string"], "open_ports": [int], "services": {}, "os": "string"}],
  "endpoints": [{"url": "string", "method": "string", "status_code": int, "interesting": bool}],
  "technologies": {"key": "version"}
}

Respond ONLY with the JSON object. No markdown, no explanation.`

func isIPTarget(target string) bool {
	parts := strings.Split(target, ".")
	if len(parts) != 4 {
		return false
	}
	for _, p := range parts {
		for _, c := range p {
			if c < '0' || c > '9' {
				return false
			}
		}
	}
	return true
}

func isURLTarget(target string) bool {
	return strings.HasPrefix(target, "http://") || strings.HasPrefix(target, "https://")
}
