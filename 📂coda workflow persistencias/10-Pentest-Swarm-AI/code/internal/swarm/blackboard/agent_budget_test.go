package blackboard

import (
	"context"
	"testing"

	"github.com/google/uuid"
)

func TestMemoryBoard_AgentBudget_Defaults(t *testing.T) {
	b := NewMemoryBoard(nil)
	ctx := context.Background()
	bud, err := b.AgentBudget(ctx, uuid.New(), "recon")
	if err != nil {
		t.Fatal(err)
	}
	if bud.MaxTokens == 0 || bud.WarnAtTokens == 0 {
		t.Fatalf("want default caps, got %+v", bud)
	}
	if bud.Exceeded() || bud.ShouldWarn() {
		t.Fatalf("fresh budget should not be exceeded or warned: %+v", bud)
	}
}

func TestMemoryBoard_ChargeAgent_WarnAndExceed(t *testing.T) {
	b := NewMemoryBoard(nil)
	ctx := context.Background()
	cid := uuid.New()
	_ = b.SetAgentBudget(ctx, cid, "exploit", 100, 80)

	// Below threshold — no warn.
	_ = b.ChargeAgent(ctx, cid, "exploit", 50)
	bud, _ := b.AgentBudget(ctx, cid, "exploit")
	if bud.ShouldWarn() || bud.Exceeded() {
		t.Fatalf("50/100 shouldn't warn: %+v", bud)
	}

	// Crosses soft threshold.
	_ = b.ChargeAgent(ctx, cid, "exploit", 35)
	bud, _ = b.AgentBudget(ctx, cid, "exploit")
	if !bud.Warned {
		t.Fatalf("85/100 should have flipped Warned: %+v", bud)
	}
	if bud.Exceeded() {
		t.Fatalf("85/100 shouldn't be exceeded: %+v", bud)
	}

	// Over the cap.
	_ = b.ChargeAgent(ctx, cid, "exploit", 20)
	bud, _ = b.AgentBudget(ctx, cid, "exploit")
	if !bud.Exceeded() {
		t.Fatalf("105/100 should be exceeded: %+v", bud)
	}
}

func TestMemoryBoard_SetAgentBudget_ClearsWarnedWhenRaised(t *testing.T) {
	b := NewMemoryBoard(nil)
	ctx := context.Background()
	cid := uuid.New()
	_ = b.SetAgentBudget(ctx, cid, "classifier", 100, 50)
	_ = b.ChargeAgent(ctx, cid, "classifier", 60)
	bud, _ := b.AgentBudget(ctx, cid, "classifier")
	if !bud.Warned {
		t.Fatal("should have warned at 60/50 soft")
	}
	// Raise soft threshold above current usage — warned resets.
	_ = b.SetAgentBudget(ctx, cid, "classifier", 200, 120)
	bud, _ = b.AgentBudget(ctx, cid, "classifier")
	if bud.Warned {
		t.Fatalf("raising threshold above usage should clear warned: %+v", bud)
	}
}
