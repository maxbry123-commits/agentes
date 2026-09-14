package scope

import "testing"

func TestValidate_DomainExactMatch(t *testing.T) {
	def := ScopeDefinition{AllowedDomains: []string{"example.com"}}
	if err := Validate("example.com", def); err != nil {
		t.Fatalf("exact domain should be in scope: %v", err)
	}
}

func TestValidate_DomainSubdomainMatch(t *testing.T) {
	def := ScopeDefinition{AllowedDomains: []string{"example.com"}}
	// "api.example.com" should be allowed because example.com covers subdomains.
	if err := Validate("api.example.com", def); err != nil {
		t.Fatalf("subdomain should inherit parent scope: %v", err)
	}
}

func TestValidate_DomainWildcard(t *testing.T) {
	def := ScopeDefinition{AllowedDomains: []string{"*.example.com"}}
	if err := Validate("api.example.com", def); err != nil {
		t.Fatalf("wildcard should match: %v", err)
	}
	if err := Validate("other.com", def); err == nil {
		t.Fatal("unrelated domain should NOT match wildcard")
	}
}

func TestValidate_DomainURL(t *testing.T) {
	def := ScopeDefinition{AllowedDomains: []string{"example.com"}}
	if err := Validate("https://api.example.com/v1/users", def); err != nil {
		t.Fatalf("URL with in-scope host should pass: %v", err)
	}
}

func TestValidate_IPInCIDR(t *testing.T) {
	def := ScopeDefinition{AllowedCIDRs: []string{"10.0.0.0/24"}}
	if err := Validate("10.0.0.42", def); err != nil {
		t.Fatalf("IP in CIDR should pass: %v", err)
	}
	if err := Validate("10.0.1.1", def); err == nil {
		t.Fatal("IP outside CIDR should fail")
	}
}

func TestValidate_ExcludedCIDRWins(t *testing.T) {
	def := ScopeDefinition{
		AllowedCIDRs:  []string{"10.0.0.0/8"},
		ExcludedCIDRs: []string{"10.1.0.0/16"},
	}
	if err := Validate("10.2.0.1", def); err != nil {
		t.Fatal("allowed IP should pass")
	}
	if err := Validate("10.1.5.5", def); err == nil {
		t.Fatal("excluded CIDR should override allowed")
	}
}

func TestValidate_EmptyScopeRefused(t *testing.T) {
	if err := Validate("example.com", ScopeDefinition{}); err == nil {
		t.Fatal("empty scope must refuse everything")
	}
}

func TestValidateCommand_CatchesOutOfScopeArg(t *testing.T) {
	def := ScopeDefinition{AllowedDomains: []string{"example.com"}}
	if err := ValidateCommand("nmap -sV example.com", def); err != nil {
		t.Fatalf("in-scope command should pass: %v", err)
	}
	if err := ValidateCommand("curl http://evil.com/payload http://example.com/", def); err == nil {
		t.Fatal("out-of-scope domain in command should fail")
	}
}

func TestValidateCommand_IgnoresCommonNonTargets(t *testing.T) {
	def := ScopeDefinition{AllowedDomains: []string{"example.com"}}
	// github.com is a known non-target (tooling URL), shouldn't trip validation.
	if err := ValidateCommand("nuclei -u example.com -templates github.com/projectdiscovery/nuclei-templates", def); err != nil {
		t.Fatalf("non-target domains should be skipped: %v", err)
	}
}

func TestValidateCommand_IgnoresEmailDomainInBody(t *testing.T) {
	// Loopback-only scope, as a --lab / localhost API scan uses.
	def := ScopeDefinition{AllowedCIDRs: []string{"127.0.0.1/32"}}
	// An httpreq signup step whose JSON body carries an email at example.com —
	// the request target (the --url) is in scope; the email domain must not be
	// mistaken for an out-of-scope scan target.
	cmd := `httpreq --method POST --url http://127.0.0.1/identity/api/auth/signup --body '{"email":"atk_abc@example.com","password":"x"}'`
	if err := ValidateCommand(cmd, def); err != nil {
		t.Fatalf("email domain in body should not trip scope validation: %v", err)
	}
	// But a bare out-of-scope target (not an email) must still be caught.
	if err := ValidateCommand("httpreq --url http://evil.com/x", def); err == nil {
		t.Fatal("bare out-of-scope --url target should still fail")
	}
}

func TestValidateAndLog_PassThrough(t *testing.T) {
	def := ScopeDefinition{AllowedDomains: []string{"example.com"}}
	if err := ValidateAndLog("unit-test", "example.com", def); err != nil {
		t.Fatalf("in-scope target should pass ValidateAndLog: %v", err)
	}
	if err := ValidateAndLog("unit-test", "evil.com", def); err == nil {
		t.Fatal("out-of-scope target should fail ValidateAndLog")
	}
}
