"""
Graph Reasoning Agent - LLM-Powered Agent for Knowledge Graph Reasoning

This agent uses the Graph RAG system to reason over the knowledge graph
structure, finding hidden patterns and relationships that traditional
agents would miss.
"""

from __future__ import annotations

from time import perf_counter
from typing import Any

from .graph_rag import (
    GraphAlgorithms,
    GraphRAGResult,
    GraphRAGRetriever,
    PatternDiscoveryEngine,
)
from .knowledge_graph import build_knowledge_graph
from .llm import LLMProvider
from .reasoning_agents import AgentConclusion, ReasoningAgent, ReasoningStep
from .store import SyntheaStore
from .tools import ToolCategory, tool_registry

# ============================================================================
# Graph Reasoning Tools
# ============================================================================

@tool_registry.tool(
    name="graph_rag_retrieve",
    description="Retrieve evidence using Graph RAG - finds hidden relationships through graph traversal, path analysis, and pattern discovery. Goes beyond vector search.",
    category=ToolCategory.EVIDENCE_RETRIEVAL,
    returns="dict with evidence, paths, patterns, and graph statistics",
    examples=[
        {
            "input": {"query": "diabetes complications", "patient_id": "abc-123"},
            "output": {"evidence": [...], "paths": [...], "patterns": [...]},
        },
    ],
)
def graph_rag_retrieve(query: str, patient_id: str) -> dict[str, Any]:
    """Retrieve evidence using Graph RAG."""
    store = SyntheaStore()
    store.load()

    graph = build_knowledge_graph(store)
    retriever = GraphRAGRetriever(graph)

    result = retriever.retrieve(query, patient_id=patient_id)
    return result.to_dict()


@tool_registry.tool(
    name="find_patient_graph_patterns",
    description="Discover hidden patterns in a patient's health graph: comorbidities, treatment chains, temporal sequences, and outcome patterns.",
    category=ToolCategory.KNOWLEDGE_GRAPH,
    returns="dict with discovered patterns and their confidence scores",
)
def find_patient_graph_patterns(patient_id: str) -> dict[str, Any]:
    """Discover patterns in patient's health graph."""
    store = SyntheaStore()
    store.load()

    graph = build_knowledge_graph(store)
    pattern_engine = PatternDiscoveryEngine(graph)

    patterns = pattern_engine.discover_all_patterns(patient_id)

    return {
        "patient_id": patient_id,
        "patterns": [p.to_dict() for p in patterns],
        "pattern_count": len(patterns),
    }


@tool_registry.tool(
    name="find_causal_chains",
    description="Find causal chains in patient data: condition → treatment → outcome pathways. Useful for understanding treatment effectiveness.",
    category=ToolCategory.KNOWLEDGE_GRAPH,
    returns="dict with causal chains showing treatment pathways",
)
def find_causal_chains(patient_id: str) -> dict[str, Any]:
    """Find causal chains in patient data."""
    store = SyntheaStore()
    store.load()

    graph = build_knowledge_graph(store)
    algorithms = GraphAlgorithms()

    chains = algorithms.find_causal_chains(graph, patient_id)

    return {
        "patient_id": patient_id,
        "causal_chains": [c.to_dict() for c in chains],
        "chain_count": len(chains),
    }


@tool_registry.tool(
    name="find_condition_treatment_pathways",
    description="Find common treatment pathways for a condition across all patients. Shows what treatments are typically used.",
    category=ToolCategory.KNOWLEDGE_GRAPH,
    returns="dict with treatment pathways and their frequency",
)
def find_condition_treatment_pathways(condition_description: str) -> dict[str, Any]:
    """Find treatment pathways for a condition."""
    store = SyntheaStore()
    store.load()

    graph = build_knowledge_graph(store)
    algorithms = GraphAlgorithms()

    pathways = algorithms.find_treatment_pathways(graph, condition_description)

    return {
        "condition": condition_description,
        "pathways": [p.to_dict() for p in pathways],
        "pathway_count": len(pathways),
    }


