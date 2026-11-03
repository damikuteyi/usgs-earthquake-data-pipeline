
import duckdb
import pandas as pd
import pytest
import requests

from unittest.mock import Mock, patch

import src.analytics as analytics

from src.earthquake_pipeline import (
    fetch_earthquakes,
    transform_earthquakes,
    validate_earthquakes,
)


# --------------------------------------------------
# ANALYTICS TEST FIXTURE
# --------------------------------------------------

@pytest.fixture
def sample_analytics_database(tmp_path, monkeypatch):
    """Create a temporary DuckDB database for analytics tests."""

    database_path = tmp_path / "test_earthquakes.duckdb"

    sample_data = pd.DataFrame(
        [
            {
                "earthquake_id": "eq001",
                "magnitude": 1.5,
                "place": "Northern Example",
                "time": pd.Timestamp("2026-01-01", tz="UTC"),
                "longitude": -120.0,
                "latitude": 40.0,
                "depth_km": 10.0,
            },
            {
                "earthquake_id": "eq002",
                "magnitude": 3.2,
                "place": "Northern Example",
                "time": pd.Timestamp("2026-01-02", tz="UTC"),
                "longitude": -110.0,
                "latitude": 30.0,
                "depth_km": 15.0,
            },
            {
                "earthquake_id": "eq003",
                "magnitude": 5.5,
                "place": "Southern Example",
                "time": pd.Timestamp("2026-01-03", tz="UTC"),
                "longitude": 120.0,
                "latitude": -30.0,
                "depth_km": 20.0,
            },
            {
                "earthquake_id": "eq004",
                "magnitude": 6.2,
                "place": "Northern Example",
                "time": pd.Timestamp("2026-01-04", tz="UTC"),
                "longitude": 100.0,
                "latitude": 20.0,
                "depth_km": 25.0,
            },
        ]
    )

    with duckdb.connect(str(database_path)) as connection:
        connection.register("sample_data", sample_data)

        connection.execute("""
            CREATE TABLE earthquakes AS
            SELECT * FROM sample_data
        """)

    monkeypatch.setattr(
        analytics,
        "DATABASE_PATH",
        str(database_path),
    )


# --------------------------------------------------
# TRANSFORMATION TESTS
# --------------------------------------------------

def test_transform_earthquakes():
    """Test transformation of raw USGS records."""

    features = [
        {
            "id": "test123",
            "geometry": {
                "coordinates": [-120.5, 35.5, 8.2]
            },
            "properties": {
                "mag": 4.5,
                "place": "10 km NW of Example City",
                "time": 1700000000000,
            },
        }
    ]

    df = transform_earthquakes(features)

    assert len(df) == 1
    assert df.iloc[0]["earthquake_id"] == "test123"
    assert df.iloc[0]["magnitude"] == 4.5
    assert df.iloc[0]["longitude"] == -120.5
    assert df.iloc[0]["latitude"] == 35.5
    assert df.iloc[0]["depth_km"] == 8.2

    assert pd.api.types.is_datetime64_any_dtype(df["time"])


def test_transform_earthquakes_handles_empty_input():
    """Test transformation when no earthquake records are returned."""

    df = transform_earthquakes([])

    assert df.empty

    expected_columns = [
        "earthquake_id",
        "magnitude",
        "place",
        "time",
        "longitude",
        "latitude",
        "depth_km",
    ]

    assert list(df.columns) == expected_columns


# --------------------------------------------------
# DATA QUALITY TESTS
# --------------------------------------------------

def test_validate_earthquakes_detects_missing_magnitude(caplog):
    """Test detection and logging of a missing magnitude."""

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

    report = validate_earthquakes(df)

    assert report["record_count"] == 1
    assert report["missing_magnitude"] == 1
    assert report["missing_values"] == 1

    assert "Data quality issues detected" in caplog.text


def test_validate_earthquakes_detects_invalid_coordinates():
    """Test detection of invalid latitude and longitude values."""

    df = pd.DataFrame(
        [
            {
                "earthquake_id": "test123",
                "magnitude": 4.5,
                "place": "Example City",
                "time": pd.Timestamp("2023-11-14", tz="UTC"),
                "longitude": 200.0,
                "latitude": 95.0,
                "depth_km": 8.2,
            }
        ]
    )

    report = validate_earthquakes(df)

    assert report["invalid_latitude"] == 1
    assert report["invalid_longitude"] == 1


