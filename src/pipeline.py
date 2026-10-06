"""
Jal Dharma AI - Phase 24: End-to-End Pipeline
=============================================
Unified orchestration pipeline combining all project phases:

    The user selects:
        Date (e.g. "2025-06-29" or current date)

    System performs:
        1. Load historical data
        ↓
        2. Predict demand (Phase 11 ML Linear Regression)
        ↓
        3. Get current water availability (Phase 15 Hydro-Informatics)
        ↓
        4. Load GIS network (Phase 8 Spatial Topology)
        ↓
        5. Build graph (Phase 8 & 16 NetworkX DiGraph)
        ↓
        6. Calculate max-flow (Phase 16 Edmonds-Karp / Dinic throughput)
        ↓
        7. Run equity-aware LP (Phase 16-20 SciPy HiGHS Solver with Phase 18 Priority Weights)
        ↓
        8. Calculate shortage (Deficit analysis & Satisfaction S_i = A_i / D_i)
        ↓
        9. Calculate fairness (Phase 19 Jain's Index, Gini, Hoover, Weighted Shortage)
        ↓
        10. Store results (CSV, JSON, Dashboard live sync, PostgreSQL bridge)
        ↓
        11. Update GIS (Dynamic Folium HTML map with shortage color-coding)
        ↓
        12. Display dashboard (Terminal Executive Cockpit + Web Dashboard sync)

Run with:
    python main.py
    python -m src.pipeline --date 2025-06-29
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import folium
import networkx as nx
import numpy as np
import pandas as pd
from scipy.optimize import linprog

# Project Root Setup
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Internal Project Modules
from src.database.connection import get_engine
from src.justice.metrics import (
    average_satisfaction_ratio,
    average_shortage,
    gini_coefficient,
    hoover_index,
    jains_fairness_index,
    maximum_shortage,
    percentage_minimum_service_level,
    weighted_shortage,
)
from src.justice.priority import calculate_priority_scores
from src.prediction.models import (
    FEATURES,
    load_dataset,
    predict_demand,
    train_final_model,
)

# Standard Directory Paths
DATA_DIR = PROJECT_ROOT / "data" / "synthetic"
OUTPUTS_PIPELINE_DIR = PROJECT_ROOT / "outputs" / "pipeline"
OUTPUTS_MAPS_DIR = PROJECT_ROOT / "outputs" / "maps"
DASHBOARD_DATA_DIR = PROJECT_ROOT / "dashboard" / "src" / "data"

OUTPUTS_PIPELINE_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_MAPS_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================================
# STEP 1: LOAD HISTORICAL DATA
# =========================================================================

def step_1_load_historical_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Ingest historical water demand and weather datasets.
    Falls back cleanly from PostgreSQL to CSV synthetic datasets.
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            df_demand = pd.read_sql("SELECT * FROM historical_water_demand ORDER BY village_id, date", conn)
            df_weather = pd.read_sql("SELECT * FROM weather ORDER BY date", conn)
        df_demand["date"] = pd.to_datetime(df_demand["date"])
        df_weather["date"] = pd.to_datetime(df_weather["date"])
    except Exception:
        demand_csv = DATA_DIR / "2_historical_water_demand_dataset.csv"
        weather_csv = DATA_DIR / "3_weather_dataset.csv"
        df_demand = load_dataset(str(demand_csv))
        df_weather = pd.read_csv(weather_csv)
        df_weather["date"] = pd.to_datetime(df_weather["date"], format="%Y-%m-%d", errors="coerce")

    return df_demand, df_weather


# =========================================================================
# STEP 2: PREDICT DEMAND
# =========================================================================

def step_2_predict_demand(
    df_demand: pd.DataFrame,
    df_weather: pd.DataFrame,
    df_villages: pd.DataFrame,
    target_date: pd.Timestamp,
) -> pd.DataFrame:
    """
    Train Linear Regression model (Phase 11) and predict demand for all 45 villages
    on the user-selected target date.
    """
    # 1. Train model on chronological training window
    model, train_mean, train_std = train_final_model(df_demand)

    # 2. Extract or estimate weather for the target date
    weather_match = df_weather[df_weather["date"].dt.date == target_date.date()]
    if not weather_match.empty:
        temp_c = float(weather_match["temperature_c"].iloc[0])
        rain_mm = float(weather_match["rainfall_mm"].iloc[0])
        if "humidity" in weather_match.columns:
            humidity = float(weather_match["humidity"].iloc[0])
        elif "humidity_percent" in weather_match.columns:
            humidity = float(weather_match["humidity_percent"].iloc[0])
        else:
            humidity = 45.0
    else:
        # Default summer averages if date is outside range
        temp_c = 34.5
        rain_mm = 0.0
        humidity = 42.0

    predictions_records = []

    # 3. Predict for each village
    for _, village_row in df_villages.iterrows():
        vid = str(village_row["village_id"])
        vname = str(village_row["village_name"])
        pop = float(village_row["population"])

        # Village historical records up to target_date
        v_hist = df_demand[df_demand["village_id"] == vid].sort_values("date")
        prior_hist = v_hist[v_hist["date"] < target_date]

        if not prior_hist.empty:
            prev_demand = float(prior_hist["actual_demand_l"].iloc[-1])
            avg_7d = float(prior_hist["actual_demand_l"].tail(7).mean())
            avg_30d = float(prior_hist["actual_demand_l"].tail(30).mean())
        else:
            prev_demand = pop * 135.0  # CPHEEO 135 LPCD benchmark
            avg_7d = prev_demand
            avg_30d = prev_demand

        features_df = pd.DataFrame([{
            "population": pop,
            "temperature_c": temp_c,
            "rainfall_mm": rain_mm,
            "humidity": humidity,
            "previous_day_demand_l": prev_demand,
            "demand_7day_avg_l": avg_7d,
            "demand_30day_avg_l": avg_30d,
        }])

        pred_val = float(predict_demand(model, features_df, train_mean, train_std)[0])
        # Safety clamp to realistic LPCD envelope (70 LPCD to 200 LPCD)
        pred_val = float(np.clip(pred_val, pop * 70.0, pop * 200.0))

        predictions_records.append({
            "village_id": vid,
            "village_name": vname,
            "population": int(pop),
            "predicted_demand_l": pred_val,
        })

    return pd.DataFrame(predictions_records)


# =========================================================================
# STEP 3: GET CURRENT WATER AVAILABILITY
# =========================================================================

def step_3_get_water_availability(
    target_date: pd.Timestamp,
    scarcity_factor: float = 1.0,
) -> Tuple[pd.DataFrame, float]:
    """
    Calculate deliverable volume for all water sources on target date.
    Deliverable today = min(Available storage, Daily supply capacity) * scarcity_factor.
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            df_sources = pd.read_sql("SELECT * FROM water_sources", conn)
            df_avail = pd.read_sql("SELECT * FROM water_availability", conn)
        df_avail["date"] = pd.to_datetime(df_avail["date"])
    except Exception:
        df_sources = pd.read_csv(DATA_DIR / "4_water_source_dataset.csv")
        df_avail = pd.read_csv(DATA_DIR / "8_water_availability_dataset.csv")
        df_avail["date"] = pd.to_datetime(df_avail["date"], errors="coerce")

    # Match target date or take latest
    avail_target = df_avail[df_avail["date"].dt.date == target_date.date()]
    if avail_target.empty:
        avail_target = df_avail[df_avail["date"] == df_avail["date"].max()]

    merged = pd.merge(df_sources, avail_target, on="source_id", how="left")

    source_records = []
    for _, row in merged.iterrows():
        sid = str(row["source_id"])
        sname = str(row.get("source_name", sid))
        stype = str(row.get("source_type", "Reservoir"))

        current_storage = float(row.get("current_storage_l", 1e9))
        daily_cap = float(row.get("daily_supply_capacity_l", 5e7))
        inflow = float(row.get("inflow_l", 0.0)) if "inflow_l" in row else 0.0
        reserved = float(row.get("reserved_storage_l", 0.0)) if "reserved_storage_l" in row else 0.0

        available_storage = max(0.0, current_storage + inflow - reserved)
        deliverable = min(available_storage, daily_cap) * scarcity_factor

        source_records.append({
            "source_id": sid,
            "source_name": sname,
            "source_type": stype,
            "storage_l": current_storage,
            "daily_capacity_l": daily_cap,
            "deliverable_today_l": deliverable,
            "latitude": float(row.get("latitude", 18.5)),
            "longitude": float(row.get("longitude", 74.5)),
        })

    df_avail_out = pd.DataFrame(source_records)
    total_water_available = float(df_avail_out["deliverable_today_l"].sum())

    return df_avail_out, total_water_available


