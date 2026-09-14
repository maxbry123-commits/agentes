package report

import (
	"strings"
	"testing"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/pipeline"
	"github.com/google/uuid"
)

func fixtureFinding() (pipeline.ReportFinding, *pipeline.ClassifiedFinding) {
	cf := &pipeline.ClassifiedFinding{
		ID: uuid.New(), Title: "SQLi in /search", AttackCategory: "sqli",
		CVEIDs: []string{"CVE-2024-12345"},
		Reproduce: &pipeline.Reproduction{
			Command:           "curl 'https://acme.corp/search?q=UNION+SELECT+1'",
			ExpectedIndicator: "mysql_fetch_array",
			Tools:             []string{"nuclei", "sqlmap"},
		},
	}
	rf := pipeline.ReportFinding{
		ID: cf.ID, Title: cf.Title, Severity: pipeline.SeverityCritical,
		CVSSScore: 9.8, CVSSVector: "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
		AffectedComponents: []string{"https://acme.corp/search"},
		Description:        "UNION-based SQLi in q parameter.",
		Remediation:        "Use parameterised queries.",
	}
	return rf, cf
}

func TestRenderSubmission_HackerOne(t *testing.T) {
	rf, cf := fixtureFinding()
	v := BuildSubmissionView(rf, cf, []string{"nuclei", "sqlmap"})
	out, err := RenderSubmission("h1", v)
	if err != nil {
		t.Fatal(err)
	}
	body := string(out)
	for _, want := range []string{"## Summary", "## Steps to Reproduce", "## Impact", "## Recommendation", "CVE-2024-12345", "nvd.nist.gov", "nuclei", "sqlmap"} {
		if !strings.Contains(body, want) {
			t.Errorf("h1 output missing %q:\n%s", want, body)
		}
	}
}

func TestRenderSubmission_Bugcrowd(t *testing.T) {
	rf, cf := fixtureFinding()
	v := BuildSubmissionView(rf, cf, []string{"nuclei", "sqlmap"})
	out, err := RenderSubmission("bugcrowd", v)
	if err != nil {
		t.Fatal(err)
	}
	body := string(out)
	for _, want := range []string{"### Vulnerability Details", "VRT", "### Suggested Remediation"} {
		if !strings.Contains(body, want) {
			t.Errorf("bugcrowd output missing %q:\n%s", want, body)
		}
	}
}

func TestRenderSubmission_Intigriti(t *testing.T) {
	rf, cf := fixtureFinding()
	v := BuildSubmissionView(rf, cf, nil)
	out, err := RenderSubmission("intigriti", v)
	if err != nil {
		t.Fatal(err)
	}
	body := string(out)
	for _, want := range []string{"Type of weakness", "Proof of Concept", "Recommended Remediation"} {
		if !strings.Contains(body, want) {
			t.Errorf("intigriti output missing %q:\n%s", want, body)
		}
	}
}

func TestRenderSubmission_UnknownPlatform(t *testing.T) {
	rf, cf := fixtureFinding()
	_, err := RenderSubmission("unknown", BuildSubmissionView(rf, cf, nil))
	if err == nil {
		t.Fatal("expected error for unknown platform")
	}
}

func TestBuildSubmissionView_FillsFallbacks(t *testing.T) {
	rf := pipeline.ReportFinding{Title: "Sparse finding", Severity: pipeline.SeverityMedium}
	v := BuildSubmissionView(rf, nil, nil)
	if v.Impact == "" || v.Remediation == "" || v.Summary == "" {
		t.Fatalf("fallbacks should fill; got %+v", v)
	}
	// Ensure template renders without error when the finding is thin.
	if _, err := RenderSubmission("h1", v); err != nil {
		t.Fatalf("rendering sparse finding should succeed: %v", err)
	}
}
