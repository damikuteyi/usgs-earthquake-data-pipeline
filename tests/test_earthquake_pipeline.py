
import pandas as pd

from src.earthquake_pipeline import transform_earthquakes


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
