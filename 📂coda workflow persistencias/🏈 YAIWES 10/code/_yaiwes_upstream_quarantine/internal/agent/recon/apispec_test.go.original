package recon

import (
	"context"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

// openAPIStub serves a tiny hand-written OpenAPI v3 spec at /openapi.json,
// documenting a collection endpoint and an item endpoint with a path
// parameter — enough to exercise method extraction, parameter extraction,
// and the interesting-operation heuristics (write verb + {id}-style path).
func openAPIStub() *httptest.Server {
	const spec = `{
		"openapi": "3.0.1",
		"info": {"title": "Widget API", "version": "1.0"},
		"paths": {
			"/api/widgets": {
				"get": {
					"summary": "List all widgets",
					"parameters": [{"name": "limit", "in": "query"}]
				},
				"post": {
					"operationId": "createWidget",
					"summary": "Create a widget"
				}
			},
			"/api/widgets/{id}": {
				"get": {
					"operationId": "getWidget",
					"parameters": [{"name": "id", "in": "path"}]
				},
				"delete": {
					"operationId": "deleteWidget",
					"parameters": [{"name": "id", "in": "path"}]
				}
			}
		}
	}`

	mux := http.NewServeMux()
	mux.HandleFunc("/openapi.json", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(spec))
	})
	// Everything else 404s, like a real server with no spec at other locations.
	return httptest.NewServer(mux)
}

func TestDiscoverOpenAPI_ParsesV3Spec(t *testing.T) {
	srv := openAPIStub()
	defer srv.Close()

	eps := DiscoverOpenAPI(context.Background(), srv.URL, nil)
	if len(eps) != 4 {
		t.Fatalf("expected 4 endpoints (2 paths x 2 methods each), got %d: %+v", len(eps), eps)
	}

	byKey := make(map[string]struct {
		found bool
		idx   int
	})
	for i, e := range eps {
		byKey[e.Method+" "+e.URL] = struct {
			found bool
			idx   int
		}{true, i}
	}

	wantURL := srv.URL + "/api/widgets"
	wantItemURL := srv.URL + "/api/widgets/{id}"

	get, ok := byKey["GET "+wantURL]
	if !ok {
		t.Fatalf("expected GET %s in results; got %+v", wantURL, eps)
	}
	if eps[get.idx].Interesting {
		t.Error("plain GET on a collection should not be marked Interesting")
	}
	if len(eps[get.idx].Parameters) != 1 || eps[get.idx].Parameters[0] != "limit" {
		t.Errorf("expected GET params [limit], got %v", eps[get.idx].Parameters)
	}

	post, ok := byKey["POST "+wantURL]
	if !ok {
		t.Fatalf("expected POST %s in results; got %+v", wantURL, eps)
	}
	if !eps[post.idx].Interesting {
		t.Error("POST should be marked Interesting (write operation)")
	}
	if want := "createWidget"; !strings.Contains(eps[post.idx].Notes, want) {
		t.Errorf("expected notes to mention operationId %q, got %q", want, eps[post.idx].Notes)
	}

	getItem, ok := byKey["GET "+wantItemURL]
	if !ok {
		t.Fatalf("expected GET %s in results; got %+v", wantItemURL, eps)
	}
	if !eps[getItem.idx].Interesting {
		t.Error("GET on a {id}-style path should be marked Interesting (BOLA/IDOR candidate)")
	}
	if len(eps[getItem.idx].Parameters) != 1 || eps[getItem.idx].Parameters[0] != "id" {
		t.Errorf("expected item GET params [id], got %v", eps[getItem.idx].Parameters)
	}

	del, ok := byKey["DELETE "+wantItemURL]
	if !ok {
		t.Fatalf("expected DELETE %s in results; got %+v", wantItemURL, eps)
	}
	if !eps[del.idx].Interesting {
		t.Error("DELETE should be marked Interesting (write operation)")
	}
	if want := "OpenAPI"; !strings.Contains(eps[del.idx].Notes, want) {
		t.Errorf("expected notes to mention the spec dialect, got %q", eps[del.idx].Notes)
	}
}

func TestDiscoverOpenAPI_NoSpecReturnsNil(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusNotFound)
	}))
	defer srv.Close()

	if eps := DiscoverOpenAPI(context.Background(), srv.URL, nil); eps != nil {
		t.Errorf("expected nil for a target with no spec, got %+v", eps)
	}
}

func TestDiscoverOpenAPI_EmptyTarget(t *testing.T) {
	if eps := DiscoverOpenAPI(context.Background(), "", nil); eps != nil {
		t.Errorf("expected nil for empty target, got %v", eps)
	}
}
