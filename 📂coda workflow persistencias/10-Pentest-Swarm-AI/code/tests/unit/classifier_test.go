package unit

import (
	"testing"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/agent/classifier"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/pipeline"
)

func TestCVSSParsing(t *testing.T) {
	tests := []struct {
		name   string
		vector string
		wantAV string
	}{
		{"full critical", "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", "N"},
		{"local access", "AV:L/AC:H/PR:H/UI:R/S:U/C:L/I:N/A:N", "L"},
		{"physical", "AV:P/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", "P"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			c, err := classifier.ParseCVSSVector(tt.vector)
			if err != nil {
				t.Fatalf("parse error: %v", err)
			}
			if c.AttackVector != tt.wantAV {
				t.Errorf("AV = %s, want %s", c.AttackVector, tt.wantAV)
			}
		})
	}
}

func TestCVSSBaseScore(t *testing.T) {
	tests := []struct {
		name   string
		vector string
		want   float64 // expected CVSS score (approximate)
	}{
		{"max critical", "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", 9.8},
		{"medium", "AV:N/AC:H/PR:L/UI:R/S:U/C:L/I:L/A:N", 4.2},
		{"zero impact", "AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N", 0.0},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			c, _ := classifier.ParseCVSSVector(tt.vector)
			score := classifier.ComputeBaseScore(*c)
			// Allow 0.5 tolerance for rounding differences
			if score < tt.want-0.5 || score > tt.want+0.5 {
				t.Errorf("score = %.1f, want ~%.1f", score, tt.want)
			}
		})
	}
}

func TestScoreToSeverity(t *testing.T) {
	tests := []struct {
		score    float64
		severity pipeline.Severity
	}{
		{9.8, pipeline.SeverityCritical},
		{9.0, pipeline.SeverityCritical},
		{8.5, pipeline.SeverityHigh},
		{7.0, pipeline.SeverityHigh},
		{5.0, pipeline.SeverityMedium},
		{4.0, pipeline.SeverityMedium},
		{2.0, pipeline.SeverityLow},
		{0.0, pipeline.SeverityInformational},
	}

	for _, tt := range tests {
		got := classifier.ScoreToSeverity(tt.score)
		if got != tt.severity {
			t.Errorf("ScoreToSeverity(%.1f) = %s, want %s", tt.score, got, tt.severity)
		}
	}
}

func TestFPFilter(t *testing.T) {
	filter := classifier.NewFPFilter()

	tests := []struct {
		name     string
		finding  pipeline.RawFinding
		shouldFP bool
	}{
		{
			"generic banner = high FP",
			pipeline.RawFinding{Type: "banner", Detail: "apache server detected", RawOutput: ""},
			false, // 0.6 < 0.75
		},
		{
			"generic banner + 404 = FP",
			pipeline.RawFinding{Type: "banner", Detail: "nginx 404 not found", RawOutput: ""},
			true, // 0.6 + 0.5 > 0.75
		},
		{
			"real SQLi finding = not FP",
			pipeline.RawFinding{Type: "sqli", Detail: "SQL injection in parameter id, MySQL error in response", RawOutput: ""},
			false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := filter.ShouldFilter(tt.finding)
			if got != tt.shouldFP {
				score := filter.Score(tt.finding)
				t.Errorf("ShouldFilter = %v (score: %.2f), want %v", got, score, tt.shouldFP)
			}
		})
	}
}

func TestContextAdjustment(t *testing.T) {
	base := 7.5

	// Internet facing should increase
	adjusted := classifier.AdjustForContext(base, classifier.ScoringContext{InternetFacing: true})
	if adjusted <= base {
		t.Errorf("internet-facing should increase score: got %.1f from %.1f", adjusted, base)
	}

	// Auth required should decrease
	adjusted = classifier.AdjustForContext(base, classifier.ScoringContext{AuthenticationRequired: true})
	if adjusted >= base {
		t.Errorf("auth-required should decrease score: got %.1f from %.1f", adjusted, base)
	}

	// Score should never exceed 10.0
	adjusted = classifier.AdjustForContext(9.5, classifier.ScoringContext{InternetFacing: true, ExploitAvailable: true})
	if adjusted > 10.0 {
		t.Errorf("score should be capped at 10.0, got %.1f", adjusted)
	}
}
