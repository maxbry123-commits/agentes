package scope

import (
	"context"
	"os"
	"sync"
	"sync/atomic"
	"time"

	"go.yaml.in/yaml/v3"
)

// Watcher keeps an in-memory copy of a scope.yaml file up-to-date by
// re-reading it at a fixed interval. Tool adapters can ask the watcher
// for the current scope instead of pinning a stale snapshot at campaign
// start — so if a program removes an asset mid-campaign the swarm drops
// it within one tick.
//
// The watcher publishes changes through a channel so a scheduler can
// emit a 'scope_drift' event when the underlying file mutates.
type Watcher struct {
	path     string
	interval time.Duration
	current  atomic.Pointer[ScopeDefinition]
	changes  chan Diff
	wg       sync.WaitGroup
	stop     chan struct{}
}

// NewWatcher builds a Watcher for path, polling every interval.
// Interval <= 0 defaults to 10s.
func NewWatcher(path string, interval time.Duration) *Watcher {
	if interval <= 0 {
		interval = 10 * time.Second
	}
	w := &Watcher{
		path:     path,
		interval: interval,
		changes:  make(chan Diff, 4),
		stop:     make(chan struct{}),
	}
	// Best-effort initial read so Current() doesn't return nil.
	if def, err := readFromDisk(path); err == nil {
		w.current.Store(def)
	} else {
		w.current.Store(&ScopeDefinition{})
	}
	return w
}

// Start spins up the polling goroutine. Safe to call at most once.
func (w *Watcher) Start(ctx context.Context) {
	w.wg.Add(1)
	go func() {
		defer w.wg.Done()
		t := time.NewTicker(w.interval)
		defer t.Stop()
		for {
			select {
			case <-ctx.Done():
				return
			case <-w.stop:
				return
			case <-t.C:
				w.reload()
			}
		}
	}()
}

// Stop halts the watcher + drains. Idempotent.
func (w *Watcher) Stop() {
	select {
	case <-w.stop:
	default:
		close(w.stop)
	}
	w.wg.Wait()
}

// Current returns the most recent successfully-parsed scope.
func (w *Watcher) Current() ScopeDefinition {
	if v := w.current.Load(); v != nil {
		return *v
	}
	return ScopeDefinition{}
}

// Changes is a non-blocking channel emitting Diffs every time the file
// mutates. Use in the scheduler to surface 'scope drift' warnings.
func (w *Watcher) Changes() <-chan Diff { return w.changes }

func (w *Watcher) reload() {
	next, err := readFromDisk(w.path)
	if err != nil {
		return
	}
	prev := w.current.Load()
	if prev != nil {
		d := Compare(*prev, *next)
		if d.HasChanges() {
			select {
			case w.changes <- d:
			default:
				// Full — drop. Scheduler consumers are expected to drain promptly.
			}
		}
	}
	w.current.Store(next)
}

func readFromDisk(path string) (*ScopeDefinition, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var def ScopeDefinition
	if err := yaml.Unmarshal(data, &def); err != nil {
		return nil, err
	}
	return &def, nil
}
