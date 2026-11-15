package nvdcheck

import (
	"context"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/pipeline"
)

// A minimal NVD-shaped response the client knows how to parse.
const fakeNVDBody = `{
  "vulnerabilities": [
    {"cve": {"metrics": {"cvssMetricV31": [
      {"cvssData": {"baseScore": 9.8, "vectorString": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", "baseSeverity": "CRITICAL"}}
    ]}}}
  ]
}`

func newClientWithFakeNVD(t *testing.T, body string) (*Client, *httptest.Server) {
	t.Helper()
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		_, _ = io.WriteString(w, body)
	}))
	c, err := NewClient(Config{CacheDir: t.TempDir()})
	if err != nil {
		t.Fatal(err)
	}
	c.baseURL = srv.URL
	return c, srv
}

func TestLookup_ParsesV31(t *testing.T) {
	c, srv := newClientWithFakeNVD(t, fakeNVDBody)
	defer srv.Close()
	e, err := c.Lookup(context.Background(), "CVE-2024-12345")
	if err != nil {
		t.Fatal(err)
	}
	if e.BaseScore != 9.8 || e.Severity != "CRITICAL" {
		t.Fatalf("unexpected entry: %+v", e)
	}
}

func TestLookup_CacheHitSkipsHTTP(t *testing.T) {
	hits := 0
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		hits++
		_, _ = io.WriteString(w, fakeNVDBody)
	}))
	defer srv.Close()
	c, _ := NewClient(Config{CacheDir: t.TempDir()})
	c.baseURL = srv.URL

	_, _ = c.Lookup(context.Background(), "CVE-2024-1")
	_, _ = c.Lookup(context.Background(), "CVE-2024-1")
	if hits != 1 {
		t.Fatalf("second lookup should hit cache; got %d http calls", hits)
	}
}

func TestLookup_PersistsToDisk(t *testing.T) {
	dir := t.TempDir()

	// First client: populates disk cache.
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		_, _ = io.WriteString(w, fakeNVDBody)
	}))
	defer srv.Close()
	c1, _ := NewClient(Config{CacheDir: dir})
	c1.baseURL = srv.URL
	_, _ = c1.Lookup(context.Background(), "CVE-2024-X")

	// Second client, no HTTP: must still return the entry from disk.
	c2, _ := NewClient(Config{CacheDir: dir})
	c2.baseURL = "http://broken-invalid-host-never-reachable"
	e, err := c2.Lookup(context.Background(), "CVE-2024-X")
	if err != nil {
		t.Fatal(err)
	}
	if e.BaseScore != 9.8 {
		t.Fatalf("disk-cached entry should round-trip; got %+v", e)
	}

	// Also verify the file is where we expect.
	if _, err := os.Stat(filepath.Join(dir, "CVE-2024-X.json")); err != nil {
		t.Fatalf("disk cache file missing: %v", err)
	}
}

func TestSanityCheck_FlagsLargeMismatch(t *testing.T) {
	c, srv := newClientWithFakeNVD(t, fakeNVDBody) // NVD says 9.8
	defer srv.Close()
	_, delta, ok := c.SanityCheck(context.Background(), pipeline.ClassifiedFinding{
		CVEIDs: []string{"CVE-2024-X"}, CVSSScore: 4.0, // classifier said medium
	})
	if ok {
		t.Fatalf("5.8-point mismatch should flag; delta=%f", delta)
	}
	if delta < 5.0 {
		t.Fatalf("want large delta, got %f", delta)
	}
}

func TestSanityCheck_NoCVEIsNoOp(t *testing.T) {
	c, srv := newClientWithFakeNVD(t, fakeNVDBody)
	defer srv.Close()
	_, _, ok := c.SanityCheck(context.Background(), pipeline.ClassifiedFinding{CVSSScore: 5.0})
	if !ok {
		t.Fatal("no CVE means nothing to check — should return ok=true")
	}
}