# =========================================================================
# STEP 4: LOAD GIS NETWORK
# =========================================================================

def step_4_load_gis_network() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Loads spatial entities: villages (with Phase 18 priority scores), tanks, and pipelines.
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            villages = pd.read_sql("SELECT * FROM villages", conn)
            tanks = pd.read_sql("SELECT * FROM tanks_reservoirs", conn)
            pipelines = pd.read_sql("SELECT * FROM pipelines", conn)
    except Exception:
        villages = pd.read_csv(DATA_DIR / "1_village_dataset.csv")
        tanks = pd.read_csv(DATA_DIR / "6_tank_reservoir_dataset.csv")
        pipelines = pd.read_csv(DATA_DIR / "5_pipeline_water_network_dataset.csv")

    villages = calculate_priority_scores(villages)
    return villages, tanks, pipelines


# =========================================================================
# STEP 5: BUILD GRAPH
# =========================================================================

def step_5_build_graph(
    df_sources: pd.DataFrame,
    df_tanks: pd.DataFrame,
    df_villages: pd.DataFrame,
    df_pipelines: pd.DataFrame,
) -> nx.DiGraph:
    """
    Construct directed network graph connecting sources -> tanks -> villages.
    """
    G = nx.DiGraph()

    # Add Source Nodes
    for _, r in df_sources.iterrows():
        G.add_node(
            str(r["source_id"]),
            name=str(r["source_name"]),
            node_type="source",
            lat=float(r["latitude"]),
            lon=float(r["longitude"]),
            capacity=float(r["deliverable_today_l"]),
        )

    # Add Tank Nodes
    for _, r in df_tanks.iterrows():
        G.add_node(
            str(r["tank_id"]),
            name=str(r["tank_name"]),
            node_type="tank",
            lat=float(r["latitude"]),
            lon=float(r["longitude"]),
            capacity=float(r.get("capacity_l", 1e7)),
        )

    # Add Village Nodes
    for _, r in df_villages.iterrows():
        G.add_node(
            str(r["village_id"]),
            name=str(r["village_name"]),
            node_type="village",
            lat=float(r["latitude"]),
            lon=float(r["longitude"]),
            population=int(r["population"]),
            priority_score=float(r.get("priority_score", 0.5)),
        )

    # Add Pipeline Edges
    for _, r in df_pipelines.iterrows():
        u = str(r["source_node"])
        v = str(r["destination_node"])
        cap = float(r.get("capacity_l_per_day", 1e7))
        status = str(r.get("status", "Operational")).strip().lower()
        if status not in ["operational", "working", "1"]:
            cap = 0.0

        G.add_edge(
            u,
            v,
            pipeline_id=str(r["pipeline_id"]),
            capacity=cap,
            length_km=float(r.get("length_km", 5.0)),
            status=status,
        )

    return G


