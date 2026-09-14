package classifier

import (
	"strings"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/pipeline"
)

// FPFilter scores the false positive probability of a finding.
type FPFilter struct{}

// NewFPFilter creates a new false positive filter.
func NewFPFilter() *FPFilter {
	return &FPFilter{}
}

// Score returns a false positive probability from 0.0 (definitely real) to 1.0 (definitely FP).
func (f *FPFilter) Score(finding pipeline.RawFinding) float64 {
	probability := 0.0

	detail := strings.ToLower(finding.Detail)
	rawOutput := strings.ToLower(finding.RawOutput)

	// Rule 1: Generic server banner without version number
	if containsGenericBanner(detail) {
		probability += 0.6
	}

	// Rule 2: Port open finding without service identification
	if finding.Type == "open_port" && !hasServiceInfo(detail) {
		probability += 0.4
	}

	// Rule 3: Endpoint found but returns 4xx on all probes
	if strings.Contains(detail, "404") || strings.Contains(detail, "403") || strings.Contains(detail, "401") {
		if !strings.Contains(detail, "200") && !strings.Contains(detail, "302") {
			probability += 0.5
		}
	}

	// Rule 4: CVE mapped but version range doesn't match
	if strings.Contains(rawOutput, "version mismatch") || strings.Contains(rawOutput, "not vulnerable") {
		probability += 0.7
	}

	// Rule 5: Finding on non-standard port with no service match
	if strings.Contains(detail, "non-standard port") && !hasServiceInfo(detail) {
		probability += 0.3
	}

	// Rule 6: Info-level findings from automated scanners tend to be noise
	if strings.Contains(finding.Type, "info") || strings.Contains(detail, "informational") {
		probability += 0.2
	}

	// Cap at 1.0
	if probability > 1.0 {
		probability = 1.0
	}

	return probability
}

// ShouldFilter returns true if the finding is likely a false positive.
func (f *FPFilter) ShouldFilter(finding pipeline.RawFinding) bool {
	return f.Score(finding) > 0.75
}

func containsGenericBanner(s string) bool {
	genericBanners := []string{
		"apache", "nginx", "iis", "lighttpd",
	}
	for _, banner := range genericBanners {
		if strings.Contains(s, banner) && !containsVersion(s) {
			return true
		}
	}
	return false
}

func containsVersion(s string) bool {
	// Check for version-like patterns (digits with dots)
	for i := 0; i < len(s)-2; i++ {
		if s[i] >= '0' && s[i] <= '9' && s[i+1] == '.' && s[i+2] >= '0' && s[i+2] <= '9' {
			return true
		}
	}
	return false
}

func hasServiceInfo(s string) bool {
	services := []string{
		"http", "https", "ssh", "ftp", "smtp", "mysql", "postgres",
		"redis", "mongodb", "dns", "telnet", "rdp",
	}
	for _, svc := range services {
		if strings.Contains(s, svc) {
			return true
		}
	}
	return false
}
