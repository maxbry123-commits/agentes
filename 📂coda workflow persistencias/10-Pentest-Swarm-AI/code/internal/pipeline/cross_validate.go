package pipeline

import "sort"

// CrossValidate inspects a set of classified findings and adjusts their
// Confidence based on corroborating signal:
//
//   - 2+ distinct tools produced a finding for (target, attack_category)
//     → Confidence upgraded to High (the vuln is supported by independent
//     evidence, the strongest signal we get without a live PoC)
//   - 1 tool + a non-nil Reproduce block
//     → Confidence stays at its classified level (the ConfirmationAgent
//     gates the actual re-run; our job here is corroboration only)
//   - 1 tool + no Reproduce
//     → Confidence downgraded to Unverified (we're relying on a single
//     tool's say-so with no way for a reviewer to re-trigger)
//
// The input is mutated in-place and returned for chaining. Order is
// preserved.
func CrossValidate(findings []ClassifiedFinding) []ClassifiedFinding {
	// Bucket by (target, attack_category) and collect the union of tools
	// across all findings in the bucket.
	type key struct{ target, category string }
	tools := map[key]map[string]struct{}{}
	for _, f := range findings {
		k := key{f.Target, f.AttackCategory}
		if _, ok := tools[k]; !ok {
			tools[k] = map[string]struct{}{}
		}
		if f.Reproduce != nil {
			for _, t := range f.Reproduce.Tools {
				tools[k][t] = struct{}{}
			}
		}
	}

	for i := range findings {
		f := &findings[i]
		k := key{f.Target, f.AttackCategory}
		distinctTools := len(tools[k])

		switch {
		case distinctTools >= 2:
			f.Confidence = ConfidenceHigh
		case distinctTools == 1 && f.Reproduce != nil:
			// leave as-is; Reproduce gate decides
		default:
			// 0 or 1 tool and no reproduction plan — we can't vouch for it.
			if f.Confidence != ConfidenceHigh {
				f.Confidence = ConfidenceUnverified
			}
		}
	}
	return findings
}

// CorroboratingTools returns the sorted union of tools that reported a
// given target + category. Useful in report templates.
func CorroboratingTools(findings []ClassifiedFinding, target, category string) []string {
	seen := map[string]struct{}{}
	for _, f := range findings {
		if f.Target != target || f.AttackCategory != category {
			continue
		}
		if f.Reproduce == nil {
			continue
		}
		for _, t := range f.Reproduce.Tools {
			seen[t] = struct{}{}
		}
	}
	out := make([]string, 0, len(seen))
	for t := range seen {
		out = append(out, t)
	}
	sort.Strings(out)
	return out
}
