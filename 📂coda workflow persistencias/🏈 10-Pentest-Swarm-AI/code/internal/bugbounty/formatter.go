package bugbounty

import (
	"fmt"
	"strings"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/pipeline"
)

// HackerOneReport is formatted for HackerOne submission.
type HackerOneReport struct {
	Title                    string `json:"title"`
	VulnerabilityInformation string `json:"vulnerability_information"`
	SeverityRating           string `json:"severity_rating"`
	Impact                   string `json:"impact"`
	ProofOfConcept           string `json:"proof_of_concept"`
	RecommendedFix           string `json:"recommended_fix"`
}

// FormatForHackerOne formats a finding for HackerOne submission.
func FormatForHackerOne(finding pipeline.ClassifiedFinding) HackerOneReport {
	return HackerOneReport{
		Title:                    formatH1Title(finding),
		VulnerabilityInformation: formatVulnInfo(finding),
		SeverityRating:           mapToH1Severity(finding.Severity),
		Impact:                   formatImpact(finding),
		ProofOfConcept:           formatPoC(finding),
		RecommendedFix:           "Please refer to the remediation section in the full report.",
	}
}

func formatH1Title(f pipeline.ClassifiedFinding) string {
	// H1 convention: "Vuln Type in /path parameter `param`"
	return fmt.Sprintf("%s on %s", f.Title, f.Target)
}

func formatVulnInfo(f pipeline.ClassifiedFinding) string {
	var b strings.Builder
	b.WriteString("## Summary\n\n")
	b.WriteString(f.Description + "\n\n")

	if len(f.CVEIDs) > 0 {
		b.WriteString("## CVE References\n\n")
		for _, cve := range f.CVEIDs {
			b.WriteString(fmt.Sprintf("- %s\n", cve))
		}
		b.WriteString("\n")
	}

	b.WriteString(fmt.Sprintf("## CVSS Score\n\n%.1f (%s)\n\n", f.CVSSScore, f.Severity))

	if f.CVSSVector != "" {
		b.WriteString(fmt.Sprintf("Vector: `%s`\n\n", f.CVSSVector))
	}

	return b.String()
}

func formatImpact(f pipeline.ClassifiedFinding) string {
	switch f.Severity {
	case pipeline.SeverityCritical:
		return "This vulnerability allows an attacker to fully compromise the application and its data."
	case pipeline.SeverityHigh:
		return "This vulnerability could lead to significant data exposure or system compromise."
	case pipeline.SeverityMedium:
		return "This vulnerability could be exploited under certain conditions to access restricted data or functionality."
	default:
		return "This vulnerability has limited direct impact but may be used in conjunction with other findings."
	}
}

func formatPoC(f pipeline.ClassifiedFinding) string {
	var b strings.Builder
	b.WriteString("## Steps to Reproduce\n\n")

	for i, e := range f.Evidence {
		b.WriteString(fmt.Sprintf("### Step %d\n\n", i+1))
		if e.Description != "" {
			b.WriteString(e.Description + "\n\n")
		}
		b.WriteString(fmt.Sprintf("```\n%s\n```\n\n", e.Content))
	}

	if len(f.Evidence) == 0 {
		b.WriteString("See attached evidence in the full report.\n")
	}

	return b.String()
}

func mapToH1Severity(severity pipeline.Severity) string {
	switch severity {
	case pipeline.SeverityCritical:
		return "critical"
	case pipeline.SeverityHigh:
		return "high"
	case pipeline.SeverityMedium:
		return "medium"
	case pipeline.SeverityLow:
		return "low"
	default:
		return "none"
	}
}
