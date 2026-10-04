import pandas as pd
from sqlalchemy import text

from src.database.connection import engine


CSV_PATH = "data/synthetic/1_village_dataset.csv"


def load_villages():
    df = pd.read_csv(CSV_PATH)

    print(f"Village records found in CSV: {len(df)}")
    print("Columns:", list(df.columns))

    insert_query = text("""
        INSERT INTO public.villages
        (
            village_id,
            village_name,
            latitude,
            longitude,
            population,
            households,
            vulnerability_score,
            priority_score
        )
        VALUES
        (
            :village_id,
            :village_name,
            :latitude,
            :longitude,
            :population,
            :households,
            :vulnerability_score,
            :priority_score
        )
        ON CONFLICT (village_id)
        DO UPDATE SET
            village_name = EXCLUDED.village_name,
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude,
            population = EXCLUDED.population,
            households = EXCLUDED.households,
            vulnerability_score = EXCLUDED.vulnerability_score;
    """)

    with engine.begin() as connection:

        for _, row in df.iterrows():

            connection.execute(
                insert_query,
                {
                    "village_id": row["village_id"],
                    "village_name": row["village_name"],
                    "latitude": float(row["latitude"]),
                    "longitude": float(row["longitude"]),
                    "population": int(row["population"]),
                    "households": int(row["households"]),
                    "vulnerability_score": float(row["vulnerability_index"]),
                    "priority_score": None
                }
            )

    print("Village data loaded successfully!")


if __name__ == "__main__":
    load_villages()