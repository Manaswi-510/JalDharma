"""
Jal Dharma AI
Main Application Entry Point

The detailed experiments for Phases 9, 10 and 11
are maintained separately in the prediction module.

Final selected model:
    Linear Regression
"""

from src.prediction.models import (
    load_dataset,
    train_final_model,
    predict_demand,
)


def main():

    print("\n==========================================")
    print("JAL DHARMA AI")
    print("==========================================")
    print("Water Demand Prediction System")

    dataset_path = (
        "data/synthetic/"
        "2_historical_water_demand_dataset.csv"
    )

    print("\nLoading dataset...")

    df = load_dataset(dataset_path)

    print("Total records:", len(df))
    print("Number of villages:", df["village_id"].nunique())

    # Train the final model selected during Phase 11
    model, train_mean, train_std = train_final_model(df)

    # Test the model using one existing record
    sample = df.iloc[[0]]

    prediction = predict_demand(
        model,
        sample,
        train_mean,
        train_std
    )

    print("\n==========================================")
    print("SAMPLE PREDICTION")
    print("==========================================")

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
        f"{sample['actual_demand_l'].iloc[0]:,.2f}",
        "L/day"
    )

    print(
        "Predicted demand:",
        f"{prediction[0]:,.2f}",
        "L/day"
    )

    print("\n==========================================")
    print("MAIN APPLICATION COMPLETE")
    print("==========================================")


if __name__ == "__main__":
    main()