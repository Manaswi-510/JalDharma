"""
Jal Dharma AI
Time-Series Validation

Purpose:
    Validate baseline models using a chronological
    train / validation / test split.

Models compared:
    1. Linear Regression
    2. Random Forest
    3. Gradient Boosting

Important:
    The dataset is NOT randomly shuffled.
    Future data must not be used to train the model.
"""

import numpy as np
import pandas as pd

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import (
    RandomForestRegressor,
    GradientBoostingRegressor
)
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error
)

from src.prediction.models import (
    FEATURES,
    TARGET,
    load_dataset,
    scale_features,
    calculate_scaling_parameters
)


# ============================================================
# CONFIGURATION
# ============================================================

DATASET_PATH = (
    "data/synthetic/"
    "2_historical_water_demand_dataset.csv"
)


# ============================================================
# CHRONOLOGICAL DATA SPLIT
# ============================================================

def create_time_series_split(df):
    """
    Create the chronological Phase 11 split.

    Training:
        2025-04-01 to 2025-05-15

    Validation:
        2025-05-16 to 2025-05-31

    Testing:
        2025-06-01 to 2025-06-29
    """

    train_df = df[
        (df["date"] >= "2025-04-01") &
        (df["date"] <= "2025-05-15")
    ].copy()

    validation_df = df[
        (df["date"] >= "2025-05-16") &
        (df["date"] <= "2025-05-31")
    ].copy()

    test_df = df[
        (df["date"] >= "2025-06-01") &
        (df["date"] <= "2025-06-29")
    ].copy()

    return train_df, validation_df, test_df


# ============================================================
# EVALUATION FUNCTION
# ============================================================

def calculate_metrics(actual, predicted):
    """
    Calculate MAE, RMSE and MAPE.
    """

    mae = mean_absolute_error(
        actual,
        predicted
    )

    rmse = np.sqrt(
        mean_squared_error(
            actual,
            predicted
        )
    )

    # Avoid division by zero
    actual = np.asarray(actual)

    non_zero = actual != 0

    mape = np.mean(
        np.abs(
            (actual[non_zero] - predicted[non_zero])
            / actual[non_zero]
        )
    ) * 100

    return mae, rmse, mape


# ============================================================
# VALIDATE MODELS
# ============================================================

def validate_models(
    X_train_scaled,
    y_train,
    X_val_scaled,
    y_val
):
    """
    Train and validate the three baseline models.

    Returns the validation results and the selected model.
    """

    # --------------------------------------------------------
    # LINEAR REGRESSION
    # --------------------------------------------------------

    linear_model = LinearRegression()

    linear_model.fit(
        X_train_scaled,
        y_train
    )

    linear_predictions = linear_model.predict(
        X_val_scaled
    )

    linear_mae, linear_rmse, linear_mape = calculate_metrics(
        y_val,
        linear_predictions
    )

    # --------------------------------------------------------
    # RANDOM FOREST
    # --------------------------------------------------------

    rf_model = RandomForestRegressor(
        n_estimators=100,
        random_state=42,
        n_jobs=-1
    )

    rf_model.fit(
        X_train_scaled,
        y_train
    )

    rf_predictions = rf_model.predict(
        X_val_scaled
    )

    rf_mae, rf_rmse, rf_mape = calculate_metrics(
        y_val,
        rf_predictions
    )

    # --------------------------------------------------------
    # GRADIENT BOOSTING
    # --------------------------------------------------------

    gb_model = GradientBoostingRegressor(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=3,
        random_state=42
    )

    gb_model.fit(
        X_train_scaled,
        y_train
    )

    gb_predictions = gb_model.predict(
        X_val_scaled
    )

    gb_mae, gb_rmse, gb_mape = calculate_metrics(
        y_val,
        gb_predictions
    )

    # --------------------------------------------------------
    # RESULTS
    # --------------------------------------------------------

    results = pd.DataFrame({
        "Model": [
            "Linear Regression",
            "Random Forest",
            "Gradient Boosting"
        ],

        "MAE": [
            linear_mae,
            rf_mae,
            gb_mae
        ],

        "RMSE": [
            linear_rmse,
            rf_rmse,
            gb_rmse
        ],

        "MAPE": [
            linear_mape,
            rf_mape,
            gb_mape
        ]
    })

    # Select model with lowest MAE
    best_index = results["MAE"].idxmin()

    selected_model_name = results.loc[
        best_index,
        "Model"
    ]

    selected_model = {
        "Linear Regression": linear_model,
        "Random Forest": rf_model,
        "Gradient Boosting": gb_model
    }[selected_model_name]

    return (
        results,
        selected_model_name,
        selected_model
    )


# ============================================================
# FINAL TEST
# ============================================================

def evaluate_final_model(
    model,
    X_test_scaled,
    y_test
):
    """
    Evaluate the selected model on the completely
    unseen June test dataset.
    """

    predictions = model.predict(
        X_test_scaled
    )

    mae, rmse, mape = calculate_metrics(
        y_test,
        predictions
    )

    return predictions, mae, rmse, mape