@tool_registry.tool(
    name="find_related_conditions_graph",
    description="Find conditions related to a given condition through graph traversal. Discovers comorbidities and related conditions.",
    category=ToolCategory.KNOWLEDGE_GRAPH,
    returns="dict with related conditions and their relationships",
)
def find_related_conditions_graph(condition_description: str) -> dict[str, Any]:
    """Find related conditions using graph traversal."""
    store = SyntheaStore()
    store.load()

    graph = build_knowledge_graph(store)

    # Find matching conditions
    matching_conditions = []
    for node in graph.query(node_type="condition"):
        if condition_description.lower() in node.properties.get("description", "").lower():
            matching_conditions.append(node)

    related = []
    for condition in matching_conditions[:3]:
        # Find patients with this condition
        for edge in graph.edges:
            if edge.target == condition.id and edge.edge_type == "has_condition":
                patient_id = edge.source

                # Get other conditions
                other_conditions = graph.get_patient_conditions(patient_id)
                for other in other_conditions:
                    if other.id != condition.id:
                        related.append({
                            "condition": other.properties.get("description", ""),
                            "relationship": "co-occurs with",
                            "patient_id": patient_id[:8] + "...",
                        })

    return {
        "query_condition": condition_description,
        "matching_conditions": [
            c.properties.get("description", "") for c in matching_conditions
        ],
        "related_conditions": related[:20],
    }


@tool_registry.tool(
    name="get_patient_graph_summary",
    description="Get a summary of a patient's health knowledge graph: nodes, edges, communities, and key patterns.",
    category=ToolCategory.KNOWLEDGE_GRAPH,
    returns="dict with graph summary and statistics",
)
def get_patient_graph_summary(patient_id: str) -> dict[str, Any]:
    """Get a summary of patient's health graph."""
    store = SyntheaStore()
    store.load()

    graph = build_knowledge_graph(store)

    # Get patient subgraph
    subgraph = graph.get_subgraph(patient_id, depth=2)

    # Calculate statistics
    algorithms = GraphAlgorithms()
    centrality = algorithms.calculate_centrality(subgraph)
    communities = algorithms.find_communities(subgraph)

    # Get node type counts
    node_types = {}
    for node in subgraph.nodes.values():
        node_types[node.node_type] = node_types.get(node.node_type, 0) + 1

    # Get most central nodes
    top_central = sorted(
        centrality.items(),
        key=lambda x: x[1],
        reverse=True,
    )[:5]

    return {
        "patient_id": patient_id,
        "graph_stats": {
            "total_nodes": len(subgraph.nodes),
            "total_edges": len(subgraph.edges),
            "node_types": node_types,
            "community_count": len(communities),
        },
        "most_central_nodes": [
            {
                "node_id": nid,
                "centrality": score,
                "description": graph.get_node(nid).properties.get("description", "") if graph.get_node(nid) else "",
            }
            for nid, score in top_central
        ],
        "communities": [
            {
                "size": len(c.nodes),
                "types": c.node_types,
                "cohesion": c.cohesion_score,
            }
            for c in communities[:3]
        ],
    }


# ============================================================================
# Graph Reasoning Agent
# ============================================================================

