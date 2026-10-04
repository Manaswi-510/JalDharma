"""
Jal Dharma AI - Phase 18: Village Priority & Vulnerability Scoring
==================================================================
Methodology for determining village water allocation priority.

Objective:
    Calculate an explicit, transparent, and multi-criteria PriorityScore_i
    for each village based on:
        1. Population Need (Scale of human need)
        2. Vulnerability Index (Socio-economic & climate resilience)
        3. Historical Shortage Severity (Chronic water deprivation)
        4. Inaccessibility / Remoteness (Difficulty in alternative water access)

Formula:
    PriorityScore_i = (
        w_pop     * Norm(Population_i) +
        w_vuln    * Vulnerability_i +
        w_shortage* ShortageScore_i +
        w_access  * (1 - Accessibility_i)
    )

Weights are explicitly documented and normalized to sum to 1.0.
Sensitivity analysis assesses how different policy weightings affect allocations.

Outputs:
    Priority scores and weights for LP formulation (Phase 16) and
    equity/fairness evaluation (Phase 19).
"""

from pathlib import Path
from typing import Dict, Optional, Tuple
import numpy as np
import pandas as pd

# Default path for synthetic data fallback
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "synthetic"
DEFAULT_VILLAGE_FILE = DATA_DIR / "1_village_dataset.csv"

# -------------------------------------------------------------------------
# Explicit Weighting Documentation (Phase 18 Requirement)
# -------------------------------------------------------------------------
DEFAULT_WEIGHTS: Dict[str, float] = {
    "population": 0.25,          # Population size / basic human count
    "vulnerability": 0.35,       # Climate & socio-economic vulnerability (highest weight)
    "historical_shortage": 0.25, # Chronic deprivation & repeat crisis frequency
    "inaccessibility": 0.15,     # Remoteness / distance from primary infrastructure (1 - access)
}

# Qualitative to quantitative mapping for historical shortage
SHORTAGE_SEVERITY_MAP: Dict[str, float] = {
    "none": 0.00,
    "low": 0.25,
    "moderate": 0.50,
    "medium": 0.50,
    "high": 0.75,
    "critical": 1.00,
    "severe": 1.00,
}


def load_villages_data(filepath: Optional[Path] = None) -> pd.DataFrame:
    """Load villages dataset with geographic, demographic, and vulnerability attributes."""
    target_path = Path(filepath) if filepath else DEFAULT_VILLAGE_FILE
    if not target_path.exists():
        raise FileNotFoundError(f"Village dataset not found at: {target_path}")
    return pd.read_csv(target_path)


def min_max_normalize(series: pd.Series) -> pd.Series:
    """Normalize a pandas Series to [0, 1] range safely."""
    s_min = series.min()
    s_max = series.max()
    if pd.isna(s_min) or pd.isna(s_max) or s_max == s_min:
        return pd.Series(0.5, index=series.index)
    return (series - s_min) / (s_max - s_min)


def calculate_priority_scores(
    villages_df: Optional[pd.DataFrame] = None,
    weights: Optional[Dict[str, float]] = None,
    normalize_weights_sum_to_one: bool = True,
) -> pd.DataFrame:
    """
    Calculate documented multi-criteria priority scores for all villages.

    Args:
        villages_df: DataFrame with village records. If None, loads from synthetic CSV.
        weights: Dictionary with keys 'population', 'vulnerability',
                 'historical_shortage', 'inaccessibility'.
        normalize_weights_sum_to_one: Normalize input weights to sum to 1.0.

    Returns:
        DataFrame with original columns plus:
            - norm_population: Normalized population [0, 1]
            - norm_shortage: Normalized historical shortage [0, 1]
            - norm_inaccessibility: 1 - accessibility_score [0, 1]
            - priority_score: Composite score in [0, 1]
            - priority_weight: Relative weight normalized across all villages
            - priority_rank: Integer rank (1 = highest priority)
    """
    if villages_df is None:
        villages_df = load_villages_data()

    df = villages_df.copy()

    # 1. Resolve and normalize weights
    w = dict(weights) if weights else dict(DEFAULT_WEIGHTS)
    total_w = sum(w.values())
    if normalize_weights_sum_to_one and total_w > 0:
        w = {k: v / total_w for k, v in w.items()}

    # 2. Extract or impute components
    # Population component
    if "population" in df.columns:
        norm_pop = min_max_normalize(df["population"].astype(float))
    else:
        norm_pop = pd.Series(0.5, index=df.index)

    # Vulnerability component
    if "vulnerability_index" in df.columns:
        norm_vuln = df["vulnerability_index"].astype(float).clip(0.0, 1.0)
    elif "vulnerability_score" in df.columns:
        norm_vuln = df["vulnerability_score"].astype(float).clip(0.0, 1.0)
    else:
        norm_vuln = pd.Series(0.5, index=df.index)

    # Historical shortage component
    if "historical_shortage" in df.columns:
        if pd.api.types.is_numeric_dtype(df["historical_shortage"]):
            norm_shortage = min_max_normalize(df["historical_shortage"].astype(float))
        else:
            norm_shortage = (
                df["historical_shortage"]
                .astype(str)
                .str.strip()
                .str.lower()
                .map(SHORTAGE_SEVERITY_MAP)
                .fillna(0.50)
            )
    else:
        norm_shortage = pd.Series(0.5, index=df.index)

    # Inaccessibility component (Lower accessibility score means higher priority)
    if "accessibility_score" in df.columns:
        # accessibility_score: 1.0 = easy access, 0.0 = hard access
        inaccessibility = 1.0 - df["accessibility_score"].astype(float).clip(0.0, 1.0)
    else:
        inaccessibility = pd.Series(0.5, index=df.index)

    # 3. Calculate Composite Priority Score
    df["norm_population"] = norm_pop.round(4)
    df["norm_vulnerability"] = norm_vuln.round(4)
    df["norm_shortage"] = norm_shortage.round(4)
    df["norm_inaccessibility"] = inaccessibility.round(4)

    priority_score = (
        w["population"] * df["norm_population"]
        + w["vulnerability"] * df["norm_vulnerability"]
        + w["historical_shortage"] * df["norm_shortage"]
        + w["inaccessibility"] * df["norm_inaccessibility"]
    )

    df["priority_score"] = priority_score.round(4)

    # Normalized weight summing to 1.0 across all villages (used in LP objective)
    score_sum = df["priority_score"].sum()
    if score_sum > 0:
        df["priority_weight"] = (df["priority_score"] / score_sum).round(5)
    else:
        df["priority_weight"] = (1.0 / len(df)).round(5)

    # Priority Ranking (1 = highest priority / most needy)
    df["priority_rank"] = df["priority_score"].rank(ascending=False, method="min").astype(int)

    return df.sort_values("priority_rank").reset_index(drop=True)


