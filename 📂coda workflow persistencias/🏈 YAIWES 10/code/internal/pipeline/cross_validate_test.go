package pipeline

import "testing"

func build(title, target, cat string, conf Confidence, tools ...string) ClassifiedFinding {
	f := ClassifiedFinding{Title: title, Target: target, AttackCategory: cat, Confidence: conf}
	if len(tools) > 0 {
		f.Reproduce = &Reproduction{Tools: tools}
	}
	return f
}

func TestCrossValidate_TwoToolsUpgradeToHigh(t *testing.T) {
	fs := []ClassifiedFinding{
		build("Nuclei saw SQLi", "example.com", "sqli", ConfidenceMedium, "nuclei"),
		build("Sqlmap saw SQLi", "example.com", "sqli", ConfidenceMedium, "sqlmap"),
	}
	CrossValidate(fs)
	for _, f := range fs {
		if f.Confidence != ConfidenceHigh {
			t.Errorf("%s: want High (2 tools agree), got %s", f.Title, f.Confidence)
		}
	}
}

func TestCrossValidate_SingleToolNoReproduceDowngrades(t *testing.T) {
	fs := []ClassifiedFinding{
		build("Lone nuclei hit", "example.com", "xss", ConfidenceMedium),
	}
	CrossValidate(fs)
	if fs[0].Confidence != ConfidenceUnverified {
		t.Fatalf("want Unverified, got %s", fs[0].Confidence)
	}
}

func TestCrossValidate_SingleToolWithReproducePreserved(t *testing.T) {
	fs := []ClassifiedFinding{
		build("Nuclei hit with repro", "example.com", "xss", ConfidenceMedium, "nuclei"),
	}
	CrossValidate(fs)
	if fs[0].Confidence != ConfidenceMedium {
		t.Fatalf("single tool + repro should stay at Medium, got %s", fs[0].Confidence)
	}
}

func TestCrossValidate_HighPreservedAcrossDowngrade(t *testing.T) {
	fs := []ClassifiedFinding{
		build("Classifier already high", "example.com", "rce", ConfidenceHigh),
	}
	CrossValidate(fs)
	if fs[0].Confidence != ConfidenceHigh {
		t.Fatalf("pre-existing High should not downgrade, got %s", fs[0].Confidence)
	}
}

func TestCorroboratingTools_Sorted(t *testing.T) {
	fs := []ClassifiedFinding{
		build("nuclei", "example.com", "sqli", ConfidenceMedium, "nuclei"),
		build("sqlmap", "example.com", "sqli", ConfidenceHigh, "sqlmap"),
		build("ffuf", "example.com", "sqli", ConfidenceLow, "ffuf"),
		build("elsewhere", "other.com", "sqli", ConfidenceHigh, "burp"),
	}
	got := CorroboratingTools(fs, "example.com", "sqli")
	if len(got) != 3 || got[0] != "ffuf" || got[1] != "nuclei" || got[2] != "sqlmap" {
		t.Fatalf("want [ffuf nuclei sqlmap], got %v", got)
	}
}
