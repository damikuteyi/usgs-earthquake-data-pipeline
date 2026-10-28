
import pandas as pd

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