from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class GraphNode:
    """A node in the knowledge graph."""
    id: str
    node_type: str  # patient, condition, medication, procedure, etc.
    properties: dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, GraphNode) and self.id == other.id


@dataclass
class GraphEdge:
    """An edge in the knowledge graph."""
    source: str  # Source node ID
    target: str  # Target node ID
    edge_type: str  # has_condition, takes_medication, etc.
    properties: dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash((self.source, self.target, self.edge_type))


class KnowledgeGraph:
    """In-memory knowledge graph for medical reasoning."""

    def __init__(self):
        self.nodes: dict[str, GraphNode] = {}
        self.edges: list[GraphEdge] = []
        self.adjacency: dict[str, list[str]] = defaultdict(list)  # node_id -> [connected node_ids]
        self.type_index: dict[str, list[str]] = defaultdict(list)  # type -> [node_ids]

    def add_node(self, node: GraphNode) -> None:
        """Add a node to the graph."""
        self.nodes[node.id] = node
        self.type_index[node.node_type].append(node.id)

    def add_edge(self, edge: GraphEdge) -> None:
        """Add an edge to the graph."""
        self.edges.append(edge)
        self.adjacency[edge.source].append(edge.target)
        self.adjacency[edge.target].append(edge.source)

    def get_node(self, node_id: str) -> GraphNode | None:
        """Get a node by ID."""
        return self.nodes.get(node_id)

    def get_neighbors(self, node_id: str, edge_type: str | None = None) -> list[GraphNode]:
        """Get neighboring nodes, optionally filtered by edge type."""
        neighbors = []
        for edge in self.edges:
            if edge.source == node_id and (edge_type is None or edge.edge_type == edge_type):
                neighbor = self.nodes.get(edge.target)
                if neighbor:
                    neighbors.append(neighbor)
            elif edge.target == node_id and (edge_type is None or edge.edge_type == edge_type):
                neighbor = self.nodes.get(edge.source)
                if neighbor:
                    neighbors.append(neighbor)
        return neighbors

    def get_edges(self, node_id: str, edge_type: str | None = None) -> list[GraphEdge]:
        """Get edges connected to a node, optionally filtered by type."""
        return [
            edge for edge in self.edges
            if (edge.source == node_id or edge.target == node_id)
            and (edge_type is None or edge.edge_type == edge_type)
        ]

    def find_path(self, start: str, end: str, max_depth: int = 5) -> list[str] | None:
        """Find a path between two nodes using BFS."""
        if start == end:
            return [start]

        visited = {start}
        queue = [(start, [start])]

        while queue:
            current, path = queue.pop(0)
            if len(path) > max_depth:
                continue

            for neighbor_id in self.adjacency.get(current, []):
                if neighbor_id == end:
                    return path + [neighbor_id]

                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, path + [neighbor_id]))

        return None

    def get_subgraph(self, node_id: str, depth: int = 2) -> KnowledgeGraph:
        """Get a subgraph around a node up to a certain depth."""
        subgraph = KnowledgeGraph()
        visited = set()
        queue = [(node_id, 0)]

        while queue:
            current_id, current_depth = queue.pop(0)
            if current_id in visited or current_depth > depth:
                continue

            visited.add(current_id)
            node = self.nodes.get(current_id)
            if node:
                subgraph.add_node(node)

            for edge in self.edges:
                if edge.source == current_id:
                    target_node = self.nodes.get(edge.target)
                    if target_node and edge.target not in visited:
                        subgraph.add_node(target_node)
                        subgraph.add_edge(edge)
                        if current_depth < depth:
                            queue.append((edge.target, current_depth + 1))
                elif edge.target == current_id:
                    source_node = self.nodes.get(edge.source)
                    if source_node and edge.source not in visited:
                        subgraph.add_node(source_node)
                        subgraph.add_edge(edge)
                        if current_depth < depth:
                            queue.append((edge.source, current_depth + 1))

        return subgraph

    def query(self, node_type: str | None = None, **properties) -> list[GraphNode]:
        """Query nodes by type and properties."""
        results = []

        if node_type:
            node_ids = self.type_index.get(node_type, [])
        else:
            node_ids = list(self.nodes.keys())

        for node_id in node_ids:
            node = self.nodes[node_id]
            match = True
            for key, value in properties.items():
                if node.properties.get(key) != value:
                    match = False
                    break
            if match:
                results.append(node)

        return results

    def to_dict(self) -> dict[str, Any]:
        """Export graph as dictionary."""
        return {
            "nodes": [
                {
                    "id": node.id,
                    "type": node.node_type,
                    "properties": node.properties,
                }
                for node in self.nodes.values()
            ],
            "edges": [
                {
                    "source": edge.source,
                    "target": edge.target,
                    "type": edge.edge_type,
                    "properties": edge.properties,
                }
                for edge in self.edges
            ],
        }


