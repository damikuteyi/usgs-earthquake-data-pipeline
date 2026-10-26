# USGS Earthquake Data Engineering Pipeline

## Overview

A Python data engineering project that retrieves earthquake records from the United States Geological Survey (USGS) public API, transforms the data into a structured pandas DataFrame, performs basic data-quality checks, and loads the results into DuckDB for SQL analysis.

## Pipeline Workflow

1. **Extract:** Fetch earthquake records from the USGS all-day GeoJSON feed.
2. **Transform:** Select seven fields, including earthquake ID, magnitude, location, timestamp, longitude, latitude, and depth.
3. **Validate:** Check for missing values, invalid geographic coordinates, and missing magnitudes.
4. **Load:** Store the transformed records in a local DuckDB database.
5. **Verify:** Query DuckDB to confirm the number of records loaded.

## Technology Stack

- Python
- Requests
- pandas
- DuckDB
- USGS Earthquake API

## Project Structure

```text
usgs-earthquake-data-pipeline/
├── data/
├── src/
│   └── earthquake_pipeline.py
├── tests/
│   └── test_earthquake_pipeline.py
├── .gitignore
└── README.md
```

## Setup and Usage

Create and activate a virtual environment, then install the dependencies:

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install requests pandas duckdb
```

Run the pipeline from the project root:

```bash
python src/earthquake_pipeline.py
```

The pipeline creates `data/earthquakes.duckdb` locally. Database files are excluded from Git.

## Data Source

USGS Earthquake Hazards Program — [Earthquake GeoJSON Feeds](https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php)

## Current Scope

This initial version implements API extraction, data transformation, basic validation, and database loading. Automated tests and additional SQL analyses are planned as the project develops.