// Package dashboard serves a live, self-contained web view of a running swarm
// campaign. When a scan starts it listens on a loopback port, prints the URL,
// and streams progress to the browser over Server-Sent Events — agents
// activating, findings being graded, attack chains, and the final report.
//
// It has zero external dependencies (stdlib HTTP + SSE, an embedded single-page
// UI with inline SVG charts), so it works fully offline / air-gapped, matching
// the project's local-first stance. Nothing here reaches the network except the
// viewer's own browser on localhost.
package dashboard

import (
	"context"
	"embed"
	"encoding/json"
	"fmt"
	"net"
	"net/http"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"time"
)

//go:embed index.html
var assets embed.FS

// Event is one message pushed to the browser over SSE. Kind selects how the UI
// renders it: "log" (feed line), "finding" (graded vuln), "status" (campaign
// lifecycle), "meta" (target/objective header), "spend" (running LLM cost).
type Event struct {
	Kind     string `json:"kind"`
	Ts       string `json:"ts,omitempty"`
	Type     string `json:"type,omitempty"`   // pipeline event type, for "log"
	Agent    string `json:"agent,omitempty"`  // which agent, for "log"
	Detail   string `json:"detail,omitempty"` // human text
	Severity string `json:"severity,omitempty"`
	Title    string `json:"title,omitempty"`
	Category string `json:"category,omitempty"`
	// Finding detail (for the click-to-read panel).
	Cvss        float64 `json:"cvss,omitempty"`
	Confidence  string  `json:"confidence,omitempty"`
	Description string  `json:"description,omitempty"`
	Status      string  `json:"status,omitempty"` // "running" | "complete", for "status"
	// Attack-chain fields ("chain" carries ChainID+ChainName+Steps; "chainstep"
	// carries ChainID+Step+Ok).
	ChainID   string      `json:"chainId,omitempty"`
	ChainName string      `json:"chainName,omitempty"`
	Steps     []ChainStep `json:"steps,omitempty"`
	Step      string      `json:"step,omitempty"`
	Ok        bool        `json:"ok,omitempty"`
}

// ChainStep is one step of an attack chain sent to the dashboard.
type ChainStep struct {
	Name      string `json:"name"`
	Technique string `json:"technique,omitempty"` // MITRE ATT&CK id
}

// Server is a running dashboard instance for one campaign.
type Server struct {
	httpSrv   *http.Server
	url       string
	reportDir string

	mu       sync.Mutex
	buffer   []Event // replayed to late-joining browsers
	clients  map[chan Event]struct{}
	seenFind map[string]struct{} // finding-title dedup for the live stream

	onStop  func() // killswitch callback (set via OnStop); fired by POST /api/stop
	stopped bool
}

// New builds a dashboard server. reportDir is where the campaign writes its
// report files; the dashboard serves the newest *.json from there as the final
// graded report once it appears.
func New(reportDir string) *Server {
	return &Server{
		reportDir: reportDir,
		clients:   make(map[chan Event]struct{}),
		seenFind:  make(map[string]struct{}),
	}
}

// Start binds a loopback port (preferring 7777, then 7778…, else an OS-chosen
// port) and begins serving. It returns the base URL to hand the user.
func (s *Server) Start() (string, error) {
	ln, err := listenLoopback()
	if err != nil {
		return "", err
	}
	mux := http.NewServeMux()
	mux.HandleFunc("/", s.handleIndex)
	mux.HandleFunc("/events", s.handleEvents)
	mux.HandleFunc("/api/report", s.handleReport)
	mux.HandleFunc("/api/stop", s.handleStop)
	s.httpSrv = &http.Server{Handler: mux}
	s.url = "http://" + ln.Addr().String()
	go func() { _ = s.httpSrv.Serve(ln) }()
	return s.url, nil
}

// listenLoopback tries a few friendly fixed ports before falling back to any
// free port, so the URL is stable across runs when possible.
func listenLoopback() (net.Listener, error) {
	for _, p := range []int{7777, 7778, 7799, 8899} {
		if ln, err := net.Listen("tcp", fmt.Sprintf("127.0.0.1:%d", p)); err == nil {
			return ln, nil
		}
	}
	return net.Listen("tcp", "127.0.0.1:0")
}

// URL returns the dashboard's base URL (valid after Start).
func (s *Server) URL() string { return s.url }

// OnStop registers the killswitch callback invoked when a viewer clicks the
// dashboard's Stop button (POST /api/stop). Typically wired to cancel the
// running campaign. Safe to call before or after Start.
func (s *Server) OnStop(fn func()) {
	s.mu.Lock()
	s.onStop = fn
	s.mu.Unlock()
}

