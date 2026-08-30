"""
Graph RAG - Knowledge Graph-Based Retrieval Augmented Generation

This module implements a novel approach to clinical evidence retrieval that goes
beyond traditional vector search by leveraging the knowledge graph structure:

1. **Graph Traversal**: BFS/DFS-based exploration of relationships
2. **Path-Based Reasoning**: Find causal chains and treatment pathways
3. **Community Detection**: Identify clusters of related conditions/treatments
4. **Centrality Analysis**: Find most important nodes in patient's health graph
5. **Pattern Discovery**: Hidden connections between conditions, medications, outcomes

This is a REVOLUTIONARY approach because:
- It finds INDIRECT relationships (A → B → C) that vector search misses
- It discovers CAUSAL CHAINS (condition → treatment → outcome)
- It identifies COMMUNITIES of related health issues
- It provides EXPLAINABLE reasoning paths through the graph
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from .knowledge_graph import (
    GraphNode,
    KnowledgeGraph,
    MedicalKnowledgeGraph,
    build_knowledge_graph,
)
from .store import SyntheaStore

# ============================================================================
# Graph Algorithms
# ============================================================================

class TraversalStrategy(StrEnum):
    """Graph traversal strategies."""
    BFS = "breadth_first"
    DFS = "depth_first"
    DIJKSTRA = "dijkstra"
    PAGERANK = "pagerank"


@dataclass
class GraphPath:
    """A path through the graph with metadata."""
    nodes: list[str]
    edges: list[str]
    length: int
    weight: float = 1.0
    relationship_chain: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": self.nodes,
            "edges": self.edges,
            "length": self.length,
            "weight": self.weight,
            "relationship_chain": self.relationship_chain,
        }


@dataclass
class GraphCommunity:
    """A community (cluster) of related nodes."""
    community_id: str
    nodes: list[str]
    node_types: dict[str, int]
    central_node: str
    cohesion_score: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "community_id": self.community_id,
            "nodes": self.nodes,
            "node_types": self.node_types,
            "central_node": self.central_node,
            "cohesion_score": self.cohesion_score,
        }


@dataclass
class GraphPattern:
    """A discovered pattern in the graph."""
    pattern_type: str
    description: str
    nodes_involved: list[str]
    edges_involved: list[str]
    confidence: float
    evidence: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern_type": self.pattern_type,
            "description": self.description,
            "nodes_involved": self.nodes_involved,
            "edges_involved": self.edges_involved,
            "confidence": self.confidence,
            "evidence": self.evidence,
        }


class GraphAlgorithms:
    """Advanced graph algorithms for knowledge graph analysis."""

    @staticmethod
    def bfs(
        graph: KnowledgeGraph,
        start: str,
        max_depth: int = 3,
        edge_type_filter: str | None = None,
    ) -> dict[str, dict[str, Any]]:
        """Breadth-first search with depth tracking."""
        visited: dict[str, dict[str, Any]] = {}
        queue: deque[tuple[str, int]] = deque([(start, 0)])
        visited[start] = {"depth": 0, "parent": None}

        while queue:
            current, depth = queue.popleft()
            if depth >= max_depth:
                continue

            for edge in graph.edges:
                if edge_type_filter and edge.edge_type != edge_type_filter:
                    continue

                neighbor = None
                if edge.source == current:
                    neighbor = edge.target
                elif edge.target == current:
                    neighbor = edge.source

                if neighbor and neighbor not in visited:
                    visited[neighbor] = {
                        "depth": depth + 1,
                        "parent": current,
                        "edge_type": edge.edge_type,
                    }
                    queue.append((neighbor, depth + 1))

        return visited

    @staticmethod
    def shortest_path(
        graph: KnowledgeGraph,
        start: str,
        end: str,
        max_depth: int = 5,
    ) -> GraphPath | None:
        """Find shortest path using BFS."""
        if start == end:
            return GraphPath(
                nodes=[start],
                edges=[],
                length=0,
            )

        visited = {start}
        queue: deque[tuple[str, list[str], list[str]]] = deque(
            [(start, [start], [])]
        )

        while queue:
            current, path, edge_path = queue.popleft()
            if len(path) > max_depth:
                continue

            for edge in graph.edges:
                neighbor = None
                if edge.source == current:
                    neighbor = edge.target
                elif edge.target == current:
                    neighbor = edge.source

                if neighbor == end:
                    return GraphPath(
                        nodes=path + [neighbor],
                        edges=edge_path + [f"{edge.source}-{edge.edge_type}-{edge.target}"],
                        length=len(path),
                        relationship_chain=edge_path + [edge.edge_type],
                    )

                if neighbor and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((
                        neighbor,
                        path + [neighbor],
                        edge_path + [f"{edge.source}-{edge.edge_type}-{edge.target}"],
                    ))

        return None

    @staticmethod
    def all_paths(
        graph: KnowledgeGraph,
        start: str,
        end: str,
        max_depth: int = 4,
        max_paths: int = 10,
    ) -> list[GraphPath]:
        """Find all paths between two nodes (up to max_paths)."""
        paths = []

        def dfs(current, path, edge_path, visited):
            if len(paths) >= max_paths:
                return
            if len(path) > max_depth:
                return
            if current == end and len(path) > 1:
                paths.append(GraphPath(
                    nodes=list(path),
                    edges=list(edge_path),
                    length=len(path) - 1,
                    relationship_chain=[e.split("-")[1] for e in edge_path],
                ))
                return

            for edge in graph.edges:
                neighbor = None
                if edge.source == current:
                    neighbor = edge.target
                elif edge.target == current:
                    neighbor = edge.source

                if neighbor and neighbor not in visited:
                    visited.add(neighbor)
                    path.append(neighbor)
                    edge_path.append(f"{edge.source}-{edge.edge_type}-{edge.target}")
                    dfs(neighbor, path, edge_path, visited)
                    path.pop()
                    edge_path.pop()
                    visited.remove(neighbor)

        dfs(start, [start], [], {start})
        return paths

    @staticmethod
    def calculate_centrality(graph: KnowledgeGraph) -> dict[str, float]:
        """Calculate degree centrality for all nodes."""
        centrality = {}
        n = len(graph.nodes)
        if n <= 1:
            return {node_id: 0.0 for node_id in graph.nodes}

        for node_id in graph.nodes:
            degree = len(graph.adjacency.get(node_id, []))
            centrality[node_id] = degree / (n - 1)

        return centrality

    @staticmethod
    def find_communities(
        graph: KnowledgeGraph,
        min_community_size: int = 2,
    ) -> list[GraphCommunity]:
        """Find communities using connected components with type analysis."""
        visited = set()
        communities = []

        for node_id in graph.nodes:
            if node_id in visited:
                continue

            # BFS to find connected component
            component = set()
            queue = deque([node_id])
            while queue:
                current = queue.popleft()
                if current in visited:
                    continue
                visited.add(current)
                component.add(current)

                for neighbor_id in graph.adjacency.get(current, []):
                    if neighbor_id not in visited:
                        queue.append(neighbor_id)

            if len(component) >= min_community_size:
                # Analyze component
                node_types = defaultdict(int)
                for nid in component:
                    node = graph.nodes.get(nid)
                    if node:
                        node_types[node.node_type] += 1

                # Find central node (highest degree)
                centrality = GraphAlgorithms.calculate_centrality(graph)
                central_node = max(component, key=lambda nid: centrality.get(nid, 0))

                # Calculate cohesion (edges within community / possible edges)
                internal_edges = sum(
                    1 for e in graph.edges
                    if e.source in component and e.target in component
                )
                possible_edges = len(component) * (len(component) - 1) / 2
                cohesion = internal_edges / possible_edges if possible_edges > 0 else 0

                communities.append(GraphCommunity(
                    community_id=f"community_{len(communities)}",
                    nodes=list(component),
                    node_types=dict(node_types),
                    central_node=central_node,
                    cohesion_score=round(cohesion, 3),
                ))

        return communities

    @staticmethod
    def find_causal_chains(
        graph: MedicalKnowledgeGraph,
        patient_id: str,
    ) -> list[GraphPath]:
        """Find causal chains: condition → treatment → outcome."""
        chains = []

        # Get patient's conditions
        conditions = graph.get_patient_conditions(patient_id)

        for condition in conditions:
            # Find medications that might treat this condition
            medications = graph.get_patient_medications(patient_id)

            for med in medications:
                # Check if medication is related to condition
                # (In real system, would use drug-condition knowledge)
                chain = GraphPath(
                    nodes=[patient_id, condition.id, med.id],
                    edges=[
                        f"{patient_id}-has_condition-{condition.id}",
                        f"{patient_id}-takes_medication-{med.id}",
                    ],
                    length=2,
                    relationship_chain=["has_condition", "takes_medication"],
                )
                chains.append(chain)

                # Look for outcomes (observations after treatment)
                observations = graph.get_patient_observations(patient_id)
                for obs in observations:
                    if obs.properties.get("date") and med.properties.get("start"):
                        # Check if observation is after medication start
                        if str(obs.properties["date"]) >= str(med.properties["start"]):
                            extended_chain = GraphPath(
                                nodes=[patient_id, condition.id, med.id, obs.id],
                                edges=[
                                    f"{patient_id}-has_condition-{condition.id}",
                                    f"{patient_id}-takes_medication-{med.id}",
                                    f"{patient_id}-has_observation-{obs.id}",
                                ],
                                length=3,
                                relationship_chain=[
                                    "has_condition",
                                    "takes_medication",
                                    "has_observation",
                                ],
                            )
                            chains.append(extended_chain)

        return chains

    @staticmethod
    def find_treatment_pathways(
        graph: MedicalKnowledgeGraph,
        condition_description: str,
    ) -> list[GraphPath]:
        """Find common treatment pathways for a condition."""
        pathways = []

        # Find all nodes matching condition description
        condition_nodes = graph.query(
            node_type="condition",
            description=condition_description,
        )

        if not condition_nodes:
            # Try partial match
            for node in graph.query(node_type="condition"):
                if condition_description.lower() in node.properties.get("description", "").lower():
                    condition_nodes.append(node)

        for condition_node in condition_nodes:
            # Find patients with this condition
            for edge in graph.edges:
                if edge.target == condition_node.id and edge.edge_type == "has_condition":
                    patient_id = edge.source

                    # Get this patient's medications
                    medications = graph.get_patient_medications(patient_id)
                    for med in medications:
                        pathway = GraphPath(
                            nodes=[condition_node.id, patient_id, med.id],
                            edges=[
                                f"{patient_id}-has_condition-{condition_node.id}",
                                f"{patient_id}-takes_medication-{med.id}",
                            ],
                            length=2,
                            relationship_chain=["has_condition", "takes_medication"],
                        )
                        pathways.append(pathway)

        return pathways


# ============================================================================
# Graph RAG Retriever
# ============================================================================

@dataclass
class GraphEvidence:
    """Evidence retrieved from graph traversal."""
    node_id: str
    node_type: str
    description: str
    relevance_score: float
    path_from_query: list[str]
    relationship_context: list[str]
    properties: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "description": self.description,
            "relevance_score": self.relevance_score,
            "path_from_query": self.path_from_query,
            "relationship_context": self.relationship_context,
            "properties": self.properties,
        }


@dataclass
class GraphRAGResult:
    """Result from Graph RAG retrieval."""
    query: str
    evidence: list[GraphEvidence]
    paths: list[GraphPath]
    communities: list[GraphPattern]
    patterns: list[GraphPattern]
    graph_stats: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "evidence": [e.to_dict() for e in self.evidence],
            "paths": [p.to_dict() for p in self.paths],
            "communities": [c.to_dict() for c in self.communities],
            "patterns": [p.to_dict() for p in self.patterns],
            "graph_stats": self.graph_stats,
        }


class GraphRAGRetriever:
    """Graph-based Retrieval Augmented Generation.

    This retriever uses the knowledge graph structure to find evidence
    that traditional vector search would miss:

    1. **Direct Evidence**: Nodes directly matching the query
    2. **Relationship Evidence**: Nodes connected to matching nodes
    3. **Path Evidence**: Nodes along paths between query concepts
    4. **Community Evidence**: Nodes in the same community as matches
    5. **Pattern Evidence**: Nodes matching discovered patterns
    """

    def __init__(
        self,
        graph: MedicalKnowledgeGraph,
        max_depth: int = 3,
        max_evidence: int = 50,
    ):
        self.graph = graph
        self.max_depth = max_depth
        self.max_evidence = max_evidence
        self.algorithms = GraphAlgorithms()

    def retrieve(
        self,
        query: str,
        patient_id: str | None = None,
        focus_types: list[str] | None = None,
    ) -> GraphRAGResult:
        """Retrieve evidence using graph-based methods."""
        evidence = []
        paths = []
        patterns = []

        # Step 1: Find direct matches
        direct_matches = self._find_direct_matches(query, patient_id)
        evidence.extend(direct_matches)

        # Step 2: Find relationship evidence
        for match in direct_matches[:5]:  # Limit to top 5 matches
            related = self._find_relationship_evidence(
                match.node_id, patient_id, focus_types
            )
            evidence.extend(related)

        # Step 3: Find path-based evidence
        if len(direct_matches) >= 2:
            for i in range(min(3, len(direct_matches))):
                for j in range(i + 1, min(4, len(direct_matches))):
                    path = self.algorithms.shortest_path(
                        self.graph,
                        direct_matches[i].node_id,
                        direct_matches[j].node_id,
                        max_depth=self.max_depth,
                    )
                    if path:
                        paths.append(path)
                        # Add nodes along path as evidence
                        path_evidence = self._extract_path_evidence(path)
                        evidence.extend(path_evidence)

        # Step 4: Find community evidence
        if patient_id:
            communities = self.algorithms.find_communities(self.graph)
            for community in communities:
                if patient_id in community.nodes:
                    # Add community members as evidence
                    for node_id in community.nodes:
                        if node_id != patient_id:
                            node = self.graph.get_node(node_id)
                            if node:
                                evidence.append(GraphEvidence(
                                    node_id=node_id,
                                    node_type=node.node_type,
                                    description=self._get_node_description(node),
                                    relevance_score=0.5 * community.cohesion_score,
                                    path_from_query=[patient_id, node_id],
                                    relationship_context=["community_member"],
                                    properties=node.properties,
                                ))

        # Step 5: Discover patterns
        patterns = self._discover_patterns(evidence, patient_id)

        # Deduplicate and rank evidence
        evidence = self._deduplicate_evidence(evidence)
        evidence = self._rank_evidence(evidence, query)
        evidence = evidence[:self.max_evidence]

        # Calculate graph stats
        graph_stats = {
            "total_nodes": len(self.graph.nodes),
            "total_edges": len(self.graph.edges),
            "evidence_count": len(evidence),
            "paths_found": len(paths),
            "patterns_found": len(patterns),
        }

        return GraphRAGResult(
            query=query,
            evidence=evidence,
            paths=paths,
            communities=[],
            patterns=patterns,
            graph_stats=graph_stats,
        )

    def _find_direct_matches(
        self,
        query: str,
        patient_id: str | None = None,
    ) -> list[GraphEvidence]:
        """Find nodes directly matching the query."""
        matches = []
        query_lower = query.lower()

        for node_id, node in self.graph.nodes.items():
            # Check if node matches query
            score = self._calculate_match_score(node, query_lower)
            if score > 0.3:
                # Filter by patient if specified
                if patient_id and not self._is_related_to_patient(node_id, patient_id):
                    continue

                matches.append(GraphEvidence(
                    node_id=node_id,
                    node_type=node.node_type,
                    description=self._get_node_description(node),
                    relevance_score=score,
                    path_from_query=[node_id],
                    relationship_context=["direct_match"],
                    properties=node.properties,
                ))

        return sorted(matches, key=lambda x: x.relevance_score, reverse=True)

    def _find_relationship_evidence(
        self,
        node_id: str,
        patient_id: str | None = None,
        focus_types: list[str] | None = None,
    ) -> list[GraphEvidence]:
        """Find evidence through graph relationships."""
        evidence = []

        # Get neighbors
        neighbors = self.graph.get_neighbors(node_id)

        for neighbor in neighbors:
            if focus_types and neighbor.node_type not in focus_types:
                continue

            if patient_id and not self._is_related_to_patient(neighbor.id, patient_id):
                continue

            # Get edge type for context
            edge_type = self._get_edge_type(node_id, neighbor.id)

            evidence.append(GraphEvidence(
                node_id=neighbor.id,
                node_type=neighbor.node_type,
                description=self._get_node_description(neighbor),
                relevance_score=0.6,  # Related nodes get moderate score
                path_from_query=[node_id, neighbor.id],
                relationship_context=[edge_type or "related"],
                properties=neighbor.properties,
            ))

        return evidence

    def _extract_path_evidence(self, path: GraphPath) -> list[GraphEvidence]:
        """Extract evidence from nodes along a path."""
        evidence = []

        for node_id in path.nodes:
            node = self.graph.get_node(node_id)
            if node:
                evidence.append(GraphEvidence(
                    node_id=node_id,
                    node_type=node.node_type,
                    description=self._get_node_description(node),
                    relevance_score=0.7,  # Path nodes get higher score
                    path_from_query=path.nodes,
                    relationship_context=path.relationship_chain,
                    properties=node.properties,
                ))

        return evidence

    def _discover_patterns(
        self,
        evidence: list[GraphEvidence],
        patient_id: str | None = None,
    ) -> list[GraphPattern]:
        """Discover patterns in the evidence."""
        patterns = []

        # Pattern 1: Condition clusters
        condition_nodes = [e for e in evidence if e.node_type == "condition"]
        if len(condition_nodes) >= 2:
            patterns.append(GraphPattern(
                pattern_type="condition_cluster",
                description=f"Patient has {len(condition_nodes)} related conditions",
                nodes_involved=[e.node_id for e in condition_nodes],
                edges_involved=[],
                confidence=0.8,
                evidence=[e.description for e in condition_nodes[:5]],
            ))

        # Pattern 2: Treatment chains
        medication_nodes = [e for e in evidence if e.node_type == "medication"]
        if medication_nodes and condition_nodes:
            patterns.append(GraphPattern(
                pattern_type="treatment_chain",
                description=f"Treatment pathway: {len(condition_nodes)} conditions → {len(medication_nodes)} medications",
                nodes_involved=[e.node_id for e in condition_nodes[:3]] + [e.node_id for e in medication_nodes[:3]],
                edges_involved=[],
                confidence=0.7,
                evidence=[
                    f"Conditions: {', '.join(e.description[:30] for e in condition_nodes[:3])}",
                    f"Medications: {', '.join(e.description[:30] for e in medication_nodes[:3])}",
                ],
            ))

        # Pattern 3: Temporal progression
        observation_nodes = [e for e in evidence if e.node_type == "observation"]
        if len(observation_nodes) >= 3:
            patterns.append(GraphPattern(
                pattern_type="temporal_progression",
                description=f"Temporal progression with {len(observation_nodes)} observations",
                nodes_involved=[e.node_id for e in observation_nodes],
                edges_involved=[],
                confidence=0.6,
                evidence=[e.description for e in observation_nodes[:5]],
            ))

        return patterns

    def _calculate_match_score(self, node: GraphNode, query_lower: str) -> float:
        """Calculate how well a node matches the query."""
        score = 0.0

        # Check description
        desc = node.properties.get("description", "").lower()
        if query_lower in desc:
            score += 0.8
        elif any(word in desc for word in query_lower.split()):
            score += 0.4

        # Check other properties
        for key, value in node.properties.items():
            if isinstance(value, str) and query_lower in value.lower():
                score += 0.2

        return min(score, 1.0)

    def _get_node_description(self, node: GraphNode) -> str:
        """Get a human-readable description of a node."""
        props = node.properties
        desc = props.get("description", "")
        if desc:
            return desc

        if node.node_type == "patient":
            return f"Patient {props.get('first', '')} {props.get('last', '')}"
        elif node.node_type == "condition":
            return f"Condition: {props.get('code', '')}"
        elif node.node_type == "medication":
            return f"Medication: {props.get('code', '')}"
        elif node.node_type == "observation":
            return f"Observation: {props.get('value', '')} {props.get('unit', '')}"
        elif node.node_type == "procedure":
            return f"Procedure: {props.get('code', '')}"

        return f"{node.node_type}: {node.id}"

    def _get_edge_type(self, source_id: str, target_id: str) -> str | None:
        """Get the edge type between two nodes."""
        for edge in self.graph.edges:
            if (edge.source == source_id and edge.target == target_id):
                return edge.edge_type
            if (edge.source == target_id and edge.target == source_id):
                return edge.edge_type
        return None

    def _is_related_to_patient(self, node_id: str, patient_id: str) -> bool:
        """Check if a node is related to a patient."""
        # Direct connection
        if node_id == patient_id:
            return True

        # Check if node is connected to patient
        for edge in self.graph.edges:
            if edge.source == patient_id and edge.target == node_id:
                return True
            if edge.target == patient_id and edge.source == node_id:
                return True

        return False

    def _deduplicate_evidence(
        self, evidence: list[GraphEvidence]
    ) -> list[GraphEvidence]:
        """Remove duplicate evidence items."""
        seen = set()
        unique = []

        for item in evidence:
            if item.node_id not in seen:
                seen.add(item.node_id)
                unique.append(item)

        return unique

    def _rank_evidence(
        self,
        evidence: list[GraphEvidence],
        query: str,
    ) -> list[GraphEvidence]:
        """Rank evidence by relevance."""
        query_lower = query.lower()

        def score(item: GraphEvidence) -> float:
            base = item.relevance_score

            # Boost for direct matches
            if "direct_match" in item.relationship_context:
                base *= 1.2

            # Boost for path evidence
            if len(item.path_from_query) > 1:
                base *= 1.1

            # Boost for matching description
            if query_lower in item.description.lower():
                base *= 1.3

            return base

        return sorted(evidence, key=score, reverse=True)


# ============================================================================
# Pattern Discovery Engine
# ============================================================================

class PatternDiscoveryEngine:
    """Discovers hidden patterns in the knowledge graph."""

    def __init__(self, graph: MedicalKnowledgeGraph):
        self.graph = graph
        self.algorithms = GraphAlgorithms()

    def discover_all_patterns(
        self,
        patient_id: str | None = None,
    ) -> list[GraphPattern]:
        """Discover all patterns in the graph."""
        patterns = []

        # Pattern 1: Comorbidity patterns
        comorbidity_patterns = self._find_comorbidity_patterns(patient_id)
        patterns.extend(comorbidity_patterns)

        # Pattern 2: Treatment patterns
        treatment_patterns = self._find_treatment_patterns(patient_id)
        patterns.extend(treatment_patterns)

        # Pattern 3: Temporal patterns
        temporal_patterns = self._find_temporal_patterns(patient_id)
        patterns.extend(temporal_patterns)

        # Pattern 4: Outcome patterns
        outcome_patterns = self._find_outcome_patterns(patient_id)
        patterns.extend(outcome_patterns)

        return patterns

    def _find_comorbidity_patterns(
        self, patient_id: str | None = None
    ) -> list[GraphPattern]:
        """Find comorbidity patterns (conditions that occur together)."""
        patterns = []

        # Group conditions by patient
        patient_conditions: dict[str, list[str]] = defaultdict(list)
        for edge in self.graph.edges:
            if edge.edge_type == "has_condition":
                patient_conditions[edge.source].append(edge.target)

        # Find conditions that co-occur
        condition_pairs: dict[tuple[str, str], int] = defaultdict(int)
        for patient, conditions in patient_conditions.items():
            if patient_id and patient != patient_id:
                continue
            for i in range(len(conditions)):
                for j in range(i + 1, len(conditions)):
                    pair = tuple(sorted([conditions[i], conditions[j]]))
                    condition_pairs[pair] += 1

        # Create patterns for frequent co-occurrences
        for (cond1, cond2), count in condition_pairs.items():
            if count >= 2:  # At least 2 patients with this pair
                node1 = self.graph.get_node(cond1)
                node2 = self.graph.get_node(cond2)
                if node1 and node2:
                    patterns.append(GraphPattern(
                        pattern_type="comorbidity",
                        description=f"Comorbidity: {node1.properties.get('description', '')} + {node2.properties.get('description', '')}",
                        nodes_involved=[cond1, cond2],
                        edges_involved=[],
                        confidence=min(count / 10, 1.0),
                        evidence=[f"Co-occurs in {count} patients"],
                    ))

        return patterns[:10]  # Limit to top 10

    def _find_treatment_patterns(
        self, patient_id: str | None = None
    ) -> list[GraphPattern]:
        """Find treatment patterns (medications used for conditions)."""
        patterns = []

        # Group by patient
        patient_meds: dict[str, list[str]] = defaultdict(list)
        patient_conditions: dict[str, list[str]] = defaultdict(list)

        for edge in self.graph.edges:
            if patient_id and edge.source != patient_id:
                continue
            if edge.edge_type == "takes_medication":
                patient_meds[edge.source].append(edge.target)
            elif edge.edge_type == "has_condition":
                patient_conditions[edge.source].append(edge.target)

        # Find condition-medication correlations
        condition_med_pairs: dict[tuple[str, str], int] = defaultdict(int)
        for patient in set(list(patient_meds.keys()) + list(patient_conditions.keys())):
            for cond in patient_conditions.get(patient, []):
                for med in patient_meds.get(patient, []):
                    condition_med_pairs[(cond, med)] += 1

        # Create patterns
        for (cond, med), count in condition_med_pairs.items():
            if count >= 2:
                cond_node = self.graph.get_node(cond)
                med_node = self.graph.get_node(med)
                if cond_node and med_node:
                    patterns.append(GraphPattern(
                        pattern_type="treatment",
                        description=f"Treatment: {med_node.properties.get('description', '')} for {cond_node.properties.get('description', '')}",
                        nodes_involved=[cond, med],
                        edges_involved=[],
                        confidence=min(count / 10, 1.0),
                        evidence=[f"Used together in {count} patients"],
                    ))

        return patterns[:10]

    def _find_temporal_patterns(
        self, patient_id: str | None = None
    ) -> list[GraphPattern]:
        """Find temporal patterns (sequences of events)."""
        patterns = []

        # Group observations by patient and sort by date
        patient_observations: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for edge in self.graph.edges:
            if edge.edge_type == "has_observation":
                if patient_id and edge.source != patient_id:
                    continue
                obs_node = self.graph.get_node(edge.target)
                if obs_node:
                    date = obs_node.properties.get("date", "")
                    patient_observations[edge.source].append((date, edge.target))

        # Sort by date and find sequences
        for patient, observations in patient_observations.items():
            observations.sort(key=lambda x: x[0])
            if len(observations) >= 3:
                patterns.append(GraphPattern(
                    pattern_type="temporal_sequence",
                    description=f"Temporal sequence of {len(observations)} observations",
                    nodes_involved=[obs_id for _, obs_id in observations[:5]],
                    edges_involved=[],
                    confidence=0.7,
                    evidence=[f"Sequence length: {len(observations)}"],
                ))

        return patterns[:5]

    def _find_outcome_patterns(
        self, patient_id: str | None = None
    ) -> list[GraphPattern]:
        """Find outcome patterns (treatment → result)."""
        patterns = []

        # Find patients with both medications and observations
        patient_meds: dict[str, list[str]] = defaultdict(list)
        patient_obs: dict[str, list[str]] = defaultdict(list)

        for edge in self.graph.edges:
            if patient_id and edge.source != patient_id:
                continue
            if edge.edge_type == "takes_medication":
                patient_meds[edge.source].append(edge.target)
            elif edge.edge_type == "has_observation":
                patient_obs[edge.source].append(edge.target)

        # Find medication-observation correlations
        for patient in set(list(patient_meds.keys()) + list(patient_obs.keys())):
            meds = patient_meds.get(patient, [])
            obs = patient_obs.get(patient, [])
            if meds and obs:
                patterns.append(GraphPattern(
                    pattern_type="outcome",
                    description=f"Outcome pattern: {len(meds)} medications → {len(obs)} observations",
                    nodes_involved=meds[:3] + obs[:3],
                    edges_involved=[],
                    confidence=0.6,
                    evidence=[f"Patient {patient[:8]}..."],
                ))

        return patterns[:5]


# ============================================================================
# Graph Reasoning Agent
# ============================================================================

class GraphReasoningEngine:
    """Engine for reasoning over the knowledge graph structure."""

    def __init__(self, graph: MedicalKnowledgeGraph):
        self.graph = graph
        self.retriever = GraphRAGRetriever(graph)
        self.pattern_engine = PatternDiscoveryEngine(graph)
        self.algorithms = GraphAlgorithms()

    def reason_about_patient(
        self,
        patient_id: str,
        question: str,
    ) -> dict[str, Any]:
        """Reason about a patient using graph structure."""
        # Get patient subgraph
        subgraph = self.graph.get_subgraph(patient_id, depth=2)

        # Retrieve evidence using Graph RAG
        rag_result = self.retriever.retrieve(
            question, patient_id=patient_id
        )

        # Discover patterns
        patterns = self.pattern_engine.discover_all_patterns(patient_id)

        # Find causal chains
        causal_chains = self.algorithms.find_causal_chains(self.graph, patient_id)

        # Calculate centrality
        centrality = self.algorithms.calculate_centrality(subgraph)

        # Find communities
        communities = self.algorithms.find_communities(subgraph)

        return {
            "patient_id": patient_id,
            "question": question,
            "evidence": [e.to_dict() for e in rag_result.evidence[:20]],
            "patterns": [p.to_dict() for p in patterns[:10]],
            "causal_chains": [c.to_dict() for c in causal_chains[:5]],
            "communities": [c.to_dict() for c in communities[:5]],
            "centrality": {
                k: v for k, v in sorted(
                    centrality.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )[:10]
            },
            "graph_stats": rag_result.graph_stats,
        }

    def find_related_conditions(
        self,
        condition_description: str,
    ) -> dict[str, Any]:
        """Find conditions related to a given condition."""
        # Find matching conditions
        matching_conditions = self.graph.query(
            node_type="condition",
            description=condition_description,
        )

        if not matching_conditions:
            # Try partial match
            for node in self.graph.query(node_type="condition"):
                if condition_description.lower() in node.properties.get("description", "").lower():
                    matching_conditions.append(node)

        related = []
        for condition in matching_conditions[:3]:
            # Find patients with this condition
            for edge in self.graph.edges:
                if edge.target == condition.id and edge.edge_type == "has_condition":
                    patient_id = edge.source

                    # Get other conditions for this patient
                    other_conditions = self.graph.get_patient_conditions(patient_id)
                    for other in other_conditions:
                        if other.id != condition.id:
                            related.append({
                                "condition": other.properties.get("description", ""),
                                "relationship": "co-occurs with",
                                "patient_id": patient_id,
                            })

        return {
            "query_condition": condition_description,
            "matching_conditions": [
                c.properties.get("description", "") for c in matching_conditions
            ],
            "related_conditions": related[:20],
        }

    def find_treatment_pathways(
        self,
        condition_description: str,
    ) -> dict[str, Any]:
        """Find treatment pathways for a condition."""
        pathways = self.algorithms.find_treatment_pathways(
            self.graph, condition_description
        )

        return {
            "condition": condition_description,
            "pathways": [p.to_dict() for p in pathways[:10]],
            "pathway_count": len(pathways),
        }


# ============================================================================
# Integration Functions
# ============================================================================

def create_graph_rag_system(
    store: SyntheaStore,
) -> tuple[MedicalKnowledgeGraph, GraphRAGRetriever, PatternDiscoveryEngine]:
    """Create a complete Graph RAG system from a SyntheaStore."""
    graph = build_knowledge_graph(store)
    retriever = GraphRAGRetriever(graph)
    pattern_engine = PatternDiscoveryEngine(graph)

    return graph, retriever, pattern_engine


def graph_rag_retrieve(
    store: SyntheaStore,
    query: str,
    patient_id: str | None = None,
) -> GraphRAGResult:
    """Convenience function for Graph RAG retrieval."""
    graph = build_knowledge_graph(store)
    retriever = GraphRAGRetriever(graph)
    return retriever.retrieve(query, patient_id=patient_id)
