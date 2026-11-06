from pathlib import Path
import logging

import duckdb
import pandas as pd
import requests

USGS_API_URL = (
    "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
)

DATABASE_PATH = Path(__file__).resolve().parent.parent / "data" / "earthquakes.duckdb"

logger = logging.getLogger(__name__)


def fetch_earthquakes():
    """Fetch the latest earthquake records from the USGS API."""

    logger.info("Starting earthquake data extraction from USGS.")

    try:
        response = requests.get(USGS_API_URL, timeout=30)
        response.raise_for_status()

        data = response.json()

        if not isinstance(data, dict) or "features" not in data:
            raise ValueError(
                "USGS response does not contain earthquake features."
            )

        features = data["features"]

        logger.info(
            "Successfully extracted %s earthquake records.",
            len(features),
        )

        return features

    except requests.exceptions.JSONDecodeError as error:
        logger.error("Invalid JSON received from USGS: %s", error)

        raise RuntimeError(
            f"Invalid response received from USGS: {error}"
        ) from error

    except requests.exceptions.RequestException as error:
        logger.error("USGS API request failed: %s", error)

        raise RuntimeError(
            f"Failed to fetch earthquake data from USGS: {error}"
        ) from error

    except (ValueError, TypeError) as error:
        logger.error("Invalid response received from USGS: %s", error)

        raise RuntimeError(
            f"Invalid response received from USGS: {error}"
        ) from error

def transform_earthquakes(features):
    """Transform raw USGS records into a structured DataFrame."""

    logger.info(
        "Starting transformation of %s earthquake records.",
        len(features),
    )

    earthquakes = []

    for feature in features:
        coordinates = feature["geometry"]["coordinates"]
        properties = feature["properties"]

        earthquake = {
            "earthquake_id": feature["id"],
            "magnitude": properties["mag"],
            "place": properties["place"],
            "time": properties["time"],
            "longitude": coordinates[0],
            "latitude": coordinates[1],
            "depth_km": coordinates[2],
        }

        earthquakes.append(earthquake)

    columns = [
        "earthquake_id",
        "magnitude",
        "place",
        "time",
        "longitude",
        "latitude",
        "depth_km",
    ]

    df = pd.DataFrame(earthquakes, columns=columns)

    df["time"] = pd.to_datetime(
        df["time"],
        unit="ms",
        utc=True,
    )

    logger.info(
        "Successfully transformed %s earthquake records.",
        len(df),
    )

    return df


def validate_earthquakes(df):
    """Run data quality checks on the transformed earthquake data."""

    logger.info(
        "Starting data quality validation for %s records.",
        len(df),
    )

    missing_values = int(df.isnull().sum().sum())

    report = {
        "record_count": len(df),
        "missing_values": missing_values,
        "invalid_latitude": int(
            ((df["latitude"] < -90) | (df["latitude"] > 90)).sum()
        ),
        "invalid_longitude": int(
            ((df["longitude"] < -180) | (df["longitude"] > 180)).sum()
        ),
        "missing_magnitude": int(df["magnitude"].isnull().sum()),
    }

    has_quality_issues = (
        report["missing_values"] > 0
        or report["invalid_latitude"] > 0
        or report["invalid_longitude"] > 0
        or report["missing_magnitude"] > 0
    )

    if has_quality_issues:
        logger.warning("Data quality issues detected: %s", report)
    else:
        logger.info("No data quality issues detected.")

    logger.info(
        "Data quality validation completed. Records checked: %s.",
        report["record_count"],
    )

    return report

def load_earthquakes(
    df,
    database_path=DATABASE_PATH,
):
    """Load transformed earthquake records into DuckDB."""

    logger.info(
        "Starting database load of %s earthquake records.",
        len(df),
    )

    try:
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        with duckdb.connect(database_path) as connection:
            connection.register("earthquake_df", df)

            connection.execute("""
                CREATE OR REPLACE TABLE earthquakes AS
                SELECT * FROM earthquake_df
            """)

            result = connection.execute(
                "SELECT COUNT(*) FROM earthquakes"
            ).fetchone()[0]

        if result != len(df):
            raise RuntimeError(
                f"Database row count mismatch: expected {len(df)}, "
                f"loaded {result}."
            )

        logger.info(
            "Successfully loaded %s records into %s.",
            result,
            database_path,
        )

        return result

    except Exception:
        logger.exception("Failed to load earthquake records into DuckDB.")
        raise

def main():
    """Run the complete earthquake data pipeline."""

    logger.info("Earthquake data pipeline started.")

    try:
        features = fetch_earthquakes()

        df = transform_earthquakes(features)

        quality_report = validate_earthquakes(df)

        print("\nData Quality Report:")
        for check, result in quality_report.items():
            print(f"{check}: {result}")

        loaded_records = load_earthquakes(df)

        print(f"\nSuccessfully loaded {loaded_records} records.")
        print("\nSample earthquake records:")
        print(df.head())

        logger.info("Earthquake data pipeline completed successfully.")

    except Exception:
        logger.exception("Earthquake data pipeline failed.")
        raise


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    main()
