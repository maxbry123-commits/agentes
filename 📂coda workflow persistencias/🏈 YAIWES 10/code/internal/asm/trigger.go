package asm

import (
	"sync"
	"time"

	"github.com/google/uuid"
)

// TriggerEngine auto-creates campaigns when significant asset changes are detected.
type TriggerEngine struct {
	mu                 sync.Mutex
	campaignCounts     map[uuid.UUID][]time.Time // scopeID -> timestamps of triggered campaigns
	maxPerDay          int
	createCampaignFunc func(scopeID uuid.UUID, target string, diff *AssetDiff) error
}

// NewTriggerEngine creates a new trigger engine.
func NewTriggerEngine(maxPerDay int, createFn func(scopeID uuid.UUID, target string, diff *AssetDiff) error) *TriggerEngine {
	if maxPerDay <= 0 {
		maxPerDay = 3
	}
	return &TriggerEngine{
		campaignCounts:     make(map[uuid.UUID][]time.Time),
		maxPerDay:          maxPerDay,
		createCampaignFunc: createFn,
	}
}

// OnAssetChange is called when a significant diff is detected.
func (t *TriggerEngine) OnAssetChange(scopeID uuid.UUID, target string, diff *AssetDiff) error {
	if !diff.IsSignificant() {
		return nil
	}

	if !t.canTrigger(scopeID) {
		return nil // rate limited
	}

	t.recordTrigger(scopeID)

	return t.createCampaignFunc(scopeID, target, diff)
}

func (t *TriggerEngine) canTrigger(scopeID uuid.UUID) bool {
	t.mu.Lock()
	defer t.mu.Unlock()

	now := time.Now()
	cutoff := now.Add(-24 * time.Hour)

	// Clean old entries
	var recent []time.Time
	for _, ts := range t.campaignCounts[scopeID] {
		if ts.After(cutoff) {
			recent = append(recent, ts)
		}
	}
	t.campaignCounts[scopeID] = recent

	return len(recent) < t.maxPerDay
}

func (t *TriggerEngine) recordTrigger(scopeID uuid.UUID) {
	t.mu.Lock()
	defer t.mu.Unlock()

	t.campaignCounts[scopeID] = append(t.campaignCounts[scopeID], time.Now())
}
