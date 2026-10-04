"""
Jal Dharma AI
Final Demand Prediction Model

Phase 11 selected Linear Regression as the final model.

Features used:
1. population
2. temperature_c
3. rainfall_mm
4. humidity
5. previous_day_demand_l
6. demand_7day_avg_l
7. demand_30day_avg_l

The model is trained using chronological training data
and the feature scaling statistics are calculated only
from the training data.
"""

import pandas as pd
import numpy as np

from sklearn.linear_model import LinearRegression


# ============================================================
# FEATURE CONFIGURATION
# ============================================================

FEATURES = [
    "population",
    "temperature_c",
    "rainfall_mm",
    "humidity",
    "previous_day_demand_l",
    "demand_7day_avg_l",
    "demand_30day_avg_l",
]

TARGET = "actual_demand_l"


# ============================================================
# LOAD DATASET
# ============================================================

def load_dataset(file_path):
    """
    Load the historical water demand dataset.

    Parameters
    ----------
    file_path : str
        Path to the historical demand CSV file.

    Returns
    -------
    pandas.DataFrame
        Cleaned and sorted dataset.
    """

    df = pd.read_csv(file_path)

    # Convert date column
    df["date"] = pd.to_datetime(
        df["date"],
        dayfirst=True
    )

    # Sort chronologically for every village
    df = df.sort_values(
        ["village_id", "date"]
    ).reset_index(drop=True)

    return df


# ============================================================
# CHRONOLOGICAL TRAINING DATA
# ============================================================

def prepare_training_data(df):
    """
    Prepare the Phase 11 training dataset.

    Training period:
        2025-04-01 to 2025-05-15

    This follows the chronological time-series split
    used during Phase 11.
    """

    train_df = df[
        (df["date"] >= "2025-04-01") &
        (df["date"] <= "2025-05-15")
    ].copy()

    X_train = train_df[FEATURES]
    y_train = train_df[TARGET]

    return train_df, X_train, y_train


# ============================================================
# FEATURE SCALING
# ============================================================

def calculate_scaling_parameters(X_train):
    """
    Calculate mean and standard deviation using
    ONLY the training data.

    These values must not be calculated using
    validation or test data.
    """

    train_mean = X_train.mean()

    train_std = X_train.std()

    # Prevent division by zero
    train_std[train_std == 0] = 1

    return train_mean, train_std


def scale_features(X, train_mean, train_std):
    """
    Scale features using training-data statistics.
    """

    return (
        X - train_mean
    ) / train_std


# ============================================================
# TRAIN FINAL MODEL
# ============================================================

def train_final_model(df):
    """
    Train the final Linear Regression model.

    Returns
    -------
    model
        Trained Linear Regression model.

    train_mean
        Mean of training features.

    train_std
        Standard deviation of training features.
    """

    # Prepare training data
    train_df, X_train, y_train = prepare_training_data(df)

    # Calculate scaling parameters
    train_mean, train_std = calculate_scaling_parameters(
        X_train
    )

    # Scale training features
    X_train_scaled = scale_features(
        X_train,
        train_mean,
        train_std
    )

    # Create Linear Regression model
    model = LinearRegression()

    # Train model
    model.fit(
        X_train_scaled,
        y_train
    )

    print("\n===================================")
    print("FINAL DEMAND MODEL")
    print("===================================")

    print("Model: Linear Regression")

    print(
        "Training period:",
        train_df["date"].min().date(),
        "to",
        train_df["date"].max().date()
    )

    print(
        "Training records:",
        len(train_df)
    )

    print(
        "Number of features:",
        len(FEATURES)
    )

    print("\nFeatures:")

    for feature in FEATURES:
        print(" -", feature)

    return model, train_mean, train_std


# ============================================================
# PREDICT DEMAND
# ============================================================

def predict_demand(
    model,
    input_data,
    train_mean,
    train_std
):
    """
    Predict water demand using the trained model.

    input_data must contain the seven required features.
    """

    # Make sure input is a DataFrame
    if isinstance(input_data, dict):
        input_data = pd.DataFrame([input_data])

    # Select features in the correct order
    X = input_data[FEATURES]

    # Apply training-data scaling
    X_scaled = scale_features(
        X,
        train_mean,
        train_std
    )

    # Generate prediction
    predictions = model.predict(
        X_scaled
    )

    return predictions


# ============================================================
# TEST MODEL
# ============================================================

if __name__ == "__main__":

    DATASET_PATH = (
        "data/synthetic/"
        "2_historical_water_demand_dataset.csv"
    )

    print("Loading dataset...")

    df = load_dataset(
        DATASET_PATH
    )

    print(
        "Dataset records:",
        len(df)
    )

    print(
        "Number of villages:",
        df["village_id"].nunique()
    )

    # Train final model
    model, train_mean, train_std = train_final_model(
        df
    )

    # Take one record as a test example
    sample = df.iloc[[0]].copy()

    # Remove target because it is not required
    sample_input = sample[FEATURES]

    # Predict
    prediction = predict_demand(
        model,
        sample_input,
        train_mean,
        train_std
    )

    print("\n===================================")
    print("TEST PREDICTION")
    print("===================================")

    print(
        "Village:",
        sample["village_id"].iloc[0]
    )

    print(
        "Date:",
        sample["date"].iloc[0].date()
    )

    print(
        "Actual demand:",
        round(
            sample[TARGET].iloc[0],
            2
        ),
        "L/day"
    )

    print(
        "Predicted demand:",
        round(
            prediction[0],
            2
        ),
        "L/day"
    )