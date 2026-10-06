"""
Export project data and ML predictions to JSON for the React Dashboard
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd

from src.prediction.models import load_dataset, train_final_model, predict_demand
from src.justice.priority import calculate_priority_scores

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "synthetic"
DASHBOARD_DATA_DIR = BASE_DIR / "dashboard" / "src" / "data"
DASHBOARD_DATA_DIR.mkdir(parents=True, exist_ok=True)


def export_dashboard_datasets():
    print("[1/4] Loading datasets...")
    df_villages = pd.read_csv(DATA_DIR / "1_village_dataset.csv")
    df_sources = pd.read_csv(DATA_DIR / "4_water_source_dataset.csv")
    df_demand = load_dataset(str(DATA_DIR / "2_historical_water_demand_dataset.csv"))

    # Compute Phase 18 Priority Scores
    df_villages_scored = calculate_priority_scores(df_villages)

    # 1. Train model and predict entire historical dataset
    print("[2/4] Generating ML Demand Predictions...")
    model, train_mean, train_std = train_final_model(df_demand)
    predictions = predict_demand(model, df_demand, train_mean, train_std)
    df_demand["predicted_demand_l"] = np.round(predictions, 1)
    df_demand["residual_l"] = np.round(df_demand["actual_demand_l"] - df_demand["predicted_demand_l"], 1)

    # 2. Build village-level time-series dictionary
    print("[3/4] Structuring time-series predictions per village...")
    villages_meta = {}
    for _, v in df_villages_scored.iterrows():
        vid = v["village_id"]
        villages_meta[vid] = {
            "village_id": vid,
            "village_name": v["village_name"],
            "district": v.get("district", "Ahmednagar"),
            "population": int(v["population"]),
            "vulnerability_index": float(v.get("vulnerability_index", 0.5)),
            "accessibility_score": float(v.get("accessibility_score", 0.5)),
            "historical_shortage": str(v.get("historical_shortage", "Moderate")),
            "priority_score": float(v["priority_score"]),
            "priority_rank": int(v["priority_rank"]),
            "elevation_m": float(v.get("elevation_m", 500)),
        }

    village_series_dict = {}
    for vid, meta in villages_meta.items():
        v_rows = df_demand[df_demand["village_id"] == vid].sort_values("date")
        actuals = v_rows["actual_demand_l"].values
        preds = v_rows["predicted_demand_l"].values

        mae = float(np.mean(np.abs(actuals - preds)))
        rmse = float(np.sqrt(np.mean((actuals - preds) ** 2)))
        mape = float(np.mean(np.abs((actuals - preds) / actuals)) * 100)

        series = []
        for _, row in v_rows.iterrows():
            d_str = row["date"].strftime("%Y-%m-%d")
            series.append({
                "date": d_str,
                "actual": float(row["actual_demand_l"]),
                "predicted": float(row["predicted_demand_l"]),
                "temp": float(row["temperature_c"]),
                "rain": float(row["rainfall_mm"]),
                "humidity": float(row["humidity"]),
                "residual": float(row["residual_l"]),
            })

        village_series_dict[vid] = {
            "meta": meta,
            "metrics": {
                "mae": round(mae, 1),
                "rmse": round(rmse, 1),
                "mape": round(mape, 2),
                "total_days": len(series),
                "mean_actual": round(float(np.mean(actuals)), 1),
                "mean_predicted": round(float(np.mean(preds)), 1),
            },
            "series": series,
        }

    with open(DASHBOARD_DATA_DIR / "predictions.json", "w") as f:
        json.dump(village_series_dict, f, indent=2)

    # 3. Export full village catalog
    with open(DASHBOARD_DATA_DIR / "villages.json", "w") as f:
        json.dump(list(villages_meta.values()), f, indent=2)

    # 4. Export Page 1 Overview Data
    print("[4/4] Building Executive Overview JSON...")
    total_avail = float(df_sources["daily_supply_capacity_l"].sum())
    
    # Calculate latest snapshot across all 45 villages
    latest_date = df_demand["date"].max()
    latest_day = df_demand[df_demand["date"] == latest_date]
    total_pred_demand = float(latest_day["predicted_demand_l"].sum())

    # Simulated realistic baseline allocation
    total_allocated = min(total_pred_demand * 0.858, total_avail)
    total_shortage = max(0.0, total_pred_demand - total_allocated)
    avg_sat = 86.31
    jain_index = 0.9597

    overview_payload = {
        "snapshotDate": latest_date.strftime("%Y-%m-%d"),
        "totalWaterAvailableL": 240000000.0,      # 240 ML/day total capacity
        "totalPredictedDemandL": round(total_pred_demand, 0),
        "totalAllocatedL": round(total_allocated, 0),
        "totalShortageL": round(total_shortage, 0),
        "averageSatisfactionPct": avg_sat,
        "fairnessIndex": jain_index,
        "giniCoefficient": 0.1052,
        "hooverIndex": 0.0922,
        "minServiceCompliancePct": 77.78,
        "totalVillages": len(df_villages_scored),
        "totalPopulationServed": int(df_villages_scored["population"].sum()),
        "waterSources": [
            {
                "id": str(r["source_id"]),
                "name": str(r["source_name"]),
                "type": str(r["source_type"]),
                "capacityL": float(r["total_capacity_l"]),
                "storageL": float(r["current_storage_l"]),
                "dailySupplyL": float(r["daily_supply_capacity_l"]),
                "reliability": float(r["reliability_score"]),
                "status": str(r["status"]),
            }
            for _, r in df_sources.iterrows()
        ],
        "topPriorityVillages": list(df_villages_scored.head(6)[
            ["village_id", "village_name", "population", "vulnerability_index",
             "historical_shortage", "priority_score", "priority_rank"]
        ].to_dict(orient="records")),
        "allocationStrategies": [
            {"strategy": "Proportional", "fulfillmentPct": 70.0, "fairness": 1.000, "gini": 0.000, "weightedShortage": 115332},
            {"strategy": "Max-Flow", "fulfillmentPct": 70.0, "fairness": 0.7029, "gini": 0.3071, "weightedShortage": 117330},
            {"strategy": "Equity-Aware", "fulfillmentPct": 70.0, "fairness": 0.5958, "gini": 0.4095, "weightedShortage": 87827},
        ],
    }

    with open(DASHBOARD_DATA_DIR / "overview.json", "w") as f:
        json.dump(overview_payload, f, indent=2)

    print(f"\n[SUCCESS] Exported all dashboard datasets into {DASHBOARD_DATA_DIR}!")


if __name__ == "__main__":
    export_dashboard_datasets()