class MedicalKnowledgeGraph(KnowledgeGraph):
    """Specialized knowledge graph for medical reasoning."""

    def add_patient(self, patient_id: str, **properties) -> GraphNode:
        """Add a patient node."""
        node = GraphNode(id=patient_id, node_type="patient", properties=properties)
        self.add_node(node)
        return node

    def add_condition(self, condition_id: str, patient_id: str, **properties) -> GraphNode:
        """Add a condition node and link to patient."""
        node = GraphNode(id=condition_id, node_type="condition", properties=properties)
        self.add_node(node)
        self.add_edge(GraphEdge(
            source=patient_id,
            target=condition_id,
            edge_type="has_condition",
            properties={"onset": properties.get("start"), "resolution": properties.get("stop")},
        ))
        return node

    def add_medication(self, medication_id: str, patient_id: str, **properties) -> GraphNode:
        """Add a medication node and link to patient."""
        node = GraphNode(id=medication_id, node_type="medication", properties=properties)
        self.add_node(node)
        self.add_edge(GraphEdge(
            source=patient_id,
            target=medication_id,
            edge_type="takes_medication",
            properties={"start": properties.get("start"), "stop": properties.get("stop")},
        ))
        return node

    def add_procedure(self, procedure_id: str, patient_id: str, **properties) -> GraphNode:
        """Add a procedure node and link to patient."""
        node = GraphNode(id=procedure_id, node_type="procedure", properties=properties)
        self.add_node(node)
        self.add_edge(GraphEdge(
            source=patient_id,
            target=procedure_id,
            edge_type="underwent_procedure",
            properties={"date": properties.get("date")},
        ))
        return node

    def add_observation(self, observation_id: str, patient_id: str, **properties) -> GraphNode:
        """Add an observation node and link to patient."""
        node = GraphNode(id=observation_id, node_type="observation", properties=properties)
        self.add_node(node)
        self.add_edge(GraphEdge(
            source=patient_id,
            target=observation_id,
            edge_type="has_observation",
            properties={"date": properties.get("date"), "value": properties.get("value")},
        ))
        return node

    def get_patient_conditions(self, patient_id: str) -> list[GraphNode]:
        """Get all conditions for a patient."""
        return self.get_neighbors(patient_id, "has_condition")

    def get_patient_medications(self, patient_id: str) -> list[GraphNode]:
        """Get all medications for a patient."""
        return self.get_neighbors(patient_id, "takes_medication")

    def get_patient_procedures(self, patient_id: str) -> list[GraphNode]:
        """Get all procedures for a patient."""
        return self.get_neighbors(patient_id, "underwent_procedure")

    def get_patient_observations(self, patient_id: str) -> list[GraphNode]:
        """Get all observations for a patient."""
        return self.get_neighbors(patient_id, "has_observation")

    def find_related_conditions(self, condition_id: str) -> list[GraphNode]:
        """Find conditions that share medications or procedures."""
        related = set()
        condition = self.get_node(condition_id)
        if not condition:
            return []

        # Find patients with this condition
        for edge in self.edges:
            if edge.target == condition_id and edge.edge_type == "has_condition":
                patient_id = edge.source
                # Get other conditions for this patient
                for other_condition in self.get_patient_conditions(patient_id):
                    if other_condition.id != condition_id:
                        related.add(other_condition)

        return list(related)

    def get_condition_medication_correlation(self) -> dict[str, list[str]]:
        """Get correlation between conditions and medications."""
        correlation: dict[str, list[str]] = defaultdict(list)

        for edge in self.edges:
            if edge.edge_type == "has_condition":
                patient_id = edge.source
                condition_id = edge.target
                # Get medications for this patient
                for med_edge in self.edges:
                    if med_edge.source == patient_id and med_edge.edge_type == "takes_medication":
                        medication_id = med_edge.target
                        if medication_id not in correlation[condition_id]:
                            correlation[condition_id].append(medication_id)

        return dict(correlation)


def build_knowledge_graph(store) -> MedicalKnowledgeGraph:
    """Build a knowledge graph from Synthea data."""
    kg = MedicalKnowledgeGraph()

    if not store.tables:
        store.load()

    # Add patients
    if "patients" in store.tables:
        for _, row in store.tables["patients"].iterrows():
            patient_id = row["Id"]
            kg.add_patient(
                patient_id,
                first=row.get("FIRST", ""),
                last=row.get("LAST", ""),
                gender=row.get("GENDER", ""),
                birthdate=row.get("BIRTHDATE", ""),
            )

    # Add conditions
    if "conditions" in store.tables:
        for _, row in store.tables["conditions"].iterrows():
            patient_id = str(row.get("PATIENT", ""))
            condition_id = f"cond_{row.get('CODE', '')}_{patient_id}"
            kg.add_condition(
                condition_id,
                patient_id,
                code=row.get("CODE", ""),
                description=row.get("DESCRIPTION", ""),
                start=row.get("START", ""),
                stop=row.get("STOP", ""),
            )

    # Add medications
    if "medications" in store.tables:
        for _, row in store.tables["medications"].iterrows():
            patient_id = str(row.get("PATIENT", ""))
            medication_id = f"med_{row.get('CODE', '')}_{patient_id}"
            kg.add_medication(
                medication_id,
                patient_id,
                code=row.get("CODE", ""),
                description=row.get("DESCRIPTION", ""),
                start=row.get("START", ""),
                stop=row.get("STOP", ""),
            )

    # Add procedures
    if "procedures" in store.tables:
        for _, row in store.tables["procedures"].iterrows():
            patient_id = str(row.get("PATIENT", ""))
            procedure_id = f"proc_{row.get('CODE', '')}_{patient_id}"
            kg.add_procedure(
                procedure_id,
                patient_id,
                code=row.get("CODE", ""),
                description=row.get("DESCRIPTION", ""),
                date=row.get("DATE", ""),
            )

    # Add observations
    if "observations" in store.tables:
        for _, row in store.tables["observations"].iterrows():
            patient_id = str(row.get("PATIENT", ""))
            observation_id = f"obs_{row.get('CODE', '')}_{patient_id}_{row.get('DATE', '')}"
            kg.add_observation(
                observation_id,
                patient_id,
                code=row.get("CODE", ""),
                description=row.get("DESCRIPTION", ""),
                value=row.get("VALUE", ""),
                unit=row.get("UNITS", ""),
                date=row.get("DATE", ""),
            )

    return kg
