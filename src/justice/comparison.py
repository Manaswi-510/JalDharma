"""
Jal Dharma AI - Phase 20: Compare Allocation Methods
====================================================
Rigorous comparative benchmark of three foundational water distribution strategies:

    1. Strategy A: Proportional Allocation
       - Distributes available water strictly proportional to each village's demand.
       - A_i = min(D_i, S_avail * (D_i / sum(D_k))), bounded by connecting pipeline capacity.
       - Classic egalitarian benchmark (ignores network topology and vulnerability differences).

    2. Strategy B: Maximum Flow (Throughput-Maximization)
       - Solves physical network max-flow from sources -> tanks -> villages.
       - Objective: Maximize gross water delivered (sum A_i).
       - Greedily satisfies villages along large, short pipes; neglects distant/vulnerable villages.

    3. Strategy C: Equity-Aware Optimization (Water Justice)
       - Solves multi-criteria Linear Programming (LP) with Phase 18 Priority Weights (w_i).
       - Objective: Minimize weighted shortage: min sum(w_i * (D_i - A_i)).
       - Prioritizes vulnerable and historically deprived villages under water scarcity.

Evaluation Criteria (Phase 20 Research Table):
----------------------------------------------
- Total Water Delivered (L)
- Overall Fulfillment Rate (%)
- Average Village Shortage (L)
- Maximum Single Shortage (L)
- Weighted Shortage (L)
- Average Satisfaction Ratio (%)
- Jain's Fairness Index (J)
- Gini Inequality Coefficient (G)
- Hoover (Robin Hood) Index
- % Villages Receiving >= 70% Minimum Service Level

Outputs:
    outputs/justice/allocation_comparison.csv
    outputs/justice/allocation_comparison.json
    outputs/justice/village_allocations_compared.csv

Run with:
    python -m src.justice.comparison
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json
import numpy as np
import pandas as pd
from scipy.optimize import linprog

from src.justice.priority import calculate_priority_scores
from src.justice.metrics import (
    average_satisfaction_ratio,
    maximum_shortage,
    average_shortage,
    weighted_shortage,
    jains_fairness_index,
    gini_coefficient,
    percentage_minimum_service_level,
    hoover_index,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "synthetic"
OUTPUTS_DIR = BASE_DIR / "outputs" / "justice"

SOURCES_FILE = DATA_DIR / "4_water_source_dataset.csv"
PIPELINES_FILE = DATA_DIR / "5_pipeline_water_network_dataset.csv"
VILLAGES_FILE = DATA_DIR / "1_village_dataset.csv"
HISTORICAL_DEMAND_FILE = DATA_DIR / "2_historical_water_demand_dataset.csv"


# =========================================================================
# 1. DATA INGESTION
# =========================================================================

def load_network_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load sources, pipelines, and villages with Phase 18 priority scores."""
    if not SOURCES_FILE.exists() or not PIPELINES_FILE.exists() or not VILLAGES_FILE.exists():
        raise FileNotFoundError("Synthetic dataset files missing in data/synthetic/")

    df_sources = pd.read_csv(SOURCES_FILE)
    df_pipelines = pd.read_csv(PIPELINES_FILE)
    df_villages = calculate_priority_scores(pd.read_csv(VILLAGES_FILE))

    return df_sources, df_pipelines, df_villages


def get_village_demands(
    df_villages: pd.DataFrame,
    date_str: Optional[str] = None,
) -> pd.DataFrame:
    """
    Get water demands per village.
    Pulls from historical demand dataset if available; otherwise uses population * 70 LPCD.
    """
    df = df_villages.copy()
    if HISTORICAL_DEMAND_FILE.exists():
        try:
            hist = pd.read_csv(HISTORICAL_DEMAND_FILE)
            hist["date"] = pd.to_datetime(hist["date"])
            if date_str:
                target_date = pd.to_datetime(date_str)
                day_data = hist[hist["date"] == target_date]
            else:
                max_date = hist["date"].max()
                day_data = hist[hist["date"] == max_date]

            if not day_data.empty:
                demand_map = day_data.set_index("village_id")["actual_demand_l"].to_dict()
                df["predicted_demand_l"] = df["village_id"].map(demand_map)
        except Exception:
            pass

    if "predicted_demand_l" not in df.columns or df["predicted_demand_l"].isna().any():
        df["predicted_demand_l"] = df["population"] * 70.0

    return df


