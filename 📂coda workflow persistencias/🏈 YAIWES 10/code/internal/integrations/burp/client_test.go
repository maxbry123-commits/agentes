package burp

import (
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

// buildFakeBurp stands up a minimal JSON-RPC 2.0 server that answers the
// three methods our client drives: initialize, tools/list, tools/call.
func buildFakeBurp(t *testing.T, toolResult any, isErr bool) *httptest.Server {
	t.Helper()
	return httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "method not allowed", 405)
			return
		}
		body, _ := io.ReadAll(r.Body)
		var req rpcRequest
		if err := json.Unmarshal(body, &req); err != nil {
			http.Error(w, err.Error(), 400)
			return
		}
		var resultJSON json.RawMessage
		switch req.Method {
		case "initialize":
			resultJSON = []byte(`{"protocolVersion":"2024-11-05"}`)
		case "tools/list":
			resultJSON = []byte(`{"tools":[{"name":"burp_active_scan","description":"start an active scan","inputSchema":{}}]}`)
		case "tools/call":
			payload, _ := json.Marshal(CallResult{
				Content: []ContentBlock{{Type: "text", Text: toStringJSON(toolResult)}},
				IsError: isErr,
			})
			resultJSON = payload
		default:
			http.Error(w, "unknown method: "+req.Method, 400)
			return
		}
		_ = json.NewEncoder(w).Encode(rpcResponse{JSONRPC: "2.0", ID: req.ID, Result: resultJSON})
	}))
}

func toStringJSON(v any) string {
	b, _ := json.Marshal(v)
	return string(b)
}

func TestClient_Ping(t *testing.T) {
	srv := buildFakeBurp(t, nil, false)
	defer srv.Close()

	c := NewClient(Config{Endpoint: srv.URL})
	if err := c.Ping(context.Background()); err != nil {
		t.Fatal(err)
	}
}

func TestClient_ListTools(t *testing.T) {
	srv := buildFakeBurp(t, nil, false)
	defer srv.Close()

	c := NewClient(Config{Endpoint: srv.URL})
	tools, err := c.ListTools(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if len(tools) != 1 || tools[0].Name != ToolActiveScan {
		t.Fatalf("unexpected tools: %+v", tools)
	}
}

func TestClient_StartActiveScan(t *testing.T) {
	srv := buildFakeBurp(t, "scan-1234", false)
	defer srv.Close()

	c := NewClient(Config{Endpoint: srv.URL})
	id, err := c.StartActiveScan(context.Background(), "https://example.com/")
	if err != nil {
		t.Fatal(err)
	}
	// Fake server wraps the tool result as JSON so the text block contains "scan-1234".
	if !strings.Contains(id, "scan-1234") {
		t.Fatalf("want id containing scan-1234, got %q", id)
	}
}

func TestClient_GetIssues(t *testing.T) {
	srv := buildFakeBurp(t, []map[string]any{
		{"name": "SQL injection", "severity": "High", "confidence": "Firm"},
		{"name": "XSS (reflected)", "severity": "Medium", "confidence": "Certain"},
	}, false)
	defer srv.Close()

	c := NewClient(Config{Endpoint: srv.URL})
	issues, err := c.GetIssues(context.Background(), "scan-1234")
	if err != nil {
		t.Fatal(err)
	}
	if len(issues) != 2 {
		t.Fatalf("want 2 issues, got %d", len(issues))
	}
	if issues[0]["name"] != "SQL injection" {
		t.Errorf("first issue name: %v", issues[0]["name"])
	}
}

func TestClient_BearerAuth(t *testing.T) {
	var saw string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		saw = r.Header.Get("Authorization")
		_ = json.NewEncoder(w).Encode(rpcResponse{JSONRPC: "2.0", ID: 1, Result: []byte(`{}`)})
	}))
	defer srv.Close()

	c := NewClient(Config{Endpoint: srv.URL, APIKey: "s3cret"})
	_ = c.Ping(context.Background())
	if saw != "Bearer s3cret" {
		t.Fatalf("bearer token not forwarded; saw %q", saw)
	}
}
