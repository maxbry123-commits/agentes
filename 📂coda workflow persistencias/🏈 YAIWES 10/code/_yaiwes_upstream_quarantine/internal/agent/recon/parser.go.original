package recon

import (
	"encoding/json"
	"fmt"
	"sort"
	"strings"
	"time"

	"github.com/google/uuid"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/pipeline"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/tools"
)

// fallbackSource is the value we stamp on records that came in via a
// tolerated fallback shape (flat string, single object) rather than the
// strict object-array shape. Downstream code and logs can grep for this
// marker to see when a local model is drifting from the spec.
const fallbackSource = "llm-flat"

// rawSurface mirrors AttackSurface but keeps the polymorphic fields as
// raw bytes so we can attempt multiple unmarshal shapes per field. Local
// quantized models (qwen2.5-coder, deepseek-v4-pro, …) routinely emit
// subdomains as flat string arrays and technologies as arrays instead
// of maps; this lets us recover the data instead of failing the whole
// campaign on a shape mismatch. See #16, #19, and the original #7.
type rawSurface struct {
	CampaignID   uuid.UUID       `json:"campaign_id"`
	Target       string          `json:"target"`
	Subdomains   json.RawMessage `json:"subdomains"`
	Hosts        json.RawMessage `json:"hosts"`
	Endpoints    json.RawMessage `json:"endpoints"`
	Technologies json.RawMessage `json:"technologies"`
	CreatedAt    time.Time       `json:"created_at"`
}

// ParseAttackSurface parses an LLM response into a structured AttackSurface.
// The four polymorphic fields (subdomains, hosts, endpoints, technologies)
// tolerate the common shape-drifts we see from local Ollama models.
func ParseAttackSurface(rawJSON string) (*pipeline.AttackSurface, error) {
	rawJSON = stripCodeFence(rawJSON)
	rawJSON = strings.TrimSpace(rawJSON)

	if rawJSON == "" {
		return nil, fmt.Errorf("empty response from LLM")
	}

	var raw rawSurface
	if err := json.Unmarshal([]byte(rawJSON), &raw); err != nil {
		return nil, fmt.Errorf("parsing attack surface JSON: %w (raw: %.200s)", err, rawJSON)
	}

	return &pipeline.AttackSurface{
		CampaignID:   raw.CampaignID,
		Target:       raw.Target,
		Subdomains:   parseSubdomains(raw.Subdomains),
		Hosts:        parseHosts(raw.Hosts),
		Endpoints:    parseEndpoints(raw.Endpoints),
		Technologies: parseTechnologies(raw.Technologies),
		CreatedAt:    raw.CreatedAt,
	}, nil
}

// parseSubdomains tolerates three shapes: the strict object-array, a flat
// string array (model emitted just the names), or a single object. Returns
// nil for missing / unparseable fields rather than erroring — the campaign
// continues with whatever shape we recovered.
func parseSubdomains(raw json.RawMessage) []pipeline.SubdomainRecord {
	if isEmpty(raw) {
		return nil
	}
	var strict []pipeline.SubdomainRecord
	if err := json.Unmarshal(raw, &strict); err == nil {
		return strict
	}
	var flat []string
	if err := json.Unmarshal(raw, &flat); err == nil {
		out := make([]pipeline.SubdomainRecord, 0, len(flat))
		for _, s := range flat {
			if s == "" {
				continue
			}
			out = append(out, pipeline.SubdomainRecord{Domain: s, Source: fallbackSource})
		}
		return out
	}
	var single pipeline.SubdomainRecord
	if err := json.Unmarshal(raw, &single); err == nil && single.Domain != "" {
		return []pipeline.SubdomainRecord{single}
	}
	return nil
}

// parseHosts handles three shapes: the strict object-array, a flat string
// array (treated as IPs), or a single object. Same fallback discipline.
func parseHosts(raw json.RawMessage) []pipeline.HostRecord {
	if isEmpty(raw) {
		return nil
	}
	var strict []pipeline.HostRecord
	if err := json.Unmarshal(raw, &strict); err == nil {
		return strict
	}
	var flat []string
	if err := json.Unmarshal(raw, &flat); err == nil {
		out := make([]pipeline.HostRecord, 0, len(flat))
		for _, ip := range flat {
			if ip == "" {
				continue
			}
			out = append(out, pipeline.HostRecord{IP: ip})
		}
		return out
	}
	var single pipeline.HostRecord
	if err := json.Unmarshal(raw, &single); err == nil && single.IP != "" {
		return []pipeline.HostRecord{single}
	}
	return nil
}