# =========================================================================
# STEP 6: CALCULATE MAX-FLOW
# =========================================================================

def step_6_calculate_max_flow(
    G: nx.DiGraph,
    df_sources: pd.DataFrame,
    df_demands: pd.DataFrame,
) -> Tuple[float, Dict[str, Dict[str, float]], float]:
    """
    Augment graph with SUPER_SOURCE and SUPER_SINK and calculate maximum network flow.
    """
    G_flow = G.copy()
    SUPER_SOURCE = "SUPER_SOURCE"
    SUPER_SINK = "SUPER_SINK"

    # Connect SUPER_SOURCE -> each water source
    for _, r in df_sources.iterrows():
        sid = str(r["source_id"])
        cap = float(r["deliverable_today_l"])
        G_flow.add_edge(SUPER_SOURCE, sid, capacity=cap)

    # Connect each village -> SUPER_SINK
    total_demanded = 0.0
    for _, r in df_demands.iterrows():
        vid = str(r["village_id"])
        dem = float(r["predicted_demand_l"])
        total_demanded += dem
        G_flow.add_edge(vid, SUPER_SINK, capacity=dem)

    flow_value, flow_dict = nx.maximum_flow(G_flow, SUPER_SOURCE, SUPER_SINK)
    return float(flow_value), flow_dict, total_demanded


# =========================================================================
# STEP 7: RUN EQUITY-AWARE LP
# =========================================================================

