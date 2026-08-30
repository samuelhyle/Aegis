# AEGIS — Agentic Clinical Intelligence Environment

AEGIS is a portfolio-grade, safety-oriented agentic AI environment for investigating **synthetic** patient records.

> Research/engineering demonstration only. Not a medical device and not for clinical decision-making.

## Dataset

The MVP is designed around **Synthea**, an open-source synthetic patient population simulator. Synthea generates realistic-but-synthetic longitudinal records including patients, encounters, conditions, medications, observations/labs, procedures and care plans.

- Synthea: https://github.com/synthetichealth/synthea
- Official downloads: https://synthea.mitre.org/downloads

The project deliberately does **not** bundle large datasets. The included seed/demo data is synthetic and tiny; the ingestion pipeline can import Synthea CSV exports.

## What this project demonstrates

- Multi-agent orchestration
- Tool-using agents
- Retrieval-oriented architecture
- Structured LLM outputs
- Agent traces and event logging
- Evidence/claim tracking
- Evaluation hooks
- Human-in-the-loop review
- FastAPI backend
- React/Next.js-ready frontend boundary
- Docker-ready architecture
- Safety boundaries and auditability

## MVP workflow

1. Import Synthea CSV files.
2. Select a synthetic patient.
3. Ask an investigation question.
4. Orchestrator decomposes the task.
5. Timeline, medication and evidence agents execute.
6. Critic checks the result.
7. Synthesis agent produces a structured report.
8. Evaluation records grounding, completeness, confidence and latency.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn aegis.api:app --reload
```

Then open http://127.0.0.1:8000/docs

## Generate Synthea data

Install Java 17+ and clone Synthea. Generate a small population, exporting CSV:

```bash
git clone https://github.com/synthetichealth/synthea.git
cd synthea
./run_synthea -p 100 --exporter.csv.export=true
```

Copy the generated CSV files into `data/synthea/` and run:

```bash
aegis-ingest data/synthea
```

## Architecture

See:
- docs/PROJECT_PLAN.md
- docs/ARCHITECTURE.md
- docs/AGENTS.md
- docs/EVALUATION.md
- docs/ROADMAP.md

## License

MIT for this starter code. Dataset licenses/terms remain those of their respective sources.


## Dataset acquisition — detailed instructions

### Option A: Generate your own Synthea dataset (recommended)

This is the cleanest reproducible approach because you do not need to download a pre-generated patient population.

Requirements:
- Git
- Java 17+ (Synthea recommends an LTS JDK)
- Python 3.11+

1. Clone Synthea:

```bash
git clone https://github.com/synthetichealth/synthea.git
cd synthea
```

2. Generate 100 synthetic patients with CSV export:

```bash
./run_synthea -p 100 --exporter.csv.export=true
```

On Windows PowerShell:

```powershell
.un_synthea.bat -p 100 --exporter.csv.export=true
```

3. Find the generated CSV files under:

```text
output/csv/
```

4. Copy the CSV files into the AEGIS data directory:

```text
aegis-agentic-clinical-intelligence/
└── data/
    └── synthea/
        ├── patients.csv
        ├── encounters.csv
        ├── conditions.csv
        ├── medications.csv
        ├── observations.csv
        ├── procedures.csv
        ├── allergies.csv
        ├── careplans.csv
        └── immunizations.csv
```

5. From the AEGIS root:

```bash
aegis-ingest data/synthea
```

### Option B: Download an official Synthea population

Synthea provides official downloadable synthetic populations through its project/download pages:

- Synthea project: https://github.com/synthetichealth/synthea
- Synthea downloads: https://synthea.mitre.org/downloads

If you download a population archive, extract its CSV export and place the relevant files in `data/synthea/`.

### Recommended development sizes

Start small:

```text
100 patients  -> development
1,000 patients -> integration testing
10,000+ patients -> retrieval/evaluation experiments
```

Do not commit large generated datasets to Git. The repository's `.gitignore` excludes generated Synthea data.

### Why Synthea?

Synthea generates synthetic, not real, patient histories. This is intentional: AEGIS is an AI engineering portfolio project and should not require real patient data. Synthea supports longitudinal records and multiple interoperable output formats.

## Optional FHIR track

For a more advanced version, generate FHIR output as well:

```bash
./run_synthea -p 100
```

Synthea can produce FHIR resources that can later be ingested into a FHIR-aware service. AEGIS should initially use CSV because it is easier to inspect and prototype with; add FHIR as Phase 3/4.

## First investigation after importing data

Once Synthea data is present, start the API:

```bash
uvicorn aegis.api:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

Use `POST /v1/investigations`:

```json
{
  "patient_id": "YOUR-SYNTHEA-PATIENT-ID",
  "question": "Summarize this patient's longitudinal health record and identify important changes."
}
```

The current starter returns a structured, traceable research report. Later versions will replace the deterministic agent implementations with real LLM reasoning, RAG and evaluation.
