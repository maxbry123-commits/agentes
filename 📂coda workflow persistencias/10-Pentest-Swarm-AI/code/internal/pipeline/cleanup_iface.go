package pipeline

import (
	"context"

	"github.com/google/uuid"
)

// CleanupRegistryIface is the minimum surface the runner and executor need
// from any cleanup registry implementation (Postgres, memory, or future
// backends). Concrete types are CleanupRegistry (Postgres) and
// MemoryCleanupRegistry.
type CleanupRegistryIface interface {
	Register(ctx context.Context, campaignID uuid.UUID, command, target string) error
	RunCleanup(ctx context.Context, campaignID uuid.UUID) *CleanupReport
	PendingCleanup(ctx context.Context, campaignID uuid.UUID) ([]CleanupAction, error)
}

// Compile-time assertions that our implementations satisfy the interface.
var (
	_ CleanupRegistryIface = (*CleanupRegistry)(nil)
	_ CleanupRegistryIface = (*MemoryCleanupRegistry)(nil)
)
