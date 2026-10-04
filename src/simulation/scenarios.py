"""
Jal Dharma AI - Scenario Simulation & Stress Testing Engine
===========================================================
Simulates climate shocks, infrastructure failures, and demand surges
to evaluate water network resilience and equity protection.

Supported Scenarios:
--------------------
1. Baseline Normal: Full reservoir supply, normal demand, all pipelines operational.
2. Moderate Drought: 30% reduction in water availability (70% supply).
3. Severe Summer Heatwave: 50% supply reduction + demand surge due to temperature.
4. Transmission Main Breakdown: Major feeder pipe (e.g., PIPE_001) failure.
5. Secondary Feeder Burst: Intermediate link failure (e.g., PIPE_003) under heatwave.
6. Festival / Population Surge: 25% rapid demand influx across villages.
7. Compound Climate Disaster: Extreme drought (35% supply) + main pipeline failure.

For each scenario, the engine calculates:
- Village Allocations, Shortages, and Satisfaction Ratios
- Pipeline-level Flows, Capacities, and Utilization Rates (%)
- Comprehensive Water Justice Metrics (Jain's Index, Gini, Weighted Shortage)

Outputs feed PostgreSQL storage (Phase 21) and the GIS Dashboard (Phase 22 & 23).

Run with:
    python -m src.simulation.scenarios
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
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
OUTPUTS_DIR = BASE_DIR / "outputs" / "simulation"

SOURCES_FILE = DATA_DIR / "4_water_source_dataset.csv"
PIPELINES_FILE = DATA_DIR / "5_pipeline_water_network_dataset.csv"
VILLAGES_FILE = DATA_DIR / "1_village_dataset.csv"
SCENARIOS_FILE = DATA_DIR / "11_scenario_simulation_dataset.csv"


# =========================================================================
# 1. SCENARIO DATA STRUCTURE
# =========================================================================

@dataclass
class SimulationScenario:
    scenario_id: str
    scenario_name: str
    water_availability_percent: float = 100.0  # e.g., 70.0 means 30% drought reduction
    population_change_percent: float = 0.0     # e.g., +25.0 means 25% surge in population/demand
    rainfall_change_percent: float = 0.0       # e.g., -30.0 for drought
    failed_pipeline_ids: List[str] = field(default_factory=list)
    strategy: str = "Equity-Aware"             # "Equity-Aware", "Proportional", or "Max-Flow"
    description: str = ""


def get_predefined_scenarios() -> List[SimulationScenario]:
    """
    Load predefined stress-testing scenarios.
    Pulls from synthetic dataset CSV or provides standard canonical benchmarks.
    """
    scenarios: List[SimulationScenario] = []

    if SCENARIOS_FILE.exists():
        try:
            df_scn = pd.read_csv(SCENARIOS_FILE)
            for _, r in df_scn.iterrows():
                sid = str(r["scenario_id"])
                sname = str(r["scenario_name"])
                water_pct = float(r.get("water_availability_percent", 100.0))
                pop_pct = float(r.get("population_change_percent", 0.0))
                rain_pct = float(r.get("rainfall_change_percent", 0.0))

                failed_pipes = []
                pipe_field = str(r.get("failed_pipeline_id", "")).strip()
                if pipe_field and pipe_field.lower() not in ["none", "nan", ""]:
                    failed_pipes = [p.strip() for p in pipe_field.split(",") if p.strip()]

                scenarios.append(SimulationScenario(
                    scenario_id=sid,
                    scenario_name=sname,
                    water_availability_percent=water_pct,
                    population_change_percent=pop_pct,
                    rainfall_change_percent=rain_pct,
                    failed_pipeline_ids=failed_pipes,
                    strategy="Equity-Aware",
                    description=f"{sname} (Supply: {water_pct}%, Demand shift: {pop_pct:+g}%)",
                ))
            if scenarios:
                return scenarios
        except Exception:
            pass

    # Standard Fallback Scenarios
    return [
        SimulationScenario(
            scenario_id="SCN_01",
            scenario_name="Normal Baseline Conditions",
            water_availability_percent=100.0,
            population_change_percent=0.0,
            rainfall_change_percent=0.0,
            failed_pipeline_ids=[],
            description="Baseline operating state: 100% water availability, no pipe failures.",
        ),
        SimulationScenario(
            scenario_id="SCN_02",
            scenario_name="Moderate Drought / Late Monsoon",
            water_availability_percent=70.0,
            population_change_percent=2.0,
            rainfall_change_percent=-30.0,
            failed_pipeline_ids=[],
            description="30% water deficit caused by deficient rainfall.",
        ),
        SimulationScenario(
            scenario_id="SCN_03",
            scenario_name="Severe Summer Heatwave & Drought",
            water_availability_percent=50.0,
            population_change_percent=5.0,
            rainfall_change_percent=-55.0,
            failed_pipeline_ids=[],
            description="Extreme 50% drought combined with heatwave-induced demand spike.",
        ),
        SimulationScenario(
            scenario_id="SCN_04",
            scenario_name="Critical Transmission Main Failure (Dam Feeder)",
            water_availability_percent=85.0,
            population_change_percent=0.0,
            rainfall_change_percent=0.0,
            failed_pipeline_ids=["PIPE_001"],
            description="Primary Dam transmission main PIPE_001 is broken; network must reroute.",
        ),
        SimulationScenario(
            scenario_id="SCN_05",
            scenario_name="Secondary Feeder Burst under Heatwave",
            water_availability_percent=60.0,
            population_change_percent=3.0,
            rainfall_change_percent=-40.0,
            failed_pipeline_ids=["PIPE_003"],
            description="Feeder PIPE_003 ruptured during peak summer shortage.",
        ),
        SimulationScenario(
            scenario_id="SCN_06",
            scenario_name="Mass Festival Influx / Peak Population Demand",
            water_availability_percent=90.0,
            population_change_percent=25.0,
            rainfall_change_percent=-10.0,
            failed_pipeline_ids=[],
            description="25% sudden population surge during regional pilgrimage/festival.",
        ),
        SimulationScenario(
            scenario_id="SCN_07",
            scenario_name="Compound Climate Disaster",
            water_availability_percent=35.0,
            population_change_percent=4.0,
            rainfall_change_percent=-70.0,
            failed_pipeline_ids=["PIPE_005"],
            description="Extreme catastrophic drought (35% supply) combined with aquifer pipe failure.",
        ),
    ]


# =========================================================================
# 2. SCENARIO SIMULATION EXECUTION
# =========================================================================

def simulate_scenario(
    scenario: SimulationScenario,
    df_sources: Optional[pd.DataFrame] = None,
    df_pipelines: Optional[pd.DataFrame] = None,
    df_villages: Optional[pd.DataFrame] = None,
) -> Dict[str, Any]:
    """
    Execute a single what-if scenario simulation.

    Steps:
        1. Scale water sources by water_availability_percent
        2. Scale village demands by population_change_percent
        3. Disable failed pipelines (set capacity to 0.0)
        4. Solve network optimization (LP using HiGHS)
        5. Compute pipeline utilization & bottlenecks
        6. Compute comprehensive Phase 19 Water Justice metrics
    """
    if df_sources is None:
        df_sources = pd.read_csv(SOURCES_FILE)
    if df_pipelines is None:
        df_pipelines = pd.read_csv(PIPELINES_FILE)
    if df_villages is None:
        df_villages = calculate_priority_scores(pd.read_csv(VILLAGES_FILE))

    sources_sim = df_sources.copy()
    pipes_sim = df_pipelines.copy()
    villages_sim = df_villages.copy()

    # 1. Scale Village Demands first
    pop_multiplier = 1.0 + (scenario.population_change_percent / 100.0)
    temp_demand_boost = 1.0 + max(0.0, -scenario.rainfall_change_percent * 0.002)

    base_demand = villages_sim["population"] * 70.0
    villages_sim["predicted_demand_l"] = base_demand * pop_multiplier * temp_demand_boost
    total_sim_demand = float(villages_sim["predicted_demand_l"].sum())

    # 2. Scale Source Deliverability based on scenario water availability
    # When water_availability_percent < 100, total source deliverability is throttled to that fraction of system demand
    avail_ratio = max(0.05, scenario.water_availability_percent / 100.0)
    if avail_ratio < 1.0:
        total_target_supply = total_sim_demand * avail_ratio
        orig_total_cap = float(sources_sim["daily_supply_capacity_l"].sum())
        scale_factor = total_target_supply / orig_total_cap if orig_total_cap > 0 else avail_ratio
        sources_sim["simulated_capacity_l"] = sources_sim["daily_supply_capacity_l"] * scale_factor
    else:
        sources_sim["simulated_capacity_l"] = sources_sim["daily_supply_capacity_l"].copy()

    # 3. Disable Failed Pipelines
    pipes_sim["simulated_capacity_l"] = pipes_sim["capacity_l_per_day"].astype(float)
    failed_set = set(scenario.failed_pipeline_ids)
    pipes_sim["pipe_status"] = np.where(
        pipes_sim["pipeline_id"].isin(failed_set), "Failed", "Operational"
    )
    pipes_sim.loc[pipes_sim["pipeline_id"].isin(failed_set), "simulated_capacity_l"] = 0.0

    # 4. Construct Network LP Formulation
    edges: List[Tuple[str, str]] = []
    bounds: List[Tuple[float, float]] = []
    edge_meta: List[Dict[str, Any]] = []

    # Super Source -> Sources
    for _, r in sources_sim.iterrows():
        sid = str(r["source_id"])
        cap = float(r["simulated_capacity_l"])
        edges.append(("SUPER_SOURCE", sid))
        bounds.append((0.0, cap))
        edge_meta.append({"type": "source", "id": sid})

    # Pipelines (Sources -> Tanks, Tanks -> Tanks, Tanks -> Villages)
    pipe_edge_indices: Dict[str, int] = {}
    for idx, r in pipes_sim.iterrows():
        pid = str(r["pipeline_id"])
        u = str(r["source_node"])
        v = str(r["destination_node"])
        cap = float(r["simulated_capacity_l"])
        e_idx = len(edges)
        edges.append((u, v))
        bounds.append((0.0, cap))
        edge_meta.append({"type": "pipeline", "id": pid, "cap": float(r["capacity_l_per_day"])})
        pipe_edge_indices[pid] = e_idx

    # Villages -> Super Sink
    village_edge_indices: Dict[str, int] = {}
    for _, r in villages_sim.iterrows():
        vid = str(r["village_id"])
        dem = float(r["predicted_demand_l"])
        e_idx = len(edges)
        edges.append((vid, "SUPER_SINK"))
        bounds.append((0.0, dem))
        edge_meta.append({"type": "village", "id": vid})
        village_edge_indices[vid] = e_idx

    # Conservation Equations at intermediate nodes
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

    # 5. Objective Vector (Based on Strategy)
    c = np.zeros(len(edges), dtype=float)
    p_weights = villages_sim.set_index("village_id")["priority_score"].to_dict()

    if scenario.strategy == "Equity-Aware":
        # Maximize weighted allocation: -w_i
        for vid, e_idx in village_edge_indices.items():
            w = float(p_weights.get(vid, 0.5))
            c[e_idx] = -(w ** 1.5)
    elif scenario.strategy == "Max-Flow":
        # Maximize gross throughput without weights
        for vid, e_idx in village_edge_indices.items():
            c[e_idx] = -1.0
    else:  # Proportional objective approximation
        for vid, e_idx in village_edge_indices.items():
            c[e_idx] = -1.0

    # Solve using HiGHS
    res = linprog(c, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")

    # 6. Extract Village Allocations
    allocations: Dict[str, float] = {}
    if res.success:
        for vid, e_idx in village_edge_indices.items():
            allocations[vid] = max(0.0, float(res.x[e_idx]))
    else:
        for vid in villages_sim["village_id"]:
            allocations[vid] = 0.0

    # Build Village Output DataFrame
    v_results = villages_sim[[
        "village_id", "village_name", "population", "vulnerability_index",
        "historical_shortage", "priority_score", "priority_rank", "predicted_demand_l"
    ]].copy()

    v_results["allocated_water_l"] = [allocations.get(vid, 0.0) for vid in v_results["village_id"]]
    v_results["shortage_l"] = np.maximum(0.0, v_results["predicted_demand_l"] - v_results["allocated_water_l"])

    demands = v_results["predicted_demand_l"].values
    allocs = v_results["allocated_water_l"].values
    v_results["satisfaction_ratio"] = np.clip(np.where(demands > 0, allocs / demands, 1.0), 0.0, 1.0).round(4)
    v_results["scenario_id"] = scenario.scenario_id
    v_results["scenario_name"] = scenario.scenario_name

    # 7. Extract Pipeline Flows & Utilizations (Phase 21 Schema)
    pipe_rows = []
    for pid, e_idx in pipe_edge_indices.items():
        orig_cap = float(pipes_sim.loc[pipes_sim["pipeline_id"] == pid, "capacity_l_per_day"].iloc[0])
        sim_cap = float(pipes_sim.loc[pipes_sim["pipeline_id"] == pid, "simulated_capacity_l"].iloc[0])
        p_status = pipes_sim.loc[pipes_sim["pipeline_id"] == pid, "pipe_status"].iloc[0]

        actual_flow = max(0.0, float(res.x[e_idx])) if res.success else 0.0
        utilization_pct = (actual_flow / orig_cap * 100.0) if orig_cap > 0 else 0.0

        if p_status == "Failed":
            util_status = "Failed / Ruptured"
        elif utilization_pct >= 99.0:
            util_status = "Critical Bottleneck (100%)"
        elif utilization_pct >= 80.0:
            util_status = "High Utilization"
        else:
            util_status = "Normal Flow"

        pipe_rows.append({
            "pipeline_id": pid,
            "scenario_id": scenario.scenario_id,
            "flow_l_per_day": round(actual_flow, 1),
            "design_capacity_l": orig_cap,
            "effective_capacity_l": sim_cap,
            "utilization_percent": round(utilization_pct, 2),
            "network_status": util_status,
        })

    p_results = pd.DataFrame(pipe_rows)

    # 8. Compute Phase 19 Fairness Metrics
    total_dem = float(np.sum(demands))
    total_alloc = float(np.sum(allocs))
    total_short = float(np.sum(v_results["shortage_l"]))
    weights = v_results["priority_score"].values
    sat_ratios = v_results["satisfaction_ratio"].values
    shortages = v_results["shortage_l"].values

    avg_sat = average_satisfaction_ratio(sat_ratios) * 100.0
    jain = jains_fairness_index(sat_ratios)
    gini = gini_coefficient(sat_ratios)
    hoover = hoover_index(sat_ratios)
    min_svc = percentage_minimum_service_level(sat_ratios, threshold=0.70)
    w_short = weighted_shortage(shortages, weights)

    metrics_summary = {
        "scenario_id": scenario.scenario_id,
        "scenario_name": scenario.scenario_name,
        "total_water_available_l": round(float(sources_sim["simulated_capacity_l"].sum()), 0),
        "total_demand_l": round(total_dem, 0),
        "total_allocated_l": round(total_alloc, 0),
        "total_shortage_l": round(total_short, 0),
        "fulfillment_rate_pct": round((total_alloc / total_dem * 100.0) if total_dem > 0 else 100.0, 2),
        "average_satisfaction_pct": round(avg_sat, 2),
        "maximum_shortage_l": round(maximum_shortage(shortages), 0),
        "average_shortage_l": round(average_shortage(shortages), 0),
        "weighted_shortage_l": round(w_short, 0),
        "jains_fairness_index": round(jain, 4),
        "gini_coefficient": round(gini, 4),
        "hoover_index": round(hoover, 4),
        "villages_meeting_min_service_pct": round(min_svc, 1),
        "failed_pipelines_count": len(scenario.failed_pipeline_ids),
        "bottleneck_pipelines_count": int((p_results["utilization_percent"] >= 99.0).sum()),
    }

    return {
        "scenario": scenario,
        "metrics": metrics_summary,
        "village_allocations": v_results,
        "pipeline_flows": p_results,
    }


def run_all_scenarios() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Execute all predefined scenarios and produce consolidated results.

    Returns:
        scenario_scorecard_df: Comparative metrics across all scenarios.
        all_allocations_df: Detailed village allocations across all scenarios (Phase 21 format).
        all_pipeline_flows_df: Detailed pipeline flow and utilization across all scenarios.
    """
    scenarios = get_predefined_scenarios()

    scorecard_rows: List[Dict[str, Any]] = []
    alloc_dfs: List[pd.DataFrame] = []
    pipe_dfs: List[pd.DataFrame] = []

    for scn in scenarios:
        res = simulate_scenario(scn)
        scorecard_rows.append(res["metrics"])
        alloc_dfs.append(res["village_allocations"])
        pipe_dfs.append(res["pipeline_flows"])

    scorecard_df = pd.DataFrame(scorecard_rows)
    all_alloc_df = pd.concat(alloc_dfs, ignore_index=True)
    all_pipe_df = pd.concat(pipe_dfs, ignore_index=True)

    # Export outputs to outputs/simulation/
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    scorecard_df.to_csv(OUTPUTS_DIR / "scenario_scorecard.csv", index=False)
    all_alloc_df.to_csv(OUTPUTS_DIR / "scenario_village_allocations.csv", index=False)
    all_pipe_df.to_csv(OUTPUTS_DIR / "scenario_pipeline_flows.csv", index=False)

    return scorecard_df, all_alloc_df, all_pipe_df