def step_7_run_equity_aware_lp(
    df_sources: pd.DataFrame,
    df_pipelines: pd.DataFrame,
    df_villages: pd.DataFrame,
    total_available_water: float,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Solve multi-criteria Linear Programming optimization (SciPy HiGHS Solver):
        Objective: Minimize priority-weighted shortage
                   min sum(w_i * (Demand_i - Allocated_i))
                   <=> max sum(w_i * Allocated_i)
        Subject to:
            - Flow conservation at all junction tanks
            - Pipeline capacity limits
            - Source delivery bounds
            - Non-negativity and demand upper bounds
    """
    # Build LP representation
    edges: List[Tuple[str, str]] = []
    bounds: List[Tuple[float, float]] = []

    # 1. Source injection edges: SUPER_SOURCE -> source_id
    source_edge_indices: List[int] = []
    for _, s in df_sources.iterrows():
        sid = str(s["source_id"])
        cap = float(s["deliverable_today_l"])
        source_edge_indices.append(len(edges))
        edges.append(("SUPER_SOURCE", sid))
        bounds.append((0.0, cap))

    # 2. Pipeline edges
    pipeline_edge_map: Dict[str, int] = {}
    for _, p in df_pipelines.iterrows():
        u = str(p["source_node"])
        v = str(p["destination_node"])
        pid = str(p["pipeline_id"])
        cap = float(p.get("capacity_l_per_day", 1e7))
        status = str(p.get("status", "Operational")).strip().lower()
        if status not in ["operational", "working", "1"]:
            cap = 0.0
        pipeline_edge_map[pid] = len(edges)
        edges.append((u, v))
        bounds.append((0.0, cap))

    # 3. Delivery edges: village_id -> SUPER_SINK
    village_edge_map: Dict[str, int] = {}
    for _, v in df_villages.iterrows():
        vid = str(v["village_id"])
        dem = float(v["predicted_demand_l"])
        village_edge_map[vid] = len(edges)
        edges.append((vid, "SUPER_SINK"))
        bounds.append((0.0, dem))

    # 4. Flow conservation at all intermediate nodes (Sources, Tanks, Villages)
    internal_nodes = set()
    for u, v in edges:
        if u != "SUPER_SOURCE":
            internal_nodes.add(u)
        if v != "SUPER_SINK":
            internal_nodes.add(v)

    internal_nodes_list = sorted(list(internal_nodes))
    node_to_idx = {node: idx for idx, node in enumerate(internal_nodes_list)}

    A_eq = np.zeros((len(internal_nodes_list), len(edges)), dtype=float)
    for e_idx, (u, v) in enumerate(edges):
        if u in node_to_idx:
            A_eq[node_to_idx[u], e_idx] -= 1.0  # Outflow
        if v in node_to_idx:
            A_eq[node_to_idx[v], e_idx] += 1.0  # Inflow

    b_eq = np.zeros(len(internal_nodes_list), dtype=float)

    # 5. Priority weights for Equity-Aware objective
    # w_i = priority_score ^ 1.5 ensures steep preference for vulnerable communities
    c = np.zeros(len(edges), dtype=float)
    for _, v in df_villages.iterrows():
        vid = str(v["village_id"])
        e_idx = village_edge_map[vid]
        p_score = float(v.get("priority_score", 0.5))
        c[e_idx] = -(p_score ** 1.5)

    res = linprog(c, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")

    # Extract allocations
    allocations = []
    for _, v in df_villages.iterrows():
        vid = str(v["village_id"])
        e_idx = village_edge_map[vid]
        dem = float(v["predicted_demand_l"])
        alloc = max(0.0, float(res.x[e_idx])) if res.success else 0.0
        allocations.append({
            "village_id": vid,
            "village_name": v["village_name"],
            "population": int(v["population"]),
            "vulnerability_index": float(v.get("vulnerability_index", 0.5)),
            "priority_score": float(v.get("priority_score", 0.5)),
            "priority_rank": int(v.get("priority_rank", 1)),
            "predicted_demand_l": dem,
            "allocated_water_l": alloc,
        })
    df_allocations = pd.DataFrame(allocations)

    # Extract pipeline flows
    flows = []
    for _, p in df_pipelines.iterrows():
        pid = str(p["pipeline_id"])
        cap = float(p.get("capacity_l_per_day", 1e7))
        e_idx = pipeline_edge_map.get(pid)
        flow_val = max(0.0, float(res.x[e_idx])) if (res.success and e_idx is not None) else 0.0
        util = (flow_val / cap * 100.0) if cap > 0 else 0.0
        flows.append({
            "pipeline_id": pid,
            "source_node": p["source_node"],
            "destination_node": p["destination_node"],
            "capacity_l_per_day": cap,
            "current_flow_l": flow_val,
            "utilization_pct": util,
            "status": "Warning" if util > 90 else "Operational",
        })
    df_flows = pd.DataFrame(flows)

    return df_allocations, df_flows


# =========================================================================
# STEP 8: CALCULATE SHORTAGE
# =========================================================================

def step_8_calculate_shortage(df_allocations: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    Calculate per-village shortages, satisfaction ratios, and regional aggregations.
    """
    df = df_allocations.copy()
    df["shortage_l"] = np.maximum(0.0, df["predicted_demand_l"] - df["allocated_water_l"])
    df["satisfaction_ratio"] = np.where(
        df["predicted_demand_l"] > 0,
        np.clip(df["allocated_water_l"] / df["predicted_demand_l"], 0.0, 1.0),
        1.0,
    )
    df["satisfaction_pct"] = df["satisfaction_ratio"] * 100.0

    # Categorize status
    def get_status(sat_pct: float) -> str:
        if sat_pct >= 90.0:
            return "Low"
        elif sat_pct >= 75.0:
            return "Medium"
        else:
            return "High"

    df["shortage_status"] = df["satisfaction_pct"].apply(get_status)

    total_demand = float(df["predicted_demand_l"].sum())
    total_allocated = float(df["allocated_water_l"].sum())
    total_shortage = float(df["shortage_l"].sum())
    mean_shortage = float(df["shortage_l"].mean())
    max_shortage_val = float(df["shortage_l"].max())

    worst_village = df.sort_values("shortage_l", ascending=False).iloc[0]["village_name"]

    shortage_metrics = {
        "total_demand_l": total_demand,
        "total_allocated_l": total_allocated,
        "total_shortage_l": total_shortage,
        "mean_shortage_l": mean_shortage,
        "max_shortage_l": max_shortage_val,
        "worst_village": worst_village,
        "fulfillment_pct": (total_allocated / total_demand * 100.0) if total_demand > 0 else 100.0,
    }

    return df, shortage_metrics


# =========================================================================
# STEP 9: CALCULATE FAIRNESS
# =========================================================================

def step_9_calculate_fairness(
    df_allocations: pd.DataFrame,
) -> Dict[str, Any]:
    """
    Compute rigorous Phase 19 fairness and justice metrics.
    """
    satisfactions = df_allocations["satisfaction_ratio"]
    shortages = df_allocations["shortage_l"]
    weights = df_allocations["priority_score"]

    avg_sat = average_satisfaction_ratio(satisfactions)
    jain_index = jains_fairness_index(satisfactions)
    gini_coeff = gini_coefficient(satisfactions)
    hoover_idx = hoover_index(satisfactions)
    w_shortage = weighted_shortage(shortages, weights)
    service_70 = percentage_minimum_service_level(satisfactions, threshold=0.70)
    service_75 = percentage_minimum_service_level(satisfactions, threshold=0.75)

    return {
        "jains_fairness_index": round(jain_index, 4),
        "gini_coefficient": round(gini_coeff, 4),
        "hoover_index": round(hoover_idx, 4),
        "average_satisfaction_pct": round(avg_sat * 100.0, 2),
        "weighted_shortage_l": round(w_shortage, 2),
        "pct_minimum_service_70": round(service_70, 2),
        "pct_minimum_service_75": round(service_75, 2),
    }


# =========================================================================
# STEP 10: STORE RESULTS
# =========================================================================

def step_10_store_results(
    target_date: pd.Timestamp,
    df_results: pd.DataFrame,
    df_flows: pd.DataFrame,
    shortage_metrics: Dict[str, Any],
    fairness_metrics: Dict[str, Any],
    water_available_l: float,
) -> Dict[str, Path]:
    """
    Save results to CSV, JSON, update React dashboard data, and attempt PostgreSQL insert.
    """
    date_str = target_date.strftime("%Y-%m-%d")

    # 1. Save pipeline allocation results CSV
    alloc_csv_path = OUTPUTS_PIPELINE_DIR / f"allocation_results_{date_str}.csv"
    df_results.to_csv(alloc_csv_path, index=False)

    # 2. Save pipeline flows CSV
    flows_csv_path = OUTPUTS_PIPELINE_DIR / f"pipeline_flows_{date_str}.csv"
    df_flows.to_csv(flows_csv_path, index=False)

    # 3. Save system summary JSON
    summary_data = {
        "execution_timestamp": datetime.now().isoformat(),
        "target_date": date_str,
        "water_available_l": water_available_l,
        "water_available_ml": round(water_available_l / 1e6, 2),
        "shortage_metrics": shortage_metrics,
        "fairness_metrics": fairness_metrics,
        "villages_count": len(df_results),
        "pipelines_count": len(df_flows),
    }
    summary_json_path = OUTPUTS_PIPELINE_DIR / f"pipeline_summary_{date_str}.json"
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)

    # 4. Synchronize with React Frontend (overview.json & villages.json)
    if DASHBOARD_DATA_DIR.exists():
        dashboard_overview = {
            "snapshotDate": date_str,
            "totalWaterAvailableL": water_available_l,
            "totalWaterAvailableML": round(water_available_l / 1e6, 2),
            "totalPredictedDemandL": shortage_metrics["total_demand_l"],
            "totalPredictedDemandML": round(shortage_metrics["total_demand_l"] / 1e6, 2),
            "totalAllocatedL": shortage_metrics["total_allocated_l"],
            "totalAllocatedML": round(shortage_metrics["total_allocated_l"] / 1e6, 2),
            "totalShortageL": shortage_metrics["total_shortage_l"],
            "totalShortageML": round(shortage_metrics["total_shortage_l"] / 1e6, 2),
            "averageSatisfactionPct": fairness_metrics["average_satisfaction_pct"],
            "fairnessIndex": fairness_metrics["jains_fairness_index"],
            "giniCoefficient": fairness_metrics["gini_coefficient"],
            "hooverIndex": fairness_metrics["hoover_index"],
            "minServiceCompliancePct": fairness_metrics["pct_minimum_service_75"],
            "totalVillages": len(df_results),
            "topPriorityVillages": df_results.sort_values("priority_score", ascending=False).head(5).to_dict(orient="records"),
        }
        with open(DASHBOARD_DATA_DIR / "overview.json", "w", encoding="utf-8") as f:
            json.dump(dashboard_overview, f, indent=2)

    # 5. Attempt PostgreSQL insert
    try:
        engine = get_engine()
        from sqlalchemy import text
        insert_query = text("""
            INSERT INTO allocations (
                allocation_date, village_id, village_name, population,
                vulnerability_index, predicted_demand_l, allocated_water_l,
                shortage_l, satisfaction_pct, strategy
            ) VALUES (
                :allocation_date, :village_id, :village_name, :population,
                :vulnerability_index, :predicted_demand_l, :allocated_water_l,
                :shortage_l, :satisfaction_pct, 'Equity-Aware-Phase24'
            )
        """)
        records = []
        for _, row in df_results.iterrows():
            records.append({
                "allocation_date": target_date.date(),
                "village_id": str(row["village_id"]),
                "village_name": str(row["village_name"]),
                "population": int(row["population"]),
                "vulnerability_index": float(row["vulnerability_index"]),
                "predicted_demand_l": float(row["predicted_demand_l"]),
                "allocated_water_l": float(row["allocated_water_l"]),
                "shortage_l": float(row["shortage_l"]),
                "satisfaction_pct": float(row["satisfaction_pct"]),
            })
        with engine.begin() as conn:
            conn.execute(insert_query, records)
    except Exception:
        pass  # Graceful fallback to filesystem storage

    return {
        "allocations_csv": alloc_csv_path,
        "flows_csv": flows_csv_path,
        "summary_json": summary_json_path,
    }


