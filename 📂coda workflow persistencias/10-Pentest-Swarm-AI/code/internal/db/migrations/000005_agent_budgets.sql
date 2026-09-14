-- 000005_agent_budgets.sql: per-agent budget rows so one runaway agent
-- can't burn the entire campaign budget.
--
-- Soft threshold (warn_at_tokens) emits a WARN event; hard cap
-- (max_tokens) blocks further dispatch to that agent.

CREATE TABLE IF NOT EXISTS swarm_agent_budgets (
    campaign_id     UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    agent_name      TEXT NOT NULL,
    max_tokens      BIGINT NOT NULL DEFAULT 500000,
    warn_at_tokens  BIGINT NOT NULL DEFAULT 400000,   -- 80% of max by default
    tokens_used     BIGINT NOT NULL DEFAULT 0,
    warned          BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (campaign_id, agent_name)
);

CREATE INDEX IF NOT EXISTS idx_swarm_agent_budgets_campaign
    ON swarm_agent_budgets(campaign_id);