class GraphReasoningAgent(ReasoningAgent):
    """Agent specialized in reasoning over knowledge graph structure.

    This agent uses Graph RAG to find hidden patterns and relationships
    that traditional agents would miss:

    1. **Graph Traversal**: Explores relationships through BFS/DFS
    2. **Path Analysis**: Finds causal chains and treatment pathways
    3. **Pattern Discovery**: Identifies comorbidities and temporal patterns
    4. **Community Detection**: Finds clusters of related health issues
    5. **Centrality Analysis**: Identifies most important health factors

    This is REVOLUTIONARY because it provides EXPLAINABLE reasoning
    paths through the knowledge graph.
    """

    name = "graph_reasoning"
    role = "graph-based clinical reasoner"
    description = "Reasons over knowledge graph structure to find hidden patterns and relationships"

    def __init__(
        self,
        llm: LLMProvider | None = None,
        store: SyntheaStore | None = None,
    ):
        self.store = store or SyntheaStore()
        self.store.load()

        # Build knowledge graph
        self.graph = build_knowledge_graph(self.store)
        self.retriever = GraphRAGRetriever(self.graph)
        self.pattern_engine = PatternDiscoveryEngine(self.graph)
        self.algorithms = GraphAlgorithms()

        super().__init__(llm=llm)

    def get_system_prompt(self) -> str:
        return """You are an expert graph-based clinical reasoner. Your unique capability
is reasoning over knowledge graph structure to find hidden patterns and relationships.

Your approach:
1. **Graph Traversal**: Explore relationships between conditions, medications, and outcomes
2. **Path Analysis**: Find causal chains (condition → treatment → outcome)
3. **Pattern Discovery**: Identify comorbidities, treatment patterns, and temporal sequences
4. **Community Detection**: Find clusters of related health issues
5. **Centrality Analysis**: Identify the most important health factors

Key principles:
- Follow relationship chains to find indirect connections
- Look for patterns across multiple patients
- Identify causal pathways, not just correlations
- Provide explainable reasoning paths through the graph
- Consider temporal ordering of events

You are analyzing SYNTHETIC patient data for research purposes only.
This is NOT medical advice and should NOT be used for clinical decisions."""

    def get_available_tools(self) -> list[str]:
        return [
            "get_patient_record",
            "get_patient_conditions",
            "get_patient_medications",
            "get_patient_observations",
            "graph_rag_retrieve",
            "find_patient_graph_patterns",
            "find_causal_chains",
            "find_condition_treatment_pathways",
            "find_related_conditions_graph",
            "get_patient_graph_summary",
        ]

    async def investigate(self, patient_id: str, question: str) -> AgentConclusion:
        """Run a graph-based investigation."""
        start_time = perf_counter()
        self._reasoning_chain = []
        self._tool_call_count = 0

        # Step 1: Get graph summary
        graph_summary = self._get_graph_summary(patient_id)

        self._reasoning_chain.append(ReasoningStep(
            thought=f"Patient graph: {graph_summary['graph_stats']['total_nodes']} nodes, "
                    f"{graph_summary['graph_stats']['total_edges']} edges, "
                    f"{graph_summary['graph_stats']['community_count']} communities",
            confidence=0.9,
        ))

        # Step 2: Retrieve evidence using Graph RAG
        rag_result = self.retriever.retrieve(question, patient_id=patient_id)

        self._reasoning_chain.append(ReasoningStep(
            thought=f"Graph RAG found {len(rag_result.evidence)} evidence items, "
                    f"{len(rag_result.paths)} paths, {len(rag_result.patterns)} patterns",
            confidence=0.8,
        ))

        # Step 3: Discover patterns
        patterns = self.pattern_engine.discover_all_patterns(patient_id)

        self._reasoning_chain.append(ReasoningStep(
            thought=f"Discovered {len(patterns)} patterns in patient's health graph",
            confidence=0.8,
        ))

        # Step 4: Find causal chains
        causal_chains = self.algorithms.find_causal_chains(self.graph, patient_id)

        self._reasoning_chain.append(ReasoningStep(
            thought=f"Found {len(causal_chains)} causal chains (condition → treatment → outcome)",
            confidence=0.8,
        ))

        # Step 5: Generate conclusion
        evidence_texts = []
        for item in rag_result.evidence[:10]:
            evidence_texts.append(
                f"[{item.node_type}] {item.description} "
                f"(path: {' → '.join(item.path_from_query[:3])})"
            )

        for pattern in patterns[:5]:
            evidence_texts.append(
                f"[Pattern: {pattern.pattern_type}] {pattern.description}"
            )

        for chain in causal_chains[:3]:
            evidence_texts.append(
                f"[Causal Chain] {' → '.join(chain.nodes[:4])}"
            )

        # Calculate confidence based on evidence quality
        confidence = min(0.5 + len(rag_result.evidence) * 0.02, 0.9)
        if patterns:
            confidence = min(confidence + 0.1, 0.95)
        if causal_chains:
            confidence = min(confidence + 0.05, 0.95)

        conclusion = AgentConclusion(
            summary=self._generate_summary(
                patient_id, question, rag_result, patterns, causal_chains
            ),
            key_findings=self._extract_key_findings(
                rag_result, patterns, causal_chains
            ),
            evidence=evidence_texts,
            confidence=confidence,
            uncertainties=self._identify_uncertainties(rag_result),
            recommendations=self._generate_recommendations(patterns, causal_chains),
            reasoning_chain=self._reasoning_chain,
        )

        duration_ms = (perf_counter() - start_time) * 1000
        conclusion.reasoning_chain.insert(0, ReasoningStep(
            thought=f"Graph reasoning completed in {duration_ms:.0f}ms",
            confidence=1.0,
        ))

        return conclusion

    def _get_graph_summary(self, patient_id: str) -> dict[str, Any]:
        """Get summary of patient's graph."""
        subgraph = self.graph.get_subgraph(patient_id, depth=2)

        node_types = {}
        for node in subgraph.nodes.values():
            node_types[node.node_type] = node_types.get(node.node_type, 0) + 1

        communities = self.algorithms.find_communities(subgraph)

        return {
            "graph_stats": {
                "total_nodes": len(subgraph.nodes),
                "total_edges": len(subgraph.edges),
                "node_types": node_types,
                "community_count": len(communities),
            }
        }

    def _generate_summary(
        self,
        patient_id: str,
        question: str,
        rag_result: GraphRAGResult,
        patterns: list,
        causal_chains: list,
    ) -> str:
        """Generate a summary of findings."""
        parts = []

        parts.append(f"Graph-based analysis for patient {patient_id[:8]}...")

        if rag_result.evidence:
            parts.append(f"Found {len(rag_result.evidence)} evidence items through graph traversal.")

        if rag_result.paths:
            parts.append(f"Discovered {len(rag_result.paths)} relationship paths.")

        if patterns:
            pattern_types = set(p.pattern_type for p in patterns)
            parts.append(f"Identified patterns: {', '.join(pattern_types)}.")

        if causal_chains:
            parts.append(f"Found {len(causal_chains)} causal chains showing treatment pathways.")

        return " ".join(parts)

    def _extract_key_findings(
        self,
        rag_result: GraphRAGResult,
        patterns: list,
        causal_chains: list,
    ) -> list[str]:
        """Extract key findings from analysis."""
        findings = []

        # Top evidence items
        for item in rag_result.evidence[:3]:
            findings.append(
                f"{item.node_type.title()}: {item.description[:50]}"
            )

        # Key patterns
        for pattern in patterns[:2]:
            findings.append(
                f"Pattern: {pattern.description[:50]}"
            )

        # Causal chains
        for chain in causal_chains[:2]:
            if len(chain.nodes) >= 3:
                findings.append(
                    f"Chain: {chain.nodes[0][:15]} → {chain.nodes[1][:15]} → {chain.nodes[2][:15]}"
                )

        return findings[:10]

    def _identify_uncertainties(self, rag_result: GraphRAGResult) -> list[str]:
        """Identify uncertainties in the analysis."""
        uncertainties = []

        if not rag_result.evidence:
            uncertainties.append("No evidence found through graph traversal")

        if not rag_result.paths:
            uncertainties.append("No relationship paths discovered")

        if rag_result.graph_stats.get("total_nodes", 0) < 10:
            uncertainties.append("Limited graph data available")

        return uncertainties

    def _generate_recommendations(
        self,
        patterns: list,
        causal_chains: list,
    ) -> list[str]:
        """Generate recommendations based on findings."""
        recommendations = []

        if patterns:
            recommendations.append("Review discovered patterns for clinical significance")

        if causal_chains:
            recommendations.append("Analyze causal chains for treatment effectiveness")

        recommendations.append("Consider graph structure for comprehensive patient view")

        return recommendations
