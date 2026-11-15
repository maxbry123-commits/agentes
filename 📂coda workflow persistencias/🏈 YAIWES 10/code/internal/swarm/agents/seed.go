// Package agents contains the swarm adapters that bridge the existing
// specialist agents (recon, classifier, exploit, report) into the
// blackboard + scheduler model. Each adapter implements swarm.Agent.
package agents

import (
	"context"
	"encoding/json"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/swarm/blackboard"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/swarm/tuning"
	"github.com/google/uuid"
)

// Seed writes the initial TARGET_REGISTERED finding that kicks the swarm off.
// Without a seed there is nothing on the board, so no trigger fires.
//
// Pheromone values come from tun — pass nil to get the baked-in defaults.
func Seed(ctx context.Context, board blackboard.Board, campaignID uuid.UUID, target, objective string, tun *tuning.Settings) error {
	if tun == nil {
		tun = tuning.Default()
	}
	data, _ := json.Marshal(map[string]any{
		"target":    target,
		"objective": objective,
	})
	base, half := tun.Lookup(blackboard.TypeTargetRegistered)
	_, err := board.Write(ctx, blackboard.Finding{
		CampaignID:    campaignID,
		AgentName:     "engine",
		Type:          blackboard.TypeTargetRegistered,
		Target:        target,
		Data:          data,
		PheromoneBase: base,
		HalfLifeSec:   half,
	})
	return err
}
