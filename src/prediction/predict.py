"""
Jal Dharma AI
Prediction Service

This module connects the final Phase 11 prediction model
with the PostgreSQL database.

Final model:
    Linear Regression

Features:
    1. population
    2. temperature_c
    3. rainfall_mm
    4. humidity
    5. previous_day_demand_l
    6. demand_7day_avg_l
    7. demand_30day_avg_l

The model is trained only on the chronological training period:
    2025-04-01 to 2025-05-15

For prediction:
    - village information is obtained from PostgreSQL
    - recent historical demand is obtained from PostgreSQL
    - weather values are supplied to the prediction service
    - the trained Linear Regression model predicts demand
    - the prediction is stored in PostgreSQL
"""

import sys
from pathlib import Path

# Add project root to sys.path so the file can be run directly or as a module
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from sqlalchemy import text

from src.database.connection import get_engine
from src.prediction.models import (
    FEATURES,
    load_dataset,
    train_final_model,
    predict_demand,
)


# ---------------------------------------------------------
# DATABASE FUNCTIONS
# ---------------------------------------------------------

def load_historical_data_from_database(engine):
    """
    Load historical water-demand data from PostgreSQL.

    The returned DataFrame has the same structure expected
    by models.py.
    """

    query = text("""
        SELECT
            record_id,
            village_id,
            date,
            population,
            temperature_c,
            rainfall_mm,
            humidity,
            previous_day_demand_l,
            demand_7day_avg_l,
            demand_30day_avg_l,
            actual_demand_l
        FROM historical_water_demand
        ORDER BY village_id, date
    """)

    with engine.connect() as conn:
        df = pd.read_sql(query, conn)

    if df.empty:
        raise ValueError(
            "No historical water-demand data found "
            "in the PostgreSQL database."
        )

    df["date"] = pd.to_datetime(df["date"])

    df = df.sort_values(
        ["village_id", "date"]
    ).reset_index(drop=True)

    return df


def get_village_information(engine, village_id):
    """
    Retrieve basic information about a village.

    Population is taken from the most recent historical
    demand record instead of depending on an additional
    column in the villages table.
    """

    query = text("""
        SELECT
            village_id,
            population
        FROM historical_water_demand
        WHERE village_id = :village_id
        ORDER BY date DESC
        LIMIT 1
    """)

    with engine.connect() as conn:
        result = conn.execute(
            query,
            {"village_id": village_id}
        ).mappings().first()

    if result is None:
        raise ValueError(
            f"Village '{village_id}' was not found "
            "in historical_water_demand."
        )

    return dict(result)


def get_recent_demand_features(engine, village_id):
    """
    Calculate the historical demand features required
    by the final prediction model.

    previous_day_demand_l:
        Most recent historical demand.

    demand_7day_avg_l:
        Average demand over the latest 7 available records.

    demand_30day_avg_l:
        Average demand over the latest 30 available records.
    """

    query = text("""
        SELECT
            date,
            actual_demand_l
        FROM historical_water_demand
        WHERE village_id = :village_id
        ORDER BY date DESC
        LIMIT 30
    """)

    with engine.connect() as conn:
        rows = conn.execute(
            query,
            {"village_id": village_id}
        ).mappings().all()

    if not rows:
        raise ValueError(
            f"No historical demand found for village "
            f"'{village_id}'."
        )

    recent_df = pd.DataFrame(rows)

    recent_df["date"] = pd.to_datetime(recent_df["date"])

    recent_df = recent_df.sort_values("date")

    previous_day_demand = (
        recent_df["actual_demand_l"].iloc[-1]
    )

    demand_7day_avg = (
        recent_df["actual_demand_l"]
        .tail(7)
        .mean()
    )

    demand_30day_avg = (
        recent_df["actual_demand_l"]
        .tail(30)
        .mean()
    )

    return {
        "previous_day_demand_l": previous_day_demand,
        "demand_7day_avg_l": demand_7day_avg,
        "demand_30day_avg_l": demand_30day_avg,
    }


# ---------------------------------------------------------
# PREDICTION TABLE
# ---------------------------------------------------------

