-- 000003_cleanup_registry.sql: Track cleanup actions for safe rollback

CREATE TABLE cleanup_actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    command TEXT NOT NULL,
    target TEXT NOT NULL,
    registered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    executed_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'pending' -- pending, executed, failed
);

CREATE INDEX idx_cleanup_actions_campaign ON cleanup_actions(campaign_id);
CREATE INDEX idx_cleanup_actions_status ON cleanup_actions(status);
