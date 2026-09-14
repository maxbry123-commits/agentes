// Package compliance maps a finding's already-resolved standard labels (its
// OWASP Top 10 2021 category, with CWE as a refinement) onto the specific
// governance-framework controls it touches: PCI DSS v4.0, SOC 2 (AICPA Trust
// Services Criteria), ISO/IEC 27001:2022 Annex A, and NIST CSF 2.0.
//
// This is the GRC buying accelerator: enterprises' governance teams justify a
// tool against a control framework, and startups chasing their first SOC 2 /
// ISO cert need to show which controls their testing exercises. We already
// produce OWASP + CWE per finding (see internal/taxonomy); this package is a
// pure, dependency-free enrichment over that — no new scanning.
//
// Two layers:
//   - Map(...) — per-finding: "which controls does THIS finding touch."
//   - Mandate(...) — campaign-level: the controls that *mandate* security
//     testing, which the pentest as a whole provides evidence toward
//     (e.g. PCI Req 11.4, ISO A.8.8, SOC 2 CC7.1, NIST CSF ID.RA-01).
//
// Honesty discipline (D.11.4.8): a finding *maps to* / *provides evidence
// toward* a control. This package never asserts compliance — that is an audit
// outcome, not a scan result. Unmapped classes return nothing rather than
// inventing a control, mirroring internal/taxonomy.
//
// Plan reference: D.11.4.
package compliance

import (
	"fmt"
	"sort"
	"strings"
)

// Framework is a governance/compliance standard we can map findings onto.
type Framework string

const (
	PCIDSS   Framework = "pci"      // PCI DSS v4.0
	SOC2     Framework = "soc2"     // SOC 2 — AICPA Trust Services Criteria
	ISO27001 Framework = "iso27001" // ISO/IEC 27001:2022 Annex A
	NISTCSF  Framework = "nist-csf" // NIST Cybersecurity Framework 2.0
)

// displayName is the human label for a framework, shown in reports.
var displayName = map[Framework]string{
	PCIDSS:   "PCI DSS v4.0",
	SOC2:     "SOC 2 (Trust Services Criteria)",
	ISO27001: "ISO/IEC 27001:2022",
	NISTCSF:  "NIST CSF 2.0",
}

// DisplayName returns the human-readable framework name, or the raw slug if
// unknown.
func (f Framework) DisplayName() string {
	if n, ok := displayName[f]; ok {
		return n
	}
	return string(f)
}

// AllFrameworks is the default selection (the four shipped first). Callers can
// narrow it via ParseFrameworks so a report shows only what a customer is
// audited against.
func AllFrameworks() []Framework { return []Framework{PCIDSS, SOC2, ISO27001, NISTCSF} }

// ParseFrameworks turns a comma-separated selector ("pci,soc2") into a
// validated, de-duplicated framework list, preserving AllFrameworks order.
// Empty / "all" yields AllFrameworks. Unknown tokens are an error so a typo in
// a report flag fails loudly rather than silently dropping a framework.
func ParseFrameworks(csv string) ([]Framework, error) {
	csv = strings.TrimSpace(csv)
	if csv == "" || strings.EqualFold(csv, "all") {
		return AllFrameworks(), nil
	}
	want := map[Framework]bool{}
	for _, raw := range strings.Split(csv, ",") {
		tok := Framework(strings.ToLower(strings.TrimSpace(raw)))
		if tok == "" {
			continue
		}
		if _, ok := displayName[tok]; !ok {
			return nil, fmt.Errorf("unknown compliance framework %q (valid: pci, soc2, iso27001, nist-csf, all)", raw)
		}
		want[tok] = true
	}
	if len(want) == 0 {
		return AllFrameworks(), nil
	}
	out := make([]Framework, 0, len(want))
	for _, f := range AllFrameworks() {
		if want[f] {
			out = append(out, f)
		}
	}
	return out, nil
}

// Control is one framework control a finding maps to.
type Control struct {
	Framework Framework
	ID        string // e.g. "6.2.4", "CC7.1", "A.8.8", "ID.RA-01"
	Title     string // short control title
}

// Tag is the SARIF / JSON machine tag for a control, e.g.
// "pci-dss/6.2.4", "soc2/CC7.1", "iso27001/A.8.8", "nist-csf/ID.RA-01".
func (c Control) Tag() string {
	slug := map[Framework]string{
		PCIDSS: "pci-dss", SOC2: "soc2", ISO27001: "iso27001", NISTCSF: "nist-csf",
	}[c.Framework]
	if slug == "" {
		slug = string(c.Framework)
	}
	return slug + "/" + c.ID
}

