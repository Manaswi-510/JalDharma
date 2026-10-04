"""
Jal Dharma AI
Prediction Service (ratio model, rolling refit, prediction intervals)

Flow
    1. Load ALL historical demand from PostgreSQL.
    2. Refit the ratio model on all of it (rolling refit).
    3. For each village take the latest 7 days from the DB:
         base       = mean of the last 7 actual demands
         rain_yday  = rainfall recorded on the latest day in the DB
    4. Apply the supplied weather for the prediction date.
    5. Store point + lower/upper in the `predictions` table.

The model is a 1-day-ahead model: the latest DB record should be the day
before prediction_date. A warning is printed otherwise.
"""

import pandas as pd
from sqlalchemy import text

from src.database.connection import get_engine
from src.prediction.models import train_final_model, predict_demand

MODEL_NAME = "RatioRidge"


# ---------------------------------------------------------
# DATABASE
# ---------------------------------------------------------

def load_historical_data_from_database(engine):
    query = text("""
        SELECT village_id, date, population, temperature_c, rainfall_mm,
               humidity, previous_day_demand_l, demand_7day_avg_l,
               demand_30day_avg_l, actual_demand_l
        FROM historical_water_demand
        ORDER BY village_id, date
    """)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)

    if df.empty:
        raise ValueError("No historical water-demand data in PostgreSQL.")

    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values(["village_id", "date"]).reset_index(drop=True)


def get_latest_state(engine, window=7):
    """Per village: 7-day base demand, last record date, last-day rainfall."""
    query = text("""
        SELECT village_id, date, actual_demand_l, rainfall_mm, population
        FROM (
            SELECT village_id, date, actual_demand_l, rainfall_mm, population,
                   ROW_NUMBER() OVER (PARTITION BY village_id
                                      ORDER BY date DESC) AS rn
            FROM historical_water_demand
        ) t
        WHERE rn <= :window
    """)
    with engine.connect() as conn:
        rows = pd.read_sql(query, conn, params={"window": window})
    rows["date"] = pd.to_datetime(rows["date"])

    def summarise(g):
        g = g.sort_values("date")
        return pd.Series({
            "base_demand": g["actual_demand_l"].mean(),
            "last_date": g["date"].iloc[-1],
            "rain_yesterday": g["rainfall_mm"].iloc[-1],
            "population": g["population"].iloc[-1],
            "n_days": len(g),
        })

    return rows.groupby("village_id").apply(summarise).reset_index()


def create_predictions_table(engine):
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS predictions (
                prediction_id SERIAL PRIMARY KEY,
                village_id VARCHAR(50) NOT NULL,
                prediction_date DATE NOT NULL,
                predicted_demand_l DOUBLE PRECISION NOT NULL,
                model_used VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        # Upgrade an existing table from the old version
        conn.execute(text(
            "ALTER TABLE predictions ADD COLUMN IF NOT EXISTS "
            "lower_demand_l DOUBLE PRECISION"))
        conn.execute(text(
            "ALTER TABLE predictions ADD COLUMN IF NOT EXISTS "
            "upper_demand_l DOUBLE PRECISION"))


def store_predictions(engine, results):
    rows = [
        {
            "village_id": r.village_id,
            "prediction_date": r.prediction_date,
            "point": float(r.point),
            "lower": float(r.lower),
            "upper": float(r.upper),
            "model": MODEL_NAME,
        }
        for r in results.itertuples()
    ]
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO predictions
                (village_id, prediction_date, predicted_demand_l,
                 lower_demand_l, upper_demand_l, model_used)
            VALUES (:village_id, :prediction_date, :point,
                    :lower, :upper, :model)
        """), rows)


# ---------------------------------------------------------
# PREDICTION
# ---------------------------------------------------------

def predict(engine, bundle, prediction_date, temperature_c, humidity,
            rainfall_mm, village_ids=None, store=True):
    """
    Predict demand for one, several, or all villages.

    Returns a DataFrame: village_id, prediction_date, point, lower, upper.
    `upper` is the conservative figure to plan allocations against.
    """
    prediction_date = pd.to_datetime(prediction_date)
    state = get_latest_state(engine)

    if village_ids is not None:
        if isinstance(village_ids, str):
            village_ids = [village_ids]
        state = state[state["village_id"].isin(village_ids)]
    if state.empty:
        raise ValueError("No matching villages found in historical_water_demand.")

    gap = (prediction_date - state["last_date"].max()).days
    if gap != 1:
        print(f"[WARN] Latest record is {gap} day(s) before the prediction "
              f"date. This is a 1-day-ahead model; lag inputs are stale.")

    p = predict_demand(
        bundle,
        base_demand=state["base_demand"].values,
        temperature_c=temperature_c,
        humidity=humidity,
        rainfall_mm=rainfall_mm,
        rainfall_yesterday_mm=state["rain_yesterday"].values,
    )

    results = pd.concat(
        [state[["village_id"]].reset_index(drop=True), p], axis=1
    )
    results["prediction_date"] = prediction_date.date()

    if store:
        store_predictions(engine, results)
    return results


# ---------------------------------------------------------
# DEMO
# ---------------------------------------------------------

def main():
    print("\n==========================================")
    print("JAL DHARMA AI - PREDICTION SERVICE")
    print("==========================================")

    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("Database connection successful.")

    create_predictions_table(engine)

    df = load_historical_data_from_database(engine)
    print("Historical records:", len(df), "| villages:", df["village_id"].nunique())
    bundle = train_final_model(df)

    next_day = df["date"].max() + pd.Timedelta(days=1)

    # Replace with real forecast values. Defaults are typical monsoon weather;
    # do NOT use summer values for a June date.
    results = predict(
        engine, bundle,
        prediction_date=next_day,
        temperature_c=26.0, humidity=80.0, rainfall_mm=5.0,
    )

    print(f"\nPredictions for {next_day.date()} (first 10 villages):")
    print(results.head(10).round(0).to_string(index=False))
    print(f"\nTotal point demand : {results['point'].sum():,.0f} L/day")
    print(f"Total upper bound  : {results['upper'].sum():,.0f} L/day")


if __name__ == "__main__":
    main()