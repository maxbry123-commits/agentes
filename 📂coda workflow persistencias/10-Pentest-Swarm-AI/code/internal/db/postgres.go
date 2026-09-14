package db

import (
	"context"
	"embed"
	"fmt"
	"sort"
	"strings"

	"github.com/jackc/pgx/v5/pgxpool"
)

//go:embed migrations/*.sql
var migrations embed.FS

// Connect creates a connection pool to PostgreSQL.
func Connect(ctx context.Context, dsn string) (*pgxpool.Pool, error) {
	config, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		return nil, fmt.Errorf("parsing database config: %w", err)
	}

	config.MaxConns = 20
	config.MinConns = 2

	pool, err := pgxpool.NewWithConfig(ctx, config)
	if err != nil {
		return nil, fmt.Errorf("creating connection pool: %w", err)
	}

	if err := pool.Ping(ctx); err != nil {
		pool.Close()
		return nil, fmt.Errorf("database ping failed: %w", err)
	}

	return pool, nil
}

// Migrate runs all SQL migrations in order.
func Migrate(ctx context.Context, pool *pgxpool.Pool) error {
	// Create migrations tracking table
	_, err := pool.Exec(ctx, `
		CREATE TABLE IF NOT EXISTS schema_migrations (
			version TEXT PRIMARY KEY,
			applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
		)
	`)
	if err != nil {
		return fmt.Errorf("creating migrations table: %w", err)
	}

	// Read all migration files
	entries, err := migrations.ReadDir("migrations")
	if err != nil {
		return fmt.Errorf("reading migrations directory: %w", err)
	}

	// Sort by filename
	var files []string
	for _, e := range entries {
		if strings.HasSuffix(e.Name(), ".sql") {
			files = append(files, e.Name())
		}
	}
	sort.Strings(files)

	for _, file := range files {
		// Check if already applied
		var exists bool
		err := pool.QueryRow(ctx, "SELECT EXISTS(SELECT 1 FROM schema_migrations WHERE version = $1)", file).Scan(&exists)
		if err != nil {
			return fmt.Errorf("checking migration %s: %w", file, err)
		}
		if exists {
			continue
		}

		// Read and execute migration
		content, err := migrations.ReadFile("migrations/" + file)
		if err != nil {
			return fmt.Errorf("reading migration %s: %w", file, err)
		}

		_, err = pool.Exec(ctx, string(content))
		if err != nil {
			return fmt.Errorf("executing migration %s: %w", file, err)
		}

		// Record migration
		_, err = pool.Exec(ctx, "INSERT INTO schema_migrations (version) VALUES ($1)", file)
		if err != nil {
			return fmt.Errorf("recording migration %s: %w", file, err)
		}
	}

	return nil
}
