package roi

import (
	"strings"
	"testing"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/pipeline"
)

func TestCalculate_GreenWhenBountyTrouncesSpend(t *testing.T) {
	findings := []pipeline.ClassifiedFinding{
		{Severity: pipeline.SeverityCritical}, // public-market: $1500 low
	}
	r := Calculate(10.0, findings, nil)
	if r.Verdict != VerdictGreen {
		t.Errorf("expected green, got %s (ratio %.1f)", r.Verdict, r.RatioLow)
	}
}

func TestCalculate_RedWhenSpendDwarfsBounty(t *testing.T) {
	findings := []pipeline.ClassifiedFinding{
		{Severity: pipeline.SeverityLow}, // $50 low
	}
	r := Calculate(100.0, findings, nil)
	if r.Verdict != VerdictRed {
		t.Errorf("expected red, got %s (ratio %.1f)", r.Verdict, r.RatioLow)
	}
}

func TestCalculate_ZeroSpendDoesNotPanic(t *testing.T) {
	r := Calculate(0, []pipeline.ClassifiedFinding{{Severity: pipeline.SeverityHigh}}, nil)
	if r.RatioLow != 0 || r.RatioHigh != 0 {
		t.Errorf("zero-spend should produce zero ratios, got %+v", r)
	}
	if r.Verdict != VerdictRed {
		t.Errorf("zero-spend should default to red")
	}
}

func TestFooter_IncludesAllFigures(t *testing.T) {
	r := Result{SpendUSD: 5.0, BountyLowUSD: 100, BountyHighUSD: 500, RatioLow: 20, RatioHigh: 100, Verdict: VerdictGreen}
	out := r.Footer()
	for _, want := range []string{"$5.00", "$100", "$500", "20.0", "100.0"} {
		if !strings.Contains(out, want) {
			t.Errorf("footer missing %q: %s", want, out)
		}
	}
}

func TestFooter_SpeculativeReportsCostNotHype(t *testing.T) {
	// No program stats → speculative: the footer must state cost + finding
	// count and must NOT print a bounty $ range or a ratio.
	r := Calculate(0.03, []pipeline.ClassifiedFinding{
		{Severity: pipeline.SeverityHigh}, {Severity: pipeline.SeverityHigh},
	}, nil)
	out := r.Footer()
	if !strings.Contains(out, "$0.03") || !strings.Contains(out, "2 finding") {
		t.Errorf("speculative footer should state cost and finding count: %s", out)
	}
	if strings.Contains(out, "ratio") || strings.Contains(out, "×") {
		t.Errorf("speculative footer must not print a bounty ratio: %s", out)
	}
}

func TestFooter_CapsAbsurdRatio(t *testing.T) {
	r := Result{SpendUSD: 0.03, BountyLowUSD: 1500, BountyHighUSD: 9000, RatioLow: 50000, RatioHigh: 300000, Verdict: VerdictGreen}
	out := r.Footer()
	if strings.Contains(out, "50000") || strings.Contains(out, "300000") {
		t.Errorf("absurd six-figure ratio should be capped: %s", out)
	}
	if !strings.Contains(out, ">1000×") {
		t.Errorf("expected capped >1000× display: %s", out)
	}
}
