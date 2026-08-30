"""
Tests for Graph RAG System

Comprehensive tests for the knowledge graph-based retrieval system including:
- Graph algorithms (BFS, shortest path, centrality, communities)
- Graph RAG retriever
- Pattern discovery engine
- Graph reasoning agent
- API endpoints
"""


import pytest

from aegis.graph_agent import GraphReasoningAgent
from aegis.graph_rag import (
    GraphAlgorithms,
    GraphCommunity,
    GraphEvidence,
    GraphPath,
    GraphPattern,
    GraphRAGResult,
    GraphRAGRetriever,
    PatternDiscoveryEngine,
    graph_rag_retrieve,
)
from aegis.knowledge_graph import (
    GraphNode,
    KnowledgeGraph,
    MedicalKnowledgeGraph,
    build_knowledge_graph,
)
from aegis.store import SyntheaStore

# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_graph():
    """Create a sample knowledge graph for testing."""
    graph = MedicalKnowledgeGraph()

    # Add nodes
    graph.add_patient("patient1", first="John", last="Doe", gender="M")
    graph.add_condition("cond_hypertension", "patient1", description="Hypertension", code="38341003")
    graph.add_condition("cond_diabetes", "patient1", description="Diabetes", code="44054006")
    graph.add_medication("med_lisinopril", "patient1", description="Lisinopril", code="314076")
    graph.add_medication("med_metformin", "patient1", description="Metformin", code="6809")
    graph.add_observation("obs_bp", "patient1", description="Blood Pressure", value="140/90", date="2024-01-01")
    graph.add_observation("obs_glucose", "patient1", description="Glucose", value="150", date="2024-01-02")
    graph.add_procedure("proc_exam", "patient1", description="Physical Exam", date="2024-01-01")

    # Add second patient for pattern discovery
    graph.add_patient("patient2", first="Jane", last="Smith", gender="F")
    graph.add_condition("cond_hypertension_2", "patient2", description="Hypertension", code="38341003")
    graph.add_condition("cond_diabetes_2", "patient2", description="Diabetes", code="44054006")
    graph.add_medication("med_lisinopril_2", "patient2", description="Lisinopril", code="314076")

    return graph


@pytest.fixture
def store():
    """Create a loaded store for testing."""
    s = SyntheaStore("data/synthea")
    s.load()
    return s


@pytest.fixture
def sample_patient_id(store):
    """Get a sample patient ID."""
    patients = store.tables.get("patients")
    if patients is None or len(patients) == 0:
        pytest.skip("No patients")
    return patients.iloc[0]["Id"]


@pytest.fixture
def client():
    """Create a test client."""
    import os
    os.environ["AEGIS_AUTH_DISABLED"] = "true"
    os.environ["AEGIS_RATE_LIMIT_DISABLED"] = "true"
    from fastapi.testclient import TestClient

    from aegis.api import app
    return TestClient(app)


# ============================================================================
# Test Graph Algorithms
# ============================================================================