// classControls holds, per OWASP 2021 category code (A01..A10), the controls
// each enabled framework considers that class evidence against. Mappings are
// deliberately conservative — the control a class most-directly touches — and
// leave a framework out rather than stretch a control to fit.
var classControls = map[string]map[Framework]Control{
	"A01": { // Broken Access Control
		PCIDSS:   {PCIDSS, "7.2.1", "Restrict access to system components by need-to-know"},
		SOC2:     {SOC2, "CC6.1", "Logical access security — restrict access"},
		ISO27001: {ISO27001, "A.8.3", "Information access restriction"},
		NISTCSF:  {NISTCSF, "PR.AA-05", "Access permissions enforced (least privilege)"},
	},
	"A02": { // Cryptographic Failures
		PCIDSS:   {PCIDSS, "4.2.1", "Strong cryptography for data in transit"},
		SOC2:     {SOC2, "CC6.7", "Encryption of data in transmission"},
		ISO27001: {ISO27001, "A.8.24", "Use of cryptography"},
		NISTCSF:  {NISTCSF, "PR.DS-02", "Data-in-transit is protected"},
	},
	"A03": { // Injection
		PCIDSS:   {PCIDSS, "6.2.4", "Address common software attacks in code (injection, XSS)"},
		SOC2:     {SOC2, "CC8.1", "Secure change/development to prevent software vulns"},
		ISO27001: {ISO27001, "A.8.28", "Secure coding"},
		NISTCSF:  {NISTCSF, "PR.PS-06", "Secure software development practices"},
	},
	"A05": { // Security Misconfiguration
		PCIDSS:   {PCIDSS, "2.2.1", "Secure configuration standards for system components"},
		SOC2:     {SOC2, "CC7.1", "Detect configuration vulnerabilities"},
		ISO27001: {ISO27001, "A.8.9", "Configuration management"},
		NISTCSF:  {NISTCSF, "PR.PS-01", "Configuration management baseline maintained"},
	},
	"A06": { // Vulnerable & Outdated Components
		PCIDSS:   {PCIDSS, "6.3.3", "Patch known vulnerabilities in system components"},
		SOC2:     {SOC2, "CC7.1", "Identify vulnerabilities in components"},
		ISO27001: {ISO27001, "A.8.8", "Management of technical vulnerabilities"},
		NISTCSF:  {NISTCSF, "ID.RA-01", "Vulnerabilities in assets are identified"},
	},
	"A07": { // Identification & Authentication Failures
		PCIDSS:   {PCIDSS, "8.3.1", "Strong authentication for users and administrators"},
		SOC2:     {SOC2, "CC6.1", "Logical access — identification and authentication"},
		ISO27001: {ISO27001, "A.8.5", "Secure authentication"},
		NISTCSF:  {NISTCSF, "PR.AA-01", "Identities and credentials are managed"},
	},
	"A08": { // Software & Data Integrity Failures
		PCIDSS:   {PCIDSS, "6.2.4", "Secure development to prevent integrity flaws"},
		SOC2:     {SOC2, "CC8.1", "Change management protects software integrity"},
		ISO27001: {ISO27001, "A.8.25", "Secure development lifecycle"},
		NISTCSF:  {NISTCSF, "PR.PS-06", "Secure software development practices"},
	},
	"A09": { // Security Logging & Monitoring Failures
		PCIDSS:   {PCIDSS, "10.2.1", "Audit logs capture security-relevant events"},
		SOC2:     {SOC2, "CC7.2", "Monitor system components for anomalies"},
		ISO27001: {ISO27001, "A.8.15", "Logging"},
		NISTCSF:  {NISTCSF, "DE.CM-01", "Networks and systems are monitored"},
	},
	"A10": { // Server-Side Request Forgery
		PCIDSS:   {PCIDSS, "6.2.4", "Address common software attacks in code (SSRF)"},
		SOC2:     {SOC2, "CC8.1", "Secure development to prevent software vulns"},
		ISO27001: {ISO27001, "A.8.28", "Secure coding"},
		NISTCSF:  {NISTCSF, "PR.PS-06", "Secure software development practices"},
	},
}