def create_predictions_table(engine):
    """
    Create the predictions table if it does not already exist.
    """

    query = text("""
        CREATE TABLE IF NOT EXISTS predictions (
            prediction_id SERIAL PRIMARY KEY,
            village_id VARCHAR(50) NOT NULL,
            prediction_date DATE NOT NULL,
            predicted_demand_l DOUBLE PRECISION NOT NULL,
            model_used VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    with engine.begin() as conn:
        conn.execute(query)


# ---------------------------------------------------------
# STORE PREDICTION
# ---------------------------------------------------------

def store_prediction(
    engine,
    village_id,
    prediction_date,
    predicted_demand,
):
    """
    Store a prediction in PostgreSQL.
    """

    query = text("""
        INSERT INTO predictions (
            village_id,
            prediction_date,
            predicted_demand_l,
            model_used
        )
        VALUES (
            :village_id,
            :prediction_date,
            :predicted_demand_l,
            :model_used
        )
    """)

    with engine.begin() as conn:
        conn.execute(
            query,
            {
                "village_id": village_id,
                "prediction_date": prediction_date,
                "predicted_demand_l": float(predicted_demand),
                "model_used": "LinearRegression",
            }
        )


# ---------------------------------------------------------
# TRAIN MODEL
# ---------------------------------------------------------

def train_prediction_model(engine):
    """
    Load historical data from PostgreSQL and train the
    final Phase 11 Linear Regression model.

    models.py handles:

        - chronological training period
        - feature selection
        - scaling
        - Linear Regression training
    """

    print("\n==========================================")
    print("TRAINING PREDICTION MODEL")
    print("==========================================")

    print("Loading historical data from PostgreSQL...")

    df = load_historical_data_from_database(engine)

    print("Historical records:", len(df))
    print("Villages:", df["village_id"].nunique())

    model, train_mean, train_std = train_final_model(df)

    return model, train_mean, train_std


# ---------------------------------------------------------
# MAIN PREDICTION FUNCTION
# ---------------------------------------------------------

def predict(
    village_id,
    prediction_date,
    temperature_c,
    rainfall_mm,
    humidity,
    model,
    train_mean,
    train_std,
    engine,
):
    """
    Predict water demand for a village.

    Parameters
    ----------
    village_id : str
        Village identifier, e.g. VIL_001

    prediction_date : str
        Date of prediction, e.g. 2025-06-30

    temperature_c : float
        Temperature in Celsius.

    rainfall_mm : float
        Rainfall in millimetres.

    humidity : float
        Relative humidity percentage.

    model :
        Trained Linear Regression model.

    train_mean :
        Training feature means from Phase 11.

    train_std :
        Training feature standard deviations from Phase 11.

    engine :
        PostgreSQL SQLAlchemy engine.
    """

    prediction_date = pd.to_datetime(
        prediction_date
    )

    # -----------------------------------------------------
    # 1. Get village information
    # -----------------------------------------------------

    village = get_village_information(
        engine,
        village_id
    )

    population = village["population"]

    # -----------------------------------------------------
    # 2. Get recent historical demand features
    # -----------------------------------------------------

    demand_features = get_recent_demand_features(
        engine,
        village_id
    )

    # -----------------------------------------------------
    # 3. Construct model input
    # -----------------------------------------------------

    input_data = {
        "population": population,
        "temperature_c": temperature_c,
        "rainfall_mm": rainfall_mm,
        "humidity": humidity,
        "previous_day_demand_l":
            demand_features["previous_day_demand_l"],
        "demand_7day_avg_l":
            demand_features["demand_7day_avg_l"],
        "demand_30day_avg_l":
            demand_features["demand_30day_avg_l"],
    }

    input_df = pd.DataFrame([input_data])

    # Ensure the feature order is exactly the same
    # as the Phase 11 model.
    input_df = input_df[FEATURES]

    # -----------------------------------------------------
    # 4. Generate prediction
    # -----------------------------------------------------

    prediction = predict_demand(
        model,
        input_df,
        train_mean,
        train_std,
    )

    predicted_demand = float(prediction[0])

    # Water demand cannot be negative.
    predicted_demand = max(
        0.0,
        predicted_demand
    )

    # -----------------------------------------------------
    # 5. Store prediction
    # -----------------------------------------------------

    store_prediction(
        engine,
        village_id,
        prediction_date.date(),
        predicted_demand,
    )

    # -----------------------------------------------------
    # 6. Display result
    # -----------------------------------------------------

    print("\n==========================================")
    print("WATER DEMAND PREDICTION")
    print("==========================================")

    print("Village:", village_id)
    print("Prediction date:", prediction_date.date())

    print("\nInput features:")
    for feature in FEATURES:
        print(
            f"{feature}: "
            f"{input_df[feature].iloc[0]:.2f}"
        )

    print(
        "\nPredicted water demand:",
        f"{predicted_demand:,.2f}",
        "L/day"
    )

    print("Model: Linear Regression")
    print("Prediction stored in PostgreSQL.")

    return predicted_demand


# ---------------------------------------------------------
# TEST THE SERVICE
# ---------------------------------------------------------

def main():

    print("\n==========================================")
    print("JAL DHARMA AI")
    print("PHASE 12: PREDICTION SERVICE")
    print("==========================================")

    # -----------------------------------------------------
    # 1. Connect to PostgreSQL
    # -----------------------------------------------------

    print("\n[1] Connecting to PostgreSQL...")

    engine = get_engine()

    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    print("Database connection successful.")

    # -----------------------------------------------------
    # 2. Create prediction table
    # -----------------------------------------------------

    print("\n[2] Checking predictions table...")

    create_predictions_table(engine)

    print("Predictions table ready.")

    # -----------------------------------------------------
    # 3. Train final model
    # -----------------------------------------------------

    print("\n[3] Training final prediction model...")

    model, train_mean, train_std = (
        train_prediction_model(engine)
    )

    # -----------------------------------------------------
    # 4. Test prediction
    # -----------------------------------------------------

    print("\n[4] Running test prediction...")

    predicted_demand = predict(
        village_id="VIL_001",
        prediction_date="2025-06-30",

        # Example weather inputs.
        # Replace these with actual forecast/weather values
        # when using the service in the final system.
        temperature_c=32.0,
        rainfall_mm=2.0,
        humidity=55.0,

        model=model,
        train_mean=train_mean,
        train_std=train_std,

        engine=engine,
    )

    print("\n==========================================")
    print("TEST COMPLETE")
    print("==========================================")
    print(
        f"Predicted demand: "
        f"{predicted_demand:,.2f} L/day"
    )


if __name__ == "__main__":
    main()