# --------------------------------------------------
# ANALYTICS TESTS
# --------------------------------------------------

def test_magnitude_distribution(sample_analytics_database):
    """Test earthquake magnitude distribution."""

    result = analytics.get_magnitude_distribution()

    assert len(result) == 4

    distribution = dict(zip(result.iloc[:, 0], result.iloc[:, 1]))

    assert distribution["Minor"] == 1
    assert distribution["Light"] == 1
    assert distribution["Strong"] == 1
    assert distribution["Major"] == 1
    assert "Moderate" not in distribution


def test_largest_earthquakes(sample_analytics_database):
    """Test retrieval of the largest earthquakes."""

    result = analytics.get_largest_earthquakes(limit=2)

    assert len(result) == 2
    assert result.iloc[0]["earthquake_id"] == "eq004"
    assert result.iloc[0]["magnitude"] == 6.2
    assert result.iloc[1]["earthquake_id"] == "eq003"
    assert result.iloc[1]["magnitude"] == 5.5

    assert result["magnitude"].is_monotonic_decreasing


def test_earthquakes_by_hemisphere(sample_analytics_database):
    """Test earthquake aggregation by hemisphere."""

    result = analytics.get_earthquakes_by_hemisphere()

    hemisphere_data = result.set_index(result.columns[0])

    assert hemisphere_data.loc["Northern"].iloc[0] == 3
    assert hemisphere_data.loc["Southern"].iloc[0] == 1
    assert hemisphere_data.loc["Northern"].iloc[1] == pytest.approx(3.63)
    assert hemisphere_data.loc["Southern"].iloc[1] == pytest.approx(5.5)

# --------------------------------------------------
# API ERROR-HANDLING TESTS
# --------------------------------------------------

def test_fetch_earthquakes_handles_connection_error(caplog):
    """Test handling and logging of connection errors."""

    with patch(
        "src.earthquake_pipeline.requests.get",
        side_effect=requests.exceptions.ConnectionError(
            "Unable to connect to USGS"
        ),
    ):
        with pytest.raises(
            RuntimeError,
            match="Failed to fetch earthquake data",
        ):
            fetch_earthquakes()

    assert "USGS API request failed" in caplog.text


def test_fetch_earthquakes_handles_http_error():
    """Test handling of HTTP errors."""

    mock_response = Mock()

    mock_response.raise_for_status.side_effect = (
        requests.exceptions.HTTPError("500 Server Error")
    )

    with patch(
        "src.earthquake_pipeline.requests.get",
        return_value=mock_response,
    ):
        with pytest.raises(
            RuntimeError,
            match="Failed to fetch earthquake data",
        ):
            fetch_earthquakes()


def test_fetch_earthquakes_handles_timeout():
    """Test handling of request timeouts."""

    with patch(
        "src.earthquake_pipeline.requests.get",
        side_effect=requests.exceptions.Timeout(
            "Request timed out"
        ),
    ):
        with pytest.raises(
            RuntimeError,
            match="Failed to fetch earthquake data",
        ):
            fetch_earthquakes()


def test_fetch_earthquakes_handles_invalid_json():
    """Test handling of invalid JSON responses."""

    mock_response = Mock()

    mock_response.raise_for_status.return_value = None

    mock_response.json.side_effect = (
        requests.exceptions.JSONDecodeError(
            "Invalid JSON",
            "invalid response",
            0,
        )
    )

    with patch(
        "src.earthquake_pipeline.requests.get",
        return_value=mock_response,
    ):
        with pytest.raises(
            RuntimeError,
            match="Invalid response received from USGS",
        ):
            fetch_earthquakes()


def test_fetch_earthquakes_handles_missing_features():
    """Test handling of valid JSON without the features key."""

    mock_response = Mock()

    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "type": "FeatureCollection"
    }

    with patch(
        "src.earthquake_pipeline.requests.get",
        return_value=mock_response,
    ):
        with pytest.raises(
            RuntimeError,
            match="Invalid response received from USGS",
        ):
            fetch_earthquakes()