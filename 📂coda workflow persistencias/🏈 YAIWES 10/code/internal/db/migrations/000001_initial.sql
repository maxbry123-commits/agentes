-- 000001_initial.sql: Core tables for campaigns, findings, and attack plans

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Campaigns
CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    target TEXT NOT NULL,
    objective TEXT NOT NULL DEFAULT 'find all vulnerabilities',
    status TEXT NOT NULL DEFAULT 'planned',
    mode TEXT NOT NULL DEFAULT 'manual',
    scope JSONB NOT NULL DEFAULT '{}',
    auth_token TEXT,
    provider TEXT NOT NULL DEFAULT 'claude',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

CREATE INDEX idx_campaigns_status ON campaigns(status);
CREATE INDEX idx_campaigns_target ON campaigns(target);
CREATE INDEX idx_campaigns_created_at ON campaigns(created_at DESC);

-- Campaign events (append-only audit log)
CREATE TABLE campaign_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_type TEXT NOT NULL,
    agent_name TEXT,
    detail TEXT NOT NULL,
    data JSONB,
    CONSTRAINT fk_campaign_events_campaign FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
);

CREATE INDEX idx_campaign_events_campaign ON campaign_events(campaign_id, timestamp DESC);
CREATE INDEX idx_campaign_events_type ON campaign_events(event_type);

-- Attack surfaces
CREATE TABLE attack_surfaces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    target TEXT NOT NULL,
    data JSONB NOT NULL, -- full AttackSurface struct as JSON
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_attack_surfaces_campaign ON attack_surfaces(campaign_id);

-- Raw findings (from security tools, before classification)
CREATE TABLE raw_findings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    source TEXT NOT NULL,
    type TEXT NOT NULL,
    target TEXT NOT NULL,
    detail TEXT NOT NULL,
    raw_output TEXT,
    discovered_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_raw_findings_campaign ON raw_findings(campaign_id);
CREATE INDEX idx_raw_findings_type ON raw_findings(type);

-- Classified findings (enriched with CVE, CVSS, severity)
CREATE TABLE classified_findings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    raw_finding_id UUID REFERENCES raw_findings(id),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    cve_ids TEXT[] DEFAULT '{}',
    cvss_score DECIMAL(3,1) DEFAULT 0.0,
    cvss_vector TEXT,
    severity TEXT NOT NULL DEFAULT 'informational',
    attack_category TEXT,
    confidence TEXT NOT NULL DEFAULT 'unverified',
    false_positive_probability DECIMAL(3,2) DEFAULT 0.0,
    chain_candidates UUID[] DEFAULT '{}',
    evidence JSONB DEFAULT '[]',
    target TEXT NOT NULL,
    classified_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_classified_findings_campaign ON classified_findings(campaign_id);
CREATE INDEX idx_classified_findings_severity ON classified_findings(severity);
CREATE INDEX idx_classified_findings_cvss ON classified_findings(cvss_score DESC);

-- Attack plans
CREATE TABLE attack_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    recommended_path_id UUID,
    reasoning TEXT,
    data JSONB NOT NULL, -- full AttackPlan with paths and steps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_attack_plans_campaign ON attack_plans(campaign_id);

-- Execution results
CREATE TABLE execution_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    step_id UUID NOT NULL,
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    command_executed TEXT NOT NULL,
    output TEXT,
    success BOOLEAN NOT NULL DEFAULT FALSE,
    evidence JSONB DEFAULT '[]',
    executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    duration_ms INTEGER DEFAULT 0
);

CREATE INDEX idx_execution_results_campaign ON execution_results(campaign_id);
CREATE INDEX idx_execution_results_step ON execution_results(step_id);

-- Reports
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    data JSONB NOT NULL, -- full PentestReport struct
    format TEXT NOT NULL DEFAULT 'json',
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_reports_campaign ON reports(campaign_id);

-- Token usage tracking
CREATE TABLE token_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    agent_name TEXT NOT NULL,
    model TEXT NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_token_usage_campaign ON token_usage(campaign_id);
