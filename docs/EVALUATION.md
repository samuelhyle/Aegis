# Evaluation Plan

## Benchmark

Create a versioned JSONL benchmark:

```json
{"id":"Q001","patient_id":"...","question":"Summarize the patient's recent trajectory.","expected_facts":["..."]}
```

## Metrics

### Evidence coverage
Percentage of expected factual claims supported by retrieved patient evidence.

### Citation correctness
Percentage of cited evidence items that actually support the associated claim.

### Hallucination rate
Claims not supported by the available record.

### Task completion
Whether the requested investigation was completed.

### Safety compliance
Whether unsafe medical conclusions were blocked or routed to review.

### Agent efficiency
Latency, tool calls, tokens and cost.

## Experiment tracking

Every evaluation should store:
- git commit
- prompt version
- model
- dataset version
- agent versions
- metrics
- trace ID

This enables reproducible AI experiments.
