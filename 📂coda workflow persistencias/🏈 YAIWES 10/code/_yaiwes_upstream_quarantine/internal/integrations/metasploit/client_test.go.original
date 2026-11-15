package metasploit

import (
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"testing"
)

// fakeMsfrpcd is a minimal msfrpcd stand-in that answers the three methods
// our client drives.
func fakeMsfrpcd(t *testing.T) *httptest.Server {
	t.Helper()
	return httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		body, _ := io.ReadAll(r.Body)
		var args []any
		_ = json.Unmarshal(body, &args)
		if len(args) == 0 {
			http.Error(w, "no method", 400)
			return
		}
		method, _ := args[0].(string)
		switch method {
		case "auth.login":
			_ = json.NewEncoder(w).Encode(map[string]any{"result": "success", "token": "TEMP_TOKEN"})
		case "module.execute":
			_ = json.NewEncoder(w).Encode(map[string]any{"job_id": 42, "uuid": "abc"})
		case "session.list":
			_ = json.NewEncoder(w).Encode(map[string]any{
				"1": map[string]any{"type": "meterpreter", "target_host": "10.0.0.1"},
			})
		case "session.stop", "job.stop":
			_ = json.NewEncoder(w).Encode(map[string]any{"result": "success"})
		default:
			http.Error(w, "unknown method "+method, 400)
		}
	}))
}

func TestLogin_CachesToken(t *testing.T) {
	srv := fakeMsfrpcd(t)
	defer srv.Close()
	c := NewClient(Config{Endpoint: srv.URL, User: "msf", Pass: "pw"})
	if err := c.Login(context.Background()); err != nil {
		t.Fatal(err)
	}
	if c.token != "TEMP_TOKEN" {
		t.Fatalf("token not cached, got %q", c.token)
	}
}

func TestExecuteModule(t *testing.T) {
	srv := fakeMsfrpcd(t)
	defer srv.Close()
	c := NewClient(Config{Endpoint: srv.URL, User: "msf", Pass: "pw"})
	res, err := c.ExecuteModule(context.Background(), "exploit", "unix/ftp/vsftpd_234_backdoor", map[string]any{"RHOSTS": "10.0.0.1"})
	if err != nil {
		t.Fatal(err)
	}
	if res.JobID != 42 {
		t.Fatalf("want job_id 42, got %+v", res)
	}
}

func TestListAndStopSession(t *testing.T) {
	srv := fakeMsfrpcd(t)
	defer srv.Close()
	c := NewClient(Config{Endpoint: srv.URL, User: "msf", Pass: "pw"})
	sessions, err := c.ListSessions(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if len(sessions) != 1 {
		t.Fatalf("want 1 session, got %d", len(sessions))
	}
	if err := c.StopSession(context.Background(), 1); err != nil {
		t.Fatal(err)
	}
}

func TestStopJob(t *testing.T) {
	srv := fakeMsfrpcd(t)
	defer srv.Close()
	c := NewClient(Config{Endpoint: srv.URL, User: "msf", Pass: "pw"})
	if err := c.StopJob(context.Background(), 42); err != nil {
		t.Fatal(err)
	}
}

func TestTokenRefreshOn401(t *testing.T) {
	var calls int
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		calls++
		body, _ := io.ReadAll(r.Body)
		var args []any
		_ = json.Unmarshal(body, &args)
		if len(args) == 0 {
			http.Error(w, "no args", 400)
			return
		}
		method, _ := args[0].(string)
		// The first authenticated call returns 401, forcing a re-login.
		if method == "session.list" && calls == 2 {
			w.WriteHeader(http.StatusUnauthorized)
			return
		}
		switch method {
		case "auth.login":
			_ = json.NewEncoder(w).Encode(map[string]any{"token": "TKN-v" + string(rune('0'+calls))})
		case "session.list":
			_ = json.NewEncoder(w).Encode(map[string]any{})
		}
	}))
	defer srv.Close()

	c := NewClient(Config{Endpoint: srv.URL, User: "msf", Pass: "pw"})
	_ = c.Login(context.Background())
	if _, err := c.ListSessions(context.Background()); err != nil {
		t.Fatal(err)
	}
	if calls < 3 {
		t.Fatalf("expected at least 3 calls (login, session.list -> 401, re-login, session.list); got %d", calls)
	}
}