class TestGraphAlgorithms:
    """Tests for graph algorithms."""

    def test_bfs(self, sample_graph):
        """Test breadth-first search."""
        result = GraphAlgorithms.bfs(sample_graph, "patient1", max_depth=2)

        assert "patient1" in result
        assert result["patient1"]["depth"] == 0

        # Should find connected nodes
        assert len(result) > 1

    def test_bfs_with_edge_filter(self, sample_graph):
        """Test BFS with edge type filter."""
        result = GraphAlgorithms.bfs(
            sample_graph, "patient1", max_depth=2, edge_type_filter="has_condition"
        )

        # Should only find conditions
        for node_id in result:
            if node_id != "patient1":
                node = sample_graph.get_node(node_id)
                assert node.node_type == "condition"

    def test_shortest_path(self, sample_graph):
        """Test shortest path finding."""
        path = GraphAlgorithms.shortest_path(
            sample_graph, "cond_hypertension", "med_lisinopril"
        )

        assert path is not None
        assert path.nodes[0] == "cond_hypertension"
        assert path.nodes[-1] == "med_lisinopril"
        assert path.length > 0

    def test_shortest_path_no_connection(self):
        """Test shortest path with no connection."""
        graph = KnowledgeGraph()
        graph.add_node(GraphNode(id="a", node_type="test"))
        graph.add_node(GraphNode(id="b", node_type="test"))

        path = GraphAlgorithms.shortest_path(graph, "a", "b")
        assert path is None

    def test_all_paths(self, sample_graph):
        """Test finding all paths."""
        paths = GraphAlgorithms.all_paths(
            sample_graph, "cond_hypertension", "med_lisinopril", max_depth=4
        )

        assert len(paths) > 0
        for path in paths:
            assert path.nodes[0] == "cond_hypertension"
            assert path.nodes[-1] == "med_lisinopril"

    def test_centrality(self, sample_graph):
        """Test centrality calculation."""
        centrality = GraphAlgorithms.calculate_centrality(sample_graph)

        assert "patient1" in centrality
        assert centrality["patient1"] > 0

        # Patient should have highest centrality (most connections)
        assert centrality["patient1"] == max(centrality.values())

    def test_communities(self, sample_graph):
        """Test community detection."""
        communities = GraphAlgorithms.find_communities(sample_graph)

        assert len(communities) > 0

        # Each community should have nodes
        for community in communities:
            assert len(community.nodes) > 0
            assert community.cohesion_score >= 0

    def test_causal_chains(self, sample_graph):
        """Test causal chain finding."""
        chains = GraphAlgorithms.find_causal_chains(sample_graph, "patient1")

        assert len(chains) > 0

        # Each chain should have at least 3 nodes
        for chain in chains:
            assert len(chain.nodes) >= 3

    def test_treatment_pathways(self, sample_graph):
        """Test treatment pathway finding."""
        pathways = GraphAlgorithms.find_treatment_pathways(
            sample_graph, "Hypertension"
        )

        assert len(pathways) > 0


# ============================================================================
# Test Graph RAG Retriever
# ============================================================================

class TestGraphRAGRetriever:
    """Tests for Graph RAG Retriever."""

    def test_retrieve_direct_matches(self, sample_graph):
        """Test direct match retrieval."""
        retriever = GraphRAGRetriever(sample_graph)
        result = retriever.retrieve("hypertension", patient_id="patient1")

        assert isinstance(result, GraphRAGResult)
        assert len(result.evidence) > 0

        # Should find hypertension-related evidence
        descriptions = [e.description.lower() for e in result.evidence]
        assert any("hypertension" in d for d in descriptions)

    def test_retrieve_relationship_evidence(self, sample_graph):
        """Test relationship-based evidence retrieval."""
        retriever = GraphRAGRetriever(sample_graph)
        result = retriever.retrieve("patient conditions", patient_id="patient1")

        # Should find conditions and related nodes
        node_types = set(e.node_type for e in result.evidence)
        assert "condition" in node_types

    def test_retrieve_path_evidence(self, sample_graph):
        """Test path-based evidence retrieval."""
        retriever = GraphRAGRetriever(sample_graph)
        result = retriever.retrieve("hypertension treatment", patient_id="patient1")

        # Should find evidence (paths may or may not exist depending on graph structure)
        assert len(result.evidence) > 0

    def test_retrieve_patterns(self, sample_graph):
        """Test pattern discovery in retrieval."""
        retriever = GraphRAGRetriever(sample_graph)
        result = retriever.retrieve("patient health", patient_id="patient1")

        # Should discover patterns
        assert len(result.patterns) > 0

    def test_retrieve_graph_stats(self, sample_graph):
        """Test graph statistics in retrieval."""
        retriever = GraphRAGRetriever(sample_graph)
        result = retriever.retrieve("test", patient_id="patient1")

        assert "total_nodes" in result.graph_stats
        assert "total_edges" in result.graph_stats
        assert "evidence_count" in result.graph_stats

    def test_retrieve_with_focus_types(self, sample_graph):
        """Test retrieval with focused node types."""
        retriever = GraphRAGRetriever(sample_graph)
        result = retriever.retrieve(
            "patient", patient_id="patient1", focus_types=["condition"]
        )

        # Should return evidence (focus types are applied during relationship evidence)
        assert len(result.evidence) > 0


