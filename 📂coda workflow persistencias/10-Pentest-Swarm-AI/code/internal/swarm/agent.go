// Package swarm contains the scheduler and agent contract that together
// replace the sequential 5-phase runner with a stigmergic swarm.
//
// An Agent is a long-running worker that reacts to findings on the blackboard.
// Agents declare a Trigger predicate; the scheduler subscribes and dispatches
// findings that match. There is no central planner — coordination emerges from
// the pheromone-weighted shared state agents read and write.
package swarm

import (
	"context"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/swarm/blackboard"
)

// Agent is a swarm participant. Implementations are expected to be
// stateless between Handle calls — any state that must persist across
// iterations belongs on the blackboard.
type Agent interface {
	// Name is the stable identifier for cursor / budget attribution.
	// Must be unique within a campaign.
	Name() string

	// Trigger is the predicate the scheduler subscribes with. Agents
	// return findings that match this predicate.
	Trigger() blackboard.Predicate

	// MaxConcurrency is the upper bound on parallel Handle calls for
	// this agent. Zero means 1 (serial).
	MaxConcurrency() int

	// Handle processes one finding. Returning an error emits an
	// AGENT_ERROR finding to the blackboard but does not abort the
	// campaign; the scheduler continues dispatching.
	Handle(ctx context.Context, f blackboard.Finding, board blackboard.Board) error
}

// NamedPredicate is a simple helper for small one-off agents.
type NamedPredicate struct {
	AgentName string
	Pred      blackboard.Predicate
	Parallel  int
	Fn        func(ctx context.Context, f blackboard.Finding, board blackboard.Board) error
}

// Name implements Agent.
func (n NamedPredicate) Name() string { return n.AgentName }

// Trigger implements Agent.
func (n NamedPredicate) Trigger() blackboard.Predicate { return n.Pred }

// MaxConcurrency implements Agent.
func (n NamedPredicate) MaxConcurrency() int {
	if n.Parallel <= 0 {
		return 1
	}
	return n.Parallel
}

// Handle implements Agent.
func (n NamedPredicate) Handle(ctx context.Context, f blackboard.Finding, board blackboard.Board) error {
	if n.Fn == nil {
		return nil
	}
	return n.Fn(ctx, f, board)
}
