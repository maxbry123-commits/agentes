package blackboard

import (
	"context"
	"testing"
	"time"

	"github.com/google/uuid"
)

func newTestBoard(t *testing.T) (*MemoryBoard, uuid.UUID) {
	t.Helper()
	b := NewMemoryBoard(nil)
	return b, uuid.New()
}

func TestMemoryBoard_WriteQuery(t *testing.T) {
	b, campaign := newTestBoard(t)
	ctx := context.Background()

	id, err := b.Write(ctx, Finding{
		CampaignID: campaign,
		AgentName:  "recon",
		Type:       TypeSubdomain,
		Target:     "api.example.com",
		Data:       []byte(`{"ip":"1.2.3.4"}`),
	})
	if err != nil {
		t.Fatalf("Write: %v", err)
	}
	if id == uuid.Nil {
		t.Fatal("expected non-nil id")
	}

	got, err := b.Query(ctx, Predicate{Types: []FindingType{TypeSubdomain}})
	if err != nil {
		t.Fatalf("Query: %v", err)
	}
	if len(got) != 1 {
		t.Fatalf("want 1 finding, got %d", len(got))
	}
	if got[0].Target != "api.example.com" {
		t.Fatalf("unexpected target: %s", got[0].Target)
	}
	if got[0].Pheromone <= 0 || got[0].Pheromone > 1 {
		t.Fatalf("unexpected pheromone: %f", got[0].Pheromone)
	}
}

func TestMemoryBoard_RequiredFields(t *testing.T) {
	b, _ := newTestBoard(t)
	ctx := context.Background()
	_, err := b.Write(ctx, Finding{AgentName: "x", Type: TypeSubdomain})
	if err == nil {
		t.Fatal("expected error when campaign_id missing")
	}
}

func TestMemoryBoard_PheromoneDecay(t *testing.T) {
	now := time.Now()
	fake := now
	b := NewMemoryBoard(func() time.Time { return fake })

	campaign := uuid.New()
	_, err := b.Write(context.Background(), Finding{
		CampaignID: campaign, AgentName: "recon", Type: TypeSubdomain,
		Target: "x.com", PheromoneBase: 1.0, HalfLifeSec: 60,
	})
	if err != nil {
		t.Fatal(err)
	}

	got, _ := b.Query(context.Background(), Predicate{})
	if got[0].Pheromone < 0.99 {
		t.Fatalf("fresh finding pheromone should be ~1.0, got %f", got[0].Pheromone)
	}

	// Advance 60s = one half-life → pheromone should be ~0.5
	fake = now.Add(60 * time.Second)
	got, _ = b.Query(context.Background(), Predicate{})
	if got[0].Pheromone < 0.45 || got[0].Pheromone > 0.55 {
		t.Fatalf("after 1 half-life want ~0.5, got %f", got[0].Pheromone)
	}

	// Advance another half-life → ~0.25
	fake = now.Add(120 * time.Second)
	got, _ = b.Query(context.Background(), Predicate{})
	if got[0].Pheromone > 0.3 {
		t.Fatalf("after 2 half-lives want ~0.25, got %f", got[0].Pheromone)
	}
}

func TestMemoryBoard_MinPheromoneFilter(t *testing.T) {
	now := time.Now()
	fake := now
	b := NewMemoryBoard(func() time.Time { return fake })
	campaign := uuid.New()

	_, _ = b.Write(context.Background(), Finding{
		CampaignID: campaign, AgentName: "recon", Type: TypeSubdomain,
		Target: "fresh.com", PheromoneBase: 1.0, HalfLifeSec: 60,
	})
	// Advance 4 half-lives → this finding's pheromone is ~0.0625
	fake = now.Add(240 * time.Second)
	_, _ = b.Write(context.Background(), Finding{
		CampaignID: campaign, AgentName: "recon", Type: TypeSubdomain,
		Target: "stale.com", PheromoneBase: 1.0, HalfLifeSec: 60,
	})
	// Restore clock so the second one is fresh relative to its create time.
	fake = now.Add(240 * time.Second)

	got, _ := b.Query(context.Background(), Predicate{MinPheromone: 0.5})
	if len(got) != 1 || got[0].Target != "stale.com" {
		t.Fatalf("filter should keep only fresh finding, got %+v", got)
	}
}

func TestMemoryBoard_Subscribe(t *testing.T) {
	b, campaign := newTestBoard(t)
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	ch, err := b.Subscribe(ctx, Predicate{Types: []FindingType{TypeCVEMatch}})
	if err != nil {
		t.Fatal(err)
	}

	// Off-type writes should not deliver.
	_, _ = b.Write(ctx, Finding{
		CampaignID: campaign, AgentName: "recon", Type: TypeSubdomain, Target: "a.com",
	})
	// On-type write should deliver.
	id, _ := b.Write(ctx, Finding{
		CampaignID: campaign, AgentName: "classifier", Type: TypeCVEMatch, Target: "a.com",
	})

	select {
	case f := <-ch:
		if f.ID != id {
			t.Fatalf("unexpected id: %s vs %s", f.ID, id)
		}
	case <-time.After(200 * time.Millisecond):
		t.Fatal("subscribe timed out")
	}
}

func TestMemoryBoard_Supersede(t *testing.T) {
	b, campaign := newTestBoard(t)
	ctx := context.Background()
	old, _ := b.Write(ctx, Finding{
		CampaignID: campaign, AgentName: "classifier", Type: TypeCVEMatch, Target: "a.com",
	})
	_, err := b.Write(ctx, Finding{
		CampaignID: campaign, AgentName: "classifier", Type: TypeCVEMatch, Target: "a.com",
	}, Supersedes(old))
	if err != nil {
		t.Fatal(err)
	}
	got, _ := b.Query(ctx, Predicate{})
	if len(got) != 1 {
		t.Fatalf("expected 1 active finding (old superseded), got %d", len(got))
	}
}

func TestMemoryBoard_Cursor(t *testing.T) {
	b, campaign := newTestBoard(t)
	ctx := context.Background()
	a := uuid.New()
	if err := b.CommitCursor(ctx, campaign, "recon", a); err != nil {
		t.Fatal(err)
	}
	got, err := b.Cursor(ctx, campaign, "recon")
	if err != nil || got != a {
		t.Fatalf("cursor roundtrip mismatch: got %v err %v", got, err)
	}
	// Unknown agent → uuid.Nil, no error.
	got, err = b.Cursor(ctx, campaign, "unknown")
	if err != nil || got != uuid.Nil {
		t.Fatalf("missing cursor should return Nil; got %v err %v", got, err)
	}
}

func TestMemoryBoard_Budget(t *testing.T) {
	b, campaign := newTestBoard(t)
	ctx := context.Background()
	bud, err := b.Budget(ctx, campaign)
	if err != nil {
		t.Fatal(err)
	}
	if bud.MaxAgentHours == 0 || bud.MaxTokens == 0 {
		t.Fatal("expected default limits")
	}
	if err := b.UpdateBudget(ctx, campaign, 0.5, 50000); err != nil {
		t.Fatal(err)
	}
	bud, _ = b.Budget(ctx, campaign)
	if bud.AgentHoursUsed != 0.5 || bud.TokensUsed != 50000 {
		t.Fatalf("usage not tracked: %+v", bud)
	}
	if err := b.SetBudgetLimits(ctx, campaign, 0.1, 10); err != nil {
		t.Fatal(err)
	}
	bud, _ = b.Budget(ctx, campaign)
	if !bud.Exceeded() {
		t.Fatalf("expected exceeded after lowering limits: %+v", bud)
	}
}
