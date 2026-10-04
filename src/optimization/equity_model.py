"""
Jal Dharma AI
PHASE 17: Define the Equity Model
==================================
This is what makes Jal Dharma AI different from a basic water-routing project.

For each village calculate:
    S_i = A_i / D_i

where:
    • A_i = allocated water
    • D_i = predicted demand
    • S_i = demand satisfaction ratio

Example:
    Village   Demand   Allocation   Satisfaction
    A         100k     90k          90%
    B         100k     80k          80%
    C         100k     50k          50%

Features:
  - 17.1 Calculates per-village satisfaction ratio S_i
  - 17.2 Categorizes equity status (Equitably Served, Moderately Strained, Critical Deficit)
  - 17.3 Analyzes equity vs. vulnerability index (ensures vulnerable communities are protected)
  - 17.4 Measures system-wide disparity gap: max(S_i) - min(S_i)
  - 17.5 Produces standardized equity DataFrame for Phase 18 & 19 justice metrics
"""

import sys
from pathlib import Path

# Add project root to sys.path so the file can be run directly or as a module
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np
from sqlalchemy import text

from src.database.connection import get_engine
from src.optimization.lp_allocator import run_phase16_lp


# =====================================================================
# DATA LOADING
# =====================================================================

def load_latest_allocations(engine=None):
    """
    Load the latest allocation run from PostgreSQL `allocations` table.
    If the table is empty, executes Phase 16 LP allocator dynamically.
    """
    if engine is None:
        engine = get_engine()

    query = text("""
        SELECT 
            village_id,
            village_name,
            population,
            vulnerability_index,
            predicted_demand_l,
            allocated_water_l,
            shortage_l,
            allocation_date
        FROM allocations
        WHERE allocation_date = (SELECT MAX(allocation_date) FROM allocations)
        ORDER BY village_id
    """)
    try:
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
        if not df.empty:
            return df
    except Exception as e:
        print(f"[WARN] Failed to read allocations from DB ({e}). Generating fresh LP run.")

    print("[INFO] Generating fresh allocation run from Phase 16...")
    allocations_df, _ = run_phase16_lp(engine, store=False)
    return allocations_df


# =====================================================================
# EQUITY MODEL CALCULATION
# =====================================================================