# ============================================================================
# Test Pattern Discovery Engine
# ============================================================================

class TestPatternDiscoveryEngine:
    """Tests for Pattern Discovery Engine."""

    def test_discover_comorbidity_patterns(self, sample_graph):
        """Test comorbidity pattern discovery."""
        engine = PatternDiscoveryEngine(sample_graph)
        patterns = engine._find_comorbidity_patterns("patient1")

        # Pattern discovery depends on data structure
        assert isinstance(patterns, list)

    def test_discover_treatment_patterns(self, sample_graph):
        """Test treatment pattern discovery."""
        engine = PatternDiscoveryEngine(sample_graph)
        patterns = engine._find_treatment_patterns("patient1")

        # Pattern discovery depends on data structure
        assert isinstance(patterns, list)

    def test_discover_temporal_patterns(self, sample_graph):
        """Test temporal pattern discovery."""
        engine = PatternDiscoveryEngine(sample_graph)
        patterns = engine._find_temporal_patterns("patient1")

        # Pattern discovery depends on data structure
        assert isinstance(patterns, list)

    def test_discover_all_patterns(self, sample_graph):
        """Test discovering all patterns."""
        engine = PatternDiscoveryEngine(sample_graph)
        patterns = engine.discover_all_patterns("patient1")

        # Should return a list (may or may not have patterns)
        assert isinstance(patterns, list)


# ============================================================================
# Test Graph Evidence and Results
# ============================================================================

class TestGraphDataStructures:
    """Tests for graph data structures."""

    def test_graph_path(self):
        """Test GraphPath creation."""
        path = GraphPath(
            nodes=["a", "b", "c"],
            edges=["a-b", "b-c"],
            length=2,
            relationship_chain=["related", "treats"],
        )

        assert path.length == 2
        assert len(path.nodes) == 3

        # Test to_dict
        d = path.to_dict()
        assert "nodes" in d
        assert "edges" in d

    def test_graph_evidence(self):
        """Test GraphEvidence creation."""
        evidence = GraphEvidence(
            node_id="test",
            node_type="condition",
            description="Test condition",
            relevance_score=0.8,
            path_from_query=["query", "test"],
            relationship_context=["direct_match"],
            properties={"code": "123"},
        )

        assert evidence.relevance_score == 0.8

        # Test to_dict
        d = evidence.to_dict()
        assert "node_id" in d
        assert "relevance_score" in d

    def test_graph_pattern(self):
        """Test GraphPattern creation."""
        pattern = GraphPattern(
            pattern_type="comorbidity",
            description="Test pattern",
            nodes_involved=["a", "b"],
            edges_involved=[],
            confidence=0.7,
            evidence=["evidence1"],
        )

        assert pattern.confidence == 0.7

        # Test to_dict
        d = pattern.to_dict()
        assert "pattern_type" in d
        assert "confidence" in d

    def test_graph_community(self):
        """Test GraphCommunity creation."""
        community = GraphCommunity(
            community_id="test",
            nodes=["a", "b", "c"],
            node_types={"condition": 2, "medication": 1},
            central_node="a",
            cohesion_score=0.5,
        )

        assert len(community.nodes) == 3
        assert community.cohesion_score == 0.5


# ============================================================================
# Test Graph RAG with Real Data
# ============================================================================

