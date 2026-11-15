package unit

import (
	"testing"

	apperrors "github.com/Armur-Ai/Pentest-Swarm-AI/internal/errors"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/scope"
)

func TestValidate_InScopeIP(t *testing.T) {
	s := scope.ScopeDefinition{
		AllowedCIDRs: []string{"10.0.0.0/24"},
	}

	if err := scope.Validate("10.0.0.50", s); err != nil {
		t.Errorf("expected in-scope, got error: %v", err)
	}
}

func TestValidate_OutOfScopeIP(t *testing.T) {
	s := scope.ScopeDefinition{
		AllowedCIDRs: []string{"10.0.0.0/24"},
	}

	err := scope.Validate("192.168.99.1", s)
	if err == nil {
		t.Fatal("expected scope violation, got nil")
	}
	if !apperrors.Is(err, apperrors.ErrScopeViolation) {
		t.Errorf("expected ErrScopeViolation, got: %v", err)
	}
}

func TestValidate_CIDRBoundary(t *testing.T) {
	s := scope.ScopeDefinition{
		AllowedCIDRs: []string{"10.0.0.0/24"},
	}

	tests := []struct {
		name    string
		target  string
		inScope bool
	}{
		{"first IP in range", "10.0.0.0", true},
		{"last IP in range", "10.0.0.255", true},
		{"just outside range", "10.0.1.0", false},
		{"different subnet", "10.1.0.1", false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := scope.Validate(tt.target, s)
			if tt.inScope && err != nil {
				t.Errorf("expected in-scope, got: %v", err)
			}
			if !tt.inScope && err == nil {
				t.Errorf("expected out-of-scope for %s", tt.target)
			}
		})
	}
}

func TestValidate_InScopeDomain(t *testing.T) {
	s := scope.ScopeDefinition{
		AllowedDomains: []string{"example.com"},
	}

	tests := []struct {
		name    string
		target  string
		inScope bool
	}{
		{"exact match", "example.com", true},
		{"subdomain", "sub.example.com", true},
		{"deep subdomain", "a.b.c.example.com", true},
		{"different domain", "evil.com", false},
		{"similar but different", "notexample.com", false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := scope.Validate(tt.target, s)
			if tt.inScope && err != nil {
				t.Errorf("expected in-scope, got: %v", err)
			}
			if !tt.inScope && err == nil {
				t.Errorf("expected out-of-scope for %s", tt.target)
			}
		})
	}
}

func TestValidate_WildcardDomain(t *testing.T) {
	s := scope.ScopeDefinition{
		AllowedDomains: []string{"*.example.com"},
	}

	tests := []struct {
		name    string
		target  string
		inScope bool
	}{
		{"subdomain matches wildcard", "sub.example.com", true},
		{"deep subdomain", "a.b.example.com", true},
		{"root domain does not match wildcard", "example.com", false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := scope.Validate(tt.target, s)
			if tt.inScope && err != nil {
				t.Errorf("expected in-scope, got: %v", err)
			}
			if !tt.inScope && err == nil {
				t.Errorf("expected out-of-scope for %s", tt.target)
			}
		})
	}
}

func TestValidate_URL(t *testing.T) {
	s := scope.ScopeDefinition{
		AllowedDomains: []string{"example.com"},
	}

	if err := scope.Validate("https://example.com/path?q=1", s); err != nil {
		t.Errorf("URL with in-scope domain should pass: %v", err)
	}

	err := scope.Validate("https://evil.com/path", s)
	if err == nil {
		t.Error("URL with out-of-scope domain should fail")
	}
}

func TestValidate_EmptyScope(t *testing.T) {
	s := scope.ScopeDefinition{}

	err := scope.Validate("anything.com", s)
	if err == nil {
		t.Error("empty scope should reject all targets")
	}
}

func TestValidate_ExcludedCIDR(t *testing.T) {
	s := scope.ScopeDefinition{
		AllowedCIDRs:  []string{"10.0.0.0/16"},
		ExcludedCIDRs: []string{"10.0.1.0/24"},
	}

	if err := scope.Validate("10.0.0.50", s); err != nil {
		t.Errorf("10.0.0.50 should be in scope: %v", err)
	}

	err := scope.Validate("10.0.1.50", s)
	if err == nil {
		t.Error("10.0.1.50 should be excluded")
	}
}

func TestValidateCommand_DetectsOutOfScopeTarget(t *testing.T) {
	s := scope.ScopeDefinition{
		AllowedDomains: []string{"example.com"},
		AllowedCIDRs:   []string{"10.0.0.0/24"},
	}

	// In-scope command
	if err := scope.ValidateCommand("nmap -sV 10.0.0.1", s); err != nil {
		t.Errorf("in-scope command should pass: %v", err)
	}

	// Out-of-scope command
	err := scope.ValidateCommand("nmap -sV 192.168.1.1", s)
	if err == nil {
		t.Error("command targeting 192.168.1.1 should fail scope check")
	}

	// Command with domain
	if err := scope.ValidateCommand("curl https://sub.example.com/api", s); err != nil {
		t.Errorf("in-scope domain command should pass: %v", err)
	}

	// Command with out-of-scope domain
	err = scope.ValidateCommand("sqlmap -u http://evil.com/search", s)
	if err == nil {
		t.Error("command targeting evil.com should fail scope check")
	}
}
