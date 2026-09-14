// Package bounty estimates a dollar range for a finding based on its
// severity and (optionally) the target program's published bounty stats.
//
// Used in two places:
//   - the final report footer (4.5.7 ROI), to compare expected payout
//     against LLM spend
//   - the per-finding submission view, so the researcher can see which
//     drafts are worth their time before they submit
//
// Estimates are deliberately conservative — under-promising is fine,
// over-promising erodes trust. Public-market fallbacks come from
// HackerOne's annual hacker-powered-security report ranges (rounded
// down to discourage anchoring on the high end).
package bounty

import (
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/pipeline"
)

// ProgramStats is whatever per-program data the caller can scrape from
// the platform's public profile. All fields are optional — zero values
// fall back to the conservative public-market table.
type ProgramStats struct {
	// Slug identifies the program in logs / report footers.
	Slug string

	// AveragePerSeverity, when non-empty, overrides the default table.
	// Keys are pipeline.Severity values; values are dollars (the program's
	// historical mean for that severity bucket).
	AveragePerSeverity map[pipeline.Severity]int

	// TopPerSeverity is the program's published max for each severity. We
	// surface this as the "high" end of the range so researchers see the
	// upside without us inflating the average.
	TopPerSeverity map[pipeline.Severity]int
}

// Range is an estimated bounty for a single finding.
type Range struct {
	LowUSD  int
	HighUSD int
	// Source describes where the numbers came from — useful in tooltips
	// ("from program stats" vs "industry average").
	Source string
}

// publicMarket is the conservative public-market fallback. Numbers come
// from HackerOne's published median bounty tables, rounded DOWN so we
// don't accidentally over-promise to a researcher.
var publicMarket = map[pipeline.Severity]Range{
	pipeline.SeverityCritical:      {LowUSD: 1500, HighUSD: 10000, Source: "industry-average"},
	pipeline.SeverityHigh:          {LowUSD: 500, HighUSD: 3000, Source: "industry-average"},
	pipeline.SeverityMedium:        {LowUSD: 150, HighUSD: 800, Source: "industry-average"},
	pipeline.SeverityLow:           {LowUSD: 50, HighUSD: 200, Source: "industry-average"},
	pipeline.SeverityInformational: {LowUSD: 0, HighUSD: 50, Source: "industry-average"},
}

// Estimate returns an estimated dollar range for one finding. If
// programStats has data for the finding's severity, that wins; otherwise
// falls back to the public-market table.
func Estimate(f pipeline.ClassifiedFinding, stats *ProgramStats) Range {
	if stats != nil {
		avg, hasAvg := stats.AveragePerSeverity[f.Severity]
		top, hasTop := stats.TopPerSeverity[f.Severity]
		if hasAvg || hasTop {
			low := avg
			high := top
			if !hasAvg && hasTop {
				// Only a max published — half it for the low end so the
				// range still shows meaningful spread.
				low = top / 2
			}
			if !hasTop && hasAvg {
				// Only an average — assume the top is 2.5× (a common ratio
				// observed in published H1 program stats).
				high = avg * 5 / 2
			}
			return Range{LowUSD: low, HighUSD: high, Source: "program:" + stats.Slug}
		}
	}
	if r, ok := publicMarket[f.Severity]; ok {
		return r
	}
	return Range{Source: "industry-average"}
}

// Total sums an Estimate over a slice of findings — used by the ROI
// footer. Returns the (low, high) total in dollars.
func Total(findings []pipeline.ClassifiedFinding, stats *ProgramStats) (lowUSD, highUSD int) {
	for _, f := range findings {
		r := Estimate(f, stats)
		lowUSD += r.LowUSD
		highUSD += r.HighUSD
	}
	return
}
