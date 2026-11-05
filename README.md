# USGS Earthquake Data Engineering Pipeline

## Overview

A Python-based data engineering project that retrieves earthquake records from the United States Geological Survey (USGS) public API, transforms raw GeoJSON data into a structured pandas DataFrame, performs data quality validation, and loads the results into DuckDB for SQL-based analysis.

The project demonstrates core data engineering practices, including API integration, data transformation, data validation, database loading, automated testing, error handling, structured logging, containerisation, and workflow orchestration.

Apache Airflow is used to orchestrate pipeline execution, while Docker provides a reproducible environment for running the orchestration services.

## Pipeline Workflow

1. **Extract:** Fetch earthquake records from the USGS all-day GeoJSON feed.
2. **Transform:** Extract seven structured fields, including earthquake ID, magnitude, location, timestamp, longitude, latitude, and depth.
3. **Validate:** Check for missing values, invalid geographic coordinates, and missing magnitudes.
4. **Load:** Store transformed records in a local DuckDB database.
5. **Verify:** Confirm successful database loading by checking the number of stored records.
6. **Analyze:** Execute reusable SQL queries to explore earthquake magnitude distribution, largest earthquakes, and geographic distribution.
7. **Monitor:** Record pipeline activities, progress, warnings, and failures using Python's logging module.
8. **Orchestrate:** Use Apache Airflow to execute and monitor the pipeline through a DAG, with retry and timeout configurations.

## Technology Stack

- Python
- Requests
- pandas
- DuckDB
- SQL
- pytest
- Python logging
- USGS Earthquake API
- Apache Airflow 3.1.0
- Docker and Docker Compose
- PostgreSQL 16

## Project Structure

```text
usgs-earthquake-data-pipeline/
├── airflow/
├── dags/
│   └── earthquake_pipeline_dag.py
├── data/
│   └── earthquakes.duckdb
├── src/
│   ├── analytics.py
│   └── earthquake_pipeline.py
├── tests/
│   └── test_earthquake_pipeline.py
├── .gitignore
├── .env
├── docker-compose.yaml
├── requirements.txt
└── README.md
```

Note:
- The DuckDB database is generated locally and excluded from Git.
- Airflow logs and runtime files are excluded from Git.
- The `.env` file contains local secrets and must never be committed.
- The `airflow/` directory is used for local Airflow-related files.

## Setup and Installation

### 1. Clone the repository

```bash
git clone https://github.com/damikuteyi/usgs-earthquake-data-pipeline.git

cd usgs-earthquake-data-pipeline
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the virtual environment

For Git Bash on Windows:

```bash
source .venv/Scripts/activate
```

### 4. Install dependencies

```bash
python -m pip install -r requirements.txt
python -m pip install pytest
```

## Running the Pipeline Locally

Execute the main pipeline from the project root:

```bash
python src/earthquake_pipeline.py
```

The pipeline performs extraction, transformation, data quality validation, and database loading.

It also produces timestamped log messages showing the progress of each stage.

The resulting database is stored at:

```text
data/earthquakes.duckdb
```

## Analytics

Reusable SQL analytics functions are implemented in `src/analytics.py` using DuckDB.

The project currently supports:

- **Magnitude distribution:** Groups earthquakes into Minor, Light, Moderate, Strong, and Major categories.
- **Largest earthquakes:** Retrieves the ten largest earthquakes, ordered by magnitude.
- **Hemisphere analysis:** Calculates earthquake counts and average magnitude for the Northern and Southern Hemispheres.

The analytics functions return pandas DataFrames and use read-only database connections.

Run the analytics module:

```bash
python src/analytics.py
```

## Data Quality Validation

The pipeline performs the following checks:

- Total number of records processed.
- Missing values.
- Invalid latitude values.
- Invalid longitude values.
- Missing earthquake magnitudes.

Data quality issues are reported through the validation report and warning-level logs.

## Error Handling and Reliability

The extraction process handles:

- API connection failures.
- HTTP errors.
- Request timeouts.
- Invalid JSON responses.
- Missing expected API fields.

Errors are logged and raised as exceptions so that failures are visible to the calling application.

Database loading failures are also logged with traceback information.

## Pipeline Observability and Logging

The project uses Python's built-in logging module to monitor pipeline execution.

Three logging levels are currently used:

| Level | Purpose |
|---|---|
| INFO | Records normal pipeline operations and progress |
| WARNING | Reports data quality issues |
| ERROR | Records API and operational failures |

Log messages include:

- Timestamp.
- Logging level.
- Python module.
- Descriptive message.

Example:

```text
2026-11-03 23:03:15 | INFO | __main__ | Earthquake data pipeline started.
2026-11-03 23:03:15 | INFO | __main__ | Starting earthquake data extraction from USGS.
2026-11-03 23:03:15 | INFO | __main__ | Successfully extracted 207 earthquake records.
2026-11-03 23:03:16 | INFO | __main__ | Earthquake data pipeline completed successfully.
```

## Apache Airflow Orchestration

Apache Airflow is used to orchestrate the USGS earthquake pipeline.

The project includes an Airflow DAG:

```text
dags/earthquake_pipeline_dag.py
```

The DAG currently uses a `BashOperator` to execute the existing Python pipeline inside the Airflow container.

### Orchestration workflow

```text
Manual DAG Trigger
        |
        v
