package engine

import (
	"context"
	"os"
	"testing"
	"time"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/pipeline"
)

// The demo replay must emit a full offline campaign: 4 graded findings, attack
// chains, a probe fan-out, and a completion milestone — without any network.
func TestRunDemoReplay(t *testing.T) {
	os.Setenv("PENTESTSWARM_DEMO_SPEED", "60") // run fast
	defer os.Unsetenv("PENTESTSWARM_DEMO_SPEED")

	counts := map[pipeline.EventType]int{}
	var findings int
	err := RunDemoReplay(context.Background(), CampaignConfig{}, func(e pipeline.CampaignEvent) {
		counts[e.EventType]++
		if e.EventType == pipeline.EventFindingDiscovered {
			findings++
		}
	})
	if err != nil {
		t.Fatalf("RunDemoReplay: %v", err)
	}
	if findings != 4 {
		t.Errorf("want 4 findings, got %d", findings)
	}
	for _, want := range []pipeline.EventType{
		pipeline.EventEndpointDiscovered, pipeline.EventChainStarted, pipeline.EventChainStep,
		pipeline.EventProbe, pipeline.EventFindingDiscovered, pipeline.EventMilestone, pipeline.EventStateChange,
	} {
		if counts[want] == 0 {
			t.Errorf("expected at least one %s event", want)
		}
	}
	if counts[pipeline.EventProbe] < 20 {
		t.Errorf("expected a probe fan-out (>=20), got %d", counts[pipeline.EventProbe])
	}
}

// Cancelling the context stops the replay promptly (killswitch / TUI quit).
func TestRunDemoReplayCancels(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	cancel() // already cancelled
	done := make(chan struct{})
	go func() { RunDemoReplay(ctx, CampaignConfig{}, func(pipeline.CampaignEvent) {}); close(done) }()
	select {
	case <-done:
	case <-time.After(2 * time.Second):
		t.Fatal("RunDemoReplay did not stop on cancelled context")
	}
}
