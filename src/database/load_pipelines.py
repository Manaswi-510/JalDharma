import pandas as pd
from sqlalchemy import text

from src.database.connection import engine


CSV_PATH = "data/synthetic/5_pipeline_water_network_dataset.csv"

def load_pipelines():
    df = pd.read_csv(CSV_PATH)

    print(f"Pipeline records found in CSV: {len(df)}")

    pipeline_data = df[
        [
            "pipeline_id",
            "source_node",
            "destination_node",
            "capacity_l_per_day",
            "length_km",
            "status"
        ]
    ].copy()

    pipeline_data["status"] = pipeline_data["status"].apply(
        lambda x: 1 if str(x).strip().lower() == "working" else 0
    )

    insert_query = text("""
        INSERT INTO public.pipelines
        (
            pipeline_id,
            from_node,
            to_node,
            capacity_liters,
            length_km,
            status
        )
        VALUES
        (
            :pipeline_id,
            :from_node,
            :to_node,
            :capacity_liters,
            :length_km,
            :status
        )
        ON CONFLICT (pipeline_id)
        DO UPDATE SET
            from_node = EXCLUDED.from_node,
            to_node = EXCLUDED.to_node,
            capacity_liters = EXCLUDED.capacity_liters,
            length_km = EXCLUDED.length_km,
            status = EXCLUDED.status;
    """)

    with engine.begin() as connection:
        for _, row in pipeline_data.iterrows():
            connection.execute(
                insert_query,
                {
                    "pipeline_id": row["pipeline_id"],
                    "from_node": row["source_node"],
                    "to_node": row["destination_node"],
                    "capacity_liters": int(row["capacity_l_per_day"]),
                    "length_km": float(row["length_km"]),
                    "status": int(row["status"])
                }
            )

    print("Pipeline data loaded successfully!")


if __name__ == "__main__":
    load_pipelines()