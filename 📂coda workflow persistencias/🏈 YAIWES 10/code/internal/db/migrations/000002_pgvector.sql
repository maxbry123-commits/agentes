-- 000002_pgvector.sql: Add vector embeddings for semantic search

CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding column to classified_findings for semantic similarity search
ALTER TABLE classified_findings
    ADD COLUMN embedding vector(1536);

CREATE INDEX idx_classified_findings_embedding
    ON classified_findings
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
