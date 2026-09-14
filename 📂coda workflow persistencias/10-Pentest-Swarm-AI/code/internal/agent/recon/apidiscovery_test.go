package recon

import (
	"context"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/pipeline"
)

// crapiStub stands in for a live crAPI web tier: it answers the fingerprint
// routes the way crAPI does (login 400 on a bad body, posts/recent 401
// unauthenticated) and 404s everything else.
func crapiStub() *httptest.Server {
	mux := http.NewServeMux()
	mux.HandleFunc("/identity/api/auth/login", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusBadRequest)
	})
	mux.HandleFunc("/community/api/v2/community/posts/recent", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusUnauthorized)
	})
	// Default: 404 (unknown route), like crAPI's gateway.
	return httptest.NewServer(mux)
}

func TestDiscoverAPISurface_CrapiMatch(t *testing.T) {
	srv := crapiStub()
	defer srv.Close()

	eps := DiscoverAPISurface(context.Background(), srv.URL, nil)
	if len(eps) == 0 {
		t.Fatal("expected crAPI profile to match and emit endpoints, got none")
	}

	// The flagship BOLA endpoint must be present, templated on the captured
	// victim vehicle id, and flagged interesting so it surfaces to the exploit
	// agent quickly.
	var bola *pipeline.EndpointRecord
	for i := range eps {
		if strings.Contains(eps[i].URL, "/vehicle/{{victim_vehicle}}/location") {
			bola = &eps[i]
			break
		}
	}
	if bola == nil {
		t.Fatalf("BOLA vehicle-location endpoint not emitted; got %d endpoints", len(eps))
	}
	if !bola.Interesting {
		t.Error("BOLA endpoint should be marked Interesting")
	}
	if !strings.Contains(bola.Notes, "BOLA") {
		t.Error("BOLA endpoint notes should describe the attack")
	}

	// Auth endpoints must be discoverable so the exploit agent can build the
	// login → capture-token chain.
	var haveSignup, haveLogin bool
	for _, e := range eps {
		if strings.HasSuffix(e.URL, "/identity/api/auth/signup") {
			haveSignup = true
		}
		if strings.HasSuffix(e.URL, "/identity/api/auth/login") {
			haveLogin = true
		}
	}
	if !haveSignup || !haveLogin {
		t.Errorf("expected signup+login endpoints; signup=%v login=%v", haveSignup, haveLogin)
	}
}

func TestDiscoverPlaybooks_CrapiLibrary(t *testing.T) {
	srv := crapiStub()
	defer srv.Close()

	pbs := DiscoverPlaybooks(context.Background(), srv.URL, nil)
	if len(pbs) < 3 {
		t.Fatalf("expected the crAPI playbook library (>=3 chains), got %d", len(pbs))
	}
	// Each playbook must be a complete, runnable chain that opens with the
	// register+login auth bootstrap and carries a proof step.
	want := map[string]bool{"BOLA": false, "excessive data exposure": false, "NoSQL injection": false}
	for _, pb := range pbs {
		if len(pb.Steps) < 3 {
			t.Errorf("playbook %q too short (%d steps)", pb.Name, len(pb.Steps))
		}
		if !strings.Contains(pb.Steps[0].Command, "/identity/api/auth/signup") {
			t.Errorf("playbook %q should open with signup", pb.Name)
		}
		for k := range want {
			if strings.Contains(pb.Name, k) {
				want[k] = true
			}
		}
	}
	for k, ok := range want {
		if !ok {
			t.Errorf("expected a playbook covering %q", k)
		}
	}
}

func TestDiscoverAPISurface_NoMatchOnUnrelatedTarget(t *testing.T) {
	// A server that 404s the signature routes must not trigger the profile.
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusNotFound)
	}))
	defer srv.Close()

	if eps := DiscoverAPISurface(context.Background(), srv.URL, nil); len(eps) != 0 {
		t.Errorf("expected no endpoints for a non-crAPI target, got %d", len(eps))
	}
}

func TestDiscoverAPISurface_EmptyTarget(t *testing.T) {
	if eps := DiscoverAPISurface(context.Background(), "", nil); eps != nil {
		t.Errorf("expected nil for empty target, got %v", eps)
	}
}

func TestMergeEndpoints_DedupsOnMethodAndURL(t *testing.T) {
	existing := []pipeline.EndpointRecord{
		{URL: "http://x/a", Method: "GET", StatusCode: 200},
	}
	discovered := []pipeline.EndpointRecord{
		{URL: "http://x/a", Method: "GET", Notes: "dup — should be skipped"},
		{URL: "http://x/a", Method: "POST", Notes: "different method — kept"},
		{URL: "http://x/b", Method: "GET", Notes: "new — kept"},
	}
	merged := mergeEndpoints(existing, discovered)
	if len(merged) != 3 {
		t.Fatalf("expected 3 endpoints after merge, got %d", len(merged))
	}
	// The pre-existing GET /a keeps its status code (crawler data wins).
	if merged[0].StatusCode != 200 {
		t.Errorf("existing endpoint should be preserved, got %+v", merged[0])
	}
}

func TestMergeEndpoints_EmptyMethodTreatedAsGET(t *testing.T) {
	existing := []pipeline.EndpointRecord{{URL: "http://x/a", Method: ""}}
	discovered := []pipeline.EndpointRecord{{URL: "http://x/a", Method: "GET"}}
	if merged := mergeEndpoints(existing, discovered); len(merged) != 1 {
		t.Errorf("empty method should collide with GET; got %d endpoints", len(merged))
	}
}
