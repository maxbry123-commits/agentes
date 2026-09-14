package intigriti

import (
	"context"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func fakeInti(t *testing.T, body string) *httptest.Server {
	t.Helper()
	return httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if !strings.Contains(r.URL.Path, "/programs/") {
			http.NotFound(w, r)
			return
		}
		_, _ = io.WriteString(w, body)
	}))
}

func TestImport_RequiresToken(t *testing.T) {
	c := NewClient(Config{})
	if _, err := c.Import(context.Background(), "acme"); err == nil {
		t.Fatal("expected error when token missing")
	}
}

func TestImport_MapsDomainTypes(t *testing.T) {
	srv := fakeInti(t, `{
		"domains": [
			{"endpoint": "*.acme.corp", "type": {"value": "wildcard"}, "inScope": true},
			{"endpoint": "api.acme.corp","type": {"value": "api"},      "inScope": true},
			{"endpoint": "10.0.0.0/24",  "type": {"value": "cidr"},     "inScope": true},
			{"endpoint": "1.2.3.4",      "type": {"value": "ip"},       "inScope": true},
			{"endpoint": "app.acme.com", "type": {"value": "android"},  "inScope": true},
			{"endpoint": "secret.corp",  "type": {"value": "domain"},   "inScope": false}
		]
	}`)
	defer srv.Close()

	c := NewClient(Config{Token: "tkn"})
	c.baseURL = srv.URL + "/external/researcher/v1"

	def, err := c.Import(context.Background(), "acme")
	if err != nil {
		t.Fatal(err)
	}
	if len(def.AllowedDomains) != 2 {
		t.Fatalf("domains: want 2, got %v", def.AllowedDomains)
	}
	if len(def.AllowedCIDRs) != 2 {
		t.Fatalf("cidrs: want 2, got %v", def.AllowedCIDRs)
	}
}

func TestImport_BearerHeader(t *testing.T) {
	var seen string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		seen = r.Header.Get("Authorization")
		_, _ = io.WriteString(w, `{"domains":[]}`)
	}))
	defer srv.Close()
	c := NewClient(Config{Token: "tkn"})
	c.baseURL = srv.URL + "/external/researcher/v1"
	_, _ = c.Import(context.Background(), "acme")
	if seen != "Bearer tkn" {
		t.Fatalf("want 'Bearer tkn', got %q", seen)
	}
}