# ============================================================
# MAIN VALIDATION WORKFLOW
# ============================================================

def run_validation():

    print("\n==========================================")
    print("JAL DHARMA AI")
    print("TIME-SERIES VALIDATION")
    print("==========================================")

    # --------------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------------

    print("\n[1] Loading dataset...")

    df = load_dataset(
        DATASET_PATH
    )

    print(
        "Total records:",
        len(df)
    )

    print(
        "Villages:",
        df["village_id"].nunique()
    )

    # --------------------------------------------------------
    # CREATE CHRONOLOGICAL SPLIT
    # --------------------------------------------------------

    print("\n[2] Creating chronological split...")

    train_df, validation_df, test_df = (
        create_time_series_split(df)
    )

    print("\nTraining:")
    print(
        train_df["date"].min().date(),
        "to",
        train_df["date"].max().date()
    )
    print(
        "Records:",
        len(train_df)
    )

    print("\nValidation:")
    print(
        validation_df["date"].min().date(),
        "to",
        validation_df["date"].max().date()
    )
    print(
        "Records:",
        len(validation_df)
    )

    print("\nTesting:")
    print(
        test_df["date"].min().date(),
        "to",
        test_df["date"].max().date()
    )
    print(
        "Records:",
        len(test_df)
    )

    # --------------------------------------------------------
    # FEATURES AND TARGET
    # --------------------------------------------------------

    X_train = train_df[FEATURES]
    y_train = train_df[TARGET]

    X_val = validation_df[FEATURES]
    y_val = validation_df[TARGET]

    X_test = test_df[FEATURES]
    y_test = test_df[TARGET]

    # --------------------------------------------------------
    # SCALE USING TRAINING DATA ONLY
    # --------------------------------------------------------

    print("\n[3] Scaling features")

    train_mean, train_std = (
        calculate_scaling_parameters(
            X_train
        )
    )

    X_train_scaled = scale_features(
        X_train,
        train_mean,
        train_std
    )

    X_val_scaled = scale_features(
        X_val,
        train_mean,
        train_std
    )

    X_test_scaled = scale_features(
        X_test,
        train_mean,
        train_std
    )

    print(
        "Scaling parameters calculated from training data only."
    )

    # --------------------------------------------------------
    # MODEL VALIDATION
    # --------------------------------------------------------

    print("\n[4] Validating baseline models...")

    (
        results,
        selected_model_name,
        selected_model
    ) = validate_models(
        X_train_scaled,
        y_train,
        X_val_scaled,
        y_val
    )

    print("\n==========================================")
    print("VALIDATION RESULTS")
    print("==========================================")

    for _, row in results.iterrows():

        print(
            f"\n{row['Model']}"
        )

        print(
            f"MAE  : {row['MAE']:,.2f} L"
        )

        print(
            f"RMSE : {row['RMSE']:,.2f} L"
        )

        print(
            f"MAPE : {row['MAPE']:.2f}%"
        )

    # --------------------------------------------------------
    # SELECT BEST MODEL
    # --------------------------------------------------------

    print("\n==========================================")
    print("MODEL SELECTION")
    print("==========================================")

    print(
        "Selected model:",
        selected_model_name
    )

    # --------------------------------------------------------
    # FINAL TEST
    # --------------------------------------------------------

    print("\n[5] Evaluating selected model on June data...")

    (
        final_predictions,
        final_mae,
        final_rmse,
        final_mape
    ) = evaluate_final_model(
        selected_model,
        X_test_scaled,
        y_test
    )

    print("\n==========================================")
    print("FINAL TEST RESULTS")
    print("==========================================")

    print(
        "Selected Model:",
        selected_model_name
    )

    print(
        f"MAE  : {final_mae:,.2f} L"
    )

    print(
        f"RMSE : {final_rmse:,.2f} L"
    )

    print(
        f"MAPE : {final_mape:.2f}%"
    )

    # --------------------------------------------------------
    # SAMPLE PREDICTIONS
    # --------------------------------------------------------

    print("\n==========================================")
    print("TEST PREDICTIONS")
    print("==========================================")

    comparison = pd.DataFrame({
        "Actual": y_test.values[:10],
        "Predicted": final_predictions[:10]
    })

    print(comparison.to_string(index=False))

    print("\n==========================================")
    print("VALIDATION COMPLETE")
    print("==========================================")

    return {
        "results": results,
        "selected_model_name": selected_model_name,
        "selected_model": selected_model,
        "train_mean": train_mean,
        "train_std": train_std,
        "final_predictions": final_predictions,
        "final_mae": final_mae,
        "final_rmse": final_rmse,
        "final_mape": final_mape
    }


# ============================================================
# RUN DIRECTLY
# ============================================================

if __name__ == "__main__":
    run_validation()