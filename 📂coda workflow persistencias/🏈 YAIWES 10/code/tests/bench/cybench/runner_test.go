package cybench

import "testing"

func TestScore_PureSummation(t *testing.T) {
	results := []Result{
		{ChallengeID: "a", Solved: true, CostUSD: 1.20},
		{ChallengeID: "b", Solved: false, CostUSD: 0.50},
		{ChallengeID: "c", Solved: true, CostUSD: 2.10},
	}
	solved, total, usd := Score(results)
	if solved != 2 || total != 3 {
		t.Errorf("Score solved/total: got %d/%d, want 2/3", solved, total)
	}
	if usd < 3.79 || usd > 3.81 {
		t.Errorf("Score usd: got %.2f, want 3.80", usd)
	}
}

func TestLoadChallenges_FailsLoudlyUntilFixturesVendored(t *testing.T) {
	_, err := LoadChallenges("./fixtures")
	if err == nil {
		t.Error("expected an error until fixtures are vendored")
	}
}
