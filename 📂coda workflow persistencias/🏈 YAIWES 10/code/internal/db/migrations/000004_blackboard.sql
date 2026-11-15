-- 000004_blackboard.sql: Stigmergic swarm blackboard
--
-- The blackboard is the shared environment state that enables swarm
-- coordination without a central planner. Every agent writes findings
-- tagged with a type and a pheromone weight; every agent reads findings
-- matching trigger predicates.
--
-- Pheromones decay over time, biasing the swarm toward recent/high-signal
-- findings. This replaces the sequential 5-phase runner.

CREATE TABLE IF NOT EXISTS swarm_findings (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id     UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    agent_name      TEXT NOT NULL,           -- author agent
    finding_type    TEXT NOT NULL,           -- e.g. SUBDOMAIN, CVE_MATCH, EXPLOIT_CHAIN
    target          TEXT NOT NULL,           -- host, url, asset identifier
    data            JSONB NOT NULL,          -- structured payload per finding_type
    pheromone_base  DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    half_life_sec   INTEGER NOT NULL DEFAULT 3600, -- per-type decay half-life
    embedding       vector(1536),            -- optional semantic embedding
    superseded_by   UUID REFERENCES swarm_findings(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_swarm_findings_campaign
    ON swarm_findings(campaign_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_swarm_findings_type
    ON swarm_findings(campaign_id, finding_type);

CREATE INDEX IF NOT EXISTS idx_swarm_findings_target
    ON swarm_findings(campaign_id, target);

CREATE INDEX IF NOT EXISTS idx_swarm_findings_active
    ON swarm_findings(campaign_id, finding_type)
    WHERE superseded_by IS NULL;

-- Pheromone weight with exponential decay.
-- weight(t) = base * 0.5 ^ (age / half_life)
CREATE OR REPLACE FUNCTION swarm_pheromone(
    base DOUBLE PRECISION,
    half_life_sec INTEGER,
    age_sec DOUBLE PRECISION
) RETURNS DOUBLE PRECISION AS $$
    SELECT base * POWER(0.5, age_sec / GREATEST(half_life_sec, 1))
$$ LANGUAGE SQL IMMUTABLE;

-- View: active findings with current pheromone strength
CREATE OR REPLACE VIEW swarm_findings_active AS
SELECT
    f.*,
    swarm_pheromone(
        f.pheromone_base,
        f.half_life_sec,
        EXTRACT(EPOCH FROM (NOW() - f.created_at))
    ) AS pheromone
FROM swarm_findings f
WHERE f.superseded_by IS NULL;

-- Per-agent cursor: last finding each agent has processed. Used by the
-- scheduler to deliver new work exactly once.
CREATE TABLE IF NOT EXISTS swarm_agent_cursors (
    campaign_id   UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    agent_name    TEXT NOT NULL,
    last_seen_id  UUID,
    last_seen_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (campaign_id, agent_name)
);

-- Campaign-level budget tracking (hard caps enforced by scheduler)
CREATE TABLE IF NOT EXISTS swarm_budgets (
    campaign_id     UUID PRIMARY KEY REFERENCES campaigns(id) ON DELETE CASCADE,
    max_agent_hours DOUBLE PRECISION NOT NULL DEFAULT 2.0,
    max_tokens      BIGINT NOT NULL DEFAULT 2000000,
    agent_hours_used DOUBLE PRECISION NOT NULL DEFAULT 0,
    tokens_used     BIGINT NOT NULL DEFAULT 0,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
