
import logging

import duckdb


DATABASE_PATH = "data/earthquakes.duckdb"

logger = logging.getLogger(__name__)


def get_magnitude_distribution():
    """Return earthquake counts grouped by magnitude category."""

    logger.info("Starting earthquake magnitude distribution analysis.")

    try:
        with duckdb.connect(DATABASE_PATH, read_only=True) as connection:
            result = connection.execute("""
                SELECT
                    CASE
                        WHEN magnitude < 2.0 THEN 'Minor'
                        WHEN magnitude < 4.0 THEN 'Light'
                        WHEN magnitude < 5.0 THEN 'Moderate'
                        WHEN magnitude < 6.0 THEN 'Strong'
                        ELSE 'Major'
                    END AS magnitude_category,
                    COUNT(*) AS earthquake_count
                FROM earthquakes
                WHERE magnitude IS NOT NULL
                GROUP BY magnitude_category
                ORDER BY earthquake_count DESC
            """).fetchdf()

        logger.info(
            "Magnitude distribution analysis completed. Categories found: %s.",
            len(result),
        )

        return result

    except Exception:
        logger.exception("Magnitude distribution analysis failed.")
        raise


def get_largest_earthquakes(limit=10):
    """Return the largest earthquakes, ordered by magnitude."""

    logger.info(
        "Starting largest earthquake analysis. Requested records: %s.",
        limit,
    )

    try:
        with duckdb.connect(DATABASE_PATH, read_only=True) as connection:
            result = connection.execute("""
                SELECT
                    earthquake_id,
                    magnitude,
                    place,
                    time,
                    longitude,
                    latitude,
                    depth_km
                FROM earthquakes
                WHERE magnitude IS NOT NULL
                ORDER BY magnitude DESC, time DESC
                LIMIT ?
            """, [limit]).fetchdf()

        logger.info(
            "Largest earthquake analysis completed. Records returned: %s.",
            len(result),
        )

        return result

    except Exception:
        logger.exception("Largest earthquake analysis failed.")
        raise


def get_earthquakes_by_hemisphere():
    """Return earthquake counts and average magnitude by hemisphere."""

    logger.info("Starting earthquake hemisphere analysis.")

    try:
        with duckdb.connect(DATABASE_PATH, read_only=True) as connection:
            result = connection.execute("""
                SELECT
                    CASE
                        WHEN latitude >= 0 THEN 'Northern'
                        ELSE 'Southern'
                    END AS hemisphere,
                    COUNT(*) AS earthquake_count,
                    ROUND(AVG(magnitude), 2) AS average_magnitude
                FROM earthquakes
                WHERE latitude IS NOT NULL
                GROUP BY hemisphere
                ORDER BY earthquake_count DESC
            """).fetchdf()

        logger.info(
            "Hemisphere analysis completed. Regions found: %s.",
            len(result),
        )

        return result

    except Exception:
        logger.exception("Hemisphere analysis failed.")
        raise


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logger.info("Earthquake analytics execution started.")

    distribution = get_magnitude_distribution()
    print("\nEarthquake Magnitude Distribution:")
    print(distribution)

    largest = get_largest_earthquakes()
    print("\nTop 10 Largest Earthquakes:")
    print(largest)

    geographic = get_earthquakes_by_hemisphere()
    print("\nEarthquakes by Hemisphere:")
    print(geographic)

    logger.info("Earthquake analytics execution completed successfully.")