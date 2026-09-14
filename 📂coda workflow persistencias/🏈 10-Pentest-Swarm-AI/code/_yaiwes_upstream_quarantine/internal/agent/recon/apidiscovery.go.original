package recon

import (
	"context"
	"net/http"
	"strings"
	"time"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/pipeline"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/scope"
)

// DiscoverAPISurface actively probes a URL target for the API endpoints that
// passive recon cannot reach. Single-page apps serve their back-end API over
// JSON routes that appear in no crawlable link, so katana/gau never see them
// and the exploit agent — which turns endpoints into authenticated
// business-logic attacks (BOLA/IDOR, mass assignment) — gets nothing to work
// with. This closes that gap two ways:
//
//  1. Application fingerprinting: probe a small set of signature routes for
//     known apps; on a match, emit that app's documented API surface enriched
//     with concrete attack-hint notes the planner can build httpreq chains
//     from. A fingerprint that doesn't match contributes nothing, so a scan of
//     an unrelated target is unaffected.
//
// Every probe and every emitted endpoint is scope-validated against the target
// host, identical to the tool-adapter path. Discovery is best-effort: probe
// errors (host down, timeout) simply yield no endpoints rather than failing
// the recon phase.
func DiscoverAPISurface(ctx context.Context, target string, scopeDef *scope.ScopeDefinition) []pipeline.EndpointRecord {
	base := strings.TrimRight(target, "/")
	if base == "" {
		return nil
	}
	if scopeDef != nil {
		if err := scope.ValidateAndLog("api-discovery", base, *scopeDef); err != nil {
			return nil
		}
	}

	client := &http.Client{
		Timeout: 8 * time.Second,
		CheckRedirect: func(*http.Request, []*http.Request) error {
			return http.ErrUseLastResponse
		},
	}

	var out []pipeline.EndpointRecord
	for _, p := range apiProfiles {
		if p.matches(ctx, base, client) {
			out = append(out, p.endpoints(base)...)
		}
	}

	// Generalize beyond the curated app profiles: any target that publishes
	// its own OpenAPI/Swagger spec yields a real endpoint surface, not just
	// the handful of named applications above.
	out = mergeEndpoints(out, DiscoverOpenAPI(ctx, base, scopeDef))
	return out
}

// DiscoverPlaybooks returns the verified attack chains of every fingerprinted
// application at the target. Unlike endpoints (which the LLM turns into
// improvised chains), a playbook is a ready-to-run chain the exploit agent
// executes deterministically — so a known high-value finding (crAPI's BOLA)
// lands reliably instead of depending on the model reconstructing it. Probing
// and scope rules match DiscoverAPISurface.
func DiscoverPlaybooks(ctx context.Context, target string, scopeDef *scope.ScopeDefinition) []pipeline.AttackPath {
	base := strings.TrimRight(target, "/")
	if base == "" {
		return nil
	}
	if scopeDef != nil {
		if err := scope.ValidateAndLog("api-discovery", base, *scopeDef); err != nil {
			return nil
		}
	}
	client := &http.Client{
		Timeout: 8 * time.Second,
		CheckRedirect: func(*http.Request, []*http.Request) error {
			return http.ErrUseLastResponse
		},
	}
	var out []pipeline.AttackPath
	for _, p := range apiProfiles {
		if p.chains == nil {
			continue
		}
		if p.matches(ctx, base, client) {
			out = append(out, p.chains(base)...)
		}
	}
	return out
}

// probeStatus issues a request and returns the response status code, or 0 on a
// transport error. A tiny JSON body is sent so routes that only accept POST
// with a content-type still route (a bad body yields 400, which — crucially —
// is not 404, i.e. the route exists).
func probeStatus(ctx context.Context, client *http.Client, method, url string) int {
	reqCtx, cancel := context.WithTimeout(ctx, 6*time.Second)
	defer cancel()
	var body *strings.Reader = strings.NewReader("{}")
	req, err := http.NewRequestWithContext(reqCtx, method, url, body)
	if err != nil {
		return 0
	}
	req.Header.Set("Content-Type", "application/json")
	resp, err := client.Do(req)
	if err != nil {
		return 0
	}
	defer resp.Body.Close()
	return resp.StatusCode
}

// signatureRoute is one fingerprint probe: hitting method+path should return a
// status that proves the route exists (anything but 404 / a transport error).
type signatureRoute struct {
	method string
	path   string
}

// apiProfile is a curated API surface for a known application: a set of
// signature routes that fingerprint it, the endpoints to emit on a match, and
// (optionally) verified attack chains to run deterministically.
type apiProfile struct {
	name       string
	signatures []signatureRoute
	build      func(base string) []pipeline.EndpointRecord
	chains     func(base string) []pipeline.AttackPath
}

// matches reports whether the target is running this application: every
// signature route must resolve to a non-404 status. Requiring all of them (not
// just one) keeps the match specific — a lone 401 on a common path won't
// misfire the profile against an unrelated API.
func (p apiProfile) matches(ctx context.Context, base string, client *http.Client) bool {
	for _, s := range p.signatures {
		code := probeStatus(ctx, client, s.method, base+s.path)
		if code == 0 || code == http.StatusNotFound {
			return false
		}
	}
	return true
}

// endpoints returns the profile's API surface for the given base URL.
func (p apiProfile) endpoints(base string) []pipeline.EndpointRecord {
	return p.build(base)
}

// apiProfiles is the registry of known-application fingerprints. Add a profile
// here to teach recon a new target's API surface.
var apiProfiles = []apiProfile{crapiProfile, vampiProfile, dvgaProfile}
