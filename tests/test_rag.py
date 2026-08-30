from __future__ import annotations

import tempfile
from pathlib import Path

from aegis.rag import (
    CitationEnforcer,
    DocumentChunk,
    DocumentLoader,
    InMemoryVectorStore,
    MockEmbeddings,
    NoOpReranker,
    TextChunker,
    create_rag_pipeline,
)


class TestTextChunker:
    def test_chunk_simple_text(self):
        chunker = TextChunker(chunk_size=5, chunk_overlap=1, min_chunk_size=5)
        text = "word1 word2 word3 word4 word5 word6 word7 word8 word9 word10"
        chunks = chunker.chunk_text(text)
        assert len(chunks) > 0
        assert all(c.token_count <= 5 for c in chunks)

    def test_chunk_empty_text(self):
        chunker = TextChunker()
        chunks = chunker.chunk_text("")
        assert chunks == []

    def test_chunk_produces_multiple_chunks(self):
        chunker = TextChunker(chunk_size=3, chunk_overlap=1, min_chunk_size=5)
        text = "a " * 20  # 20 words
        chunks = chunker.chunk_text(text)
        assert len(chunks) > 1

    def test_chunk_document(self):
        chunker = TextChunker(chunk_size=3, chunk_overlap=1, min_chunk_size=1)
        from aegis.rag import Document
        doc = Document(
            document_id="doc1",
            source_path="/test/path.txt",
            title="Test",
            content="word " * 20,
        )
        chunks = chunker.chunk_document(doc)
        assert len(chunks) > 0
        assert doc.chunks == chunks


class TestDocumentLoader:
    def test_load_txt_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "myreport.txt"
            test_file.write_text("Test content\nLine 2\nLine 3")
            loader = DocumentLoader()
            doc = loader.load_file(test_file)
            assert doc.title == "myreport"
            assert "Test content" in doc.content
            assert doc.metadata["extension"] == ".txt"

    def test_load_json_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "data.json"
            test_file.write_text('{"key": "value", "number": 42}')
            loader = DocumentLoader()
            doc = loader.load_file(test_file)
            assert "key" in doc.content
            assert doc.metadata["extension"] == ".json"

    def test_load_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "file1.txt").write_text("Content 1")
            Path(tmpdir, "file2.md").write_text("Content 2")
            Path(tmpdir, "ignored.xyz").write_text("Should be ignored")

            loader = DocumentLoader()
            docs = loader.load_directory(tmpdir)
            assert len(docs) == 2


class TestMockEmbeddings:
    def test_embed(self):
        embeddings = MockEmbeddings(dimension=128)
        result = embeddings.embed(["text 1", "text 2"])
        assert len(result) == 2
        assert len(result[0]) == 128

    def test_embed_query(self):
        embeddings = MockEmbeddings()
        result = embeddings.embed_query("test query")
        assert len(result) == embeddings.dimension

    def test_same_text_same_embedding(self):
        embeddings = MockEmbeddings(dimension=4)
        result1 = embeddings.embed(["same text"])
        result2 = embeddings.embed(["same text"])
        assert result1 == result2

    def test_different_text_different_embedding(self):
        embeddings = MockEmbeddings(dimension=4)
        result1 = embeddings.embed(["text A"])
        result2 = embeddings.embed(["text B"])
        assert result1 != result2


class TestInMemoryVectorStore:
    def test_add_and_search(self):
        store = InMemoryVectorStore()
        embeddings = MockEmbeddings(dimension=4)

        q1 = embeddings.embed_query("query 1")
        q2 = embeddings.embed_query("query 2")

        chunks = [
            DocumentChunk(
                chunk_id="c1",
                document_id="doc1",
                content="chunk one",
                chunk_index=0,
                embedding=q1,
            ),
            DocumentChunk(
                chunk_id="c2",
                document_id="doc1",
                content="chunk two",
                chunk_index=1,
                embedding=q2,
            ),
        ]
        store.add(chunks)

        results = store.search(q1, top_k=2)
        assert len(results) > 0
        chunk_ids = [r[0].chunk_id for r in results]
        assert "c1" in chunk_ids

    def test_search_with_filter(self):
        store = InMemoryVectorStore()
        embeddings = MockEmbeddings(dimension=4)

        chunks = [
            DocumentChunk(
                chunk_id="c1",
                document_id="doc1",
                content="chunk one",
                chunk_index=0,
                metadata={"category": "medical"},
                embedding=embeddings.embed_query("query 1"),
            ),
            DocumentChunk(
                chunk_id="c2",
                document_id="doc2",
                content="chunk two",
                chunk_index=0,
                metadata={"category": "legal"},
                embedding=embeddings.embed_query("query 2"),
            ),
        ]
        store.add(chunks)

        results = store.search(
            embeddings.embed_query("query 1"),
            top_k=2,
            filter_metadata={"category": "medical"},
        )
        assert len(results) == 1
        assert results[0][0].metadata["category"] == "medical"

    def test_delete(self):
        store = InMemoryVectorStore()
        embeddings = MockEmbeddings(dimension=4)

        chunks = [
            DocumentChunk(
                chunk_id="c1",
                document_id="doc1",
                content="chunk one",
                chunk_index=0,
                embedding=embeddings.embed_query("query 1"),
            ),
        ]
        store.add(chunks)
        store.delete(["c1"])

        results = store.search(embeddings.embed_query("query 1"), top_k=1)
        assert len(results) == 0

    def test_clear(self):
        store = InMemoryVectorStore()
        embeddings = MockEmbeddings(dimension=4)
        chunks = [
            DocumentChunk(
                chunk_id="c1", document_id="doc1",
                content="x", chunk_index=0,
                embedding=embeddings.embed_query("q"),
            ),
        ]
        store.add(chunks)
        store.clear()
        assert store.search(embeddings.embed_query("q")) == []


