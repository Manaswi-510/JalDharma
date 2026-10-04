import pandas as pd
from sqlalchemy import text

from src.database.connection import engine


CSV_PATH = "data/synthetic/2_historical_water_demand_dataset.csv"


def load_water_demand():
    df = pd.read_csv(CSV_PATH)

    print(f"Water demand records found in CSV: {len(df)}")
    print("Columns:", list(df.columns))

    # Convert date from DD-MM-YYYY to Python date
    df["date"] = pd.to_datetime(
        df["date"],
        format="%d-%m-%Y"
    ).dt.date

    insert_query = text("""
        INSERT INTO public.water_demand
        (
            date,
            village_id,
            population,
            temperature_c,
            rainfall_mm,
            humidity,
            previous_day_demand_l,
            demand_7day_avg_l,
            demand_30day_avg_l,
            actual_demand_l
        )
        VALUES
        (
            :date,
            :village_id,
            :population,
            :temperature_c,
            :rainfall_mm,
            :humidity,
            :previous_day_demand_l,
            :demand_7day_avg_l,
            :demand_30day_avg_l,
            :actual_demand_l
        );
    """)

    with engine.begin() as connection:

        for _, row in df.iterrows():

            connection.execute(
                insert_query,
                {
                    "date": row["date"],
                    "village_id": row["village_id"],
                    "population": int(row["population"]),
                    "temperature_c": float(row["temperature_c"]),
                    "rainfall_mm": float(row["rainfall_mm"]),
                    "humidity": float(row["humidity"]),
                    "previous_day_demand_l": float(
                        row["previous_day_demand_l"]
                    ),
                    "demand_7day_avg_l": float(
                        row["demand_7day_avg_l"]
                    ),
                    "demand_30day_avg_l": float(
                        row["demand_30day_avg_l"]
                    ),
                    "actual_demand_l": float(
                        row["actual_demand_l"]
                    )
                }
            )

    print("Water demand data loaded successfully!")


if __name__ == "__main__":
    load_water_demand()