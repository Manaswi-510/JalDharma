"""
Jal Dharma AI - Phase 19: Water Justice & Fairness Metrics
==========================================================
Quantitative evaluation of equity, justice, and service reliability
in rural drinking water distribution.

Mathematical Metrics Implemented (Phase 19 Checklist):
------------------------------------------------------
19.1  Average Satisfaction Ratio:
      mean(S_i) where S_i = Allocated_i / Demand_i
19.2  Maximum Shortage:
      max(Demand_i - Allocated_i) in Litres/day
19.3  Average Shortage:
      mean(Demand_i - Allocated_i) in Litres/day
19.4  Weighted Shortage:
      sum(w_i * Shortage_i) / sum(w_i)
      Penalizes shortages falling upon vulnerable villages more heavily.
19.5  Jain's Fairness Index:
      J(x) = (sum(x_i))^2 / (n * sum(x_i^2))
      Bounded in [1/n, 1.0]. Perfect fairness = 1.0.
19.6  Gini Coefficient:
      G = sum_i sum_j |x_i - x_j| / (2 * n * sum_i x_i)
      Bounded in [0, 1]. 0 = Perfect equality, 1 = Complete inequality.
19.7  Percentage of Villages Receiving Minimum Service Level:
      % of villages with S_i >= threshold (default 70% satisfaction).
Additional:
      Hoover Index (Robin Hood Index):
      Fraction of total water that would need redistribution for equal satisfaction.

Run independently with:
    python -m src.justice.metrics
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import json
import numpy as np
import pandas as pd

# Default paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "synthetic"
OUTPUTS_DIR = BASE_DIR / "outputs" / "justice"
DEFAULT_ALLOCATIONS_FILE = DATA_DIR / "7_historical_water_allocation_dataset.csv"
DEFAULT_VILLAGES_FILE = DATA_DIR / "1_village_dataset.csv"


# =========================================================================
# 1. CORE METRIC MATHEMATICAL FORMULATIONS
# =========================================================================

def calculate_satisfaction_ratios(
    allocated: Union[pd.Series, np.ndarray, List[float]],
    demanded: Union[pd.Series, np.ndarray, List[float]],
) -> pd.Series:
    """
    Compute demand satisfaction ratio S_i = A_i / D_i.
    Capped at 1.0 (over-allocation does not create >100% satisfaction) and min 0.0.
    """
    alloc_arr = np.asarray(allocated, dtype=float)
    demand_arr = np.asarray(demanded, dtype=float)

    # Protect against divide-by-zero
    with np.errstate(divide="ignore", invalid="ignore"):
        ratios = np.where(demand_arr > 0, alloc_arr / demand_arr, 1.0)
    # Clip between 0.0 and 1.0
    ratios = np.clip(ratios, 0.0, 1.0)
    return pd.Series(ratios)


def average_satisfaction_ratio(satisfaction_ratios: Union[pd.Series, np.ndarray]) -> float:
    """Checklist 19.1: Mean satisfaction ratio across all communities (0.0 to 1.0)."""
    s = np.asarray(satisfaction_ratios, dtype=float)
    if len(s) == 0:
        return 0.0
    return float(np.mean(s))


def maximum_shortage(shortages: Union[pd.Series, np.ndarray]) -> float:
    """Checklist 19.2: Maximum single-village water deficit in Litres."""
    sh = np.asarray(shortages, dtype=float)
    if len(sh) == 0:
        return 0.0
    return float(np.max(sh))


def average_shortage(shortages: Union[pd.Series, np.ndarray]) -> float:
    """Checklist 19.3: Mean water deficit per village in Litres."""
    sh = np.asarray(shortages, dtype=float)
    if len(sh) == 0:
        return 0.0
    return float(np.mean(sh))


def weighted_shortage(
    shortages: Union[pd.Series, np.ndarray],
    weights: Union[pd.Series, np.ndarray],
) -> float:
    """
    Checklist 19.4: Shortage weighted by village priority/vulnerability.
    Formula: sum(w_i * shortage_i) / sum(w_i)
    """
    sh = np.asarray(shortages, dtype=float)
    w = np.asarray(weights, dtype=float)
    if len(sh) == 0 or len(w) == 0 or np.sum(w) == 0:
        return 0.0
    return float(np.sum(sh * w) / np.sum(w))


def jains_fairness_index(values: Union[pd.Series, np.ndarray, List[float]]) -> float:
    """
    Checklist 19.5: Jain's Fairness Index.
        J(x) = (sum(x_i))^2 / (n * sum(x_i^2))
    Range: [1/n, 1.0].
    If all allocations/satisfactions are equal, J = 1.0 (ideal fairness).
    """
    x = np.asarray(values, dtype=float)
    n = len(x)
    if n == 0:
        return 0.0

    sum_x = np.sum(x)
    sum_sq_x = np.sum(x ** 2)

    if sum_sq_x == 0:
        return 1.0  # All zeros is technically identical (or no allocation)

    j_index = (sum_x ** 2) / (n * sum_sq_x)
    return float(np.clip(j_index, 1.0 / n, 1.0))


def gini_coefficient(values: Union[pd.Series, np.ndarray, List[float]]) -> float:
    """
    Checklist 19.6: Gini Inequality Coefficient.
        G = sum_i sum_j |x_i - x_j| / (2 * n * sum_i x_i)
    Range: [0, 1].
    0.0 represents perfect equality, 1.0 represents absolute inequality.
    """
    x = np.asarray(values, dtype=float)
    x = x[x >= 0]  # non-negative
    n = len(x)
    if n == 0:
        return 0.0

    sum_x = np.sum(x)
    if sum_x == 0:
        return 0.0

    # Fast calculation via sorted array
    sorted_x = np.sort(x)
    index = np.arange(1, n + 1)
    # Gini formula using cumulative ranks: (2 * sum(i * y_i)) / (n * sum(y)) - (n + 1) / n
    gini = (2.0 * np.sum(index * sorted_x)) / (n * sum_x) - (n + 1.0) / n
    return float(np.clip(gini, 0.0, 1.0))


def hoover_index(values: Union[pd.Series, np.ndarray, List[float]]) -> float:
    """
    Hoover Index (Robin Hood Index):
        H = (1 / 2) * sum(|x_i - mean(x)|) / sum(x_i)
    Represents the proportion of total water that would have to be redistributed
    from villages above the mean to those below the mean to achieve complete equality.
    """
    x = np.asarray(values, dtype=float)
    total = np.sum(x)
    if len(x) == 0 or total == 0:
        return 0.0
    mean_val = np.mean(x)
    hoover = 0.5 * np.sum(np.abs(x - mean_val)) / total
    return float(np.clip(hoover, 0.0, 1.0))


def percentage_minimum_service_level(
    satisfaction_ratios: Union[pd.Series, np.ndarray],
    threshold: float = 0.70,
) -> float:
    """
    Checklist 19.7: Percentage of villages receiving at least minimum service level.
    Args:
        satisfaction_ratios: Array of satisfaction ratios S_i
        threshold: Minimum acceptable satisfaction ratio (default: 70% or 0.70)
    Returns:
        Percentage between 0.0 and 100.0
    """
    s = np.asarray(satisfaction_ratios, dtype=float)
    if len(s) == 0:
        return 0.0
    compliant_count = np.sum(s >= threshold)
    return float((compliant_count / len(s)) * 100.0)


# =========================================================================
# 2. COMPREHENSIVE SUITE RUNNER
# =========================================================================

def calculate_all_fairness_metrics(
    allocation_df: pd.DataFrame,
    weights_col: Optional[str] = "priority_score",
    min_service_threshold: float = 0.70,
) -> Dict[str, Any]:
    """
    Calculate the complete suite of Phase 19 Water Justice & Fairness Metrics
    for an allocation dataset.

    Args:
        allocation_df: DataFrame conforming to shared contract:
            - predicted_demand_l
            - allocated_water_l
            - (optional) shortage_l
            - (optional) satisfaction_ratio
            - (optional) priority_score or priority_weight
        weights_col: Column name to use for weighted shortage penalty.
        min_service_threshold: Fraction (e.g. 0.70 = 70%) for minimum service.

    Returns:
        Dictionary containing all metrics and formatted percentages/units.
    """
    df = allocation_df.copy()

    # Ensure required columns exist
    if "predicted_demand_l" not in df.columns or "allocated_water_l" not in df.columns:
        raise ValueError(
            "DataFrame must contain 'predicted_demand_l' and 'allocated_water_l'."
        )

    # Compute shortages if missing
    if "shortage_l" not in df.columns:
        df["shortage_l"] = np.maximum(0.0, df["predicted_demand_l"] - df["allocated_water_l"])

    # Compute satisfaction ratios if missing
    if "satisfaction_ratio" not in df.columns:
        df["satisfaction_ratio"] = calculate_satisfaction_ratios(
            df["allocated_water_l"], df["predicted_demand_l"]
        )

    # Weights for weighted shortage
    if weights_col and weights_col in df.columns:
        weights = df[weights_col].values
    else:
        weights = np.ones(len(df))

    total_demand = float(df["predicted_demand_l"].sum())
    total_allocated = float(df["allocated_water_l"].sum())
    total_shortage = float(df["shortage_l"].sum())

    # Individual metrics
    avg_sat = average_satisfaction_ratio(df["satisfaction_ratio"].values)
    max_short = maximum_shortage(df["shortage_l"].values)
    avg_short = average_shortage(df["shortage_l"].values)
    w_short = weighted_shortage(df["shortage_l"].values, weights)
    jain_sat = jains_fairness_index(df["satisfaction_ratio"].values)
    gini_sat = gini_coefficient(df["satisfaction_ratio"].values)
    hoover_sat = hoover_index(df["satisfaction_ratio"].values)
    min_svc_pct = percentage_minimum_service_level(
        df["satisfaction_ratio"].values, threshold=min_service_threshold
    )

    # Gini on per capita allocation if population is present
    gini_per_capita = None
    if "population" in df.columns and (df["population"] > 0).all():
        per_capita_alloc = df["allocated_water_l"] / df["population"]
        gini_per_capita = round(gini_coefficient(per_capita_alloc.values), 4)

    results: Dict[str, Any] = {
        "summary": {
            "num_villages": int(len(df)),
            "total_demand_l": round(total_demand, 2),
            "total_allocated_l": round(total_allocated, 2),
            "total_shortage_l": round(total_shortage, 2),
            "overall_fulfillment_pct": round((total_allocated / total_demand * 100) if total_demand > 0 else 100.0, 2),
        },
        "phase_19_metrics": {
            "19.1_average_satisfaction_ratio": round(avg_sat, 4),
            "19.1_average_satisfaction_pct": round(avg_sat * 100.0, 2),
            "19.2_maximum_shortage_l": round(max_short, 2),
            "19.3_average_shortage_l": round(avg_short, 2),
            "19.4_weighted_shortage_l": round(w_short, 2),
            "19.5_jains_fairness_index": round(jain_sat, 4),
            "19.6_gini_coefficient_satisfaction": round(gini_sat, 4),
            "19.6_gini_coefficient_per_capita": gini_per_capita,
            "19.7_villages_meeting_min_service_pct": round(min_svc_pct, 2),
            "service_threshold_used": round(min_service_threshold * 100, 1),
            "additional_hoover_index": round(hoover_sat, 4),
        },
        "interpretations": {
            "jains_fairness": "Excellent (>=0.90)" if jain_sat >= 0.90 else ("Moderate (0.75-0.90)" if jain_sat >= 0.75 else "Unequal (<0.75)"),
            "gini_satisfaction": "High Equality (<0.15)" if gini_sat < 0.15 else ("Moderate Inequality (0.15-0.30)" if gini_sat < 0.30 else "High Inequality (>=0.30)"),
            "water_justice_grade": (
                "Grade A (Water Justice Compliant)" if (jain_sat >= 0.85 and min_svc_pct >= 85.0)
                else ("Grade B (Moderate Equity)" if (jain_sat >= 0.70 and min_svc_pct >= 70.0)
                else "Grade C (Severe Water Inequity)")
            ),
        },
    }

    return results


# =========================================================================
# 3. LOADER & CLI RUNNER
# =========================================================================

def load_sample_allocations(date_str: Optional[str] = None) -> pd.DataFrame:
    """
    Load allocation dataset for evaluation.
    If date_str is provided, filters for that specific day.
    Merges population and village attributes if available.
    """
    if not DEFAULT_ALLOCATIONS_FILE.exists():
        raise FileNotFoundError(f"Allocations dataset not found at: {DEFAULT_ALLOCATIONS_FILE}")

    df_alloc = pd.read_csv(DEFAULT_ALLOCATIONS_FILE)

    if date_str:
        df_alloc = df_alloc[df_alloc["date"] == date_str].copy()
    else:
        # Default to the most recent date in the historical file
        latest_date = df_alloc["date"].max()
        df_alloc = df_alloc[df_alloc["date"] == latest_date].copy()

    # Try merging population & vulnerability from village dataset
    if DEFAULT_VILLAGES_FILE.exists():
        try:
            df_vill = pd.read_csv(DEFAULT_VILLAGES_FILE)[
                ["village_id", "village_name", "population", "vulnerability_index"]
            ]
            df_alloc = df_alloc.merge(df_vill, on="village_id", how="left")
        except Exception:
            pass

    return df_alloc.reset_index(drop=True)


if __name__ == "__main__":
    print("\n" + "=" * 75)
    print(" JAL DHARMA AI - PHASE 19: WATER JUSTICE & FAIRNESS METRICS EVALUATION")
    print("=" * 75)

    sample_df = load_sample_allocations()
    target_date = sample_df["date"].iloc[0] if "date" in sample_df.columns else "Sample Date"
    print(f"\n[INFO] Loaded {len(sample_df)} village allocations for date: {target_date}")

    metrics = calculate_all_fairness_metrics(sample_df, min_service_threshold=0.70)

    p19 = metrics["phase_19_metrics"]
    summ = metrics["summary"]
    interp = metrics["interpretations"]

    print("\n" + "-" * 75)
    print(" EXECUTIVE WATER JUSTICE SCORECARD")
    print("-" * 75)
    print(f"  • Total Villages Evaluated         : {summ['num_villages']}")
    print(f"  • Total Water Demanded             : {summ['total_demand_l']:,.0f} L")
    print(f"  • Total Water Allocated            : {summ['total_allocated_l']:,.0f} L ({summ['overall_fulfillment_pct']}%)")
    print(f"  • Total Water Shortage             : {summ['total_shortage_l']:,.0f} L")
    print("-" * 75)
    print(f"  [19.1] Average Satisfaction Ratio   : {p19['19.1_average_satisfaction_pct']}%  ({p19['19.1_average_satisfaction_ratio']})")
    print(f"  [19.2] Maximum Single Shortage     : {p19['19.2_maximum_shortage_l']:,.0f} L")
    print(f"  [19.3] Average Village Shortage    : {p19['19.3_average_shortage_l']:,.0f} L")
    print(f"  [19.4] Weighted Shortage (Equity)  : {p19['19.4_weighted_shortage_l']:,.0f} L")
    print(f"  [19.5] Jain's Fairness Index (J)   : {p19['19.5_jains_fairness_index']:.4f}  [{interp['jains_fairness']}]")
    print(f"  [19.6] Gini Coefficient (Alloc)    : {p19['19.6_gini_coefficient_satisfaction']:.4f}  [{interp['gini_satisfaction']}]")
    if p19['19.6_gini_coefficient_per_capita'] is not None:
        print(f"         Gini (Per Capita Water)     : {p19['19.6_gini_coefficient_per_capita']:.4f}")
    print(f"  [19.7] Receiving >= {p19['service_threshold_used']}% Min Service: {p19['19.7_villages_meeting_min_service_pct']}%")
    print(f"  [EXTRA] Hoover (Robin Hood) Index  : {p19['additional_hoover_index']:.4f}")
    print("-" * 75)
    print(f"  OVERALL SYSTEM RATING              : {interp['water_justice_grade']}")
    print("=" * 75)

    # Save to outputs
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUTPUTS_DIR / "water_justice_metrics.json"
    with open(out_file, "w") as f:
        json.dump(metrics, f, indent=4)
    print(f"\n[INFO] Complete metrics exported to: {out_file}\n")
