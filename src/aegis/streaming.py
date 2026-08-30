from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from time import perf_counter
from typing import Any
from uuid import uuid4

from .models import InvestigationReport
from .monitoring import metrics, structured_logger
from .orchestrator import Orchestrator
from .store import SyntheaStore


class StreamingOrchestrator:
    """Orchestrator that streams investigation results in real-time."""

    def __init__(self, store: SyntheaStore | None = None):
        self.store = store or SyntheaStore()
        self.orchestrator = Orchestrator(store)

    async def investigate_stream(
        self,
        patient_id: str,
        question: str,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stream investigation results as they complete."""
        trace_id = str(uuid4())
        start_time = perf_counter()

        # Send investigation started event
        yield {
            "type": "investigation_started",
            "trace_id": trace_id,
            "patient_id": patient_id,
            "question": question,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Run agents sequentially and stream results
        results = []
        for agent in self.orchestrator.agents:
            agent_start = perf_counter()

            # Send agent started event
            yield {
                "type": "agent_started",
                "trace_id": trace_id,
                "agent": agent.name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            try:
                # Run agent (in thread pool for CPU-bound work)
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    agent.run,
                    patient_id,
                    question,
                )
                results.append(result)

                # Send agent completed event
                yield {
                    "type": "agent_completed",
                    "trace_id": trace_id,
                    "agent": agent.name,
                    "result": result.model_dump(),
                    "duration_ms": (perf_counter() - agent_start) * 1000,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

                # Log agent execution
                structured_logger.log_agent_execution(
                    agent_name=agent.name,
                    patient_id=patient_id,
                    confidence=result.confidence,
                    duration_ms=result.duration_ms,
                    evidence_count=len(result.evidence),
                )

            except Exception as e:
                # Send agent failed event
                yield {
                    "type": "agent_failed",
                    "trace_id": trace_id,
                    "agent": agent.name,
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

                structured_logger.log_error(e, {
                    "agent": agent.name,
                    "patient_id": patient_id,
                    "trace_id": trace_id,
                })

        # Calculate overall results
        if results:
            confidence = sum(r.confidence for r in results) / len(results)
        else:
            confidence = 0.0

        evidence = [item for r in results for item in r.evidence]
        conclusion = self.orchestrator._generate_conclusion(results, patient_id, question)
        review_required = self.orchestrator._determine_review_required(results, confidence)

        # Create final report
        report = InvestigationReport(
            patient_id=patient_id,
            question=question,
            conclusion=conclusion,
            evidence=evidence,
            confidence=confidence,
            review_required=review_required,
            trace_id=trace_id,
            generated_at=datetime.now(timezone.utc),
            agent_results=results,
        )

        # Record metrics
        duration_ms = (perf_counter() - start_time) * 1000
        metrics.inc_counter("investigations_total")
        metrics.observe_histogram("investigation_duration_ms", duration_ms)
        metrics.set_gauge("investigation_confidence", confidence)

        # Send investigation completed event
        yield {
            "type": "investigation_completed",
            "trace_id": trace_id,
            "report": report.model_dump(),
            "total_duration_ms": duration_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def investigate_sse(
        self,
        patient_id: str,
        question: str,
    ) -> AsyncGenerator[str, None]:
        """Stream investigation results as Server-Sent Events."""
        async for event in self.investigate_stream(patient_id, question):
            # Format as SSE
            event_type = event.get("type", "message")
            event_data = json.dumps(event, default=str)
            yield f"event: {event_type}\ndata: {event_data}\n\n"


class WebSocketManager:
    """Manager for WebSocket connections."""

    def __init__(self):
        self.active_connections: dict[str, list] = {}
        self.journey_connections: dict[str, list] = {}  # patient_id -> websockets

    async def connect(self, websocket, trace_id: str):
        """Accept a WebSocket connection and add to tracking."""
        await websocket.accept()
        if trace_id not in self.active_connections:
            self.active_connections[trace_id] = []
        self.active_connections[trace_id].append(websocket)

    def disconnect(self, websocket, trace_id: str):
        """Remove a WebSocket connection from tracking."""
        if trace_id in self.active_connections:
            self.active_connections[trace_id].remove(websocket)
            if not self.active_connections[trace_id]:
                del self.active_connections[trace_id]

    async def journey_connect(self, websocket, patient_id: str):
        """Accept a WebSocket connection for patient journey updates."""
        await websocket.accept()
        if patient_id not in self.journey_connections:
            self.journey_connections[patient_id] = []
        self.journey_connections[patient_id].append(websocket)

    def journey_disconnect(self, websocket, patient_id: str):
        """Remove a WebSocket journey connection."""
        if patient_id in self.journey_connections:
            self.journey_connections[patient_id].remove(websocket)
            if not self.journey_connections[patient_id]:
                del self.journey_connections[patient_id]

    async def broadcast_journey(self, patient_id: str, message: dict[str, Any]):
        """Broadcast a journey update to all connected patients."""
        if patient_id in self.journey_connections:
            for connection in self.journey_connections[patient_id][:]:
                try:
                    await connection.send_json(message)
                except Exception:
                    # Connection closed, remove it
                    self.journey_connections[patient_id].remove(connection)


# Global WebSocket manager
ws_manager = WebSocketManager()