// handleStop is the killswitch endpoint. It fires the registered stop callback
// at most once and tells connected browsers the run is being stopped.
func (s *Server) handleStop(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "POST only", http.StatusMethodNotAllowed)
		return
	}
	s.mu.Lock()
	fn := s.onStop
	already := s.stopped
	s.stopped = true
	s.mu.Unlock()

	if !already && fn != nil {
		fn()
	}
	s.PublishStatus("stopping")
	w.Header().Set("Content-Type", "application/json")
	_, _ = w.Write([]byte(`{"ok":true}`))
}

// Stop shuts the server down.
func (s *Server) Stop() {
	if s.httpSrv != nil {
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()
		_ = s.httpSrv.Shutdown(ctx)
	}
}

// Publish fans an event out to every connected browser and buffers it for
// late joiners. Safe for concurrent use.
func (s *Server) Publish(e Event) {
	s.mu.Lock()
	s.buffer = append(s.buffer, e)
	if len(s.buffer) > 2000 { // bound memory on a long campaign
		s.buffer = s.buffer[len(s.buffer)-2000:]
	}
	clients := make([]chan Event, 0, len(s.clients))
	for c := range s.clients {
		clients = append(clients, c)
	}
	s.mu.Unlock()
	for _, c := range clients {
		select {
		case c <- e:
		default: // drop for a slow client rather than block the campaign
		}
	}
}

// PublishFinding surfaces a graded finding to the live view, de-duplicated by
// title so the same vuln isn't listed twice as it flows through the board.
func (s *Server) PublishFinding(f Event) {
	s.mu.Lock()
	key := strings.ToLower(strings.TrimSpace(f.Title))
	if _, dup := s.seenFind[key]; dup {
		s.mu.Unlock()
		return
	}
	s.seenFind[key] = struct{}{}
	s.mu.Unlock()
	f.Kind = "finding"
	f.Ts = time.Now().Format("15:04:05")
	s.Publish(f)
}

// PublishStatus marks the campaign lifecycle ("running" / "complete").
func (s *Server) PublishStatus(status string) {
	s.Publish(Event{Kind: "status", Status: status})
}

func (s *Server) handleIndex(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/" {
		http.NotFound(w, r)
		return
	}
	b, err := assets.ReadFile("index.html")
	if err != nil {
		http.Error(w, "dashboard asset missing", http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	_, _ = w.Write(b)
}

// handleEvents is the SSE endpoint: it replays the buffer, then streams live
// events until the client disconnects.
func (s *Server) handleEvents(w http.ResponseWriter, r *http.Request) {
	flusher, ok := w.(http.Flusher)
	if !ok {
		http.Error(w, "streaming unsupported", http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")

	ch := make(chan Event, 256)
	s.mu.Lock()
	backlog := append([]Event(nil), s.buffer...)
	s.clients[ch] = struct{}{}
	s.mu.Unlock()
	defer func() {
		s.mu.Lock()
		delete(s.clients, ch)
		s.mu.Unlock()
	}()

	write := func(e Event) bool {
		b, _ := json.Marshal(e)
		if _, err := fmt.Fprintf(w, "data: %s\n\n", b); err != nil {
			return false
		}
		flusher.Flush()
		return true
	}
	for _, e := range backlog {
		if !write(e) {
			return
		}
	}
	keepAlive := time.NewTicker(15 * time.Second)
	defer keepAlive.Stop()
	for {
		select {
		case <-r.Context().Done():
			return
		case e := <-ch:
			if !write(e) {
				return
			}
		case <-keepAlive.C:
			if _, err := fmt.Fprintf(w, ": keep-alive\n\n"); err != nil {
				return
			}
			flusher.Flush()
		}
	}
}

// handleReport serves the newest JSON report from the campaign's output dir.
// Returns 204 until one exists, so the UI can poll and render when ready.
func (s *Server) handleReport(w http.ResponseWriter, r *http.Request) {
	path := s.newestReport()
	if path == "" {
		w.WriteHeader(http.StatusNoContent)
		return
	}
	b, err := os.ReadFile(path)
	if err != nil {
		w.WriteHeader(http.StatusNoContent)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	_, _ = w.Write(b)
}

// newestReport returns the most recently modified .json in the report dir.
func (s *Server) newestReport() string {
	if s.reportDir == "" {
		return ""
	}
	entries, err := os.ReadDir(s.reportDir)
	if err != nil {
		return ""
	}
	type f struct {
		path string
		mod  time.Time
	}
	var files []f
	for _, e := range entries {
		if e.IsDir() || !strings.HasSuffix(e.Name(), ".json") {
			continue
		}
		info, err := e.Info()
		if err != nil {
			continue
		}
		files = append(files, f{filepath.Join(s.reportDir, e.Name()), info.ModTime()})
	}
	if len(files) == 0 {
		return ""
	}
	sort.Slice(files, func(i, j int) bool { return files[i].mod.After(files[j].mod) })
	return files[0].path
}