# =========================================================================
# STEP 11: UPDATE GIS
# =========================================================================

def step_11_update_gis(
    df_results: pd.DataFrame,
    df_sources: pd.DataFrame,
    df_tanks: pd.DataFrame,
    df_pipelines: pd.DataFrame,
    df_flows: pd.DataFrame,
    target_date: pd.Timestamp,
) -> Path:
    """
    Generate an updated spatial HTML Folium map with village shortage color-coding:
        - Green (<10% shortage)
        - Yellow (10-25% shortage)
        - Red (>25% shortage / Critical)
    """
    center_lat = float(df_results["latitude"].mean()) if "latitude" in df_results else 18.52
    center_lon = float(df_results["longitude"].mean()) if "longitude" in df_results else 74.65

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=10,
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri &mdash; Jal Dharma AI GIS",
    )

    # 1. Add Pipelines
    flow_map = df_flows.set_index("pipeline_id")["utilization_pct"].to_dict() if not df_flows.empty else {}
    for _, p in df_pipelines.iterrows():
        u = str(p["source_node"])
        v = str(p["destination_node"])
        pid = str(p["pipeline_id"])
        cap_mld = float(p.get("capacity_l_per_day", 1e7)) / 1e6
        util = flow_map.get(pid, 50.0)

        pipe_color = "#ef4444" if util > 90 else "#f59e0b" if util > 80 else "#0284c7"

        # Coordinates if present
        u_lat = float(p.get("source_lat", center_lat))
        u_lon = float(p.get("source_lon", center_lon))
        v_lat = float(p.get("dest_lat", center_lat + 0.05))
        v_lon = float(p.get("dest_lon", center_lon + 0.05))

        folium.PolyLine(
            locations=[[u_lat, u_lon], [v_lat, v_lon]],
            color=pipe_color,
            weight=3,
            opacity=0.8,
            tooltip=f"Pipeline {pid} | Flow: {util:.1f}% ({cap_mld:.1f} ML/d)",
        ).add_to(m)

    # 2. Add Sources
    for _, s in df_sources.iterrows():
        folium.Marker(
            location=[float(s["latitude"]), float(s["longitude"])],
            popup=f"<b>Source:</b> {s['source_name']}<br><b>Capacity:</b> {float(s['daily_capacity_l'])/1e6:.1f} ML/d",
            icon=folium.Icon(color="blue", icon="tint", prefix="fa"),
        ).add_to(m)

    # 3. Add Storage Tanks
    for _, t in df_tanks.iterrows():
        folium.Marker(
            location=[float(t["latitude"]), float(t["longitude"])],
            popup=f"<b>Storage Tank:</b> {t['tank_name']}",
            icon=folium.Icon(color="cadetblue", icon="database", prefix="fa"),
        ).add_to(m)

    # 4. Add Villages (Color-coded by Shortage)
    for _, v in df_results.iterrows():
        sat = float(v["satisfaction_pct"])
        status = v["shortage_status"]
        marker_color = "green" if status == "Low" else "orange" if status == "Medium" else "red"

        v_lat = float(v.get("latitude", center_lat))
        v_lon = float(v.get("longitude", center_lon))

        popup_html = f"""
        <b>Village:</b> {v['village_name']} ({v['village_id']})<br>
        <b>Population:</b> {int(v['population']):,}<br>
        <b>Priority Rank:</b> #{int(v.get('priority_rank', 1))}<br>
        <b>Predicted Demand:</b> {float(v['predicted_demand_l']):,.0f} L<br>
        <b>Allocated Water:</b> {float(v['allocated_water_l']):,.0f} L<br>
        <b>Shortage:</b> {float(v['shortage_l']):,.0f} L<br>
        <b>Satisfaction:</b> <b>{sat:.1f}%</b> ({status} Shortage)
        """

        folium.CircleMarker(
            location=[v_lat, v_lon],
            radius=7,
            color="#ffffff",
            weight=1.5,
            fill=True,
            fill_color=marker_color,
            fill_opacity=0.9,
            popup=popup_html,
            tooltip=f"{v['village_name']}: {sat:.1f}% Satisfaction ({status})",
        ).add_to(m)

    date_str = target_date.strftime("%Y-%m-%d")
    map_path = OUTPUTS_MAPS_DIR / f"gis_shortage_map_{date_str}.html"
    m.save(str(map_path))

    # Also save standard interactive_network_map.html
    m.save(str(OUTPUTS_MAPS_DIR / "interactive_network_map.html"))

    return map_path