class TestNoOpReranker:
    def test_rerank(self):
        reranker = NoOpReranker()
        chunks = [
            DocumentChunk(chunk_id="c1", document_id="d1", content="a", chunk_index=0),
            DocumentChunk(chunk_id="c2", document_id="d1", content="b", chunk_index=1),
        ]
        results = reranker.rerank("query", chunks, top_k=1)
        assert len(results) == 1
        assert results[0][0].chunk_id == "c1"


class TestCitationEnforcer:
    def test_check_citations_passes(self):
        enforcer = CitationEnforcer(required_citation_rate=0.5)
        response = "The patient has hypertension [doc1] and diabetes [doc2]."
        evidence = [
            {"source_id": "doc1", "snippet": "..."},
            {"source_id": "doc2", "snippet": "..."},
        ]
        result = enforcer.check_citations(response, evidence)
        assert result["has_citations"] is True
        assert result["valid_citation_count"] == 2
        assert result["meets_threshold"] is True

    def test_check_citations_fails(self):
        enforcer = CitationEnforcer(required_citation_rate=0.5)
        response = "The patient has hypertension and diabetes."
        evidence = [
            {"source_id": "doc1", "snippet": "..."},
            {"source_id": "doc2", "snippet": "..."},
        ]
        result = enforcer.check_citations(response, evidence)
        assert result["has_citations"] is False
        assert result["meets_threshold"] is False

    def test_enforce_citations_adds_missing(self):
        enforcer = CitationEnforcer(required_citation_rate=0.5)
        response = "The patient has hypertension."
        evidence = [{"source_id": "doc1", "snippet": "..."}]
        result = enforcer.enforce_citations(response, evidence)
        assert "[doc1]" in result

    def test_enforce_no_change_when_citations_present(self):
        enforcer = CitationEnforcer(required_citation_rate=0.5)
        response = "The patient has hypertension [doc1]."
        evidence = [{"source_id": "doc1", "snippet": "..."}]
        result = enforcer.enforce_citations(response, evidence)
        assert result == response


class TestRAGPipeline:
    def test_ingest_and_retrieve(self):
        pipeline = create_rag_pipeline(use_mock=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "test.txt").write_text(
                "Patient has hypertension and diabetes. "
                "Medication includes metformin and lisinopril. "
                "Lab results show elevated glucose. "
                "Cardiology follow up scheduled."
            )

            docs = pipeline.ingest(tmpdir)
            assert len(docs) == 1

            results = pipeline.retrieve("hypertension medication", top_k=5)
            assert len(results) > 0
            assert results[0][1] > 0

    def test_retrieve_as_evidence(self):
        pipeline = create_rag_pipeline(use_mock=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "test.txt").write_text(
                "Patient has hypertension and diabetes. "
                "Medication includes metformin and lisinopril. "
                "Lab results show elevated glucose."
            )

            pipeline.ingest(tmpdir)
            evidence = pipeline.retrieve_as_evidence(
                "hypertension", patient_id="patient-123"
            )

            assert len(evidence) > 0
            assert evidence[0]["relevance_score"] > 0
            assert evidence[0]["metadata"].get("patient_id") == "patient-123"

    def test_empty_retrieve(self):
        pipeline = create_rag_pipeline(use_mock=True)
        evidence = pipeline.retrieve_as_evidence("nonexistent topic")
        assert evidence == []

    def test_multiple_documents(self):
        pipeline = create_rag_pipeline(use_mock=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "doc1.txt").write_text(
                "Hypertension treatment guidelines include ACE inhibitors."
            )
            Path(tmpdir, "doc2.txt").write_text(
                "Diabetes management focuses on blood glucose control."
            )

            docs = pipeline.ingest(tmpdir)
            assert len(docs) == 2

            results = pipeline.retrieve("hypertension", top_k=5)
            assert len(results) > 0
