package memory

import (
	"fmt"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/pipeline"
)

// ExtractPatterns pulls anonymized patterns from a completed campaign.
func ExtractPatterns(surface *pipeline.AttackSurface, findings []pipeline.ClassifiedFinding) []MemoryEntry {
	var patterns []MemoryEntry

	// Tech stack patterns
	if len(surface.Technologies) > 0 {
		techs := ""
		for name, version := range surface.Technologies {
			techs += fmt.Sprintf("%s/%s ", name, version)
		}
		patterns = append(patterns, MemoryEntry{
			Category:   "tech_stack",
			Pattern:    fmt.Sprintf("Target uses: %s", techs),
			Confidence: 0.9,
		})
	}

	// Finding patterns per tech stack
	categoryCounts := make(map[string]int)
	for _, f := range findings {
		categoryCounts[f.AttackCategory]++
	}
	for category, count := range categoryCounts {
		patterns = append(patterns, MemoryEntry{
			Category:   "finding_pattern",
			Pattern:    fmt.Sprintf("%s findings are common (%d instances) on this tech stack", category, count),
			Confidence: float64(count) / float64(len(findings)),
		})
	}

	// False positive patterns
	for _, f := range findings {
		if f.FalsePositiveProbability > 0.7 {
			patterns = append(patterns, MemoryEntry{
				Category:   "false_positive",
				Pattern:    fmt.Sprintf("Finding type '%s' on '%s' is likely FP (%.0f%%)", f.AttackCategory, anonymizeTarget(f.Target), f.FalsePositiveProbability*100),
				Confidence: f.FalsePositiveProbability,
			})
		}
	}

	return patterns
}

// anonymizeTarget strips specific identifiers from targets.
func anonymizeTarget(target string) string {
	// Replace specific domains with generic descriptors
	// e.g., "api.example.com" -> "api.*.com"
	// Simplified for now
	if len(target) > 20 {
		return target[:10] + "..."
	}
	return target
}

// FormatForPrompt converts memory entries to a string for LLM injection.
func FormatForPrompt(entries []MemoryEntry) string {
	if len(entries) == 0 {
		return ""
	}

	result := "## Prior Intelligence (from previous engagements)\n\n"
	for _, e := range entries {
		result += fmt.Sprintf("- [%s] %s (confidence: %.0f%%)\n", e.Category, e.Pattern, e.Confidence*100)
	}
	result += "\nUse this intelligence to prioritize your approach.\n"

	return result
}