# =========================================================================
# 2. NETWORK LP BUILDER (Physical Flow Conservation)
# =========================================================================

def _build_network_lp_matrices(
    df_sources: pd.DataFrame,
    df_pipelines: pd.DataFrame,
    df_villages: pd.DataFrame,
    total_supply_limit: Optional[float] = None,
) -> Tuple[List[Tuple[str, str]], List[Tuple[float, float]], np.ndarray, np.ndarray, Dict[str, int]]:
    """
    Construct flow conservation matrices (A_eq, b_eq) and edge capacity bounds
    for the complete physical pipeline graph.

    Graph Topology:
        SUPER_SOURCE -> Source Nodes -> Tanks -> Villages -> SUPER_SINK
    """
    edges: List[Tuple[str, str]] = []
    bounds: List[Tuple[float, float]] = []

    # 1. Super Source -> Sources
    total_src_cap = float(df_sources["daily_supply_capacity_l"].sum())
    src_scaling = 1.0
    if total_supply_limit is not None and total_src_cap > 0:
        src_scaling = total_supply_limit / total_src_cap

    for _, r in df_sources.iterrows():
        sid = str(r["source_id"])
        cap = float(r["daily_supply_capacity_l"]) * src_scaling
        edges.append(("SUPER_SOURCE", sid))
        bounds.append((0.0, max(0.0, cap)))

    # 2. Internal Pipelines (Source -> Tank, Tank -> Tank, Tank -> Village)
    for _, r in df_pipelines.iterrows():
        u = str(r["source_node"])
        v = str(r["destination_node"])
        cap = float(r["capacity_l_per_day"])
        edges.append((u, v))
        bounds.append((0.0, cap))

    # 3. Villages -> Super Sink
    village_edge_map: Dict[str, int] = {}
    for _, r in df_villages.iterrows():
        vid = str(r["village_id"])
        demand = float(r["predicted_demand_l"])
        e_idx = len(edges)
        edges.append((vid, "SUPER_SINK"))
        bounds.append((0.0, max(0.0, demand)))
        village_edge_map[vid] = e_idx

    # 4. Conservation constraints at all intermediate nodes
    all_nodes = set()
    for u, v in edges:
        if u != "SUPER_SOURCE":
            all_nodes.add(u)
        if v != "SUPER_SINK":
            all_nodes.add(v)

    internal_nodes = sorted(list(all_nodes))
    node_to_idx = {n: i for i, n in enumerate(internal_nodes)}

    A_eq = np.zeros((len(internal_nodes), len(edges)), dtype=float)
    for e_idx, (u, v) in enumerate(edges):
        if u in node_to_idx:
            A_eq[node_to_idx[u], e_idx] -= 1.0  # Outflow
        if v in node_to_idx:
            A_eq[node_to_idx[v], e_idx] += 1.0  # Inflow

    b_eq = np.zeros(len(internal_nodes), dtype=float)

    return edges, bounds, A_eq, b_eq, village_edge_map


# =========================================================================
# 3. ALLOCATION STRATEGIES
# =========================================================================

def solve_proportional(
    df_villages: pd.DataFrame,
    total_available_water: float,
    df_pipelines: pd.DataFrame,
) -> pd.Series:
    """
    Strategy A: Proportional Allocation.
    A_i = min(D_i, S_avail * (D_i / sum(D_k))), bounded by connecting pipe limit.
    """
    demands = df_villages["predicted_demand_l"].values
    total_demand = np.sum(demands)

    if total_demand <= 0:
        return pd.Series(0.0, index=df_villages.index)

    proportional_ratio = min(1.0, total_available_water / total_demand)
    allocations = demands * proportional_ratio

    # Bounded by local pipeline capacity
    pipe_cap_map: Dict[str, float] = {}
    for _, row in df_pipelines[df_pipelines["destination_node"].isin(df_villages["village_id"])].iterrows():
        vid = row["destination_node"]
        cap = float(row["capacity_l_per_day"])
        pipe_cap_map[vid] = pipe_cap_map.get(vid, 0.0) + cap

    bounded = []
    for vid, a in zip(df_villages["village_id"], allocations):
        limit = pipe_cap_map.get(vid, a)
        bounded.append(min(a, limit))

    return pd.Series(bounded, index=df_villages.index)