Airflow Scheduler
        |
        v
run_earthquake_pipeline
        |
        v
Python Pipeline
        |
        v
USGS API Extraction
        |
        v
Transformation
        |
        v
Data Quality Validation
        |
        v
DuckDB Database Load
        |
        v
Successful Completion
```

### Airflow configuration

The DAG includes:

| Configuration | Value |
|---|---|
| DAG ID | usgs_earthquake_pipeline |
| Operator | BashOperator |
| Schedule | Manual (`schedule=None`) |
| Catchup | Disabled |
| Retries | 2 |
| Retry delay | 5 minutes |
| Task execution timeout | 10 minutes |
| DAG run timeout | 15 minutes |

The retry configuration allows Airflow to make two additional attempts when a task fails. The task execution timeout limits how long an individual task can run.

### Running Airflow with Docker

Docker Desktop and Docker Compose must be installed and running.

#### 1. Configure Airflow secrets

Create a `.env` file in the project root.

Generate two separate random secrets using Git Bash:

```bash
openssl rand -hex 32
openssl rand -hex 32
```

Add the generated values to `.env`:

```dotenv
AIRFLOW__API__SECRET_KEY=your_generated_api_secret
AIRFLOW__API_AUTH__JWT_SECRET=your_generated_jwt_secret
```

Use the actual generated values locally. Do not commit this file or publish its contents.

#### 2. Initialise the Airflow database

Run:

```bash
docker compose up airflow-init
```

This initialises the Airflow metadata database using PostgreSQL.

Wait for the initialisation process to finish successfully.

#### 3. Start the Airflow services

Run:

```bash
docker compose up -d
```

This starts the Airflow API server, scheduler, DAG processor, and PostgreSQL services.

#### 4. Check running services

Run:

```bash
docker compose ps
```

Confirm that the Airflow services are running and PostgreSQL is healthy.

#### 5. Access the Airflow dashboard

Open:

http://localhost:8080

The configured Simple Auth Manager username is:

```text
admin
```

Retrieve the generated password from the running API server:

```bash
MSYS_NO_PATHCONV=1 docker compose exec airflow-apiserver cat /opt/airflow/simple_auth_manager_passwords.json.generated
```

Use the generated password for the `admin` account. Keep it private.

#### 6. Trigger the earthquake pipeline

1. Open the Airflow dashboard.
2. Locate `usgs_earthquake_pipeline`.
3. Select the DAG.
4. Trigger a manual run.
5. Monitor the task status and execution logs.

A successful run should show the task in green and report the number of records loaded into DuckDB.

#### 7. View Airflow logs

To inspect Airflow DAG processor logs:

```bash
docker compose logs airflow-dag-processor
```

To inspect scheduler logs:

```bash
docker compose logs airflow-scheduler
```

#### 8. Stop the Airflow environment

Run:

```bash
docker compose down
```

This stops and removes the containers while preserving the PostgreSQL data volume and local project files.

To also remove the PostgreSQL data volume, use:

```bash
docker compose down -v
```

**Warning:** The second command deletes the persisted PostgreSQL metadata volume. Use it only when you intentionally want to reset the Airflow database.

## Automated Testing

The project uses pytest to validate its functionality.

The current test suite contains 12 automated tests covering:

- Earthquake data transformation.
- Empty input handling.
- Missing magnitude detection.
- Invalid geographic coordinates.
- Magnitude distribution analytics.
- Largest earthquake queries.
- Geographic hemisphere analysis.
- API connection failures.
- HTTP errors.
- Request timeouts.
- Invalid JSON responses.
- Missing API response fields.

Logging behaviour is also verified through pytest's log-capturing fixture.

Run the tests:

```bash
python -m pytest tests/ -v
```

The tests are restricted to the `tests/` directory to avoid collecting Airflow runtime files.

## Data Source

United States Geological Survey (USGS) Earthquake Hazards Program:

[Earthquake GeoJSON Feeds](https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php)

The project uses the public all-day GeoJSON feed and does not require an API key.

## Current Scope

The pipeline retrieves the latest USGS all-day earthquake feed, transforms and validates the records, loads them into DuckDB, and supports reusable SQL-based analysis.

It also includes automated testing, API error handling, structured logging, and Apache Airflow orchestration through Docker.

The Airflow DAG currently runs the complete Python pipeline as one task and supports manual triggering, retries, and execution timeouts.

The database is refreshed using the latest feed whenever the pipeline runs.
