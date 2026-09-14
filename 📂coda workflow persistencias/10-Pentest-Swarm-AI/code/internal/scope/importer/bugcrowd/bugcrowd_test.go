package bugcrowd

import (
	"context"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func fakeBC(t *testing.T, body string) *httptest.Server {
	t.Helper()
	return httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if !strings.Contains(r.URL.Path, "/engagements/") {
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

func TestImport_MapsCategories(t *testing.T) {
	srv := fakeBC(t, `{
		"data": [
			{"attributes": {"name": "public site", "uri": "*.acme.corp",     "category": "website", "in_scope": true}},
			{"attributes": {"name": "api",         "uri": "api.acme.corp",   "category": "api",     "in_scope": true}},
			{"attributes": {"name": "range",       "uri": "10.0.0.0/24",     "category": "ip",      "in_scope": true}},
			{"attributes": {"name": "single ip",   "uri": "1.2.3.4",         "category": "ip",      "in_scope": true}},
			{"attributes": {"name": "ios app",     "uri": "com.acme.app",    "category": "ios",     "in_scope": true}},
			{"attributes": {"name": "staging",     "uri": "staging.acme.corp","category":"website", "in_scope": false}}
		]
	}`)
	defer srv.Close()

	c := NewClient(Config{Token: "tkn"})
	c.baseURL = srv.URL + "/v4"

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
	found132 := false
	for _, c := range def.AllowedCIDRs {
		if c == "1.2.3.4/32" {
			found132 = true
		}
	}
	if !found132 {
		t.Errorf("bare IP should be normalised to /32; got %v", def.AllowedCIDRs)
	}
}

func TestImport_BearerAuth(t *testing.T) {
	var seen string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		seen = r.Header.Get("Authorization")
		_, _ = io.WriteString(w, `{"data":[]}`)
	}))
	defer srv.Close()
	c := NewClient(Config{Token: "tkn"})
	c.baseURL = srv.URL + "/v4"
	_, _ = c.Import(context.Background(), "acme")
	if seen != "Token tkn" {
		t.Fatalf("want 'Token tkn', got %q", seen)
	}
}