# =========================================================================
# STEP 12: DISPLAY DASHBOARD
# =========================================================================

def step_12_display_dashboard(
    target_date: pd.Timestamp,
    water_available_l: float,
    shortage_metrics: Dict[str, Any],
    fairness_metrics: Dict[str, Any],
    df_results: pd.DataFrame,
    df_flows: pd.DataFrame,
    max_flow_l: float,
    map_path: Path,
):
    """
    Print an executive terminal dashboard summarizing the entire end-to-end pipeline run.
    """
    date_str = target_date.strftime("%Y-%m-%d")
    avail_ml = water_available_l / 1e6
    demand_ml = shortage_metrics["total_demand_l"] / 1e6
    alloc_ml = shortage_metrics["total_allocated_l"] / 1e6
    shortage_ml = shortage_metrics["total_shortage_l"] / 1e6
    maxflow_ml = max_flow_l / 1e6

    print("\n" + "=" * 78)
    print(f"       JAI DHARMA AI • END-TO-END PIPELINE EXECUTION SUMMARY")
    print(f"                     TARGET DATE: {date_str}")
    print("=" * 78)

    print("\n[EXECUTIVE HYDRO-INFORMATICS KPIS]")
    print(f"  • Total Water Available       : {avail_ml:8.2f} ML/day ({water_available_l:,.0f} L)")
    print(f"  • Total Predicted Demand      : {demand_ml:8.2f} ML/day ({shortage_metrics['total_demand_l']:,.0f} L)")
    print(f"  • Total Water Allocated       : {alloc_ml:8.2f} ML/day ({shortage_metrics['total_allocated_l']:,.0f} L)")
    print(f"  • Total Regional Shortage     : {shortage_ml:8.2f} ML/day ({shortage_metrics['total_shortage_l']:,.0f} L)")
    print(f"  • Physical Max-Flow Throughput: {maxflow_ml:8.2f} ML/day ({max_flow_l:,.0f} L)")
    print(f"  • Regional Fulfillment Rate   : {shortage_metrics['fulfillment_pct']:8.2f}%")

    print("\n[WATER JUSTICE & EQUITY METRICS (Phase 19)]")
    print(f"  • Jain's Fairness Index (J)   : {fairness_metrics['jains_fairness_index']:.4f}  (Optimal equity >= 0.90)")
    print(f"  • Average Satisfaction (mean) : {fairness_metrics['average_satisfaction_pct']:.2f}%")
    print(f"  • Gini Inequality Coefficient : {fairness_metrics['gini_coefficient']:.4f}  (Near 0 = perfect equity)")
    print(f"  • Hoover (Robin Hood) Index   : {fairness_metrics['hoover_index']:.4f}")
    print(f"  • Demographic Weighted Shortage: {fairness_metrics['weighted_shortage_l']:,.0f} L")
    print(f"  • Minimum Service (>=75%)     : {fairness_metrics['pct_minimum_service_75']:.2f}% compliance")

    print("\n[TOP 5 HIGH-PRIORITY VILLAGE ALLOCATIONS]")
    print("-" * 78)
    print(f"{'Rank':<5} {'Village':<16} {'Population':<11} {'Demand (L)':<12} {'Allocated (L)':<14} {'Shortage':<11} {'Sat %':<6}")
    print("-" * 78)
    top_5 = df_results.sort_values("priority_score", ascending=False).head(5)
    for _, r in top_5.iterrows():
        print(f"#{int(r['priority_rank']):<4} {r['village_name']:<16} {int(r['population']):<11,d} {float(r['predicted_demand_l']):<12,.0f} {float(r['allocated_water_l']):<14,.0f} {float(r['shortage_l']):<11,.0f} {float(r['satisfaction_pct']):.1f}%")
    print("-" * 78)

    print("\n[PIPELINE BOTTLENECKS & TELEMETRY WARNINGS]")
    high_util = df_flows[df_flows["utilization_pct"] > 85.0]
    if not high_util.empty:
        for _, p in high_util.iterrows():
            print(f"  [ALERT] Pipeline {p['pipeline_id']} ({p['source_node']} -> {p['destination_node']}): {p['utilization_pct']:.1f}% capacity utilized!")
    else:
        print("  [OK] All pipeline segments operating safely within standard hydraulic margins (<85%).")

    print("\n[GIS MAP & PERSISTENCE ARTIFACTS]")
    print(f"  • Interactive GIS Map         : {map_path.resolve()}")
    print(f"  • Pipeline Storage Folder     : {OUTPUTS_PIPELINE_DIR.resolve()}")
    print(f"  • React Web Dashboard         : http://localhost:5173/")
    print("=" * 78 + "\n")


