package blackboard

import (
	"context"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/logger"
	"github.com/google/uuid"
	"go.uber.org/zap"
)

// LoggingBoard wraps a Board and emits a structured JSON log line for
// every mutation. Reads are not logged because they're high-volume and
// low-signal — subscribe the zap sink to INFO to see writes only.
//
// Use the Postgres or memory board as the inner for production or tests.
type LoggingBoard struct {
	inner Board
	log   *zap.Logger
}

// NewLoggingBoard wraps inner with structured logging. Passes through if
// inner is nil so tests can compose cheaply.
func NewLoggingBoard(inner Board) *LoggingBoard {
	return &LoggingBoard{inner: inner, log: logger.Get().With(zap.String("subsystem", "blackboard"))}
}

// Write logs the operation before delegating.
func (b *LoggingBoard) Write(ctx context.Context, f Finding, opts ...WriteOption) (uuid.UUID, error) {
	id, err := b.inner.Write(ctx, f, opts...)
	if err != nil {
		b.log.Warn("blackboard.write.failed",
			zap.String("agent", f.AgentName),
			zap.String("type", string(f.Type)),
			zap.String("target", f.Target),
			zap.Error(err))
		return id, err
	}
	b.log.Info("blackboard.write",
		zap.String("id", id.String()),
		zap.String("campaign_id", f.CampaignID.String()),
		zap.String("agent", f.AgentName),
		zap.String("type", string(f.Type)),
		zap.String("target", f.Target),
		zap.Float64("pheromone_base", f.PheromoneBase),
		zap.Int("half_life_sec", f.HalfLifeSec),
		zap.Int("data_bytes", len(f.Data)),
	)
	return id, nil
}

// Query passes through without logging (high-volume).
func (b *LoggingBoard) Query(ctx context.Context, p Predicate) ([]Finding, error) {
	return b.inner.Query(ctx, p)
}

// Subscribe passes through without logging.
func (b *LoggingBoard) Subscribe(ctx context.Context, p Predicate) (<-chan Finding, error) {
	return b.inner.Subscribe(ctx, p)
}

// Cursor passes through.
func (b *LoggingBoard) Cursor(ctx context.Context, campaignID uuid.UUID, agentName string) (uuid.UUID, error) {
	return b.inner.Cursor(ctx, campaignID, agentName)
}

// CommitCursor logs cursor commits at DEBUG.
func (b *LoggingBoard) CommitCursor(ctx context.Context, campaignID uuid.UUID, agentName string, findingID uuid.UUID) error {
	err := b.inner.CommitCursor(ctx, campaignID, agentName, findingID)
	b.log.Debug("blackboard.cursor.commit",
		zap.String("agent", agentName),
		zap.String("campaign_id", campaignID.String()),
		zap.String("cursor", findingID.String()),
		zap.Error(err))
	return err
}

// Pheromone passes through.
func (b *LoggingBoard) Pheromone(ctx context.Context, findingID uuid.UUID) (float64, error) {
	return b.inner.Pheromone(ctx, findingID)
}

// Supersede logs supersede events (they're rare and high-signal).
func (b *LoggingBoard) Supersede(ctx context.Context, oldID, newID uuid.UUID) error {
	err := b.inner.Supersede(ctx, oldID, newID)
	b.log.Info("blackboard.supersede",
		zap.String("old", oldID.String()),
		zap.String("new", newID.String()),
		zap.Error(err))
	return err
}

// Budget passes through.
func (b *LoggingBoard) Budget(ctx context.Context, campaignID uuid.UUID) (Budget, error) {
	return b.inner.Budget(ctx, campaignID)
}

// UpdateBudget logs at DEBUG so operators can audit token spend.
func (b *LoggingBoard) UpdateBudget(ctx context.Context, campaignID uuid.UUID, deltaHours float64, deltaTokens int64) error {
	err := b.inner.UpdateBudget(ctx, campaignID, deltaHours, deltaTokens)
	b.log.Debug("blackboard.budget.update",
		zap.String("campaign_id", campaignID.String()),
		zap.Float64("delta_hours", deltaHours),
		zap.Int64("delta_tokens", deltaTokens),
		zap.Error(err))
	return err
}

// SetBudgetLimits logs budget limit changes (important for audit).
func (b *LoggingBoard) SetBudgetLimits(ctx context.Context, campaignID uuid.UUID, maxHours float64, maxTokens int64) error {
	err := b.inner.SetBudgetLimits(ctx, campaignID, maxHours, maxTokens)
	b.log.Info("blackboard.budget.limits",
		zap.String("campaign_id", campaignID.String()),
		zap.Float64("max_hours", maxHours),
		zap.Int64("max_tokens", maxTokens),
		zap.Error(err))
	return err
}

// AgentBudget passes through.
func (b *LoggingBoard) AgentBudget(ctx context.Context, campaignID uuid.UUID, agent string) (AgentBudget, error) {
	return b.inner.AgentBudget(ctx, campaignID, agent)
}

// ChargeAgent logs at DEBUG (high volume per LLM call).
func (b *LoggingBoard) ChargeAgent(ctx context.Context, campaignID uuid.UUID, agent string, tokens int64) error {
	err := b.inner.ChargeAgent(ctx, campaignID, agent, tokens)
	b.log.Debug("blackboard.agent.charge",
		zap.String("agent", agent),
		zap.Int64("tokens", tokens),
		zap.Error(err))
	return err
}

// SetAgentBudget logs at INFO — important for audit.
func (b *LoggingBoard) SetAgentBudget(ctx context.Context, campaignID uuid.UUID, agent string, maxTokens, warnAt int64) error {
	err := b.inner.SetAgentBudget(ctx, campaignID, agent, maxTokens, warnAt)
	b.log.Info("blackboard.agent.budget.limits",
		zap.String("campaign_id", campaignID.String()),
		zap.String("agent", agent),
		zap.Int64("max_tokens", maxTokens),
		zap.Int64("warn_at", warnAt),
		zap.Error(err))
	return err
}