def run_priority_sensitivity_analysis(
    villages_df: Optional[pd.DataFrame] = None,
) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame]]:
    """
    Sensitivity Analysis (Phase 18 Requirement):
    Examine how different policy weighting philosophies shift priority rankings.

    Scenarios compared:
        - Baseline (Balanced): 25% Pop, 35% Vuln, 25% Shortage, 15% Access
        - Vulnerability-First: 10% Pop, 60% Vuln, 20% Shortage, 10% Access
        - Population-First:    50% Pop, 20% Vuln, 20% Shortage, 10% Access
        - Crisis/Shortage-First: 15% Pop, 25% Vuln, 50% Shortage, 10% Access
        - Remoteness-First:    15% Pop, 25% Vuln, 20% Shortage, 40% Access

    Returns:
        rank_comparison_df: Table comparing ranks across scenarios for each village
        detailed_dfs: Dict of scenario name to full DataFrame
    """
    scenarios: Dict[str, Dict[str, float]] = {
        "Balanced (Default)": DEFAULT_WEIGHTS,
        "Vulnerability-Centric": {
            "population": 0.10,
            "vulnerability": 0.60,
            "historical_shortage": 0.20,
            "inaccessibility": 0.10,
        },
        "Population-Centric": {
            "population": 0.50,
            "vulnerability": 0.20,
            "historical_shortage": 0.20,
            "inaccessibility": 0.10,
        },
        "Crisis-Shortage-Centric": {
            "population": 0.15,
            "vulnerability": 0.25,
            "historical_shortage": 0.50,
            "inaccessibility": 0.10,
        },
        "Remoteness-Centric": {
            "population": 0.15,
            "vulnerability": 0.25,
            "historical_shortage": 0.20,
            "inaccessibility": 0.40,
        },
    }

    if villages_df is None:
        villages_df = load_villages_data()

    detailed_dfs: Dict[str, pd.DataFrame] = {}
    rank_dict: Dict[str, pd.Series] = {}

    for name, w in scenarios.items():
        res = calculate_priority_scores(villages_df, weights=w)
        detailed_dfs[name] = res
        rank_dict[f"Rank: {name}"] = res.set_index("village_id")["priority_rank"]

    rank_df = pd.DataFrame(rank_dict)
    # Add village names
    id_to_name = villages_df.set_index("village_id")["village_name"].to_dict()
    rank_df.insert(0, "village_name", rank_df.index.map(id_to_name))

    return rank_df, detailed_dfs


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print(" JAL DHARMA AI - PHASE 18: VILLAGE PRIORITY & VULNERABILITY MODEL")
    print("=" * 70)

    df_scored = calculate_priority_scores()
    print("\n[INFO] Top 10 Priority Villages (Highest Need):")
    cols_to_show = [
        "priority_rank",
        "village_id",
        "village_name",
        "population",
        "vulnerability_index",
        "historical_shortage",
        "priority_score",
        "priority_weight",
    ]
    print(df_scored[cols_to_show].head(10).to_string(index=False))

    print("\n[INFO] Running Sensitivity Analysis across 5 Weight Schemes...")
    rank_comp, _ = run_priority_sensitivity_analysis()
    print("\nTop 5 Villages Rank Shifts:")
    print(rank_comp.head(5).to_string())
    print("\n" + "=" * 70)
    print(" PHASE 18 COMPLETED SUCCESSFULLY")
    print("=" * 70)
