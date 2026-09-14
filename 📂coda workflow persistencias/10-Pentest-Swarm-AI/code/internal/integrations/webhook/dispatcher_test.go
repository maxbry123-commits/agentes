package webhook

import (
	"context"
	"io"
	"net/http"
	"net/http/httptest"
	"sync/atomic"
	"testing"
	"time"
)

func TestSend_DeliversSignedBody(t *testing.T) {
	var gotSig, gotBody string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		body, _ := io.ReadAll(r.Body)
		gotBody = string(body)
		gotSig = r.Header.Get("X-PentestSwarm-Signature")
		w.WriteHeader(200)
	}))
	defer srv.Close()

	d := New(Config{Endpoint: srv.URL, Secret: "swarm-secret"})
	err := d.SendSync(context.Background(), map[string]string{"hello": "world"})
	if err != nil {
		t.Fatal(err)
	}
	if gotBody != `{"hello":"world"}` {
		t.Errorf("body: %q", gotBody)
	}
	if !Verify([]byte("swarm-secret"), []byte(gotBody), gotSig) {
		t.Errorf("signature %q didn't verify", gotSig)
	}
}

func TestSend_RetryOn500(t *testing.T) {
	var attempts int32
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if atomic.AddInt32(&attempts, 1) < 3 {
			w.WriteHeader(500)
			return
		}
		w.WriteHeader(200)
	}))
	defer srv.Close()

	d := New(Config{Endpoint: srv.URL, Secret: "x", MaxTries: 5})
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	if err := d.SendSync(ctx, map[string]string{"x": "y"}); err != nil {
		t.Fatal(err)
	}
	if attempts != 3 {
		t.Fatalf("want 3 attempts, got %d", attempts)
	}
}

func TestSend_4xxIsPermanent(t *testing.T) {
	var attempts int32
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		atomic.AddInt32(&attempts, 1)
		w.WriteHeader(400)
	}))
	defer srv.Close()

	d := New(Config{Endpoint: srv.URL, Secret: "x", MaxTries: 5, DLQSize: 2})
	_ = d.SendSync(context.Background(), map[string]string{"x": "y"})
	// 4xx should NOT retry 5 times.
	if atomic.LoadInt32(&attempts) > 2 {
		t.Fatalf("4xx should not retry heavily; got %d attempts", attempts)
	}
	select {
	case <-d.DLQ():
		// expected — permanent failure goes to DLQ
	case <-time.After(100 * time.Millisecond):
		t.Fatal("4xx body should have landed in DLQ")
	}
}

func TestVerify_Correctness(t *testing.T) {
	body := []byte(`{"x":"y"}`)
	sig := "sha256=" + sign([]byte("key"), body)
	if !Verify([]byte("key"), body, sig) {
		t.Fatal("valid sig didn't verify")
	}
	if Verify([]byte("wrong"), body, sig) {
		t.Fatal("bad key verified")
	}
	if Verify([]byte("key"), []byte(`{"x":"z"}`), sig) {
		t.Fatal("tampered body verified")
	}
}