if __name__ == "__main__":
    print("\n" + "=" * 85)
    print(" JAL DHARMA AI - PHASE 21: SCENARIO SIMULATION & STRESS TESTING SUITE")
    print("=" * 85)

    scorecard, allocs, pipes = run_all_scenarios()

    print("\n" + "-" * 85)
    print(" STRESS-TEST SCENARIOS COMPARATIVE SCORECARD (Phase 21 Results)")
    print("-" * 85)
    display_cols = [
        "scenario_id",
        "scenario_name",
        "fulfillment_rate_pct",
        "total_shortage_l",
        "average_satisfaction_pct",
        "weighted_shortage_l",
        "jains_fairness_index",
        "gini_coefficient",
        "villages_meeting_min_service_pct",
    ]
    print(scorecard[display_cols].to_string(index=False))
    print("-" * 85)

    print("\n[INFO] Sample Pipeline Bottlenecks Detected during SCN_04 (Pipeline Failure):")
    scn4_pipes = pipes[pipes["scenario_id"] == "SCN_04"]
    bottlenecks = scn4_pipes[scn4_pipes["network_status"].str.contains("Bottleneck|Failed")][
        ["pipeline_id", "flow_l_per_day", "design_capacity_l", "utilization_percent", "network_status"]
    ]
    print(bottlenecks.head(6).to_string(index=False))

    print("\n" + "=" * 85)
    print(" ALL SCENARIOS SIMULATED & EXPORTED TO outputs/simulation/")
    print("=" * 85)
