# Agent Specification

## Agent contract

Every agent must have:
- name
- purpose
- allowed tools
- input schema
- output schema
- confidence
- evidence
- failure mode
- timeout
- observability events

## Orchestrator

Input: user investigation request.

Output: task graph.

Rules:
1. Never allow an agent to invent patient data.
2. Patient facts must originate from the data layer.
3. Medical knowledge claims must reference retrieved evidence.
4. Conflicting evidence triggers critic review.
5. Clinical recommendations require human review.

## Timeline Agent

Tools:
- get_patient
- get_encounters
- get_conditions
- get_observations

## Medication Agent

Tools:
- get_medications
- get_allergies

## Evidence Agent

Future tools:
- search_documents
- retrieve_document
- rerank

## Critic Agent

Responsibilities:
- claim/evidence matching
- contradiction detection
- uncertainty estimation

## Safety Agent

Responsibilities:
- reject diagnosis/treatment claims as authoritative
- detect missing evidence
- enforce review_required=true

## Synthesis Agent

Output:

```json
{
  "facts": [],
  "observations": [],
  "hypotheses": [],
  "unknowns": [],
  "evidence": [],
  "confidence": 0.0,
  "review_required": true
}
```
