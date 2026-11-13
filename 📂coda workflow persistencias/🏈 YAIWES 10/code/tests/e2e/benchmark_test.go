//go:build e2e

package e2e

import (
	"testing"
	"time"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/agent/classifier"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/pipeline"
	"github.com/google/uuid"
)

// BenchmarkClassification measures classification performance.
// Target: <60 seconds for 50 findings.
func BenchmarkClassification(b *testing.B) {
	// Generate 50 test findings
	var findings []pipeline.RawFinding
	types := []string{"sqli", "xss", "ssrf", "misconfig", "info_disclosure"}
	for i := 0; i < 50; i++ {
		findings = append(findings, pipeline.RawFinding{
			ID:           uuid.New(),
			CampaignID:   uuid.New(),
			Source:       "nuclei",
			Type:         types[i%len(types)],
			Target:       "example.com",
			Detail:       "Test finding " + types[i%len(types)],
			DiscoveredAt: time.Now(),
		})
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		fpFilter := classifier.NewFPFilter()
		for _, f := range findings {
			fpFilter.Score(f)
		}
	}
}

// BenchmarkCVSSScoring measures CVSS computation performance.
func BenchmarkCVSSScoring(b *testing.B) {
	vectors := []string{
		"AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
		"AV:N/AC:H/PR:L/UI:R/S:C/C:L/I:L/A:N",
		"AV:L/AC:L/PR:H/UI:N/S:U/C:H/I:N/A:N",
		"AV:A/AC:L/PR:N/UI:N/S:U/C:N/I:L/A:L",
		"AV:P/AC:H/PR:H/UI:R/S:U/C:L/I:N/A:N",
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		for _, v := range vectors {
			components, err := classifier.ParseCVSSVector(v)
			if err != nil {
				b.Fatal(err)
			}
			classifier.ComputeBaseScore(*components)
		}
	}
}
