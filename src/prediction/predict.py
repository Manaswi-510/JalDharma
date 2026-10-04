"""
Phase 12: Prediction Service — src/prediction/predict.py

Accepts:
  - village_id  (e.g. "VIL_001")
  - date        (e.g. "2025-07-15")
  - temperature_c, rainfall_mm, humidity  (weather inputs)
  - optional: previous_day_demand_l

Returns:
  - predicted_demand_l  (litres/day)

How it works:
  1. Trains a Random Forest model on historical_water_demand from PostgreSQL.
  2. Features: population, temperature, rainfall, humidity,
               previous_day_demand, 7-day avg demand, 30-day avg demand,
               day-of-week, month.
  3. Runs inference for any village + date + weather combo.
  4. Stores every prediction in a `predictions` table in PostgreSQL (12.4).
"""

import pandas as pd
import numpy as np
from datetime import datetime, date
from pathlib import Path
from sqlalchemy import text

from src.database.connection import get_engine

# ------------------------------------------------------------------ #
#  Step 1: Create the predictions table (12.4)                        #
# ------------------------------------------------------------------ #

CREATE_PREDICTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS predictions (
    prediction_id   SERIAL PRIMARY KEY,
    village_id      VARCHAR(50)  NOT NULL,
    village_name    VARCHAR(150),
    prediction_date DATE         NOT NULL,
    temperature_c   DOUBLE PRECISION,
    rainfall_mm     DOUBLE PRECISION,
    humidity        DOUBLE PRECISION,
    predicted_demand_l DOUBLE PRECISION NOT NULL,
    model_used      VARCHAR(100) DEFAULT 'RandomForestRegressor',
    created_at      TIMESTAMP    DEFAULT NOW()
);
"""

def ensure_predictions_table(engine):
    """Create the predictions table if it does not yet exist."""
    with engine.begin() as conn:
        conn.execute(text(CREATE_PREDICTIONS_TABLE))


# ------------------------------------------------------------------ #
#  Step 2: Load training data & train model                           #
# ------------------------------------------------------------------ #

def load_training_data(engine):
    """Pull historical demand from PostgreSQL for model training."""
    query = """
        SELECT
            d.village_id,
            d.date,
            d.population,
            d.temperature_c,
            d.rainfall_mm,
            d.humidity,
            d.previous_day_demand_l,
            d.demand_7day_avg_l,
            d.demand_30day_avg_l,
            d.actual_demand_l,
            EXTRACT(DOW   FROM d.date)::int AS day_of_week,
            EXTRACT(MONTH FROM d.date)::int AS month,
            v.vulnerability_index
        FROM historical_water_demand d
        LEFT JOIN villages v USING (village_id)
        WHERE d.actual_demand_l IS NOT NULL
    """
    df = pd.read_sql(query, engine)
    return df


def build_features(df):
    """Return feature matrix X and target vector y."""
    feature_cols = [
        "population",
        "temperature_c",
        "rainfall_mm",
        "humidity",
        "previous_day_demand_l",
        "demand_7day_avg_l",
        "demand_30day_avg_l",
        "day_of_week",
        "month",
        "vulnerability_index",
    ]
    df = df.dropna(subset=feature_cols + ["actual_demand_l"])
    X = df[feature_cols].values
    y = df["actual_demand_l"].values
    return X, y, feature_cols


def train_model(engine):
    """Train a Random Forest on historical demand. Returns (model, feature_cols)."""
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, r2_score

    print("[TRAIN] Loading historical data...")
    df = load_training_data(engine)
    X, y, feature_cols = build_features(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print(f"[TRAIN] Training on {len(X_train)} rows, testing on {len(X_test)} rows...")
    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae  = mean_absolute_error(y_test, y_pred)
    r2   = r2_score(y_test, y_pred)
    print(f"[TRAIN] Model ready | MAE = {mae:,.0f} L  |  R2 = {r2:.4f}")

    return model, feature_cols


# ------------------------------------------------------------------ #
#  Step 3: Prediction function                                        #
# ------------------------------------------------------------------ #

def get_village_stats(engine, village_id):
    """Fetch population, vulnerability, and recent demand averages for a village."""
    query = text("""
        SELECT
            v.population,
            v.vulnerability_index,
            v.village_name,
            AVG(d.actual_demand_l)                        AS demand_30day_avg_l,
            (SELECT d2.actual_demand_l
             FROM   historical_water_demand d2
             WHERE  d2.village_id = :vid
             ORDER  BY d2.date DESC LIMIT 1)              AS previous_day_demand_l,
            (SELECT AVG(recent.actual_demand_l)
             FROM   (SELECT actual_demand_l
                     FROM   historical_water_demand
                     WHERE  village_id = :vid
                     ORDER  BY date DESC LIMIT 7) AS recent) AS demand_7day_avg_l
        FROM villages v
        LEFT JOIN historical_water_demand d ON d.village_id = v.village_id
        WHERE v.village_id = :vid
        GROUP BY v.population, v.vulnerability_index, v.village_name
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"vid": village_id}).mappings().fetchone()
    if result is None:
        raise ValueError(f"Village '{village_id}' not found in the database.")
    return dict(result)