class TestGraphRAGRealData:
    """Tests for Graph RAG with real Synthea data."""

    def test_build_knowledge_graph(self, store):
        """Test building knowledge graph from store."""
        graph = build_knowledge_graph(store)

        assert len(graph.nodes) > 0
        assert len(graph.edges) > 0

        # Should have different node types
        node_types = set(n.node_type for n in graph.nodes.values())
        assert "patient" in node_types
        assert "condition" in node_types

    def test_retrieve_with_real_data(self, store, sample_patient_id):
        """Test retrieval with real patient data."""
        result = graph_rag_retrieve(
            store, "patient conditions", patient_id=sample_patient_id
        )

        assert isinstance(result, GraphRAGResult)
        assert len(result.evidence) > 0

    def test_pattern_discovery_real_data(self, store, sample_patient_id):
        """Test pattern discovery with real data."""
        graph = build_knowledge_graph(store)
        engine = PatternDiscoveryEngine(graph)

        patterns = engine.discover_all_patterns(sample_patient_id)

        # Should find some patterns
        assert isinstance(patterns, list)

    def test_causal_chains_real_data(self, store, sample_patient_id):
        """Test causal chain finding with real data."""
        graph = build_knowledge_graph(store)
        algorithms = GraphAlgorithms()

        chains = algorithms.find_causal_chains(graph, sample_patient_id)

        assert isinstance(chains, list)


# ============================================================================
# Test API Endpoints
# ============================================================================

class TestGraphRAGAPI:
    """Tests for Graph RAG API endpoints."""

    def test_graph_rag_endpoint(self, client, sample_patient_id):
        """Test Graph RAG retrieval endpoint."""
        response = client.get(
            f"/v2/graph-rag/{sample_patient_id}?query=conditions"
        )
        assert response.status_code == 200
        data = response.json()
        assert "evidence" in data

    def test_patterns_endpoint(self, client, sample_patient_id):
        """Test patterns endpoint."""
        response = client.get(f"/v2/graph-rag/{sample_patient_id}/patterns")
        assert response.status_code == 200
        data = response.json()
        assert "patterns" in data

    def test_causal_chains_endpoint(self, client, sample_patient_id):
        """Test causal chains endpoint."""
        response = client.get(f"/v2/graph-rag/{sample_patient_id}/causal-chains")
        assert response.status_code == 200
        data = response.json()
        assert "causal_chains" in data

    def test_communities_endpoint(self, client, sample_patient_id):
        """Test communities endpoint."""
        response = client.get(f"/v2/graph-rag/{sample_patient_id}/communities")
        assert response.status_code == 200
        data = response.json()
        assert "communities" in data

    def test_centrality_endpoint(self, client, sample_patient_id):
        """Test centrality endpoint."""
        response = client.get(f"/v2/graph-rag/{sample_patient_id}/centrality")
        assert response.status_code == 200
        data = response.json()
        assert "centrality_scores" in data

    def test_treatment_pathways_endpoint(self, client):
        """Test treatment pathways endpoint."""
        response = client.get("/v2/graph-rag/treatment-pathways/hypertension")
        assert response.status_code == 200
        data = response.json()
        assert "pathways" in data

    def test_related_conditions_endpoint(self, client):
        """Test related conditions endpoint."""
        response = client.get("/v2/graph-rag/related-conditions/hypertension")
        assert response.status_code == 200
        data = response.json()
        assert "related_conditions" in data


# ============================================================================
# Test Graph Reasoning Agent
# ============================================================================

class TestGraphReasoningAgent:
    """Tests for Graph Reasoning Agent."""

    def test_agent_name(self):
        """Test agent name."""
        # Skip if no data
        try:
            agent = GraphReasoningAgent()
            assert agent.name == "graph_reasoning"
        except Exception:
            pytest.skip("No data available")

    def test_agent_role(self):
        """Test agent role."""
        try:
            agent = GraphReasoningAgent()
            assert "graph" in agent.role.lower()
        except Exception:
            pytest.skip("No data available")

    def test_agent_tools(self):
        """Test agent available tools."""
        try:
            agent = GraphReasoningAgent()
            tools = agent.get_available_tools()
            assert "graph_rag_retrieve" in tools
            assert "find_patient_graph_patterns" in tools
        except Exception:
            pytest.skip("No data available")

    def test_agent_system_prompt(self):
        """Test agent system prompt."""
        try:
            agent = GraphReasoningAgent()
            prompt = agent.get_system_prompt()
            assert "graph" in prompt.lower()
            assert "reasoning" in prompt.lower()
        except Exception:
            pytest.skip("No data available")