# =========================================================================
# MASTER PIPELINE ORCHESTRATOR
# =========================================================================

def run_end_to_end_pipeline(
    date_str: str = "2025-06-29",
    scarcity_factor: float = 1.0,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Executes the complete 12-step end-to-end pipeline.
    """
    target_date = pd.to_datetime(date_str)
    if verbose:
        print("\n" + "=" * 65)
        print(f" STARTING JAI DHARMA AI PIPELINE • DATE: {target_date.date()}")
        print("=" * 65)

    # 1. Load historical data
    if verbose:
        print("[STEP 1/12] Loading historical demand & weather data...")
    df_demand, df_weather = step_1_load_historical_data()

    # 4. Load GIS network (needed early for village list)
    if verbose:
        print("[STEP 4/12] Ingesting GIS network entities & priority scores...")
    df_villages, df_tanks, df_pipelines = step_4_load_gis_network()

    # 2. Predict demand
    if verbose:
        print("[STEP 2/12] Training Linear Regression & predicting village demands...")
    df_predictions = step_2_predict_demand(df_demand, df_weather, df_villages, target_date)
    # Merge coordinates into predictions
    df_villages_merged = pd.merge(
        df_predictions,
        df_villages[["village_id", "priority_score", "priority_rank", "vulnerability_index", "latitude", "longitude"]],
        on="village_id",
        how="left",
    )

    # 3. Get current water availability
    if verbose:
        print("[STEP 3/12] Calculating deliverable source water availability...")
    df_sources, total_available_l = step_3_get_water_availability(target_date, scarcity_factor)

    # 5. Build graph
    if verbose:
        print("[STEP 5/12] Building spatial NetworkX directed graph...")
    G = step_5_build_graph(df_sources, df_tanks, df_villages_merged, df_pipelines)

    # 6. Calculate max-flow
    if verbose:
        print("[STEP 6/12] Computing physical network maximum flow throughput...")
    max_flow_l, flow_dict, total_demanded_l = step_6_calculate_max_flow(G, df_sources, df_villages_merged)

    # 7. Run equity-aware LP
    if verbose:
        print("[STEP 7/12] Solving Equity-Aware Multi-Criteria LP (HiGHS Solver)...")
    df_allocations, df_flows = step_7_run_equity_aware_lp(
        df_sources, df_pipelines, df_villages_merged, total_available_l
    )
    # Re-merge coordinates
    df_allocations = pd.merge(
        df_allocations,
        df_villages[["village_id", "latitude", "longitude"]],
        on="village_id",
        how="left",
    )

    # 8. Calculate shortage
    if verbose:
        print("[STEP 8/12] Calculating per-village shortages & satisfaction rates...")
    df_results, shortage_metrics = step_8_calculate_shortage(df_allocations)

    # 9. Calculate fairness
    if verbose:
        print("[STEP 9/12] Evaluating Phase 19 fairness, Gini & Jain's index...")
    fairness_metrics = step_9_calculate_fairness(df_results)

    # 10. Store results
    if verbose:
        print("[STEP 10/12] Persisting results to CSV, JSON & Dashboard store...")
    stored_paths = step_10_store_results(
        target_date, df_results, df_flows, shortage_metrics, fairness_metrics, total_available_l
    )

    # 11. Update GIS
    if verbose:
        print("[STEP 11/12] Updating interactive GIS Folium map with shortage layers...")
    map_path = step_11_update_gis(
        df_results, df_sources, df_tanks, df_pipelines, df_flows, target_date
    )

    # 12. Display dashboard
    if verbose:
        print("[STEP 12/12] Rendering Executive Terminal Dashboard...")
        step_12_display_dashboard(
            target_date,
            total_available_l,
            shortage_metrics,
            fairness_metrics,
            df_results,
            df_flows,
            max_flow_l,
            map_path,
        )

    return {
        "target_date": target_date.strftime("%Y-%m-%d"),
        "water_available_l": total_available_l,
        "max_flow_l": max_flow_l,
        "shortage_metrics": shortage_metrics,
        "fairness_metrics": fairness_metrics,
        "df_results": df_results,
        "df_flows": df_flows,
        "stored_paths": stored_paths,
        "map_path": map_path,
    }


# =========================================================================
# CLI ENTRY POINT
# =========================================================================

def main():
    parser = argparse.ArgumentParser(description="Jai Dharma AI - End-to-End Pipeline")
    parser.add_argument(
        "--date",
        type=str,
        default="2025-06-29",
        help="Target date for demand prediction and allocation (YYYY-MM-DD). Default: 2025-06-29",
    )
    parser.add_argument(
        "--scarcity",
        type=float,
        default=1.0,
        help="Supply scarcity factor (e.g. 0.70 for 30%% drought reduction). Default: 1.0",
    )
    args = parser.parse_args()

    run_end_to_end_pipeline(date_str=args.date, scarcity_factor=args.scarcity, verbose=True)


if __name__ == "__main__":
    main()
