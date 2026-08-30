from __future__ import annotations

import hashlib
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

try:
    from sentence_transformers import CrossEncoder, SentenceTransformer
    _ST_AVAILABLE = True
except ImportError:
    _ST_AVAILABLE = False


# ---------------------------------------------------------------------------
# Document Processing
# ---------------------------------------------------------------------------

@dataclass
class DocumentChunk:
    """A chunk of a document with metadata."""
    chunk_id: str
    document_id: str
    content: str
    chunk_index: int
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None
    token_count: int = 0


@dataclass
class Document:
    """A source document for RAG."""
    document_id: str
    source_path: str
    title: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    chunks: list[DocumentChunk] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class TextChunker:
    """Splits documents into overlapping chunks for retrieval."""

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        min_chunk_size: int = 50,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def chunk_text(self, text: str, metadata: dict[str, Any] | None = None) -> list[DocumentChunk]:
        """Split text into chunks with overlap."""
        if not text.strip():
            return []

        meta = metadata or {}
        words = text.split()
        chunks = []
        start = 0
        chunk_index = 0

        while start < len(words):
            end = min(start + self.chunk_size, len(words))
            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words)

            if len(chunk_text) >= self.min_chunk_size:
                chunk_id = hashlib.md5(f"{meta.get('document_id', 'unknown')}:{chunk_index}".encode()).hexdigest()[:12]
                chunks.append(DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=meta.get("document_id", "unknown"),
                    content=chunk_text,
                    chunk_index=chunk_index,
                    metadata=meta,
                    token_count=len(chunk_words),
                ))
                chunk_index += 1

            if end >= len(words):
                break

            start = end - self.chunk_overlap
            if start <= end - self.chunk_size:
                start = end

        return chunks

    def chunk_document(self, document: Document) -> list[DocumentChunk]:
        """Chunk a document and store chunks in it."""
        metadata = {
            "document_id": document.document_id,
            "source_path": document.source_path,
            "title": document.title,
            **document.metadata,
        }
        chunks = self.chunk_text(document.content, metadata)
        document.chunks = chunks
        return chunks


class DocumentLoader:
    """Loads documents from various sources."""

    def __init__(self):
        self.supported_extensions = {".txt", ".md", ".pdf", ".json", ".csv"}

    def load_file(self, file_path: str | Path) -> Document:
        """Load a single file as a document."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if path.suffix.lower() not in self.supported_extensions:
            raise ValueError(f"Unsupported file type: {path.suffix}")

        if path.suffix.lower() == ".json":
            import json
            with open(path) as f:
                data = json.load(f)
            content = json.dumps(data, indent=2)
        elif path.suffix.lower() == ".csv":
            import pandas as pd
            df = pd.read_csv(path)
            content = df.to_string()
        else:
            content = path.read_text(encoding="utf-8")

        return Document(
            document_id=str(uuid.uuid4())[:12],
            source_path=str(path),
            title=path.stem,
            content=content,
            metadata={"extension": path.suffix, "size": len(content)},
        )

    def load_directory(self, directory: str | Path, recursive: bool = True) -> list[Document]:
        """Load all supported files from a directory."""
        path = Path(directory)
        pattern = "**/*" if recursive else "*"
        files = [f for f in path.glob(pattern) if f.is_file() and f.suffix.lower() in self.supported_extensions]
        return [self.load_file(f) for f in files]


# ---------------------------------------------------------------------------
# Embedding Models
# ---------------------------------------------------------------------------

class EmbeddingProvider(ABC):
    """Abstract base for embedding providers."""

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        raise NotImplementedError

    @abstractmethod
    def embed_query(self, query: str) -> list[float]:
        """Generate embedding for a single query."""
        raise NotImplementedError

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Embedding dimension."""
        raise NotImplementedError