// parseEndpoints handles three shapes: the strict object-array, a flat
// string array (treated as URLs), or a single object.
func parseEndpoints(raw json.RawMessage) []pipeline.EndpointRecord {
	if isEmpty(raw) {
		return nil
	}
	var strict []pipeline.EndpointRecord
	if err := json.Unmarshal(raw, &strict); err == nil {
		return strict
	}
	var flat []string
	if err := json.Unmarshal(raw, &flat); err == nil {
		out := make([]pipeline.EndpointRecord, 0, len(flat))
		for _, u := range flat {
			if u == "" {
				continue
			}
			out = append(out, pipeline.EndpointRecord{URL: u})
		}
		return out
	}
	var single pipeline.EndpointRecord
	if err := json.Unmarshal(raw, &single); err == nil && single.URL != "" {
		return []pipeline.EndpointRecord{single}
	}
	return nil
}

// parseTechnologies handles two shapes: the strict map[name]version, or a
// flat array of names (version stamped as empty). Closes the same family
// as #7 — local models often emit tech stacks as a list, not a map.
func parseTechnologies(raw json.RawMessage) map[string]string {
	if isEmpty(raw) {
		return nil
	}
	var m map[string]string
	if err := json.Unmarshal(raw, &m); err == nil {
		return m
	}
	var flat []string
	if err := json.Unmarshal(raw, &flat); err == nil {
		out := make(map[string]string, len(flat))
		for _, t := range flat {
			if t != "" {
				out[t] = ""
			}
		}
		return out
	}
	return nil
}

// isEmpty returns true for missing fields and explicit JSON null. Avoids
// per-field nil-vs-null branching in every parser.
func isEmpty(raw json.RawMessage) bool {
	s := strings.TrimSpace(string(raw))
	return s == "" || s == "null"
}

// MergeToolResults deduplicates and enriches findings from multiple tools.
func MergeToolResults(results []*tools.ToolResult) MergedData {
	merged := MergedData{
		Subdomains: make(map[string]bool),
		Hosts:      make(map[string]bool),
		Endpoints:  make(map[string]bool),
	}

	for _, r := range results {
		if r == nil || r.Error != nil {
			continue
		}

		for _, finding := range r.ParsedFindings {
			addStringFinding(merged.Subdomains, finding["subdomain"])
			addStringFinding(merged.Hosts, finding["host"])
			addStringFinding(merged.Endpoints, finding["url"])

			request, ok := finding["request"].(map[string]any)
			if ok {
				addStringFinding(merged.Endpoints, request["endpoint"])
			}
		}
	}

	return merged
}

// MergedData holds deduplicated data from multiple tool results.
type MergedData struct {
	Subdomains map[string]bool
	Hosts      map[string]bool
	Endpoints  map[string]bool
}

func addStringFinding(destination map[string]bool, value any) {
	text, ok := value.(string)
	if !ok {
		return
	}
	text = strings.TrimSpace(text)
	if text != "" {
		destination[text] = true
	}
}

// UniqueSubdomains returns the deduplicated subdomain list.
func (m MergedData) UniqueSubdomains() []string {
	return sortedKeys(m.Subdomains)
}

// UniqueHosts returns the deduplicated host list.
func (m MergedData) UniqueHosts() []string {
	return sortedKeys(m.Hosts)
}

// UniqueEndpoints returns the deduplicated endpoint list.
func (m MergedData) UniqueEndpoints() []string {
	return sortedKeys(m.Endpoints)
}

func sortedKeys(values map[string]bool) []string {
	result := make([]string, 0, len(values))
	for value := range values {
		result = append(result, value)
	}
	sort.Strings(result)
	return result
}

