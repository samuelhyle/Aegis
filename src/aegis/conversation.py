from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class ConversationMessage:
    """A message in a conversation."""
    role: str  # user, assistant, system
    content: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationContext:
    """Context for a conversation session."""
    session_id: str
    patient_id: str | None = None
    messages: list[ConversationMessage] = field(default_factory=list)
    investigation_history: list[dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class QuestionClassifier:
    """Classify user questions to determine intent."""

    # Question patterns and their intents
    PATTERNS = {
        "patient_summary": [
            "summarize", "overview", "health status", "patient record",
            "tell me about", "describe", "what is the patient's",
        ],
        "conditions": [
            "condition", "diagnosis", "disease", "illness", "disorder",
            "what conditions", "medical history",
        ],
        "medications": [
            "medication", "drug", "prescription", "taking", "medicine",
            "what medications", "pharmacy",
        ],
        "observations": [
            "lab", "test", "result", "observation", "value",
            "blood work", "vitals", "measurement",
        ],
        "procedures": [
            "procedure", "surgery", "operation", "treatment",
            "what procedures", "medical procedures",
        ],
        "timeline": [
            "timeline", "history", "when", "dates", "chronological",
            "over time", "progression",
        ],
        "risk_assessment": [
            "risk", "chance", "probability", "likelihood",
            "predict", "forecast", "outlook",
        ],
        "comparison": [
            "compare", "difference", "versus", "vs", "better",
            "worse", "improved", "declined",
        ],
    }

    def classify(self, question: str) -> str:
        """Classify a question to determine intent."""
        question_lower = question.lower()

        # Check each pattern
        for intent, patterns in self.PATTERNS.items():
            for pattern in patterns:
                if pattern in question_lower:
                    return intent

        # Default to general investigation
        return "general"

    def extract_entities(self, question: str) -> dict[str, Any]:
        """Extract entities from a question."""
        entities = {}
        question_lower = question.lower()

        # Extract time references
        time_patterns = {
            "recent": "recent",
            "last": "recent",
            "past": "historical",
            "history": "historical",
            "current": "current",
            "now": "current",
            "today": "current",
        }

        for pattern, time_ref in time_patterns.items():
            if pattern in question_lower:
                entities["time_reference"] = time_ref
                break

        # Extract specificity
        if "all" in question_lower:
            entities["scope"] = "all"
        elif "specific" in question_lower or "particular" in question_lower:
            entities["scope"] = "specific"

        return entities


class ConversationManager:
    """Manager for conversational investigations."""

    def __init__(self):
        self.sessions: dict[str, ConversationContext] = {}
        self.classifier = QuestionClassifier()

    def create_session(self, patient_id: str | None = None) -> ConversationContext:
        """Create a new conversation session."""
        session_id = str(uuid4())
        context = ConversationContext(
            session_id=session_id,
            patient_id=patient_id,
        )
        self.sessions[session_id] = context

        # Add system message
        system_message = ConversationMessage(
            role="system",
            content="Welcome to AEGIS. I can help you investigate patient records. What would you like to know?",
        )
        context.messages.append(system_message)

        return context

    def get_session(self, session_id: str) -> ConversationContext | None:
        """Get a conversation session by ID."""
        return self.sessions.get(session_id)

    def add_user_message(
        self,
        session_id: str,
        message: str,
    ) -> ConversationContext | None:
        """Add a user message to the conversation."""
        context = self.sessions.get(session_id)
        if not context:
            return None

        user_message = ConversationMessage(
            role="user",
            content=message,
        )
        context.messages.append(user_message)
        context.updated_at = datetime.now(timezone.utc)

        return context

    def add_assistant_message(
        self,
        session_id: str,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationContext | None:
        """Add an assistant message to the conversation."""
        context = self.sessions.get(session_id)
        if not context:
            return None

        assistant_message = ConversationMessage(
            role="assistant",
            content=message,
            metadata=metadata or {},
        )
        context.messages.append(assistant_message)
        context.updated_at = datetime.now(timezone.utc)

        return context

    def process_question(
        self,
        session_id: str,
        question: str,
        orchestrator,
    ) -> dict[str, Any]:
        """Process a user question and generate a response."""
        context = self.sessions.get(session_id)
        if not context:
            return {"error": "Session not found"}

        # Add user message
        self.add_user_message(session_id, question)

        # Classify question
        intent = self.classifier.classify(question)
        entities = self.classifier.extract_entities(question)

        # Get patient ID from context or question
        patient_id = context.patient_id
        if not patient_id:
            return {
                "response": "Please specify a patient ID to investigate.",
                "intent": intent,
                "entities": entities,
            }

        # Run investigation
        report = orchestrator.investigate(patient_id, question)

        # Store investigation in history
        context.investigation_history.append({
            "question": question,
            "intent": intent,
            "entities": entities,
            "trace_id": report.trace_id,
            "confidence": report.confidence,
        })

        # Generate response based on intent
        response = self._generate_response(intent, report, context)

        # Add assistant message
        self.add_assistant_message(session_id, response, {
            "intent": intent,
            "trace_id": report.trace_id,
            "confidence": report.confidence,
        })

        return {
            "response": response,
            "intent": intent,
            "entities": entities,
            "trace_id": report.trace_id,
            "confidence": report.confidence,
            "review_required": report.review_required,
        }

    def _generate_response(
        self,
        intent: str,
        report,
        context: ConversationContext,
    ) -> str:
        """Generate a response based on intent and investigation results."""
        # Get patient info
        patient_info = ""
        if context.patient_id:
            patient_info = f" for patient {context.patient_id[:8]}..."

        # Base response from investigation
        base_response = report.conclusion

        # Add intent-specific framing
        if intent == "patient_summary":
            response = f"Here's a summary{patient_info}:\n\n{base_response}"
        elif intent == "conditions":
            response = f"Regarding conditions{patient_info}:\n\n{base_response}"
        elif intent == "medications":
            response = f"Regarding medications{patient_info}:\n\n{base_response}"
        elif intent == "observations":
            response = f"Regarding lab results and observations{patient_info}:\n\n{base_response}"
        elif intent == "procedures":
            response = f"Regarding procedures{patient_info}:\n\n{base_response}"
        elif intent == "timeline":
            response = f"Regarding the patient timeline{patient_info}:\n\n{base_response}"
        elif intent == "risk_assessment":
            response = f"Regarding risk assessment{patient_info}:\n\n{base_response}"
        elif intent == "comparison":
            response = f"Regarding comparison{patient_info}:\n\n{base_response}"
        else:
            response = base_response

        # Add confidence note
        if report.confidence < 0.5:
            response += "\n\nNote: This analysis has low confidence. Please verify with additional sources."
        elif report.review_required:
            response += "\n\nNote: This analysis requires human review before clinical decisions."

        return response

    def get_conversation_history(self, session_id: str) -> list[dict[str, Any]]:
        """Get conversation history for a session."""
        context = self.sessions.get(session_id)
        if not context:
            return []

        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "metadata": msg.metadata,
            }
            for msg in context.messages
        ]

    def get_suggested_questions(self, session_id: str) -> list[str]:
        """Get suggested follow-up questions."""
        context = self.sessions.get(session_id)
        if not context:
            return []

        suggestions = []

        # Based on investigation history
        if context.investigation_history:
            last_investigation = context.investigation_history[-1]
            intent = last_investigation.get("intent", "")

            if intent == "patient_summary":
                suggestions.extend([
                    "What are the patient's main conditions?",
                    "What medications is the patient taking?",
                    "Are there any concerning lab results?",
                ])
            elif intent == "conditions":
                suggestions.extend([
                    "What medications are being used to treat these conditions?",
                    "How have these conditions changed over time?",
                    "Are there any related procedures?",
                ])
            elif intent == "medications":
                suggestions.extend([
                    "Are there any drug interactions?",
                    "How long has the patient been on these medications?",
                    "Are there any side effects to monitor?",
                ])
        else:
            # Default suggestions
            suggestions.extend([
                "Summarize this patient's health record",
                "What conditions does this patient have?",
                "What medications is this patient taking?",
                "Are there any concerning findings?",
            ])

        return suggestions[:5]  # Limit to 5 suggestions
