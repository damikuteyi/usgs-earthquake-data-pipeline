
import requests
import pandas as pd


USGS_API_URL = (
    "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
)


def fetch_earthquakes():
    """Fetch the latest earthquake records from the USGS API."""
    response = requests.get(USGS_API_URL, timeout=40)
    response.raise_for_status()

    data = response.json()
    return data["features"]


def transform_earthquakes(features):
    """Transform raw USGS records into a structured DataFrame."""
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

    if not df.empty:
        df["time"] = pd.to_datetime(
            df["time"],
            unit="ms",
            utc=True,
        )

    return df


def validate_earthquakes(df):
    """Run basic data-quality checks and return their results."""
    return {
        "record_count": len(df),
        "missing_values": int(df.isnull().sum().sum()),
        "invalid_latitude": int(
            (~df["latitude"].between(-90, 90)).sum()
        ),
        "invalid_longitude": int(
            (~df["longitude"].between(-180, 180)).sum()
        ),
        "missing_magnitude": int(df["magnitude"].isnull().sum()),
    }

def load_earthquakes(df, database_path="data/earthquakes.duckdb"):
    """Load transformed earthquake records into DuckDB."""
    import duckdb

    with duckdb.connect(database_path) as connection:
        connection.register("earthquakes_df", df)

        connection.execute("""
            CREATE OR REPLACE TABLE earthquakes AS
            SELECT * FROM earthquakes_df
        """)

        count = connection.execute(
            "SELECT COUNT(*) FROM earthquakes"
        ).fetchone()[0]

        print(f"Records verified in DuckDB: {count}")

    return len(df)

def main():
    """Run the earthquake data extraction and transformation pipeline."""
    print("Fetching earthquake data from USGS...")

    features = fetch_earthquakes()
    print(f"Records fetched: {len(features)}")

    df = transform_earthquakes(features)
    print(f"Transformed DataFrame shape: {df.shape}")

    quality_report = validate_earthquakes(df)

    print("\nData quality report:")
    for check, result in quality_report.items():
        print(f"{check}: {result}")

    loaded_count = load_earthquakes(df)
    print(f"\nRecords loaded into DuckDB: {loaded_count}")

    print("\nSample records:")
    print(df.head())


if __name__ == "__main__":
    main()