def solve_max_flow(
    df_sources: pd.DataFrame,
    df_pipelines: pd.DataFrame,
    df_villages: pd.DataFrame,
    total_available_water: Optional[float] = None,
) -> pd.Series:
    """
    Strategy B: Network Maximum Flow (Throughput Maximization).
    Objective: max sum(A_i) -> min -sum(A_i).
    """
    edges, bounds, A_eq, b_eq, v_map = _build_network_lp_matrices(
        df_sources, df_pipelines, df_villages, total_supply_limit=total_available_water
    )

    # Cost vector: -1 for all village deliveries
    c = np.zeros(len(edges), dtype=float)
    for vid, e_idx in v_map.items():
        c[e_idx] = -1.0

    res = linprog(c, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")

    alloc_map = {}
    if res.success:
        for vid, e_idx in v_map.items():
            alloc_map[vid] = max(0.0, float(res.x[e_idx]))
    else:
        for vid in df_villages["village_id"]:
            alloc_map[vid] = 0.0

    return pd.Series([alloc_map.get(vid, 0.0) for vid in df_villages["village_id"]], index=df_villages.index)


def solve_equity_aware(
    df_sources: pd.DataFrame,
    df_pipelines: pd.DataFrame,
    df_villages: pd.DataFrame,
    total_available_water: Optional[float] = None,
) -> pd.Series:
    """
    Strategy C: Equity-Aware Water Justice Optimization.
    Objective: min sum(w_i * (D_i - A_i)) <=> max sum(w_i * A_i).
    w_i = priority_score from Phase 18.
    """
    edges, bounds, A_eq, b_eq, v_map = _build_network_lp_matrices(
        df_sources, df_pipelines, df_villages, total_supply_limit=total_available_water
    )

    p_scores = df_villages.set_index("village_id")["priority_score"].to_dict()

    # Cost vector: -w_i for each village delivery (scaled so highest priority has steep preference)
    c = np.zeros(len(edges), dtype=float)
    for vid, e_idx in v_map.items():
        weight = p_scores.get(vid, 0.5)
        # Weight exponentiation sharpens justice distinction under scarce regimes
        c[e_idx] = -(float(weight) ** 1.5)

    res = linprog(c, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")

    alloc_map = {}
    if res.success:
        for vid, e_idx in v_map.items():
            alloc_map[vid] = max(0.0, float(res.x[e_idx]))
    else:
        for vid in df_villages["village_id"]:
            alloc_map[vid] = 0.0

    return pd.Series([alloc_map.get(vid, 0.0) for vid in df_villages["village_id"]], index=df_villages.index)


# =========================================================================
# 4. BENCHMARK COMPARISON SUITE (Phase 20 Scorecard)
# =========================================================================

def run_allocation_comparison(
    scarcity_factor: float = 0.70,
    min_service_threshold: float = 0.70,
    date_str: Optional[str] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Execute benchmark across all three strategies and build the Phase 20 scorecard.

    Args:
        scarcity_factor: Available water supply relative to total demand (0.70 = 30% shortage).
        min_service_threshold: Minimum service satisfaction threshold (default 70%).
        date_str: Optional historical date to load demands.

    Returns:
        comparison_table: Research comparison table with all Phase 20 metrics.
        detailed_table: Per-village breakdown across the three strategies.
    """
    df_sources, df_pipelines, df_villages = load_network_data()
    df_villages = get_village_demands(df_villages, date_str=date_str)

    total_demand = float(df_villages["predicted_demand_l"].sum())
    total_available_water = total_demand * scarcity_factor

    # 1. Run all 3 strategies
    alloc_prop = solve_proportional(df_villages, total_available_water, df_pipelines)
    alloc_max = solve_max_flow(df_sources, df_pipelines, df_villages, total_available_water=total_available_water)
    alloc_eq = solve_equity_aware(df_sources, df_pipelines, df_villages, total_available_water=total_available_water)

    # 2. Detailed village breakdown table
    detailed_df = df_villages[[
        "village_id", "village_name", "population", "vulnerability_index",
        "historical_shortage", "priority_score", "priority_rank", "predicted_demand_l"
    ]].copy()

    detailed_df["alloc_proportional_l"] = alloc_prop.round(1)
    detailed_df["alloc_max_flow_l"] = alloc_max.round(1)
    detailed_df["alloc_equity_aware_l"] = alloc_eq.round(1)

    demands = detailed_df["predicted_demand_l"].values
    detailed_df["sat_proportional"] = np.clip(np.where(demands > 0, alloc_prop / demands, 1.0), 0.0, 1.0).round(4)
    detailed_df["sat_max_flow"] = np.clip(np.where(demands > 0, alloc_max / demands, 1.0), 0.0, 1.0).round(4)
    detailed_df["sat_equity_aware"] = np.clip(np.where(demands > 0, alloc_eq / demands, 1.0), 0.0, 1.0).round(4)

    # 3. Evaluate Metrics for each strategy
    strategies = {
        "Proportional": alloc_prop,
        "Max-Flow": alloc_max,
        "Equity-Aware": alloc_eq,
    }

    weights = df_villages["priority_score"].values
    summary_dict: Dict[str, Dict[str, str]] = {}

    for strat_name, alloc in strategies.items():
        sh = np.maximum(0.0, demands - alloc)
        sat = np.clip(np.where(demands > 0, alloc / demands, 1.0), 0.0, 1.0)

        tot_alloc = float(np.sum(alloc))
        fulfillment = (tot_alloc / total_demand) * 100.0 if total_demand > 0 else 100.0
        avg_sh = average_shortage(sh)
        max_sh = maximum_shortage(sh)
        w_sh = weighted_shortage(sh, weights)
        avg_sat = average_satisfaction_ratio(sat) * 100.0
        jain = jains_fairness_index(sat)
        gini = gini_coefficient(sat)
        hoover = hoover_index(sat)
        min_svc = percentage_minimum_service_level(sat, threshold=min_service_threshold)

        summary_dict[strat_name] = {
            "Total Water Delivered (L)": f"{tot_alloc:,.0f}",
            "Fulfillment Rate (%)": f"{fulfillment:.2f}%",
            "Average Shortage (L)": f"{avg_sh:,.0f}",
            "Maximum Shortage (L)": f"{max_sh:,.0f}",
            "Weighted Shortage (L)": f"{w_sh:,.0f}",
            "Average Satisfaction (%)": f"{avg_sat:.2f}%",
            "Jain's Fairness Index": f"{jain:.4f}",
            "Gini Coefficient": f"{gini:.4f}",
            "Hoover (Robin Hood) Index": f"{hoover:.4f}",
            f"% Villages >= {int(min_service_threshold*100)}% Service": f"{min_svc:.1f}%",
        }

    # Format into DataFrame with Metric as index
    summary_df = pd.DataFrame(summary_dict)
    summary_df.index.name = "Metric"

    # Export to outputs directory
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(OUTPUTS_DIR / "allocation_comparison.csv")
    detailed_df.to_csv(OUTPUTS_DIR / "village_allocations_compared.csv", index=False)

    with open(OUTPUTS_DIR / "allocation_comparison.json", "w") as f:
        json.dump(summary_df.to_dict(), f, indent=4)

    return summary_df, detailed_df


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print(" JAL DHARMA AI - PHASE 20: ALLOCATION METHOD COMPARISON")
    print("=" * 80)
    print(" Simulating Water Scarcity: Total Supply = 70% of Predicted Total Demand\n")

    summary_table, detailed_table = run_allocation_comparison(scarcity_factor=0.70)

    print("-" * 80)
    print(" COMPARATIVE RESEARCH SCORECARD (Phase 20 Requirements):")
    print("-" * 80)
    print(summary_table.to_string())
    print("-" * 80)

    print("\n[INFO] Top 5 High-Priority Villages Allocation Comparison:")
    top_5_cols = [
        "village_id", "village_name", "priority_rank", "predicted_demand_l",
        "sat_prop", "sat_max", "sat_eq"
    ]
    disp_df = detailed_table.head(5).copy()
    disp_df["sat_prop"] = (disp_df["sat_proportional"] * 100).map("{:.1f}%".format)
    disp_df["sat_max"] = (disp_df["sat_max_flow"] * 100).map("{:.1f}%".format)
    disp_df["sat_eq"] = (disp_df["sat_equity_aware"] * 100).map("{:.1f}%".format)
    print(disp_df[top_5_cols].to_string(index=False))

    print("\n" + "=" * 80)
    print(" PHASE 20 COMPARISON COMPLETED & RESULTS EXPORTED")
    print("=" * 80)
