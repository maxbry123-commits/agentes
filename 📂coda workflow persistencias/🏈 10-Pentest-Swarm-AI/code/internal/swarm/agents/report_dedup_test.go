package agents

import (
	"strings"
	"testing"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/pipeline"
)

func TestCollapseDuplicateFindings_MergesSameURLNucleiHits(t *testing.T) {
	in := []pipeline.ClassifiedFinding{
		{Title: "Generic Env File Disclosure", Target: "http://t/.env", Severity: pipeline.SeverityHigh, AttackCategory: "nuclei", CVSSScore: 8.0},
		{Title: "Laravel - Sensitive Information Disclosure", Target: "http://t/.env", Severity: pipeline.SeverityHigh, AttackCategory: "nuclei", CVSSScore: 8.0},
		{Title: "Codeigniter - .env File Discovery", Target: "http://t/.env", Severity: pipeline.SeverityHigh, AttackCategory: "nuclei", CVSSScore: 8.0},
		// Distinct business-logic finding on a different target — must survive.
		{Title: "crAPI BOLA", Target: "http://t/vehicle/x/location", Severity: pipeline.SeverityHigh, AttackCategory: "api_business_logic", CVSSScore: 8.2},
	}
	out := collapseDuplicateFindings(in)
	if len(out) != 2 {
		t.Fatalf("expected 3 env hits collapsed to 1 + the BOLA = 2, got %d", len(out))
	}
	// The kept env finding should note the other detectors.
	var env *pipeline.ClassifiedFinding
	for i := range out {
		if strings.Contains(out[i].Target, ".env") {
			env = &out[i]
		}
	}
	if env == nil {
		t.Fatal("env finding missing after collapse")
	}
	if !strings.Contains(env.Description, "Also reported by") {
		t.Errorf("collapsed env finding should list merged detectors: %q", env.Description)
	}
}

func TestCollapseDuplicateFindings_KeepsDistinctAndEmptyTargets(t *testing.T) {
	in := []pipeline.ClassifiedFinding{
		{Title: "A", Target: "", Severity: pipeline.SeverityHigh, AttackCategory: "x"},
		{Title: "B", Target: "", Severity: pipeline.SeverityHigh, AttackCategory: "x"},
		{Title: "C", Target: "http://t/a", Severity: pipeline.SeverityHigh, AttackCategory: "x"},
		{Title: "D", Target: "http://t/a", Severity: pipeline.SeverityMedium, AttackCategory: "x"}, // diff severity
	}
	out := collapseDuplicateFindings(in)
	if len(out) != 4 {
		t.Fatalf("empty-target findings and different-severity findings must not collapse; got %d", len(out))
	}
}

func TestNormalizeFindingTarget_CollapsesIDs(t *testing.T) {
	cases := map[string]string{
		"http://t/identity/api/v2/vehicle/4bae9968-ec7f-4de3-a3a0-ba1b2ab5e5e5/location": "http://t/identity/api/v2/vehicle/:id/location",
		"http://t/identity/api/v2/vehicle/{{victim_vehicle}}/location":                    "http://t/identity/api/v2/vehicle/:id/location",
		"http://t/users/v1/42": "http://t/users/v1/:id",
	}
	for in, want := range cases {
		if got := normalizeFindingTarget(in); got != want {
			t.Errorf("normalizeFindingTarget(%q) = %q, want %q", in, got, want)
		}
	}
}
