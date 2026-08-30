from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TimelineEvent:
    """An event in a patient timeline."""
    event_id: str
    event_type: str  # encounter, condition, medication, procedure, observation
    date: str
    title: str
    description: str
    category: str = ""
    severity: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TimelineData:
    """Data structure for timeline visualization."""
    patient_id: str
    events: list[TimelineEvent] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    date_range: dict[str, str] = field(default_factory=dict)
    statistics: dict[str, int] = field(default_factory=dict)


@dataclass
class NetworkNode:
    """A node in a network graph."""
    id: str
    label: str
    node_type: str
    size: int = 10
    color: str = "#4A90D9"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class NetworkEdge:
    """An edge in a network graph."""
    source: str
    target: str
    label: str = ""
    weight: float = 1.0
    color: str = "#999999"


@dataclass
class NetworkData:
    """Data structure for network visualization."""
    nodes: list[NetworkNode] = field(default_factory=list)
    edges: list[NetworkEdge] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class HeatmapData:
    """Data structure for heatmap visualization."""
    x_labels: list[str] = field(default_factory=list)
    y_labels: list[str] = field(default_factory=list)
    values: list[list[float]] = field(default_factory=list)
    title: str = ""
    x_axis: str = ""
    y_axis: str = ""


@dataclass
class SankeyNode:
    """A node in a Sankey diagram."""
    id: str
    name: str
    category: str = ""


@dataclass
class SankeyLink:
    """A link in a Sankey diagram."""
    source: str
    target: str
    value: float


@dataclass
class SankeyData:
    """Data structure for Sankey diagram."""
    nodes: list[SankeyNode] = field(default_factory=list)
    links: list[SankeyLink] = field(default_factory=list)
    title: str = ""


class TimelineBuilder:
    """Build timeline visualizations from patient data."""

    def build_patient_timeline(self, store, patient_id: str) -> TimelineData:
        """Build a timeline for a patient."""
        events = []

        # Add encounters
        encounters = store.rows("encounters", patient_id)
        for enc in encounters:
            events.append(TimelineEvent(
                event_id=str(enc.get("Id", "")),
                event_type="encounter",
                date=str(enc.get("START", "")),
                title=enc.get("DESCRIPTION", "Encounter"),
                description=f"{enc.get('ENCOUNTERCLASS', '')} encounter",
                category="encounters",
                metadata={"class": enc.get("ENCOUNTERCLASS", "")},
            ))

        # Add conditions
        conditions = store.rows("conditions", patient_id)
        for cond in conditions:
            events.append(TimelineEvent(
                event_id=str(cond.get("Id", "")),
                event_type="condition",
                date=str(cond.get("START", "")),
                title=cond.get("DESCRIPTION", "Condition"),
                description=f"Condition: {cond.get('DESCRIPTION', '')}",
                category="conditions",
                severity="active" if not cond.get("STOP") else "resolved",
            ))

        # Add medications
        medications = store.rows("medications", patient_id)
        for med in medications:
            events.append(TimelineEvent(
                event_id=str(med.get("Id", "")),
                event_type="medication",
                date=str(med.get("START", "")),
                title=med.get("DESCRIPTION", "Medication"),
                description=f"Medication: {med.get('DESCRIPTION', '')}",
                category="medications",
            ))

        # Add procedures
        procedures = store.rows("procedures", patient_id)
        for proc in procedures:
            events.append(TimelineEvent(
                event_id=str(proc.get("Id", "")),
                event_type="procedure",
                date=str(proc.get("DATE", proc.get("START", ""))),
                title=proc.get("DESCRIPTION", "Procedure"),
                description=f"Procedure: {proc.get('DESCRIPTION', '')}",
                category="procedures",
            ))

        # Sort events by date
        events.sort(key=lambda e: e.date if e.date else "")

        # Get date range
        dates = [e.date for e in events if e.date]
        date_range = {
            "start": min(dates) if dates else "",
            "end": max(dates) if dates else "",
        }

        # Get statistics
        statistics = {}
        for event in events:
            statistics[event.event_type] = statistics.get(event.event_type, 0) + 1

        return TimelineData(
            patient_id=patient_id,
            events=events,
            categories=["encounters", "conditions", "medications", "procedures"],
            date_range=date_range,
            statistics=statistics,
        )

    def build_3d_timeline(self, store, patient_id: str) -> dict[str, Any]:
        """Build data for 3D timeline visualization."""
        timeline = self.build_patient_timeline(store, patient_id)

        # Create 3D data structure
        nodes = []
        links = []

        # Category colors
        colors = {
            "encounters": "#4A90D9",
            "conditions": "#E74C3C",
            "medications": "#2ECC71",
            "procedures": "#F39C12",
        }

        # Create nodes for each event
        for i, event in enumerate(timeline.events):
            nodes.append({
                "id": event.event_id,
                "label": event.title[:30],
                "type": event.event_type,
                "date": event.date,
                "color": colors.get(event.category, "#999999"),
                "size": 10,
                "position": {
                    "x": i * 2,  # Time axis
                    "y": list(colors.keys()).index(event.category) * 2 if event.category in colors else 0,
                    "z": 0,
                },
            })

        # Create links between related events
        for i in range(len(nodes) - 1):
            links.append({
                "source": nodes[i]["id"],
                "target": nodes[i + 1]["id"],
                "type": "temporal",
            })

        return {
            "nodes": nodes,
            "links": links,
            "metadata": {
                "patient_id": patient_id,
                "date_range": timeline.date_range,
                "statistics": timeline.statistics,
            },
        }