// reconcileToolResults supplements an LLM-produced surface with findings
// deterministically parsed from successful recon tool output. Existing LLM
// records win so their richer metadata is preserved.
func reconcileToolResults(surface *pipeline.AttackSurface, results []*tools.ToolResult) bool {
	merged := MergeToolResults(results)
	recovered := false

	subdomains := make(map[string]bool, len(surface.Subdomains))
	for _, record := range surface.Subdomains {
		if domain := strings.TrimSpace(record.Domain); domain != "" {
			subdomains[domain] = true
		}
	}
	for _, domain := range merged.UniqueSubdomains() {
		if subdomains[domain] {
			continue
		}
		surface.Subdomains = append(surface.Subdomains, pipeline.SubdomainRecord{
			Domain: domain,
			Source: "tool",
		})
		subdomains[domain] = true
		recovered = true
	}

	hosts := make(map[string]bool, len(surface.Hosts))
	for _, record := range surface.Hosts {
		if host := strings.TrimSpace(record.IP); host != "" {
			hosts[host] = true
		}
	}
	for _, host := range merged.UniqueHosts() {
		if hosts[host] {
			continue
		}
		surface.Hosts = append(surface.Hosts, pipeline.HostRecord{IP: host})
		hosts[host] = true
		recovered = true
	}

	endpoints := make(map[string]bool, len(surface.Endpoints))
	for _, record := range surface.Endpoints {
		if endpoint := strings.TrimSpace(record.URL); endpoint != "" {
			endpoints[endpoint] = true
		}
	}
	for _, endpoint := range merged.UniqueEndpoints() {
		if endpoints[endpoint] {
			continue
		}
		surface.Endpoints = append(surface.Endpoints, pipeline.EndpointRecord{URL: endpoint})
		endpoints[endpoint] = true
		recovered = true
	}

	return recovered
}

// stripCodeFence removes markdown ```json ... ``` wrappers.
func stripCodeFence(s string) string {
	s = strings.TrimSpace(s)

	// Remove ```json prefix
	if strings.HasPrefix(s, "```json") {
		s = s[7:]
	} else if strings.HasPrefix(s, "```") {
		s = s[3:]
	}

	// Remove ``` suffix
	if strings.HasSuffix(s, "```") {
		s = s[:len(s)-3]
	}

	return strings.TrimSpace(s)
}

// --- Vulnerability extraction ---
//
// ExtractVulnerabilities pulls the actual security issues out of each tool's
// parsed output and returns them with clean, human-readable titles. This is
// deliberately separate from the LLM attack-surface analysis: Analyze maps the
// terrain (endpoints/hosts/tech), while this captures the vulnerabilities the
// tools reported. Without it, tool vuln output is discarded and only
// attack-surface context reaches the blackboard.
func ExtractVulnerabilities(results []*tools.ToolResult) []pipeline.VulnerabilityRecord {
	var vulns []pipeline.VulnerabilityRecord
	for _, r := range results {
		if r == nil {
			continue
		}
		switch r.ToolName {
		case "nuclei":
			vulns = append(vulns, extractNucleiVulns(r)...)
		case "dalfox":
			vulns = append(vulns, extractDalfoxVulns(r)...)
		case "nikto":
			vulns = append(vulns, extractNiktoVulns(r)...)
		case "sqlmap":
			vulns = append(vulns, extractSqlmapVulns(r)...)
		case "crlfuzz":
			vulns = append(vulns, extractCRLFuzzVulns(r)...)
		case "gxss":
			vulns = append(vulns, extractGXSSVulns(r)...)
		}
	}
	return vulns
}

func mapStr(m map[string]any, key string) string {
	if v, ok := m[key]; ok {
		if s, ok := v.(string); ok {
			return s
		}
	}
	return ""
}

// extractNucleiVulns reads nuclei JSONL findings: {template-id, info:{name,
// severity}, matched-at, host, ...}.
func extractNucleiVulns(r *tools.ToolResult) []pipeline.VulnerabilityRecord {
	var out []pipeline.VulnerabilityRecord
	for _, f := range r.ParsedFindings {
		name, severity, ref := "", "", mapStr(f, "template-id")
		if info, ok := f["info"].(map[string]any); ok {
			name = mapStr(info, "name")
			severity = mapStr(info, "severity")
		}
		url := mapStr(f, "matched-at")
		if url == "" {
			url = mapStr(f, "host")
		}
		if name == "" {
			name = ref
		}
		if name == "" {
			continue
		}
		out = append(out, pipeline.VulnerabilityRecord{
			Tool: "nuclei", Title: name, Severity: normalizeSeverity(severity),
			URL: url, Reference: ref, Description: mapStr(f, "matched-at"),
		})
	}
	return out
}

// extractDalfoxVulns reads dalfox findings: {type:R|V, param, evidence,
// severity:H|M|L, data(url)}. type V = verified (higher confidence).
func extractDalfoxVulns(r *tools.ToolResult) []pipeline.VulnerabilityRecord {
	var out []pipeline.VulnerabilityRecord
	for _, f := range r.ParsedFindings {
		kind := "Reflected"
		if mapStr(f, "type") == "V" {
			kind = "Verified"
		}
		param := mapStr(f, "param")
		title := "Cross-Site Scripting (XSS)"
		if param != "" {
			title = fmt.Sprintf("Cross-Site Scripting (XSS) in parameter %q", param)
		}
		out = append(out, pipeline.VulnerabilityRecord{
			Tool: "dalfox", Title: title, Severity: normalizeSeverity(mapStr(f, "severity")),
			URL: mapStr(f, "data"), Description: fmt.Sprintf("%s XSS; evidence: %s", kind, mapStr(f, "evidence")),
		})
	}
	return out
}

