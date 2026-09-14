package recon

import (
	"context"
	"encoding/json"
	"io"
	"net/http"
	"sort"
	"strings"
	"time"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/pipeline"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/scope"
	yaml "go.yaml.in/yaml/v3"
)

// specLocations are the common paths a target serves its OpenAPI/Swagger
// definition from. Frameworks disagree wildly on convention (springdoc puts
// v3 at /v3/api-docs, swagger-php defaults to /openapi.json, older Swagger 2
// stacks use /v2/api-docs or /swagger.json, …) so we probe the whole set and
// stop at the first hit rather than betting on one.
var specLocations = []string{
	"/openapi.json",
	"/openapi.yaml",
	"/swagger.json",
	"/swagger.yaml",
	"/v3/api-docs",
	"/v2/api-docs",
	"/api-docs",
	"/api/openapi.json",
	"/api/swagger.json",
	"/swagger/v1/swagger.json",
	"/docs/openapi.json",
}

// DiscoverOpenAPI probes a target for a self-published OpenAPI (v3) or
// Swagger (v2) specification and, if one is found, turns every documented
// path+method into an EndpointRecord. Unlike the curated apiProfiles (which
// only know a handful of named applications), this generalizes to ANY target
// that exposes machine-readable API docs — which covers a large share of
// real-world APIs (most API gateways and frameworks serve one by default).
//
// Discovery is best-effort: scope violations, transport errors, and
// unparseable bodies all simply yield no endpoints rather than failing recon.
func DiscoverOpenAPI(ctx context.Context, base string, scopeDef *scope.ScopeDefinition) []pipeline.EndpointRecord {
	base = strings.TrimRight(base, "/")
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

	for _, loc := range specLocations {
		body, ok := fetchSpec(ctx, client, base+loc)
		if !ok {
			continue
		}
		if eps := parseOpenAPISpec(base, body); eps != nil {
			return eps
		}
	}
	return nil
}

// fetchSpec issues a short-timeout GET and returns the response body if the
// request succeeded with a 200 status. Anything else (404, transport error,
// non-200) is treated as "no spec here".
func fetchSpec(ctx context.Context, client *http.Client, url string) ([]byte, bool) {
	reqCtx, cancel := context.WithTimeout(ctx, 6*time.Second)
	defer cancel()
	req, err := http.NewRequestWithContext(reqCtx, http.MethodGet, url, nil)
	if err != nil {
		return nil, false
	}
	req.Header.Set("Accept", "application/json, application/yaml, text/yaml, */*")
	resp, err := client.Do(req)
	if err != nil {
		return nil, false
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, false
	}
	body, err := io.ReadAll(io.LimitReader(resp.Body, 8<<20)) // 8MB cap
	if err != nil || len(body) == 0 {
		return nil, false
	}
	return body, true
}

// specDoc is the subset of an OpenAPI v3 / Swagger v2 document we need. Both
// dialects share enough shape (a top-level "paths" map of path -> method ->
// operation) that one struct covers both; the dialect-specific fields
// (openapi/swagger version markers, basePath) select how the base URL for
// each path is constructed.
type specDoc struct {
	OpenAPI  string                  `json:"openapi" yaml:"openapi"`
	Swagger  string                  `json:"swagger" yaml:"swagger"`
	BasePath string                  `json:"basePath" yaml:"basePath"`
	Paths    map[string]specPathItem `json:"paths" yaml:"paths"`
}

// specPathItem maps HTTP methods to their operation for one path.
type specPathItem map[string]specOperation

type specOperation struct {
	OperationID string          `json:"operationId" yaml:"operationId"`
	Summary     string          `json:"summary" yaml:"summary"`
	Parameters  []specParameter `json:"parameters" yaml:"parameters"`
}

type specParameter struct {
	Name string `json:"name" yaml:"name"`
	In   string `json:"in" yaml:"in"`
}

// httpMethods is the set of keys under a path item that name an actual HTTP
// operation (as opposed to shared fields like "parameters" that can also
// appear at the path-item level in both dialects).
var httpMethods = map[string]bool{
	"get": true, "post": true, "put": true, "delete": true,
	"patch": true, "head": true, "options": true, "trace": true,
}

// parseOpenAPISpec parses raw spec bytes (JSON or YAML) as either OpenAPI v3
// or Swagger v2 and flattens every documented path+method into
// EndpointRecords. Returns nil if the bytes don't parse as a recognizable
// spec (e.g. an HTML error page served with a 200 status, or a body that
// isn't a spec at all).
func parseOpenAPISpec(base string, body []byte) []pipeline.EndpointRecord {
	var doc specDoc
	// Try JSON first (the common case, and stricter — it won't silently
	// misparse arbitrary text the way a permissive YAML parser can), then
	// fall back to YAML for specs published as .yaml/.yml.
	if err := json.Unmarshal(body, &doc); err != nil {
		doc = specDoc{}
		if yerr := yaml.Unmarshal(body, &doc); yerr != nil {
			return nil
		}
	}

	version, isV3 := "", strings.HasPrefix(doc.OpenAPI, "3")
	isV2 := strings.HasPrefix(doc.Swagger, "2")
	switch {
	case isV3:
		version = "OpenAPI " + doc.OpenAPI
	case isV2:
		version = "Swagger " + doc.Swagger
	default:
		// Not a recognizable spec — could be an unrelated JSON document.
		return nil
	}
	if len(doc.Paths) == 0 {
		return nil
	}

	pathBase := base
	if isV2 && doc.BasePath != "" && doc.BasePath != "/" {
		pathBase = base + strings.TrimRight(doc.BasePath, "/")
	}

	// Sort path keys so output is deterministic (map iteration order isn't).
	paths := make([]string, 0, len(doc.Paths))
	for p := range doc.Paths {
		paths = append(paths, p)
	}
	sort.Strings(paths)

	var out []pipeline.EndpointRecord
	for _, p := range paths {
		item := doc.Paths[p]
		methods := make([]string, 0, len(item))
		for m := range item {
			if httpMethods[strings.ToLower(m)] {
				methods = append(methods, m)
			}
		}
		sort.Strings(methods)
		for _, m := range methods {
			op := item[m]
			method := strings.ToUpper(m)
			url := pathBase + p

			params := make([]string, 0, len(op.Parameters))
			for _, param := range op.Parameters {
				if param.Name != "" {
					params = append(params, param.Name)
				}
			}

			note := "Discovered from the target's OpenAPI spec (" + version + ")."
			if op.OperationID != "" {
				note += " operationId: " + op.OperationID + "."
			}
			if op.Summary != "" {
				note += " " + op.Summary
			}

			out = append(out, pipeline.EndpointRecord{
				URL:         url,
				Method:      method,
				Parameters:  params,
				Interesting: interestingOperation(method, p),
				Notes:       note,
			})
		}
	}
	return out
}

// interestingOperation flags operations most likely to carry authorization
// or business-logic bugs: state-changing verbs (mass assignment, injection)
// and any path with an {id}-style parameter (BOLA/IDOR candidates).
func interestingOperation(method, path string) bool {
	switch method {
	case http.MethodPost, http.MethodPut, http.MethodDelete, http.MethodPatch:
		return true
	}
	return strings.Contains(path, "{")
}