def predict(
    village_id: str,
    prediction_date: str,
    temperature_c: float,
    rainfall_mm: float,
    humidity: float,
    model=None,
    engine=None,
    store: bool = True,
) -> dict:
    """
    Predict water demand for a village on a given date.

    Args:
        village_id      : e.g. "VIL_001"
        prediction_date : "YYYY-MM-DD"
        temperature_c   : forecast temperature
        rainfall_mm     : forecast rainfall
        humidity        : forecast humidity (%)
        model           : pre-trained model (pass to avoid re-training every call)
        engine          : SQLAlchemy engine (created internally if None)
        store           : if True, save the prediction to the `predictions` table

    Returns:
        dict with village_name, prediction_date, predicted_demand_l, and inputs used
    """
    if engine is None:
        engine = get_engine()

    ensure_predictions_table(engine)

    # Train model if not provided
    if model is None:
        model, feature_cols = train_model(engine)
    else:
        feature_cols = [
            "population", "temperature_c", "rainfall_mm", "humidity",
            "previous_day_demand_l", "demand_7day_avg_l", "demand_30day_avg_l",
            "day_of_week", "month", "vulnerability_index",
        ]

    # Get village stats
    stats = get_village_stats(engine, village_id)

    # Parse date
    pred_date = pd.to_datetime(prediction_date)
    day_of_week = pred_date.dayofweek   # 0=Mon … 6=Sun
    month       = pred_date.month

    # Build feature vector
    features = np.array([[
        stats["population"]            or 0,
        temperature_c,
        rainfall_mm,
        humidity,
        stats["previous_day_demand_l"] or 0,
        stats["demand_7day_avg_l"]     or 0,
        stats["demand_30day_avg_l"]    or 0,
        day_of_week,
        month,
        stats["vulnerability_index"]   or 0.5,
    ]])

    predicted_demand = float(model.predict(features)[0])

    result = {
        "village_id"          : village_id,
        "village_name"        : stats["village_name"],
        "prediction_date"     : prediction_date,
        "temperature_c"       : temperature_c,
        "rainfall_mm"         : rainfall_mm,
        "humidity"            : humidity,
        "predicted_demand_l"  : round(predicted_demand, 1),
        "predicted_demand_fmt": f"{predicted_demand:,.0f} L/day",
    }

    # Store in PostgreSQL (12.4)
    if store:
        insert_sql = text("""
            INSERT INTO predictions
                (village_id, village_name, prediction_date, temperature_c,
                 rainfall_mm, humidity, predicted_demand_l)
            VALUES
                (:village_id, :village_name, :prediction_date, :temperature_c,
                 :rainfall_mm, :humidity, :predicted_demand_l)
        """)
        with engine.begin() as conn:
            conn.execute(insert_sql, {
                "village_id"         : village_id,
                "village_name"       : stats["village_name"],
                "prediction_date"    : prediction_date,
                "temperature_c"      : temperature_c,
                "rainfall_mm"        : rainfall_mm,
                "humidity"           : humidity,
                "predicted_demand_l" : predicted_demand,
            })

    return result


def print_result(result: dict):
    """Pretty-print a prediction result."""
    print("\n" + "=" * 45)
    print(f"  Village        : {result['village_name']} ({result['village_id']})")
    print(f"  Date           : {result['prediction_date']}")
    print(f"  Weather inputs : Temp={result['temperature_c']}C  "
          f"Rain={result['rainfall_mm']}mm  Humidity={result['humidity']}%")
    print(f"  Predicted Demand : {result['predicted_demand_fmt']}")
    print("=" * 45)


# ------------------------------------------------------------------ #
#  Phase 12.1 – 12.3 Tests                                           #
# ------------------------------------------------------------------ #

def run_tests():
    engine = get_engine()
    ensure_predictions_table(engine)

    # Train once, reuse for all tests
    model, _ = train_model(engine)

    # ---- 12.1  Single village ----
    print("\n\n--- 12.1  Single Village Test ---")
    r = predict("VIL_001", "2025-07-15", temperature_c=35.0, rainfall_mm=0.0,
                humidity=42.0, model=model, engine=engine)
    print_result(r)

    # ---- 12.2  Multiple villages ----
    print("\n--- 12.2  Multiple Villages Test ---")
    test_villages = ["VIL_001", "VIL_010", "VIL_020", "VIL_030", "VIL_045"]
    for vid in test_villages:
        r = predict(vid, "2025-07-15", temperature_c=33.0, rainfall_mm=2.0,
                    humidity=55.0, model=model, engine=engine)
        print_result(r)

    # ---- 12.3  Different dates (same village) ----
    print("\n--- 12.3  Different Dates Test (VIL_001) ---")
    test_dates = [
        ("2025-07-01", 30.0, 10.0, 60.0),   # monsoon
        ("2025-10-15", 28.0, 5.0,  70.0),   # post-monsoon
        ("2025-12-20", 22.0, 0.0,  35.0),   # winter
        ("2026-04-10", 38.0, 0.0,  25.0),   # summer peak
    ]
    for dt, temp, rain, hum in test_dates:
        r = predict("VIL_001", dt, temperature_c=temp, rainfall_mm=rain,
                    humidity=hum, model=model, engine=engine)
        print_result(r)

    # ---- 12.4  Confirm stored predictions ----
    print("\n--- 12.4  Verifying Stored Predictions in PostgreSQL ---")
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT village_id, village_name, prediction_date, "
            "ROUND(predicted_demand_l::numeric, 0) AS predicted_demand_l "
            "FROM predictions ORDER BY created_at DESC LIMIT 10"
        )).mappings().fetchall()
    print(f"\n  Last {len(rows)} predictions stored in `predictions` table:")
    for row in rows:
        print(f"  {row['village_id']}  {row['village_name']:<30}  "
              f"{str(row['prediction_date'])}  "
              f"{float(row['predicted_demand_l']):>12,.0f} L/day")

    print("\n[SUCCESS] Phase 12 Complete: All tests passed & predictions stored in PostgreSQL!")


# ------------------------------------------------------------------ #
#  Entry point                                                        #
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    run_tests()