class SentenceTransformerEmbeddings(EmbeddingProvider):
    """Sentence-transformers based embeddings."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        if not _ST_AVAILABLE:
            raise ImportError("sentence-transformers not installed")
        self.model = SentenceTransformer(model_name)
        self._dimension = self.model.get_sentence_embedding_dimension()

    def embed(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        embedding = self.model.encode(query, normalize_embeddings=True)
        return embedding.tolist()

    @property
    def dimension(self) -> int:
        return self._dimension


class MockEmbeddings(EmbeddingProvider):
    """Mock embeddings for testing without model dependencies."""

    def __init__(self, dimension: int = 384):
        self._dimension = dimension

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(t) for t in texts]

    def embed_query(self, query: str) -> list[float]:
        seed = int(hashlib.md5(query.encode()).hexdigest()[:8], 16) % (2**31)
        rng = np.random.RandomState(seed)
        return rng.randn(self._dimension).tolist()

    @property
    def dimension(self) -> int:
        return self._dimension


# ---------------------------------------------------------------------------
# Vector Store Abstraction
# ---------------------------------------------------------------------------

class VectorStore(ABC):
    """Abstract base for vector stores."""

    @abstractmethod
    def add(self, chunks: list[DocumentChunk]) -> None:
        """Add chunks to the store."""
        raise NotImplementedError

    @abstractmethod
    def search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[tuple[DocumentChunk, float]]:
        """Search for similar chunks."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, chunk_ids: list[str]) -> None:
        """Delete chunks by ID."""
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        """Clear all data."""
        raise NotImplementedError


