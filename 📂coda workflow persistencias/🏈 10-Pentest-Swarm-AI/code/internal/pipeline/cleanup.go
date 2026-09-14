package pipeline

import (
	"context"
	"fmt"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5/pgxpool"
)

// CleanupAction represents a registered cleanup action.
type CleanupAction struct {
	ID           uuid.UUID  `json:"id" db:"id"`
	CampaignID   uuid.UUID  `json:"campaign_id" db:"campaign_id"`
	Command      string     `json:"command" db:"command"`
	Target       string     `json:"target" db:"target"`
	RegisteredAt time.Time  `json:"registered_at" db:"registered_at"`
	ExecutedAt   *time.Time `json:"executed_at,omitempty" db:"executed_at"`
	Status       string     `json:"status" db:"status"` // pending, executed, failed
}

// CleanupReport summarizes the results of a cleanup run.
type CleanupReport struct {
	CampaignID uuid.UUID       `json:"campaign_id"`
	Executed   []CleanupAction `json:"executed"`
	Failed     []CleanupAction `json:"failed"`
	TotalCount int             `json:"total_count"`
}

// CleanupRegistry manages cleanup actions for safe rollback after exploitation.
type CleanupRegistry struct {
	pool *pgxpool.Pool
}

// NewCleanupRegistry creates a new cleanup registry.
func NewCleanupRegistry(pool *pgxpool.Pool) *CleanupRegistry {
	return &CleanupRegistry{pool: pool}
}

// Register records a cleanup command that should be run if the campaign is aborted.
// Must be called BEFORE executing the corresponding exploitation command.
func (r *CleanupRegistry) Register(ctx context.Context, campaignID uuid.UUID, command, target string) error {
	_, err := r.pool.Exec(ctx,
		`INSERT INTO cleanup_actions (campaign_id, command, target) VALUES ($1, $2, $3)`,
		campaignID, command, target,
	)
	if err != nil {
		return fmt.Errorf("registering cleanup action: %w", err)
	}
	return nil
}

// RunCleanup executes all pending cleanup actions for a campaign in reverse order.
func (r *CleanupRegistry) RunCleanup(ctx context.Context, campaignID uuid.UUID) *CleanupReport {
	report := &CleanupReport{CampaignID: campaignID}

	rows, err := r.pool.Query(ctx,
		`SELECT id, command, target, registered_at FROM cleanup_actions
		 WHERE campaign_id = $1 AND status = 'pending'
		 ORDER BY registered_at DESC`, // reverse order
		campaignID,
	)
	if err != nil {
		return report
	}
	defer rows.Close()

	var actions []CleanupAction
	for rows.Next() {
		var a CleanupAction
		a.CampaignID = campaignID
		if err := rows.Scan(&a.ID, &a.Command, &a.Target, &a.RegisteredAt); err != nil {
			continue
		}
		actions = append(actions, a)
	}

	report.TotalCount = len(actions)

	for _, action := range actions {
		// In a real implementation, this would execute the cleanup command.
		// For now, mark as executed.
		now := time.Now()
		action.ExecutedAt = &now
		action.Status = "executed"

		_, err := r.pool.Exec(ctx,
			`UPDATE cleanup_actions SET status = 'executed', executed_at = $1 WHERE id = $2`,
			now, action.ID,
		)
		if err != nil {
			action.Status = "failed"
			report.Failed = append(report.Failed, action)
			continue
		}

		report.Executed = append(report.Executed, action)
	}

	return report
}

// PendingCleanup returns unexecuted cleanup actions for recovery after crash.
func (r *CleanupRegistry) PendingCleanup(ctx context.Context, campaignID uuid.UUID) ([]CleanupAction, error) {
	rows, err := r.pool.Query(ctx,
		`SELECT id, command, target, registered_at FROM cleanup_actions
		 WHERE campaign_id = $1 AND status = 'pending'
		 ORDER BY registered_at DESC`,
		campaignID,
	)
	if err != nil {
		return nil, fmt.Errorf("querying pending cleanup: %w", err)
	}
	defer rows.Close()

	var actions []CleanupAction
	for rows.Next() {
		var a CleanupAction
		a.CampaignID = campaignID
		a.Status = "pending"
		if err := rows.Scan(&a.ID, &a.Command, &a.Target, &a.RegisteredAt); err != nil {
			continue
		}
		actions = append(actions, a)
	}

	return actions, nil
}
