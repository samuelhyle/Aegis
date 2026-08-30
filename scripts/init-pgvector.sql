-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create embeddings table for clinical evidence
CREATE TABLE IF NOT EXISTS embeddings (
    id SERIAL PRIMARY KEY,
    patient_id VARCHAR(36) NOT NULL,
    source_type VARCHAR(50) NOT NULL,  -- 'condition', 'medication', 'observation', 'procedure', 'encounter'
    source_id VARCHAR(100) NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(768) NOT NULL,  -- 768-dim for nomic-embed-text or gemma embeddings
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast patient lookups
CREATE INDEX IF NOT EXISTS idx_embeddings_patient_id ON embeddings(patient_id);

-- Index for source type filtering
CREATE INDEX IF NOT EXISTS idx_embeddings_source_type ON embeddings(source_type);

-- HNSW index for approximate nearest neighbor search (cosine distance)
CREATE INDEX IF NOT EXISTS idx_embeddings_hnsw ON embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Composite index for patient + source type queries
CREATE INDEX IF NOT EXISTS idx_embeddings_patient_source ON embeddings(patient_id, source_type);