// extractNiktoVulns reads nikto findings: {id, method, url, title(msg), host}.
func extractNiktoVulns(r *tools.ToolResult) []pipeline.VulnerabilityRecord {
	var out []pipeline.VulnerabilityRecord
	for _, f := range r.ParsedFindings {
		title := mapStr(f, "title")
		if title == "" {
			title = mapStr(f, "msg")
		}
		if title == "" {
			continue
		}
		sev := normalizeSeverity(mapStr(f, "severity"))
		if sev == "" {
			sev = "low"
		}
		out = append(out, pipeline.VulnerabilityRecord{
			Tool: "nikto", Title: title, Severity: sev,
			URL: mapStr(f, "url"), Reference: mapStr(f, "id"),
		})
	}
	return out
}

// extractSqlmapVulns flags SQL injection when the sqlmap API reports any data.
// sqlmap's per-scan data is verbose and structured differently across versions,
// so we keep this conservative: presence of parsed data means an injection
// point was found.
func extractSqlmapVulns(r *tools.ToolResult) []pipeline.VulnerabilityRecord {
	if len(r.ParsedFindings) == 0 {
		return nil
	}
	return []pipeline.VulnerabilityRecord{{
		Tool: "sqlmap", Title: "SQL Injection", Severity: "critical",
		URL: r.Target, Description: "sqlmap identified an injectable parameter on the target.",
	}}
}

// extractCRLFuzzVulns reads crlfuzz findings: {url, severity:high,
// category:crlf_injection}. crlfuzz only emits a line when it confirms the
// server reflects an injected CR/LF, so each finding is a real, directly-
// exploitable CRLF injection (response splitting → XSS / cache poisoning).
func extractCRLFuzzVulns(r *tools.ToolResult) []pipeline.VulnerabilityRecord {
	var out []pipeline.VulnerabilityRecord
	for _, f := range r.ParsedFindings {
		url := mapStr(f, "url")
		if url == "" {
			continue
		}
		sev := normalizeSeverity(mapStr(f, "severity"))
		if sev == "" {
			sev = "high"
		}
		out = append(out, pipeline.VulnerabilityRecord{
			Tool: "crlfuzz", Title: "CRLF Injection (HTTP response splitting)", Severity: sev,
			URL:         url,
			Description: "crlfuzz confirmed the server reflects an injected CR/LF sequence, allowing HTTP response splitting — a vector for reflected XSS, cache poisoning, and open redirect.",
		})
	}
	return out
}

// extractGXSSVulns reads gxss findings: {url, severity, category:reflected_input}.
// gxss only confirms that a parameter is reflected unfiltered — not that it is
// exploitable — so these are recorded at LOW severity as a reflected-input lead
// (dalfox is what promotes a confirmed reflection to an exploitable XSS). This
// keeps the report honest: a reflection is a lead, not a proven vulnerability.
func extractGXSSVulns(r *tools.ToolResult) []pipeline.VulnerabilityRecord {
	var out []pipeline.VulnerabilityRecord
	for _, f := range r.ParsedFindings {
		url := mapStr(f, "url")
		if url == "" {
			continue
		}
		out = append(out, pipeline.VulnerabilityRecord{
			Tool: "gxss", Title: "Reflected input (potential XSS)", Severity: "low",
			URL:         url,
			Description: "gxss confirmed a parameter is reflected unfiltered into the response. This is a lead for reflected XSS, not a confirmed exploit — validate with a payload-fuzzing pass (dalfox) before treating it as exploitable.",
		})
	}
	return out
}

// normalizeSeverity maps tool-specific severity spellings to the pipeline set.
func normalizeSeverity(s string) string {
	switch strings.ToLower(strings.TrimSpace(s)) {
	case "critical", "crit":
		return "critical"
	case "high", "h":
		return "high"
	case "medium", "med", "m":
		return "medium"
	case "low", "l":
		return "low"
	case "info", "informational", "information", "unknown", "":
		return "info"
	default:
		return strings.ToLower(s)
	}
}
