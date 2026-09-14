// Package roi computes the return-on-investment footer that lands at
// the bottom of every campaign report: expected bounty value vs. LLM
// spend, with a green/yellow/red traffic light.
//
// The whole point is to keep researchers honest about whether a scan
// was worth running. A campaign that burns $40 in tokens to surface
// $50 of speculative findings is yellow at best — the researcher
// should know that BEFORE filing reports, not after triage closes
// most of them as info-only.
package roi

import (
	"fmt"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/agent/report/bounty"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/pipeline"
)

// Verdict is the traffic-light colour the report footer renders.
type Verdict string

const (
	VerdictGreen  Verdict = "green"  // ratio > 10×
	VerdictYellow Verdict = "yellow" // ratio 2× – 10×
	VerdictRed    Verdict = "red"    // ratio < 2×
)

// Result is the computed ROI for a campaign.
type Result struct {
	SpendUSD      float64
	BountyLowUSD  int
	BountyHighUSD int
	RatioLow      float64 // BountyLow / Spend
	RatioHigh     float64 // BountyHigh / Spend
	Verdict       Verdict
	FindingCount  int
	// Speculative is true when no program payout data was supplied, so the
	// bounty range is an industry-average guess rather than a real estimate.
	// The footer then reports cost factually instead of a headline dollar
	// range and an eye-watering ratio that reads as hype.
	Speculative bool
}

// Calculate runs the bounty estimator over every finding, totals the
// range, and grades against the spend.
//
// Verdict is decided on the *low* end of the bounty range — better to
// flag a marginal campaign yellow than to render green on optimism
// alone.
func Calculate(spendUSD float64, findings []pipeline.ClassifiedFinding, stats *bounty.ProgramStats) Result {
	low, high := bounty.Total(findings, stats)
	r := Result{
		SpendUSD:      spendUSD,
		BountyLowUSD:  low,
		BountyHighUSD: high,
		FindingCount:  len(findings),
		Speculative:   stats == nil,
	}
	if spendUSD > 0 {
		r.RatioLow = float64(low) / spendUSD
		r.RatioHigh = float64(high) / spendUSD
	}
	switch {
	case r.RatioLow > 10:
		r.Verdict = VerdictGreen
	case r.RatioLow >= 2:
		r.Verdict = VerdictYellow
	default:
		r.Verdict = VerdictRed
	}
	return r
}

// Footer is the markdown block for the report — lives at the bottom of
// every campaign report so the researcher sees it without scrolling
// past 50 findings to get the verdict.
func (r Result) Footer() string {
	// Without real program payout data, a headline bounty range and a huge
	// ratio (a few cents of spend divides into a speculative $ figure and
	// explodes) read as hype. Report cost factually instead and say the
	// bounty estimate needs the target program's data.
	if r.Speculative {
		return fmt.Sprintf(
			"**Campaign cost:** $%.2f in LLM spend across %d finding(s). "+
				"Bounty value depends on the target's bug-bounty program — configure its payout data for an ROI estimate.",
			r.SpendUSD, r.FindingCount,
		)
	}
	icon := map[Verdict]string{
		VerdictGreen:  "🟢",
		VerdictYellow: "🟡",
		VerdictRed:    "🔴",
	}[r.Verdict]
	return fmt.Sprintf(
		"**Campaign ROI:** %s estimated bounty $%d–$%d  ·  LLM spend $%.2f  ·  ratio %s–%s",
		icon, r.BountyLowUSD, r.BountyHighUSD, r.SpendUSD, fmtRatio(r.RatioLow), fmtRatio(r.RatioHigh),
	)
}

// fmtRatio renders an ROI multiple, capping the display at ">1000×" so a
// tiny-spend campaign doesn't print an absurd six-figure ratio.
func fmtRatio(x float64) string {
	if x >= 1000 {
		return ">1000×"
	}
	return fmt.Sprintf("%.1f×", x)
}