def calculate_satisfaction_ratios(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate demand satisfaction ratio for each village:
        S_i = A_i / D_i
    """
    out = df.copy()

    # Ensure numeric columns
    out["predicted_demand_l"] = pd.to_numeric(out["predicted_demand_l"], errors="coerce").fillna(0.0)
    out["allocated_water_l"] = pd.to_numeric(out["allocated_water_l"], errors="coerce").fillna(0.0)

    # S_i = A_i / D_i
    # Handle division by zero: if demand is 0, satisfaction is 1.0 (100%)
    out["satisfaction_ratio"] = np.where(
        out["predicted_demand_l"] > 0,
        out["allocated_water_l"] / out["predicted_demand_l"],
        1.0
    )
    # Cap satisfaction ratio between 0.0 and 1.0
    out["satisfaction_ratio"] = out["satisfaction_ratio"].clip(lower=0.0, upper=1.0)
    out["satisfaction_pct"] = out["satisfaction_ratio"] * 100.0

    # Deficit / shortage
    out["shortage_l"] = np.maximum(0.0, out["predicted_demand_l"] - out["allocated_water_l"])

    return out


def classify_equity_tiers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Classify villages into equity tiers based on satisfaction ratio S_i:
      • High Equity (S_i >= 90%)
      • Moderate Deficit (70% <= S_i < 90%)
      • Critical Shortage (S_i < 70%)
    """
    out = df.copy()
    conditions = [
        out["satisfaction_ratio"] >= 0.90,
        out["satisfaction_ratio"] >= 0.70,
        out["satisfaction_ratio"] < 0.70,
    ]
    choices = [
        "High Satisfaction (>=90%)",
        "Moderate Deficit (70-89%)",
        "Critical Shortage (<70%)",
    ]
    out["equity_status"] = np.select(conditions, choices, default="Unknown")
    return out


def evaluate_equity_summary(df: pd.DataFrame) -> dict:
    """
    Compute system-level water equity statistics:
      - Average satisfaction ratio (mean S_i)
      - Minimum satisfaction (worst-served village)
      - Maximum satisfaction (best-served village)
      - Equity Disparity Gap: max(S_i) - min(S_i)
      - Vulnerability-Satisfaction Correlation
    """
    total_demand = df["predicted_demand_l"].sum()
    total_allocated = df["allocated_water_l"].sum()
    total_shortage = df["shortage_l"].sum()

    overall_satisfaction = (total_allocated / total_demand) if total_demand > 0 else 1.0

    min_s = df["satisfaction_ratio"].min()
    max_s = df["satisfaction_ratio"].max()
    mean_s = df["satisfaction_ratio"].mean()
    disparity_gap = max_s - min_s

    # Correlation between vulnerability and satisfaction (should be non-negative)
    corr = 0.0
    if "vulnerability_index" in df.columns and len(df) > 1:
        corr = df["vulnerability_index"].corr(df["satisfaction_ratio"])
        if np.isnan(corr):
            corr = 0.0

    return {
        "total_villages": len(df),
        "total_demand_l": total_demand,
        "total_allocated_l": total_allocated,
        "total_shortage_l": total_shortage,
        "overall_satisfaction_pct": overall_satisfaction * 100.0,
        "mean_satisfaction_pct": mean_s * 100.0,
        "min_satisfaction_pct": min_s * 100.0,
        "max_satisfaction_pct": max_s * 100.0,
        "disparity_gap_pct": disparity_gap * 100.0,
        "vulnerability_correlation": corr,
    }


# =====================================================================
# REPORTING & DISPLAY
# =====================================================================

def format_volume(litres: float) -> str:
    """Format volume nicely into k or M units."""
    if litres >= 1_000_000:
        return f"{litres / 1_000_000:.2f}M"
    elif litres >= 1_000:
        return f"{litres / 1_000:.1f}k"
    else:
        return f"{litres:,.0f}"


def print_equity_report(df: pd.DataFrame, summary: dict):
    """Print the formatted Phase 17 Equity Report matching example."""
    print("\n" + "=" * 70)
    print("PHASE 17 - WATER EQUITY MODEL (S_i = A_i / D_i)")
    print("=" * 70)

    print("\n--- VILLAGE DEMAND SATISFACTION (S_i) ---")
    display_rows = []
    for _, row in df.iterrows():
        display_rows.append({
            "Village ID": row["village_id"],
            "Village": row.get("village_name", row["village_id"]),
            "Demand (D_i)": format_volume(row["predicted_demand_l"]),
            "Allocation (A_i)": format_volume(row["allocated_water_l"]),
            "Satisfaction (S_i)": f"{row['satisfaction_pct']:.1f}%",
            "Shortage": format_volume(row["shortage_l"]),
            "Equity Status": row.get("equity_status", "N/A"),
        })

    display_df = pd.DataFrame(display_rows)
    print(display_df.to_string(index=False))

    print("\n" + "-" * 70)
    print("EQUITY SUMMARY METRICS")
    print("-" * 70)
    print(f"Total Villages Evaluated   : {summary['total_villages']}")
    print(f"Total Predicted Demand (D) : {summary['total_demand_l']:>14,.0f} L/day")
    print(f"Total Water Allocated (A)  : {summary['total_allocated_l']:>14,.0f} L/day")
    print(f"Total System Shortage      : {summary['total_shortage_l']:>14,.0f} L/day")
    print(f"Overall Satisfaction Ratio : {summary['overall_satisfaction_pct']:>13.1f}%")
    print(f"Average Village Satisfaction: {summary['mean_satisfaction_pct']:>12.1f}%")
    print(f"Min Satisfaction (Worst)   : {summary['min_satisfaction_pct']:>13.1f}%")
    print(f"Max Satisfaction (Best)    : {summary['max_satisfaction_pct']:>13.1f}%")
    print(f"Satisfaction Disparity Gap : {summary['disparity_gap_pct']:>13.1f}%  [Max - Min]")
    print("-" * 70)

    if summary["disparity_gap_pct"] < 10.0:
        print("[EQUITY ASSESSMENT] HIGHLY EQUITABLE: Variance in satisfaction across villages is minimal.")
    elif summary["disparity_gap_pct"] < 30.0:
        print("[EQUITY ASSESSMENT] MODERATE EQUITY: Moderate disparity exists due to pipeline constraints.")
    else:
        print("[EQUITY ASSESSMENT] INEQUITY DETECTED: Significant satisfaction gap across villages.")

    print("\n[SUCCESS] Phase 17 Complete: Demand satisfaction ratios calculated & equity model defined!")


# =====================================================================
# DEMONSTRATION OF SPECIFICATION EXAMPLE
# =====================================================================

def demonstrate_example_from_spec():
    """Demonstrate the exact example given in the Phase 17 specification."""
    print("\n" + "=" * 70)
    print("PHASE 17 - VERIFICATION ON SPECIFICATION EXAMPLE")
    print("=" * 70)
    sample_data = pd.DataFrame([
        {"village_id": "VIL_A", "village_name": "Village A", "predicted_demand_l": 100000.0, "allocated_water_l": 90000.0},
        {"village_id": "VIL_B", "village_name": "Village B", "predicted_demand_l": 100000.0, "allocated_water_l": 80000.0},
        {"village_id": "VIL_C", "village_name": "Village C", "predicted_demand_l": 100000.0, "allocated_water_l": 50000.0},
    ])
    demo_df = calculate_satisfaction_ratios(sample_data)
    demo_df = classify_equity_tiers(demo_df)
    summary = evaluate_equity_summary(demo_df)
    print_equity_report(demo_df, summary)


# =====================================================================
# MAIN ENTRY POINT
# =====================================================================

def run_phase17_equity_model(engine=None):
    """Execute Phase 17 workflow."""
    # First: Run the specification benchmark example
    demonstrate_example_from_spec()

    # Second: Run against live PostgreSQL database
    if engine is None:
        engine = get_engine()

    print("\n" + "=" * 70)
    print("RUNNING PHASE 17 ON LIVE DATABASE ALLOCATIONS")
    print("=" * 70)
    print("[STEP 1] Loading allocation results from database...")
    raw_df = load_latest_allocations(engine)

    print("[STEP 2] Computing satisfaction ratios S_i = A_i / D_i...")
    equity_df = calculate_satisfaction_ratios(raw_df)

    print("[STEP 3] Classifying equity tiers & computing disparity metrics...")
    equity_df = classify_equity_tiers(equity_df)
    summary = evaluate_equity_summary(equity_df)

    print_equity_report(equity_df, summary)
    return equity_df, summary


if __name__ == "__main__":
    run_phase17_equity_model()

