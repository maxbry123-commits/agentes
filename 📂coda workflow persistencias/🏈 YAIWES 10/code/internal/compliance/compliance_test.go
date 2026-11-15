package compliance

import "testing"

func TestMap_CoreFrameworks(t *testing.T) {
	// Injection (A03) should touch a control in every enabled framework.
	got := Map("A03:2021-Injection", "CWE-89", AllFrameworks())
	if len(got) != 4 {
		t.Fatalf("A03 mapped to %d controls, want 4: %+v", len(got), got)
	}
	want := map[Framework]string{
		PCIDSS: "6.2.4", SOC2: "CC8.1", ISO27001: "A.8.28", NISTCSF: "PR.PS-06",
	}
	for _, c := range got {
		if want[c.Framework] != c.ID {
			t.Errorf("%s -> %s, want %s", c.Framework, c.ID, want[c.Framework])
		}
	}
}

func TestMap_SOC2_CC7_ForMisconfig(t *testing.T) {
	// The user specifically asked for SOC 2 CC7 (security monitoring): a
	// misconfiguration finding must surface CC7.1.
	got := Map("A05:2021-Security Misconfiguration", "CWE-16", []Framework{SOC2})
	if len(got) != 1 || got[0].ID != "CC7.1" {
		t.Fatalf("misconfig SOC2 = %+v, want CC7.1", got)
	}
}

func TestMap_AnchorControls(t *testing.T) {
	// Outdated components is the classic ISO A.8.8 / NIST ID.RA-01 anchor.
	got := Map("A06:2021-Vulnerable and Outdated Components", "CWE-1035", []Framework{ISO27001, NISTCSF})
	byF := map[Framework]string{}
	for _, c := range got {
		byF[c.Framework] = c.ID
	}
	if byF[ISO27001] != "A.8.8" {
		t.Errorf("ISO27001 = %q, want A.8.8", byF[ISO27001])
	}
	if byF[NISTCSF] != "ID.RA-01" {
		t.Errorf("NIST CSF = %q, want ID.RA-01", byF[NISTCSF])
	}
}

func TestMap_CWEOverride(t *testing.T) {
	// Security-header finding (A05, CWE-693) should pin PCI 6.4.1 via override,
	// not the A05 class default 2.2.1.
	got := Map("A05:2021-Security Misconfiguration", "CWE-693", []Framework{PCIDSS})
	if len(got) != 1 || got[0].ID != "6.4.1" {
		t.Fatalf("header override PCI = %+v, want 6.4.1", got)
	}
}

func TestMap_Filtering(t *testing.T) {
	got := Map("A02:2021-Cryptographic Failures", "CWE-311", []Framework{PCIDSS})
	if len(got) != 1 || got[0].Framework != PCIDSS || got[0].ID != "4.2.1" {
		t.Fatalf("crypto PCI-only = %+v, want just PCI 4.2.1", got)
	}
}

func TestMap_UnmappedYieldsNil(t *testing.T) {
	if got := Map("", "", AllFrameworks()); got != nil {
		t.Errorf("empty OWASP mapped to %+v, want nil", got)
	}
	if got := Map("A04:2021-Insecure Design", "CWE-1", AllFrameworks()); got != nil {
		t.Errorf("unmapped class A04 -> %+v, want nil", got)
	}
}

func TestMandate(t *testing.T) {
	got := Mandate([]Framework{PCIDSS, SOC2, ISO27001, NISTCSF})
	// Two anchor controls per framework => 8 total.
	if len(got) != 8 {
		t.Fatalf("mandate returned %d controls, want 8: %+v", len(got), got)
	}
	// PCI Req 11.4.1 (pentest) must be present — that's the wedge.
	found := false
	for _, c := range got {
		if c.Framework == PCIDSS && c.ID == "11.4.1" {
			found = true
		}
	}
	if !found {
		t.Errorf("mandate missing PCI 11.4.1: %+v", got)
	}
}

func TestParseFrameworks(t *testing.T) {
	cases := []struct {
		in      string
		want    int
		wantErr bool
	}{
		{"", 4, false},
		{"all", 4, false},
		{"pci", 1, false},
		{"pci,soc2", 2, false},
		{"soc2, pci", 2, false}, // order normalized to AllFrameworks order
		{"PCI,SOC2", 2, false},  // case-insensitive
		{"pci,pci", 1, false},   // de-duped
		{"bogus", 0, true},
		{"pci,bogus", 0, true},
	}
	for _, c := range cases {
		got, err := ParseFrameworks(c.in)
		if c.wantErr {
			if err == nil {
				t.Errorf("ParseFrameworks(%q) err = nil, want error", c.in)
			}
			continue
		}
		if err != nil {
			t.Errorf("ParseFrameworks(%q) err = %v", c.in, err)
			continue
		}
		if len(got) != c.want {
			t.Errorf("ParseFrameworks(%q) = %v (%d), want %d", c.in, got, len(got), c.want)
		}
	}
	// order normalization: "soc2,pci" -> [pci, soc2]
	got, _ := ParseFrameworks("soc2,pci")
	if len(got) != 2 || got[0] != PCIDSS || got[1] != SOC2 {
		t.Errorf("order = %v, want [pci soc2]", got)
	}
}

func TestControlTag(t *testing.T) {
	cases := map[Control]string{
		{PCIDSS, "11.4.1", ""}:    "pci-dss/11.4.1",
		{SOC2, "CC7.1", ""}:       "soc2/CC7.1",
		{ISO27001, "A.8.8", ""}:   "iso27001/A.8.8",
		{NISTCSF, "ID.RA-01", ""}: "nist-csf/ID.RA-01",
	}
	for c, want := range cases {
		if got := c.Tag(); got != want {
			t.Errorf("%+v.Tag() = %q, want %q", c, got, want)
		}
	}
}

func TestOWASPClass(t *testing.T) {
	cases := map[string]string{
		"A03:2021-Injection":                   "A03",
		"A1:2021-Broken Access Control":        "A01",
		"A10:2021-Server-Side Request Forgery": "A10",
		"":                                     "",
		"not-owasp":                            "",
	}
	for in, want := range cases {
		if got := owaspClass(in); got != want {
			t.Errorf("owaspClass(%q) = %q, want %q", in, got, want)
		}
	}
}