// cweOverride lets a specific CWE pin a more precise control than its OWASP
// class default for a given framework. Used sparingly — only where a CWE maps
// materially better than its class (e.g. TLS transmission vs. generic crypto).
var cweOverride = map[string]map[Framework]Control{
	// Path traversal — access to files by path; PCI access-control requirement.
	"CWE-22": {PCIDSS: {PCIDSS, "7.2.1", "Restrict access to system components (path traversal)"}},
	// Missing/weak security headers — PCI calls out client-side protections.
	"CWE-693": {PCIDSS: {PCIDSS, "6.4.1", "Protect public-facing web apps (security headers)"}},
}

// mandate is the campaign-level control set: the controls that *require*
// security / penetration testing, which running a campaign at all provides
// evidence toward. Reported once for the whole run, not per finding.
var mandate = map[Framework][]Control{
	PCIDSS: {
		{PCIDSS, "11.4.1", "Penetration testing methodology defined and performed"},
		{PCIDSS, "11.3.1", "Internal vulnerability scans performed"},
	},
	SOC2: {
		{SOC2, "CC4.1", "Monitor controls to evaluate operating effectiveness"},
		{SOC2, "CC7.1", "Detect and identify vulnerabilities (security monitoring)"},
	},
	ISO27001: {
		{ISO27001, "A.8.8", "Management of technical vulnerabilities"},
		{ISO27001, "A.8.29", "Security testing in development and acceptance"},
	},
	NISTCSF: {
		{NISTCSF, "ID.RA-01", "Vulnerabilities in assets are identified"},
		{NISTCSF, "ID.IM-02", "Improvements identified from security tests"},
	},
}

// owaspClass extracts the "A0N" category code from an OWASP Top 10 2021 label
// such as "A03:2021-Injection". Returns "" when the label isn't recognisable.
func owaspClass(owasp string) string {
	owasp = strings.TrimSpace(owasp)
	if len(owasp) < 3 || (owasp[0] != 'A' && owasp[0] != 'a') {
		return ""
	}
	// take "A" + the following digits, up to the ':'
	i := 1
	for i < len(owasp) && owasp[i] >= '0' && owasp[i] <= '9' {
		i++
	}
	if i < 2 {
		return ""
	}
	num := owasp[1:i]
	if len(num) == 1 {
		num = "0" + num
	}
	return "A" + num
}

// Map returns the controls a finding touches across the enabled frameworks,
// keyed off its OWASP class (with a CWE override where one is more precise).
// enabled == nil means AllFrameworks. Results are stable-ordered
// (AllFrameworks order) and de-duplicated. An unmapped class yields nil.
func Map(owasp, cwe string, enabled []Framework) []Control {
	if enabled == nil {
		enabled = AllFrameworks()
	}
	cls := owaspClass(owasp)
	byFramework := classControls[cls]
	if byFramework == nil {
		return nil
	}
	cwe = strings.ToUpper(strings.TrimSpace(cwe))
	over := cweOverride[cwe]

	var out []Control
	for _, f := range enabled {
		if over != nil {
			if c, ok := over[f]; ok {
				out = append(out, c)
				continue
			}
		}
		if c, ok := byFramework[f]; ok {
			out = append(out, c)
		}
	}
	return out
}

// Mandate returns the campaign-level "testing is required" controls for the
// enabled frameworks — the ones a completed campaign provides evidence toward.
// enabled == nil means AllFrameworks.
func Mandate(enabled []Framework) []Control {
	if enabled == nil {
		enabled = AllFrameworks()
	}
	var out []Control
	for _, f := range enabled {
		out = append(out, mandate[f]...)
	}
	return out
}

// SortControls orders controls by framework (AllFrameworks order) then ID, for
// deterministic report output.
func SortControls(cs []Control) {
	rank := map[Framework]int{}
	for i, f := range AllFrameworks() {
		rank[f] = i
	}
	sort.SliceStable(cs, func(i, j int) bool {
		if rank[cs[i].Framework] != rank[cs[j].Framework] {
			return rank[cs[i].Framework] < rank[cs[j].Framework]
		}
		return cs[i].ID < cs[j].ID
	})
}

// Disclaimer is the standing honesty notice for any compliance output. It must
// accompany every compliance section (D.11.4.8).
const Disclaimer = "These findings map to the controls listed and can serve as evidence toward them. " +
	"Mapping is not an attestation of compliance — compliance is determined by a qualified auditor/assessor, not by this tool."
