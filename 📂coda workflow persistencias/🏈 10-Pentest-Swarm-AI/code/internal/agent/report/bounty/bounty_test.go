package bounty

import (
	"testing"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/pipeline"
)

func TestEstimate_FallsBackToPublicMarket(t *testing.T) {
	f := pipeline.ClassifiedFinding{Severity: pipeline.SeverityCritical}
	got := Estimate(f, nil)
	if got.LowUSD <= 0 || got.HighUSD <= got.LowUSD {
		t.Errorf("public-market range invalid: %+v", got)
	}
	if got.Source != "industry-average" {
		t.Errorf("expected industry-average source, got %q", got.Source)
	}
}

func TestEstimate_PrefersProgramStats(t *testing.T) {
	stats := &ProgramStats{
		Slug:               "shopify",
		AveragePerSeverity: map[pipeline.Severity]int{pipeline.SeverityHigh: 1500},
		TopPerSeverity:     map[pipeline.Severity]int{pipeline.SeverityHigh: 5000},
	}
	got := Estimate(pipeline.ClassifiedFinding{Severity: pipeline.SeverityHigh}, stats)
	if got.LowUSD != 1500 || got.HighUSD != 5000 {
		t.Errorf("program stats not honoured: %+v", got)
	}
	if got.Source != "program:shopify" {
		t.Errorf("source not tagged with program: %q", got.Source)
	}
}

func TestEstimate_OnlyAverage_DerivesTop(t *testing.T) {
	stats := &ProgramStats{
		Slug:               "x",
		AveragePerSeverity: map[pipeline.Severity]int{pipeline.SeverityMedium: 400},
	}
	got := Estimate(pipeline.ClassifiedFinding{Severity: pipeline.SeverityMedium}, stats)
	if got.LowUSD != 400 || got.HighUSD != 1000 {
		t.Errorf("derivation off: %+v", got)
	}
}

func TestTotal_Sums(t *testing.T) {
	findings := []pipeline.ClassifiedFinding{
		{Severity: pipeline.SeverityCritical},
		{Severity: pipeline.SeverityHigh},
		{Severity: pipeline.SeverityMedium},
	}
	low, high := Total(findings, nil)
	if low <= 0 || high <= low {
		t.Errorf("total invalid: low=%d high=%d", low, high)
	}
}
