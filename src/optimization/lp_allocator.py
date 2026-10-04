"""
Jal Dharma AI
Phase 16: Linear Programming (LP) Water Allocation
===================================================
Steps 1 to 5:
  1. Load network inputs, source availability (Phase 15), and predicted demands.
  2. Formulate LP optimization model with pipeline, tank, and source bounds.
  3. Add flow conservation, pipe capacity, and source deliverable constraints.
  4. Solve LP model using SciPy HiGHS solver.
  5. Extract allocation results, shortages, and pipeline bottleneck diagnostics.
"""

import sys
from pathlib import Path

# Add project root to sys.path so the file can be run directly or as a module
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np
from scipy.optimize import linprog
from sqlalchemy import text

from src.database.connection import get_engine
from src.optimization.water_availability import (
    load_sources,
    load_availability_history,
    calculate_source_availability,
    load_predicted_demand,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "synthetic"


# =====================================================================
# STEP 1: LOAD NETWORK INPUTS & CONSTRAINTS
# =====================================================================

def load_pipelines(engine=None):
    """Load operational pipelines with capacities from PostgreSQL or CSV fallback."""
    query = text("""
        SELECT
            pipeline_id,
            source_node,
            destination_node,
            capacity_l_per_day,
            status
        FROM pipelines
        WHERE LOWER(status) IN ('operational', 'working', '1')
          AND capacity_l_per_day IS NOT NULL
          AND capacity_l_per_day > 0
        ORDER BY pipeline_id
    """)
    if engine is not None:
        try:
            with engine.connect() as conn:
                df = pd.read_sql(query, conn)
            if not df.empty:
                return df
        except Exception as e:
            print(f"[WARN] Failed to load pipelines from DB ({e}). Falling back to CSV.")

    csv_path = DATA_DIR / "5_pipeline_water_network_dataset.csv"
    df = pd.read_csv(csv_path)
    df = df[df["status"].astype(str).str.lower().isin(["operational", "working", "1"])].copy()
    return df[["pipeline_id", "source_node", "destination_node", "capacity_l_per_day", "status"]]


def load_villages_meta(engine=None):
    """Load village names, populations, and vulnerability indices."""
    query = text("SELECT village_id, village_name, population, vulnerability_index FROM villages")
    if engine is not None:
        try:
            with engine.connect() as conn:
                df = pd.read_sql(query, conn)
            if not df.empty:
                return df
        except Exception as e:
            print(f"[WARN] Failed to load villages from DB ({e}). Falling back to CSV.")

    csv_path = DATA_DIR / "1_village_dataset.csv"
    df = pd.read_csv(csv_path)
    return df[["village_id", "village_name", "population", "vulnerability_index"]]


def load_all_inputs(engine=None):
    """Gather all inputs needed for the LP model."""
    if engine is None:
        engine = get_engine()

    # 1. Sources & Daily Deliverable Limits from Phase 15
    sources_df = load_sources(engine)
    history_df = load_availability_history(engine)
    avail_df = calculate_source_availability(sources_df, history_df)

    # 2. Predicted Demands
    demand_df = load_predicted_demand(engine)

    # 3. Pipelines
    pipelines_df = load_pipelines(engine)

    # 4. Village Metadata
    villages_df = load_villages_meta(engine)

    # Merge demand with village metadata
    demands = demand_df.merge(villages_df, on="village_id", how="left")
    demands["village_name"] = demands["village_name"].fillna(demands["village_id"])
    demands["population"] = demands["population"].fillna(0)
    demands["vulnerability_index"] = demands["vulnerability_index"].fillna(0.5)

    return avail_df, demands, pipelines_df


# =====================================================================
# STEP 2, 3, 4: FORMULATE & SOLVE LP MODEL (HiGHS Solver)
# =====================================================================

def solve_water_allocation_lp(avail_df, demands_df, pipelines_df, priority_weights=None):
    """
    Formulate and solve the Water Allocation LP problem using SciPy HiGHS.
    
    Decision variables:
      - x[0 ... E-1]: Flow through each pipeline e (0 <= flow <= capacity)
      - x[E ... E+V-1]: Water allocated to each village i (0 <= alloc <= demand)
    
    Objective:
      Maximize sum(w_i * allocated_i) => Minimize -sum(w_i * allocated_i)
    
    Constraints:
      1. Source capacity: sum(outflow from source s) <= deliverable_l_per_day
      2. Tank conservation: sum(inflow to tank t) - sum(outflow from tank t) == 0
      3. Village delivery: sum(inflow to village i) - allocated_i == 0
    """
    pipe_list = pipelines_df.to_dict("records")
    village_list = demands_df.to_dict("records")

    E = len(pipe_list)
    V = len(village_list)
    num_vars = E + V

    pipe_index = {p["pipeline_id"]: idx for idx, p in enumerate(pipe_list)}
    village_index = {v["village_id"]: (E + idx) for idx, v in enumerate(village_list)}

    # Bounds on variables
    bounds = []
    # Pipeline bounds: [0, capacity]
    for p in pipe_list:
        bounds.append((0.0, float(p["capacity_l_per_day"])))

    # Village allocation bounds: [0, demand]
    for v in village_list:
        d = float(v.get("demand_upper_l") or v.get("demand_point_l") or 0.0)
        bounds.append((0.0, d))

    # Objective coefficients c (minimizing c^T x)
    c = np.zeros(num_vars)
    for idx, v in enumerate(village_list):
        vid = v["village_id"]
        vuln = float(v.get("vulnerability_index", 0.5) or 0.5)
        if priority_weights and vid in priority_weights:
            w = float(priority_weights[vid])
        else:
            w = 1.0 + vuln  # base 1.0 + vulnerability boost

        var_idx = E + idx
        c[var_idx] = -w  # negative for maximization

    # -----------------------------------------------------------------
    # Constraints Construction
    # -----------------------------------------------------------------
    A_ub = []
    b_ub = []

    A_eq = []
    b_eq = []

    # 1. Source Capacity Limits: sum(outflows from s) <= deliverable_l_per_day
    for _, src in avail_df.iterrows():
        sid = str(src["source_id"]).strip()
        max_supply = float(src["deliverable_l_per_day"])

        row = np.zeros(num_vars)
        has_outflow = False
        for p_idx, p in enumerate(pipe_list):
            if str(p["source_node"]).strip() == sid:
                row[p_idx] = 1.0
                has_outflow = True

        if has_outflow:
            A_ub.append(row)
            b_ub.append(max_supply)

    # Identify tanks / intermediate reservoirs
    all_sources = set(avail_df["source_id"].astype(str).str.strip())
    all_villages = set(demands_df["village_id"].astype(str).str.strip())
    all_nodes = set(pipelines_df["source_node"].astype(str).str.strip()).union(
        set(pipelines_df["destination_node"].astype(str).str.strip())
    )
    tanks = all_nodes - all_sources - all_villages

    # 2. Tank Conservation: sum(inflow to tank) - sum(outflow from tank) == 0
    for tank_id in sorted(tanks):
        row = np.zeros(num_vars)
        has_edges = False
        for p_idx, p in enumerate(pipe_list):
            src_n = str(p["source_node"]).strip()
            dst_n = str(p["destination_node"]).strip()
            if dst_n == tank_id:
                row[p_idx] += 1.0
                has_edges = True
            elif src_n == tank_id:
                row[p_idx] -= 1.0
                has_edges = True

        if has_edges:
            A_eq.append(row)
            b_eq.append(0.0)

    # 3. Village Delivery: sum(inflow to village i) - allocated_i == 0
    for v_idx, v in enumerate(village_list):
        vid = str(v["village_id"]).strip()
        row = np.zeros(num_vars)
        for p_idx, p in enumerate(pipe_list):
            if str(p["destination_node"]).strip() == vid:
                row[p_idx] = 1.0

        alloc_idx = E + v_idx
        row[alloc_idx] = -1.0  # sum(inflow) - allocated_i = 0
        A_eq.append(row)
        b_eq.append(0.0)

    A_ub = np.array(A_ub) if A_ub else None
    b_ub = np.array(b_ub) if b_ub else None
    A_eq = np.array(A_eq) if A_eq else None
    b_eq = np.array(b_eq) if b_eq else None

    # Solve using the HiGHS solver
    res = linprog(
        c=c,
        A_ub=A_ub,
        b_ub=b_ub,
        A_eq=A_eq,
        b_eq=b_eq,
        bounds=bounds,
        method="highs",
    )

    if not res.success:
        raise RuntimeError(f"LP optimization failed: {res.message}")

    solution_x = res.x
    status_str = "Optimal" if res.success else "Infeasible"

    return status_str, solution_x, pipe_list, village_list, E, V


# =====================================================================
# STEP 5: EXTRACT RESULTS, SHORTAGES & BOTTLENECK ANALYSIS
# =====================================================================

def extract_allocation_results(solution_x, pipe_list, village_list, E, V):
    """Process solution vector into village allocations and pipeline flow reports."""
    # 1. Village Allocations
    village_records = []
    for idx, v in enumerate(village_list):
        vid = v["village_id"]
        vname = v.get("village_name", vid)
        pop = v.get("population", 0)
        vuln = v.get("vulnerability_index", 0.5)
        dem = float(v.get("demand_upper_l") or v.get("demand_point_l") or 0.0)

        alloc_idx = E + idx
        alloc_val = max(0.0, float(solution_x[alloc_idx]))
        shortage = max(0.0, dem - alloc_val)
        sat_pct = (alloc_val / dem * 100.0) if dem > 0 else 100.0

        village_records.append({
            "village_id": vid,
            "village_name": vname,
            "population": int(pop),
            "vulnerability_index": round(float(vuln), 2),
            "predicted_demand_l": round(dem, 1),
            "allocated_water_l": round(alloc_val, 1),
            "shortage_l": round(shortage, 1),
            "satisfaction_pct": round(sat_pct, 2),
        })

    allocations_df = pd.DataFrame(village_records).sort_values("village_id").reset_index(drop=True)

    # 2. Pipeline Flows & Bottleneck Diagnostic
    pipe_records = []
    for idx, p in enumerate(pipe_list):
        flow_val = max(0.0, float(solution_x[idx]))
        cap = float(p["capacity_l_per_day"])
        util_pct = (flow_val / cap * 100.0) if cap > 0 else 0.0
        is_bottleneck = util_pct >= 99.0

        pipe_records.append({
            "pipeline_id": p["pipeline_id"],
            "source_node": p["source_node"],
            "destination_node": p["destination_node"],
            "capacity_l_per_day": cap,
            "flow_l_per_day": round(flow_val, 1),
            "utilization_pct": round(util_pct, 2),
            "is_bottleneck": is_bottleneck,
        })

    flows_df = pd.DataFrame(pipe_records).sort_values("utilization_pct", ascending=False).reset_index(drop=True)

    return allocations_df, flows_df


def print_phase16_summary(status, allocations_df, flows_df, avail_df):
    """Pretty-print Phase 16 execution and analysis results."""
    total_demand = allocations_df["predicted_demand_l"].sum()
    total_allocated = allocations_df["allocated_water_l"].sum()
    total_shortage = allocations_df["shortage_l"].sum()
    avg_satisfaction = (total_allocated / total_demand * 100.0) if total_demand > 0 else 100.0
    total_source_avail = avail_df["deliverable_l_per_day"].sum()

    print("\n" + "=" * 65)
    print("PHASE 16 - LINEAR PROGRAMMING (LP) WATER ALLOCATION REPORT")
    print("=" * 65)
    print(f"Solver Status            : {status}")
    print(f"Total Water Available    : {total_source_avail:>15,.0f} L/day ({total_source_avail/1e6:.2f} ML/day)")
    print(f"Total Predicted Demand   : {total_demand:>15,.0f} L/day ({total_demand/1e6:.2f} ML/day)")
    print(f"Total Water Allocated    : {total_allocated:>15,.0f} L/day ({total_allocated/1e6:.2f} ML/day)")
    print(f"Total Network Shortage   : {total_shortage:>15,.0f} L/day ({total_shortage/1e6:.2f} ML/day)")
    print(f"Overall Satisfaction     : {avg_satisfaction:>14.2f}%")
    print("=" * 65)

    print("\n--- SAMPLE VILLAGE ALLOCATIONS (Top 10 Villages) ---")
    cols_to_show = ["village_id", "village_name", "predicted_demand_l", "allocated_water_l", "shortage_l", "satisfaction_pct"]
    print(allocations_df[cols_to_show].head(10).to_string(index=False))

    print("\n--- PIPELINE UTILIZATION & BOTTLENECK ANALYSIS ---")
    bottlenecks = flows_df[flows_df["is_bottleneck"]]
    print(f"Pipelines at or near 100% capacity (Bottlenecks): {len(bottlenecks)}")
    if not bottlenecks.empty:
        print(bottlenecks[["pipeline_id", "source_node", "destination_node", "capacity_l_per_day", "flow_l_per_day", "utilization_pct"]].to_string(index=False))
    else:
        print("No pipelines are completely saturated. Top 5 most utilized pipelines:")
        print(flows_df[["pipeline_id", "source_node", "destination_node", "capacity_l_per_day", "flow_l_per_day", "utilization_pct"]].head(5).to_string(index=False))

    print("\n[SUCCESS] Phase 16 Complete: LP Problem formulated, solved, analyzed & stored successfully.")


# =====================================================================
# STEP 6: STORE ALLOCATIONS IN POSTGRESQL
# =====================================================================

def store_allocations(engine, allocations_df, allocation_date=None, strategy="LP_Optimized"):
    """
    Insert calculated allocations into the PostgreSQL allocations table.
    """
    if allocation_date is None:
        allocation_date = pd.Timestamp.today().date()

    insert_query = text("""
        INSERT INTO allocations (
            allocation_date,
            village_id,
            village_name,
            population,
            vulnerability_index,
            predicted_demand_l,
            allocated_water_l,
            shortage_l,
            satisfaction_pct,
            strategy
        )
        VALUES (
            :allocation_date,
            :village_id,
            :village_name,
            :population,
            :vulnerability_index,
            :predicted_demand_l,
            :allocated_water_l,
            :shortage_l,
            :satisfaction_pct,
            :strategy
        )
    """)

    records = []
    for _, row in allocations_df.iterrows():
        records.append({
            "allocation_date": allocation_date,
            "village_id": str(row["village_id"]),
            "village_name": str(row["village_name"]),
            "population": int(row["population"]),
            "vulnerability_index": float(row["vulnerability_index"]),
            "predicted_demand_l": float(row["predicted_demand_l"]),
            "allocated_water_l": float(row["allocated_water_l"]),
            "shortage_l": float(row["shortage_l"]),
            "satisfaction_pct": float(row["satisfaction_pct"]),
            "strategy": strategy,
        })

    with engine.begin() as conn:
        conn.execute(insert_query, records)

    print(f"\n[STEP 6] Successfully saved {len(records)} allocation records into PostgreSQL `allocations` table!")


# =====================================================================
# MAIN EXECUTION ENTRY POINT
# =====================================================================

def run_phase16_lp(engine=None, store=True):
    """Run Phase 16 Steps 1 to 6."""
    if engine is None:
        engine = get_engine()

    print("[STEP 1] Loading network inputs, source availability & demands...")
    avail_df, demands_df, pipelines_df = load_all_inputs(engine)

    print(f"[STEP 2 & 3] Building LP problem (HiGHS LP solver)...")
    status, solution_x, pipe_list, village_list, E, V = solve_water_allocation_lp(
        avail_df, demands_df, pipelines_df
    )

    print(f"[STEP 4 & 5] Extracting allocation results and analyzing bottlenecks...")
    allocations_df, flows_df = extract_allocation_results(solution_x, pipe_list, village_list, E, V)

    print_phase16_summary(status, allocations_df, flows_df, avail_df)

    if store:
        store_allocations(engine, allocations_df)

    return allocations_df, flows_df


if __name__ == "__main__":
    run_phase16_lp()