class InMemoryVectorStore(VectorStore):
    """In-memory vector store for development/testing."""

    def __init__(self):
        self._chunks: dict[str, DocumentChunk] = {}
        self._embeddings: dict[str, np.ndarray] = {}

    def add(self, chunks: list[DocumentChunk]) -> None:
        for chunk in chunks:
            if chunk.embedding is None:
                raise ValueError(f"Chunk {chunk.chunk_id} has no embedding")
            self._chunks[chunk.chunk_id] = chunk
            self._embeddings[chunk.chunk_id] = np.array(chunk.embedding)

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[tuple[DocumentChunk, float]]:
        if not self._embeddings:
            return []

        query_vec = np.array(query_embedding)
        scores = []

        for chunk_id, emb in self._embeddings.items():
            chunk = self._chunks[chunk_id]

            # Apply metadata filter
            if filter_metadata:
                match = all(
                    chunk.metadata.get(k) == v for k, v in filter_metadata.items()
                )
                if not match:
                    continue

            # Cosine similarity
            score = float(np.dot(query_vec, emb) / (np.linalg.norm(query_vec) * np.linalg.norm(emb)))
            scores.append((chunk, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def delete(self, chunk_ids: list[str]) -> None:
        for cid in chunk_ids:
            self._chunks.pop(cid, None)
            self._embeddings.pop(cid, None)

    def clear(self) -> None:
        self._chunks.clear()
        self._embeddings.clear()


class PgVectorVectorStore(VectorStore):
    """PostgreSQL vector store using pgvector for production RAG."""

    def __init__(self, database_url: str | None = None, table_name: str = "rag_embeddings"):
        from .vector_store import PgVectorStore, VectorStoreConfig

        config = VectorStoreConfig(
            database_url=database_url or "",
            table_name=table_name,
        )
        self._store = PgVectorStore(config)
        self._chunks: dict[str, DocumentChunk] = {}

    def initialize(self) -> None:
        """Initialize the database table."""
        self._store.ensure_table()

    def add(self, chunks: list[DocumentChunk]) -> None:
        """Add chunks to the pgvector store."""
        records = []
        for chunk in chunks:
            if chunk.embedding is None:
                raise ValueError(f"Chunk {chunk.chunk_id} has no embedding")
            self._chunks[chunk.chunk_id] = chunk
            records.append({
                "patient_id": chunk.metadata.get("patient_id", "global"),
                "source_type": chunk.metadata.get("source_type", "document"),
                "source_id": chunk.chunk_id,
                "chunk_text": chunk.content,
                "embedding": chunk.embedding,
                "metadata": {
                    "document_id": chunk.document_id,
                    "chunk_index": chunk.chunk_index,
                    "token_count": chunk.token_count,
                    **chunk.metadata,
                },
            })
        self._store.insert_embeddings_batch(records)

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[tuple[DocumentChunk, float]]:
        """Search for similar chunks using pgvector."""
        patient_id = filter_metadata.get("patient_id") if filter_metadata else None
        source_types = filter_metadata.get("source_types") if filter_metadata else None

        results = self._store.search(
            query_embedding=query_embedding,
            patient_id=patient_id,
            source_types=source_types,
            top_k=top_k,
        )

        output = []
        for result in results:
            # Try to get from cache, or reconstruct
            chunk = self._chunks.get(result.id)
            if chunk is None:
                chunk = DocumentChunk(
                    chunk_id=str(result.id),
                    document_id=result.metadata.get("document_id", "unknown"),
                    content=result.chunk_text,
                    chunk_index=result.metadata.get("chunk_index", 0),
                    metadata=result.metadata,
                    token_count=result.metadata.get("token_count", 0),
                )
            output.append((chunk, result.similarity))

        return output

    def delete(self, chunk_ids: list[str]) -> None:
        """Delete chunks by ID (not implemented for pgvector)."""
        pass

    def clear(self) -> None:
        """Clear all data (not implemented for pgvector)."""
        pass


# ---------------------------------------------------------------------------
# Reranking
# ---------------------------------------------------------------------------

class Reranker(ABC):
    """Abstract base for rerankers."""

    @abstractmethod
    def rerank(
        self,
        query: str,
        chunks: list[DocumentChunk],
        top_k: int = 10,
    ) -> list[tuple[DocumentChunk, float]]:
        """Rerank chunks by relevance to query."""
        raise NotImplementedError


class CrossEncoderReranker(Reranker):
    """Cross-encoder reranker using sentence-transformers."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        if not _ST_AVAILABLE:
            raise ImportError("sentence-transformers not installed")
        self.model = CrossEncoder(model_name)

    def rerank(
        self,
        query: str,
        chunks: list[DocumentChunk],
        top_k: int = 10,
    ) -> list[tuple[DocumentChunk, float]]:
        if not chunks:
            return []

        pairs = [(query, chunk.content) for chunk in chunks]
        scores = self.model.predict(pairs)

        ranked = sorted(
            zip(chunks, scores),
            key=lambda x: x[1],
            reverse=True,
        )
        return ranked[:top_k]


class NoOpReranker(Reranker):
    """No-op reranker (returns chunks as-is)."""

    def rerank(
        self,
        query: str,
        chunks: list[DocumentChunk],
        top_k: int = 10,
    ) -> list[tuple[DocumentChunk, float]]:
        return [(chunk, 1.0) for chunk in chunks[:top_k]]


# ---------------------------------------------------------------------------
# RAG Pipeline
# ---------------------------------------------------------------------------

@dataclass
class RAGConfig:
    """Configuration for RAG pipeline."""
    chunk_size: int = 512
    chunk_overlap: int = 50
    embedding_model: str = "all-MiniLM-L6-v2"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    top_k_retrieval: int = 20
    top_k_rerank: int = 5
    min_relevance_score: float = 0.3


class RAGPipeline:
    """End-to-end RAG pipeline: ingest -> embed -> retrieve -> rerank."""

    def __init__(
        self,
        config: RAGConfig | None = None,
        embedding_provider: EmbeddingProvider | None = None,
        vector_store: VectorStore | None = None,
        reranker: Reranker | None = None,
    ):
        self.config = config or RAGConfig()
        self.chunker = TextChunker(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
        )
        self.loader = DocumentLoader()

        self.embedding_provider = embedding_provider or (
            SentenceTransformerEmbeddings(self.config.embedding_model)
            if _ST_AVAILABLE else MockEmbeddings()
        )

        self.vector_store = vector_store or InMemoryVectorStore()

        self.reranker = reranker or (
            CrossEncoderReranker(self.config.reranker_model)
            if _ST_AVAILABLE else NoOpReranker()
        )

    def ingest(self, source: str | Path, recursive: bool = True) -> list[Document]:
        """Ingest documents from a file or directory."""
        path = Path(source)
        if path.is_file():
            documents = [self.loader.load_file(path)]
        else:
            documents = self.loader.load_directory(path, recursive)

        for doc in documents:
            self._process_document(doc)

        return documents

    def _process_document(self, document: Document) -> None:
        """Chunk, embed, and store a document."""
        chunks = self.chunker.chunk_document(document)

        if not chunks:
            return

        # Generate embeddings
        texts = [chunk.content for chunk in chunks]
        embeddings = self.embedding_provider.embed(texts)

        for chunk, emb in zip(chunks, embeddings):
            chunk.embedding = emb

        # Store in vector store
        self.vector_store.add(chunks)

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[tuple[DocumentChunk, float]]:
        """Retrieve and rerank relevant chunks."""
        top_k = top_k or self.config.top_k_retrieval

        # Embed query
        query_embedding = self.embedding_provider.embed_query(query)

        # Initial retrieval
        initial_results = self.vector_store.search(
            query_embedding,
            top_k=top_k,
            filter_metadata=filter_metadata,
        )

        if not initial_results:
            return []

        chunks = [chunk for chunk, _ in initial_results]

        # Rerank
        reranked = self.reranker.rerank(query, chunks, top_k=self.config.top_k_rerank)

        # Filter by minimum relevance
        filtered = [(chunk, score) for chunk, score in reranked if score >= self.config.min_relevance_score]

        return filtered

    def retrieve_as_evidence(
        self,
        query: str,
        patient_id: str | None = None,
        top_k: int | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve and format as evidence items for agents."""
        results = self.retrieve(query, top_k=top_k)

        evidence = []
        for chunk, score in results:
            meta = {
                **chunk.metadata,
                "chunk_id": chunk.chunk_id,
                "chunk_index": chunk.chunk_index,
                "token_count": chunk.token_count,
            }
            if patient_id:
                meta["patient_id"] = patient_id

            evidence.append({
                "source": chunk.metadata.get("source_path", "document"),
                "source_id": chunk.chunk_id,
                "snippet": chunk.content[:500],
                "relevance_score": round(score, 4),
                "metadata": meta,
            })

        return evidence


# ---------------------------------------------------------------------------
# Citation Enforcement
# ---------------------------------------------------------------------------

class CitationEnforcer:
    """Ensures generated responses include proper citations."""

    def __init__(self, required_citation_rate: float = 0.8):
        self.required_citation_rate = required_citation_rate

    def check_citations(self, response: str, evidence: list[dict[str, Any]]) -> dict[str, Any]:
        """Check if response properly cites evidence."""
        # Extract citation patterns like [1], [source_id], etc.
        import re
        citations = re.findall(r'\[([^\]]+)\]', response)
        citation_ids = set(citations)

        evidence_ids = {e.get("source_id", "") for e in evidence}
        valid_citations = citation_ids & evidence_ids

        coverage = len(valid_citations) / max(len(evidence_ids), 1)
        citation_rate = len(citations) / max(len(response.split(".")), 1)

        return {
            "has_citations": len(citations) > 0,
            "citation_count": len(citations),
            "valid_citation_count": len(valid_citations),
            "coverage": round(coverage, 2),
            "citation_rate": round(citation_rate, 2),
            "meets_threshold": coverage >= self.required_citation_rate,
            "missing_evidence": list(evidence_ids - citation_ids),
        }

    def enforce_citations(
        self,
        response: str,
        evidence: list[dict[str, Any]],
        max_attempts: int = 2,
    ) -> str:
        """Add citations to response if missing."""
        check = self.check_citations(response, evidence)

        if check["meets_threshold"] or not evidence:
            return response

        # Add citation references at the end
        evidence_refs = []
        for i, e in enumerate(evidence[:5]):
            source_id = e.get("source_id", f"doc_{i}")
            evidence_refs.append(f"[{source_id}]")

        citation_text = " ".join(evidence_refs)
        return f"{response.strip()} {citation_text}"


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_rag_pipeline(
    use_mock: bool = False,
    vector_store: VectorStore | None = None,
) -> RAGPipeline:
    """Factory function to create a configured RAG pipeline."""
    config = RAGConfig()

    if use_mock or not _ST_AVAILABLE:
        embedding_provider = MockEmbeddings()
        reranker = NoOpReranker()
    else:
        embedding_provider = SentenceTransformerEmbeddings(config.embedding_model)
        reranker = CrossEncoderReranker(config.reranker_model)

    return RAGPipeline(
        config=config,
        embedding_provider=embedding_provider,
        vector_store=vector_store,
        reranker=reranker,
    )
