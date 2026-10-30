
import pandas as pd
import duckdb
import pytest
import src.analytics as analytics


@pytest.fixture
def sample_analytics_database(tmp_path, monkeypatch):
    """Create a temporary DuckDB database for analytics tests."""

    database_path = tmp_path / "test_earthquakes.duckdb"

    with duckdb.connect(str(database_path)) as connection:
        connection.execute("""
            CREATE TABLE earthquakes (
                earthquake_id VARCHAR,
                magnitude DOUBLE,
                place VARCHAR,
                time TIMESTAMPTZ,
                longitude DOUBLE,
                latitude DOUBLE,
                depth_km DOUBLE
            )
        """)

        connection.execute("""
            INSERT INTO earthquakes VALUES
            ('eq001', 1.5, 'California', '2026-10-30 10:00:00+00:00', -120.0, 35.0, 8.0),
            ('eq002', 3.2, 'Alaska', '2026-10-30 11:00:00+00:00', -150.0, 60.0, 15.0),
            ('eq003', 5.5, 'Vanuatu', '2026-10-30 12:00:00+00:00', 167.0, -15.0, 20.0),
            ('eq004', 6.2, 'Japan', '2026-10-30 13:00:00+00:00', 140.0, 36.0, 30.0)
        """)

    monkeypatch.setattr(analytics, "DATABASE_PATH", str(database_path))

    return database_path


def test_magnitude_distribution(sample_analytics_database):
    result = analytics.get_magnitude_distribution()

    assert len(result) == 4

    distribution = dict(
        zip(
            result["magnitude_category"],
            result["earthquake_count"]
        )
    )

    assert distribution == {
        "Minor": 1,
        "Light": 1,
        "Strong": 1,
        "Major": 1,
    }

def test_largest_earthquakes(sample_analytics_database):
    result = analytics.get_largest_earthquakes(limit=2)

    assert len(result) == 2

    assert result.iloc[0]["earthquake_id"] == "eq004"
    assert result.iloc[0]["magnitude"] == 6.2

    assert result.iloc[1]["earthquake_id"] == "eq003"
    assert result.iloc[1]["magnitude"] == 5.5

    assert result["magnitude"].is_monotonic_decreasing


def test_earthquakes_by_hemisphere(sample_analytics_database):
    result = analytics.get_earthquakes_by_hemisphere()

    assert len(result) == 2

    distribution = dict(
        zip(
            result["hemisphere"],
            result["earthquake_count"]
        )
    )

    assert distribution == {
        "Northern": 3,
        "Southern": 1,
    }

    averages = dict(
        zip(
            result["hemisphere"],
            result["average_magnitude"]
        )
    )

    assert averages["Northern"] == 3.63
    assert averages["Southern"] == 5.5

from src.earthquake_pipeline import (
    transform_earthquakes,
    validate_earthquakes
)


def test_transform_earthquakes():
    # Arrange: create a sample USGS API record
    features = [
        {
            "id": "test123",
            "properties": {
                "mag": 2.5,
                "place": "10 km NW of Example City",
                "time": 1700000000000,
            },
            "geometry": {
                "coordinates": [-120.5, 35.5, 8.2]
            },
        }
    ]

    # Act: transform the raw record into a DataFrame
    df = transform_earthquakes(features)

    # Assert: check the transformed data
    assert len(df) == 1
    assert df.loc[0, "earthquake_id"] == "test123"
    assert df.loc[0, "magnitude"] == 2.5
    assert df.loc[0, "place"] == "10 km NW of Example City"
    assert df.loc[0, "longitude"] == -120.5
    assert df.loc[0, "latitude"] == 35.5
    assert df.loc[0, "depth_km"] == 8.2
    assert pd.api.types.is_datetime64_any_dtype(df["time"])

def test_validate_earthquakes_detects_missing_magnitude():
    # Arrange: create a DataFrame with one missing magnitude
    df = pd.DataFrame(
        [
            {
                "earthquake_id": "test123",
                "magnitude": None,
                "place": "10 km NW of Example City",
                "time": pd.Timestamp("2023-11-14", tz="UTC"),
                "longitude": -120.5,
                "latitude": 35.5,
                "depth_km": 8.2,
            }
        ]
    )

    # Act: run the data-quality checks
    report = validate_earthquakes(df)

    # Assert: verify that the missing magnitude is detected
    assert report["record_count"] == 1
    assert report["missing_magnitude"] == 1
    assert report["missing_values"] == 1
    assert report["invalid_latitude"] == 0
    assert report["invalid_longitude"] == 0

def test_validate_earthquakes_detects_invalid_coordinates():
    df = pd.DataFrame(
        [
            {
                "earthquake_id": "test456",
                "magnitude": 2.5,
                "place": "Example location",
                "time": pd.Timestamp("2023-11-14", tz="UTC"),
                "longitude": -200.0,
                "latitude": 95.0,
                "depth_km": 8.2,
            }
        ]
    )

    report = validate_earthquakes(df)

    assert report["invalid_latitude"] == 1
    assert report["invalid_longitude"] == 1
    assert report["missing_magnitude"] == 0

def test_transform_earthquakes_handles_empty_input():
    df = transform_earthquakes([])

    assert df.empty
    assert list(df.columns) == [
        "earthquake_id",
        "magnitude",
        "place",
        "time",
        "longitude",
        "latitude",
        "depth_km",
    ]