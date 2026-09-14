package unit

import (
	"testing"

	apperrors "github.com/Armur-Ai/Pentest-Swarm-AI/internal/errors"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/pipeline"
	"github.com/google/uuid"
)

func TestStateMachine_ValidTransitions(t *testing.T) {
	campaign := &pipeline.Campaign{ID: uuid.New(), Status: pipeline.StatusPlanned}
	sm := pipeline.NewStateMachine(campaign, nil)

	steps := []pipeline.CampaignStatus{
		pipeline.StatusInitializing,
		pipeline.StatusRecon,
		pipeline.StatusClassifying,
		pipeline.StatusPlanning,
		pipeline.StatusExecuting,
		pipeline.StatusAdapting,
		pipeline.StatusReporting,
		pipeline.StatusComplete,
	}

	for _, step := range steps {
		if err := sm.Transition(step); err != nil {
			t.Fatalf("transition to %s failed: %v", step, err)
		}
		if sm.Status() != step {
			t.Fatalf("status = %s, want %s", sm.Status(), step)
		}
	}
}

func TestStateMachine_InvalidTransition(t *testing.T) {
	campaign := &pipeline.Campaign{ID: uuid.New(), Status: pipeline.StatusPlanned}
	sm := pipeline.NewStateMachine(campaign, nil)

	// Can't go from Planned directly to Recon
	err := sm.Transition(pipeline.StatusRecon)
	if err == nil {
		t.Fatal("expected error for invalid transition Planned → Recon")
	}
	if !apperrors.Is(err, apperrors.ErrInvalidTransition) {
		t.Errorf("expected ErrInvalidTransition, got: %v", err)
	}
}

func TestStateMachine_AbortFromAnyState(t *testing.T) {
	states := []pipeline.CampaignStatus{
		pipeline.StatusInitializing,
		pipeline.StatusRecon,
		pipeline.StatusClassifying,
		pipeline.StatusPlanning,
		pipeline.StatusExecuting,
		pipeline.StatusAdapting,
		pipeline.StatusReporting,
	}

	for _, state := range states {
		campaign := &pipeline.Campaign{ID: uuid.New(), Status: state}
		sm := pipeline.NewStateMachine(campaign, nil)

		if err := sm.Abort(); err != nil {
			t.Errorf("abort from %s failed: %v", state, err)
		}
		if sm.Status() != pipeline.StatusAborted {
			t.Errorf("status = %s after abort, want aborted", sm.Status())
		}
	}
}

func TestStateMachine_CompleteTimestamp(t *testing.T) {
	campaign := &pipeline.Campaign{ID: uuid.New(), Status: pipeline.StatusPlanned}
	sm := pipeline.NewStateMachine(campaign, nil)

	sm.Transition(pipeline.StatusInitializing)
	sm.Transition(pipeline.StatusRecon)

	if campaign.StartedAt == nil {
		t.Error("StartedAt should be set after entering Recon")
	}

	sm.Transition(pipeline.StatusClassifying)
	sm.Transition(pipeline.StatusPlanning)
	sm.Transition(pipeline.StatusReporting)
	sm.Transition(pipeline.StatusComplete)

	if campaign.CompletedAt == nil {
		t.Error("CompletedAt should be set after Complete")
	}
}
