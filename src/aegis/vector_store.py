"""Vector store using pgvector for clinical evidence embeddings."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field


@dataclass
class EmbeddingResult:
    """Result from a vector similarity search."""

    id: int
    patient_id: str
    source_type: str
    source_id: str
    chunk_text: str
    similarity: float
    metadata: dict[str, Any] = field(default_factory=dict)


class VectorStoreConfig(BaseModel):
    """Configuration for the vector store."""

    database_url: str = Field(
        default_factory=lambda: os.getenv(
            "VECTOR_DATABASE_URL",
            os.getenv("DATABASE_URL", "postgresql://aegis:password@localhost:5432/aegis"),
        )
    )
    embedding_dimension: int = Field(default=768, description="Dimension of embedding vectors")
    table_name: str = Field(default="embeddings")
    default_top_k: int = Field(default=10, description="Default number of results to return")
    min_similarity: float = Field(default=0.5, description="Minimum similarity threshold")


class PgVectorStore:
    """PostgreSQL vector store using pgvector for similarity search."""

    def __init__(self, config: VectorStoreConfig | None = None):
        self.config = config or VectorStoreConfig()
        self._engine = None
        self._SessionLocal = None

    def _get_engine(self):
        """Lazy-initialize the database engine."""
        if self._engine is None:
            from sqlalchemy import create_engine
            from sqlalchemy.pool import NullPool

            self._engine = create_engine(
                self.config.database_url,
                poolclass=NullPool,
                echo=False,
            )
        return self._engine

    def _get_session(self):
        """Get a database session."""
        if self._SessionLocal is None:
            from sqlalchemy.orm import sessionmaker

            self._SessionLocal = sessionmaker(bind=self._get_engine())
        return self._SessionLocal()

    def ensure_table(self) -> None:
        """Ensure the embeddings table exists (run migrations)."""
        engine = self._get_engine()
        with engine.connect() as conn:
            conn.execute(
                __import__("sqlalchemy").text(
                    "CREATE EXTENSION IF NOT EXISTS vector;"
                )
            )
            conn.execute(
                __import__("sqlalchemy").text(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self.config.table_name} (
                        id SERIAL PRIMARY KEY,
                        patient_id VARCHAR(36) NOT NULL,
                        source_type VARCHAR(50) NOT NULL,
                        source_id VARCHAR(100) NOT NULL,
                        chunk_text TEXT NOT NULL,
                        embedding vector({self.config.embedding_dimension}) NOT NULL,
                        metadata JSONB DEFAULT '{{}}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """
                )
            )
            conn.execute(
                __import__("sqlalchemy").text(
                    f"""
                    CREATE INDEX IF NOT EXISTS idx_{self.config.table_name}_patient_id
                    ON {self.config.table_name}(patient_id);
                    """
                )
            )
            conn.execute(
                __import__("sqlalchemy").text(
                    f"""
                    CREATE INDEX IF NOT EXISTS idx_{self.config.table_name}_hnsw
                    ON {self.config.table_name}
                    USING hnsw (embedding vector_cosine_ops)
                    WITH (m = 16, ef_construction = 64);
                    """
                )
            )
            conn.commit()

    def insert_embedding(
        self,
        patient_id: str,
        source_type: str,
        source_id: str,
        chunk_text: str,
        embedding: list[float],
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """Insert a single embedding into the store.

        Returns:
            The ID of the inserted row.
        """
        from sqlalchemy import text

        session = self._get_session()
        try:
            result = session.execute(
                text(
                    f"""
                    INSERT INTO {self.config.table_name}
                    (patient_id, source_type, source_id, chunk_text, embedding, metadata)
                    VALUES (:patient_id, :source_type, :source_id, :chunk_text, :embedding, :metadata)
                    RETURNING id;
                    """
                ),
                {
                    "patient_id": patient_id,
                    "source_type": source_type,
                    "source_id": source_id,
                    "chunk_text": chunk_text,
                    "embedding": str(embedding),
                    "metadata": json.dumps(metadata or {}),
                },
            )
            row_id = result.scalar()
            session.commit()
            return row_id
        finally:
            session.close()

    def insert_embeddings_batch(
        self,
        records: list[dict[str, Any]],
    ) -> int:
        """Insert multiple embeddings in a batch.

        Args:
            records: List of dicts with keys: patient_id, source_type, source_id,
                     chunk_text, embedding, metadata (optional)

        Returns:
            Number of rows inserted.
        """
        from sqlalchemy import text

        session = self._get_session()
        try:
            count = 0
            for rec in records:
                session.execute(
                    text(
                        f"""
                        INSERT INTO {self.config.table_name}
                        (patient_id, source_type, source_id, chunk_text, embedding, metadata)
                        VALUES (:patient_id, :source_type, :source_id, :chunk_text, :embedding, :metadata);
                        """
                    ),
                    {
                        "patient_id": rec["patient_id"],
                        "source_type": rec["source_type"],
                        "source_id": rec["source_id"],
                        "chunk_text": rec["chunk_text"],
                        "embedding": str(rec["embedding"]),
                        "metadata": json.dumps(rec.get("metadata", {})),
                    },
                )
                count += 1
            session.commit()
            return count
        finally:
            session.close()

    def search(
        self,
        query_embedding: list[float],
        patient_id: str | None = None,
        source_types: list[str] | None = None,
        top_k: int | None = None,
        min_similarity: float | None = None,
    ) -> list[EmbeddingResult]:
        """Search for similar embeddings using cosine similarity.

        Args:
            query_embedding: The query vector.
            patient_id: Optional filter by patient ID.
            source_types: Optional filter by source types.
            top_k: Number of results to return (default from config).
            min_similarity: Minimum similarity threshold (default from config).

        Returns:
            List of EmbeddingResult sorted by similarity (descending).
        """
        from sqlalchemy import text

        top_k = top_k or self.config.default_top_k
        min_similarity = min_similarity or self.config.min_similarity

        # Build the query dynamically
        conditions = ["1 - (embedding <=> :query_embedding) >= :min_similarity"]
        params: dict[str, Any] = {
            "query_embedding": str(query_embedding),
            "min_similarity": min_similarity,
            "top_k": top_k,
        }

        if patient_id:
            conditions.append("patient_id = :patient_id")
            params["patient_id"] = patient_id

        if source_types:
            placeholders = ", ".join(f":stype_{i}" for i in range(len(source_types)))
            conditions.append(f"source_type IN ({placeholders})")
            for i, st in enumerate(source_types):
                params[f"stype_{i}"] = st

        where_clause = " AND ".join(conditions)

        query = text(
            f"""
            SELECT
                id,
                patient_id,
                source_type,
                source_id,
                chunk_text,
                1 - (embedding <=> :query_embedding) AS similarity,
                metadata
            FROM {self.config.table_name}
            WHERE {where_clause}
            ORDER BY embedding <=> :query_embedding
            LIMIT :top_k;
            """
        )

        session = self._get_session()
        try:
            result = session.execute(query, params)
            rows = result.fetchall()
            return [
                EmbeddingResult(
                    id=row[0],
                    patient_id=row[1],
                    source_type=row[2],
                    source_id=row[3],
                    chunk_text=row[4],
                    similarity=float(row[5]),
                    metadata=json.loads(row[6]) if row[6] else {},
                )
                for row in rows
            ]
        finally:
            session.close()

    def delete_by_patient(self, patient_id: str) -> int:
        """Delete all embeddings for a patient.

        Returns:
            Number of rows deleted.
        """
        from sqlalchemy import text

        session = self._get_session()
        try:
            result = session.execute(
                text(f"DELETE FROM {self.config.table_name} WHERE patient_id = :patient_id"),
                {"patient_id": patient_id},
            )
            session.commit()
            return result.rowcount
        finally:
            session.close()

    def count(self, patient_id: str | None = None) -> int:
        """Count embeddings, optionally filtered by patient."""
        from sqlalchemy import text

        session = self._get_session()
        try:
            if patient_id:
                result = session.execute(
                    text(f"SELECT COUNT(*) FROM {self.config.table_name} WHERE patient_id = :patient_id"),
                    {"patient_id": patient_id},
                )
            else:
                result = session.execute(text(f"SELECT COUNT(*) FROM {self.config.table_name}"))
            return result.scalar()
        finally:
            session.close()

    def health_check(self) -> dict[str, Any]:
        """Check if the vector store is healthy."""
        try:
            from sqlalchemy import text

            session = self._get_session()
            try:
                result = session.execute(text("SELECT 1"))
                result.scalar()

                # Check pgvector extension
                ext_result = session.execute(
                    text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
                )
                has_vector = ext_result.scalar() is not None

                return {
                    "status": "healthy",
                    "database": "connected",
                    "pgvector": "enabled" if has_vector else "disabled",
                    "table": self.config.table_name,
                }
            finally:
                session.close()
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }
