
# USGS Earthquake Data Engineering Pipeline

## Overview

A Python-based data engineering project that retrieves earthquake records from the United States Geological Survey (USGS) public API, transforms raw GeoJSON data into a structured pandas DataFrame, performs data quality validation, and loads the results into DuckDB for SQL-based analysis.

The project demonstrates core data engineering practices, including API integration, data transformation, data validation, database loading, automated testing, error handling, and structured logging.

## Pipeline Workflow

1. **Extract:** Fetch earthquake records from the USGS all-day GeoJSON feed.
2. **Transform:** Extract seven structured fields, including earthquake ID, magnitude, location, timestamp, longitude, latitude, and depth.
3. **Validate:** Check for missing values, invalid geographic coordinates, and missing magnitudes.
4. **Load:** Store transformed records in a local DuckDB database.
5. **Verify:** Confirm successful database loading by checking the number of stored records.
6. **Analyze:** Execute reusable SQL queries to explore earthquake magnitude distribution, largest earthquakes, and geographic distribution.
7. **Monitor:** Record pipeline activities, progress, warnings, and failures using Python's logging module.

## Technology Stack

- Python
- Requests
- pandas
- DuckDB
- SQL
- pytest
- Python logging
- USGS Earthquake API

## Project Structure

```text
usgs-earthquake-data-pipeline/
├── data/
│   └── earthquakes.duckdb
├── src/
│   ├── earthquake_pipeline.py
│   └── analytics.py
├── tests/
│   └── test_earthquake_pipeline.py
├── .gitignore
└── README.md
```

Note: The DuckDB database is generated locally and excluded from Git.

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
python -m pip install requests pandas duckdb pytest
```

## Running the Pipeline

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

Run the complete test suite:

```bash
python -m pytest -v
```

## Data Source

United States Geological Survey (USGS) Earthquake Hazards Program:

[Earthquake GeoJSON Feeds](https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php)

The project uses the public all-day GeoJSON feed and does not require an API key.

## Current Scope

The pipeline retrieves the latest USGS all-day earthquake feed, transforms and validates the records, loads them into DuckDB, and supports reusable SQL-based analysis.

It also includes automated testing, API error handling, and structured logging to improve reliability and observability.

The database is refreshed using the latest feed whenever the pipeline runs.