class NetworkGraphBuilder:
    """Build network graph visualizations."""

    def build_condition_medication_network(self, store, patient_id: str) -> NetworkData:
        """Build a network showing conditions and medications."""
        nodes = []
        edges = []

        # Get patient data
        conditions = store.rows("conditions", patient_id)
        medications = store.rows("medications", patient_id)

        # Create condition nodes
        for i, cond in enumerate(conditions):
            nodes.append(NetworkNode(
                id=f"cond-{i}",
                label=cond.get("DESCRIPTION", "")[:20],
                node_type="condition",
                size=15,
                color="#E74C3C",
                metadata={"code": cond.get("CODE", "")},
            ))

        # Create medication nodes
        for i, med in enumerate(medications):
            nodes.append(NetworkNode(
                id=f"med-{i}",
                label=med.get("DESCRIPTION", "")[:20],
                node_type="medication",
                size=12,
                color="#2ECC71",
                metadata={"code": med.get("CODE", "")},
            ))

        # Create edges between conditions and medications
        # (In a real system, this would use actual treatment relationships)
        for i, cond in enumerate(conditions):
            for j, med in enumerate(medications):
                # Simple heuristic: connect if they share keywords
                cond_desc = cond.get("DESCRIPTION", "").lower()
                med_desc = med.get("DESCRIPTION", "").lower()
                if any(word in med_desc for word in cond_desc.split()[:3]):
                    edges.append(NetworkEdge(
                        source=f"cond-{i}",
                        target=f"med-{j}",
                        label="treats",
                        weight=1.0,
                    ))

        return NetworkData(nodes=nodes, edges=edges)

    def build_patient_network(self, store, patient_id: str) -> NetworkData:
        """Build a comprehensive patient network."""
        nodes = []
        edges = []

        # Patient node (center)
        patient = store.patient(patient_id)
        nodes.append(NetworkNode(
            id=patient_id,
            label=f"{patient.get('FIRST', '')} {patient.get('LAST', '')}",
            node_type="patient",
            size=25,
            color="#3498DB",
        ))

        # Condition nodes
        conditions = store.rows("conditions", patient_id)
        for i, cond in enumerate(conditions[:10]):  # Limit to 10
            node_id = f"cond-{i}"
            nodes.append(NetworkNode(
                id=node_id,
                label=cond.get("DESCRIPTION", "")[:15],
                node_type="condition",
                size=12,
                color="#E74C3C",
            ))
            edges.append(NetworkEdge(source=patient_id, target=node_id, label="has"))

        # Medication nodes
        medications = store.rows("medications", patient_id)
        for i, med in enumerate(medications[:10]):  # Limit to 10
            node_id = f"med-{i}"
            nodes.append(NetworkNode(
                id=node_id,
                label=med.get("DESCRIPTION", "")[:15],
                node_type="medication",
                size=10,
                color="#2ECC71",
            ))
            edges.append(NetworkEdge(source=patient_id, target=node_id, label="takes"))

        # Procedure nodes
        procedures = store.rows("procedures", patient_id)
        for i, proc in enumerate(procedures[:5]):  # Limit to 5
            node_id = f"proc-{i}"
            nodes.append(NetworkNode(
                id=node_id,
                label=proc.get("DESCRIPTION", "")[:15],
                node_type="procedure",
                size=10,
                color="#F39C12",
            ))
            edges.append(NetworkEdge(source=patient_id, target=node_id, label="underwent"))

        return NetworkData(nodes=nodes, edges=edges)


