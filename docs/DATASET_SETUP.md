# Dataset Setup Guide

## Goal

Get a reproducible open synthetic healthcare dataset into AEGIS without downloading or distributing real patient data.

## Recommended path: generate Synthea locally

### 1. Install Java

Install a current Java LTS release (17+).

Check:

```bash
java -version
```

### 2. Clone Synthea

```bash
git clone https://github.com/synthetichealth/synthea.git
cd synthea
```

### 3. Generate patients

Start with 100:

```bash
./run_synthea -p 100 --exporter.csv.export=true
```

Windows:

```powershell
.\run_synthea.bat -p 100 --exporter.csv.export=true
```

The CSV output is normally under:

```text
synthea/output/csv/
```

### 4. Copy the data

Copy the CSV files to:

```text
AEGIS/data/synthea/
```

At minimum, AEGIS expects:

- patients.csv
- encounters.csv
- conditions.csv
- medications.csv
- observations.csv
- procedures.csv

The application can also load:

- allergies.csv
- careplans.csv
- immunizations.csv

### 5. Validate

From the AEGIS root:

```bash
aegis-ingest data/synthea
```

You should see the table names and row counts.

## Alternative: official downloads

Synthea's official download page contains pre-generated synthetic populations:

https://synthea.mitre.org/downloads

The source project is:

https://github.com/synthetichealth/synthea

If an archive is downloaded, extract its CSV data and copy it to `data/synthea/`.

## Data policy for this repository

- Do not commit large generated datasets.
- Do not add real patient information.
- Do not add credentials or private medical records.
- Keep only tiny synthetic fixtures in Git.
- Record the Synthea version and generation parameters for reproducibility.

## Reproducibility record

For every experiment, record:

```text
Synthea version:
Population size:
Generation command:
Output format:
AEGIS commit:
LLM/model:
Prompt version:
Evaluation benchmark version:
```