class HeatmapBuilder:
    """Build heatmap visualizations."""

    def build_lab_heatmap(self, store, patient_id: str) -> HeatmapData:
        """Build a heatmap of lab values over time."""
        observations = store.rows("observations", patient_id)

        # Group by lab type and date
        lab_data: dict[str, dict[str, float]] = {}
        for obs in observations:
            lab_name = obs.get("DESCRIPTION", "")
            date = str(obs.get("DATE", ""))[:7]  # YYYY-MM
            value = obs.get("VALUE")

            if lab_name and date and value:
                try:
                    if lab_name not in lab_data:
                        lab_data[lab_name] = {}
                    lab_data[lab_name][date] = float(value)
                except (ValueError, TypeError):
                    pass

        # Get unique dates and labs
        all_dates = sorted(set(date for dates in lab_data.values() for date in dates))
        lab_names = sorted(lab_data.keys())[:10]  # Limit to 10 labs

        # Build heatmap matrix
        values = []
        for lab in lab_names:
            row = []
            for date in all_dates:
                row.append(lab_data[lab].get(date, 0.0))
            values.append(row)

        return HeatmapData(
            x_labels=all_dates,
            y_labels=lab_names,
            values=values,
            title=f"Lab Values Over Time - Patient {patient_id[:8]}...",
            x_axis="Date",
            y_axis="Lab Test",
        )


class SankeyBuilder:
    """Build Sankey diagram visualizations."""

    def build_patient_flow(self, store, patient_id: str) -> SankeyData:
        """Build a Sankey diagram showing patient flow through care."""
        nodes = []
        links = []

        # Get encounters
        encounters = store.rows("encounters", patient_id)

        # Group encounters by class
        encounter_classes: dict[str, int] = {}
        for enc in encounters:
            enc_class = enc.get("ENCOUNTERCLASS", "unknown")
            encounter_classes[enc_class] = encounter_classes.get(enc_class, 0) + 1

        # Create source node
        nodes.append(SankeyNode(id="patient", name="Patient", category="source"))

        # Create encounter class nodes
        for enc_class, count in encounter_classes.items():
            node_id = f"enc-{enc_class}"
            nodes.append(SankeyNode(id=node_id, name=enc_class.title(), category="encounter"))
            links.append(SankeyLink(source="patient", target=node_id, value=count))

        # Get conditions and link to encounters
        conditions = store.rows("conditions", patient_id)
        condition_categories: dict[str, int] = {}
        for cond in conditions:
            # Simple categorization
            desc = cond.get("DESCRIPTION", "").lower()
            if "diabetes" in desc:
                category = "Diabetes"
            elif "hypertension" in desc:
                category = "Hypertension"
            elif "heart" in desc or "cardiac" in desc:
                category = "Cardiac"
            else:
                category = "Other"
            condition_categories[category] = condition_categories.get(category, 0) + 1

        # Create condition category nodes
        for category, count in condition_categories.items():
            node_id = f"cond-{category.lower()}"
            nodes.append(SankeyNode(id=node_id, name=category, category="condition"))

            # Link from encounter classes to conditions
            for enc_class in encounter_classes:
                links.append(SankeyLink(
                    source=f"enc-{enc_class}",
                    target=node_id,
                    value=count // len(encounter_classes),
                ))

        return SankeyData(nodes=nodes, links=links, title="Patient Care Flow")


class VisualizationEngine:
    """Engine for generating visualization data."""

    def __init__(self):
        self.timeline_builder = TimelineBuilder()
        self.network_builder = NetworkGraphBuilder()
        self.heatmap_builder = HeatmapBuilder()
        self.sankey_builder = SankeyBuilder()

    def get_patient_visualizations(self, store, patient_id: str) -> dict[str, Any]:
        """Get all visualization data for a patient."""
        return {
            "timeline": self.timeline_builder.build_patient_timeline(store, patient_id).__dict__,
            "timeline_3d": self.timeline_builder.build_3d_timeline(store, patient_id),
            "network": self.network_builder.build_patient_network(store, patient_id).__dict__,
            "heatmap": self.heatmap_builder.build_lab_heatmap(store, patient_id).__dict__,
            "sankey": self.sankey_builder.build_patient_flow(store, patient_id).__dict__,
        }
