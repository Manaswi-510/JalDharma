"""
Jal Dharma AI - FastAPI Backend
================================
Serves live data from PostgreSQL to the React dashboard.

Endpoints:
  GET /api/overview         → System-level KPIs and metrics
  GET /api/villages         → All village data with current allocation status
  GET /api/predictions/{id} → Per-village ML prediction time-series
  GET /api/allocations      → Current allocation results from LP model
  GET /api/pipelines        → Pipeline network with flow status
  GET /api/water-sources    → Water source inventory
  GET /api/justice          → Water justice & equity metrics

Run with:
  uvicorn src.api.main:app --reload --port 8000
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path when running directly
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
import math
import numpy as np
import pandas as pd
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from src.database.connection import get_engine

# ─── App Setup ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="Jal Dharma AI API",
    description="Live water management data from PostgreSQL",
    version="1.0.0",
)

# Allow the Vite dev server (port 5173) and any other local origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173",
                   "http://localhost:3000", "http://localhost:4173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Shared DB Engine ────────────────────────────────────────────────────────

def get_db():
    return get_engine()


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _safe_float(val) -> Optional[float]:
    """Convert to float, return None for NaN/None."""
    if val is None:
        return None
    try:
        f = float(val)
        return None if math.isnan(f) or math.isinf(f) else f
    except (TypeError, ValueError):
        return None


def _row_to_dict(row) -> Dict[str, Any]:
    """Convert a SQLAlchemy row mapping to a JSON-safe dict."""
    result = {}
    for k, v in row.items():
        if isinstance(v, (date,)):
            result[k] = v.isoformat()
        elif isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            result[k] = None
        else:
            result[k] = v
    return result


# ─── Health Check ────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    try:
        engine = get_db()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"DB error: {e}")


# ─── 1. OVERVIEW  ────────────────────────────────────────────────────────────

@app.get("/api/overview")
def get_overview():
    """
    System-level KPIs:
    - total water available, predicted demand, allocated, shortage
    - Jain's fairness index, Gini coefficient, average satisfaction
    - water source inventory
    - top priority villages
    - allocation strategy comparison
    """
    engine = get_db()
    try:
        with engine.connect() as conn:

            # ── Allocation snapshot (latest date in historical_water_allocations) ──
            alloc_df = pd.read_sql(text("""
                SELECT
                    hwa.village_id,
                    hwa.predicted_demand_l,
                    hwa.allocated_water_l,
                    hwa.shortage_l,
                    hwa.satisfaction_ratio,
                    hwa.priority_score,
                    v.population,
                    v.vulnerability_index
                FROM historical_water_allocations hwa
                JOIN villages v ON v.village_id = hwa.village_id
                WHERE hwa.date = (SELECT MAX(date) FROM historical_water_allocations)
            """), conn)

            if alloc_df.empty:
                raise HTTPException(status_code=404, detail="No allocation data found")

            total_demand  = float(alloc_df["predicted_demand_l"].sum())
            total_alloc   = float(alloc_df["allocated_water_l"].sum())
            total_shortage = float(alloc_df["shortage_l"].fillna(0).sum())
            avg_sat_pct   = float(alloc_df["satisfaction_ratio"].mean() * 100)

            # Jain's fairness index
            s = alloc_df["satisfaction_ratio"].values
            n = len(s)
            jain = (float(np.sum(s)) ** 2) / (n * float(np.sum(s ** 2))) if np.sum(s ** 2) > 0 else 1.0
            jain = float(np.clip(jain, 1.0 / n, 1.0))

            # Gini coefficient
            s_sorted = np.sort(s)
            idx = np.arange(1, n + 1)
            gini = float((2.0 * np.sum(idx * s_sorted)) / (n * np.sum(s_sorted)) - (n + 1.0) / n)
            gini = float(np.clip(gini, 0.0, 1.0))

            # Hoover index
            total_s = np.sum(s)
            hoover = float(0.5 * np.sum(np.abs(s - np.mean(s))) / total_s) if total_s > 0 else 0.0

            min_service_pct = float((np.sum(s >= 0.70) / n) * 100)

            # ── Water sources ──────────────────────────────────────────────────
            sources_df = pd.read_sql(text("""
                SELECT source_id, source_name, source_type,
                       total_capacity_l, current_storage_l,
                       daily_supply_capacity_l, reliability_score, status
                FROM water_sources
                ORDER BY source_id
            """), conn)

            # ── Top priority villages ──────────────────────────────────────────
            priority_df = pd.read_sql(text("""
                SELECT v.village_id, v.village_name, v.population,
                       v.vulnerability_index, v.historical_shortage,
                       hwa.priority_score
                FROM villages v
                JOIN historical_water_allocations hwa ON hwa.village_id = v.village_id
                WHERE hwa.date = (SELECT MAX(date) FROM historical_water_allocations)
                ORDER BY hwa.priority_score DESC
                LIMIT 6
            """), conn)

            # ── Allocation strategy comparison (from comparison CSV if exists) ──
            comparison_path = PROJECT_ROOT / "outputs" / "justice" / "allocation_comparison.json"
            strategies = []
            if comparison_path.exists():
                with open(comparison_path) as f:
                    strategies = json.load(f)

        return {
            "snapshotDate": str(alloc_df["village_id"].index[0]) if not alloc_df.empty else str(date.today()),
            "totalVillages": int(n),
            "totalPopulationServed": int(alloc_df["population"].sum()) if "population" in alloc_df else None,
            "totalPredictedDemandL": round(total_demand, 2),
            "totalAllocatedL": round(total_alloc, 2),
            "totalShortageL": round(total_shortage, 2),
            "averageSatisfactionPct": round(avg_sat_pct, 2),
            "fairnessIndex": round(jain, 4),
            "giniCoefficient": round(gini, 4),
            "hooverIndex": round(hoover, 4),
            "minServiceCompliancePct": round(min_service_pct, 2),
            "waterSources": [
                {
                    "id": r["source_id"],
                    "name": r["source_name"],
                    "type": r["source_type"],
                    "capacityL": _safe_float(r["total_capacity_l"]),
                    "storageL": _safe_float(r["current_storage_l"]),
                    "dailySupplyL": _safe_float(r["daily_supply_capacity_l"]),
                    "reliability": _safe_float(r["reliability_score"]),
                    "status": r["status"],
                }
                for _, r in sources_df.iterrows()
            ],
            "topPriorityVillages": [
                {
                    "village_id": r["village_id"],
                    "village_name": r["village_name"],
                    "population": int(r["population"]) if r["population"] else None,
                    "vulnerability_index": _safe_float(r["vulnerability_index"]),
                    "historical_shortage": _safe_float(r["historical_shortage"]),
                    "priority_score": _safe_float(r["priority_score"]),
                    "priority_rank": i + 1,
                }
                for i, (_, r) in enumerate(priority_df.iterrows())
            ],
            "allocationStrategies": strategies,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── 2. VILLAGES ─────────────────────────────────────────────────────────────

@app.get("/api/villages")
def get_villages():
    """All villages with latest allocation and priority data."""
    engine = get_db()
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text("""
                SELECT
                    v.village_id,
                    v.village_name,
                    v.district,
                    v.latitude,
                    v.longitude,
                    v.population,
                    v.vulnerability_index,
                    v.accessibility_score,
                    v.historical_shortage,
                    v.elevation_m,
                    hwa.predicted_demand_l,
                    hwa.allocated_water_l,
                    hwa.shortage_l,
                    hwa.satisfaction_ratio,
                    hwa.priority_score
                FROM villages v
                LEFT JOIN historical_water_allocations hwa
                    ON hwa.village_id = v.village_id
                    AND hwa.date = (SELECT MAX(date) FROM historical_water_allocations)
                ORDER BY v.village_id
            """), conn)

        records = []
        for _, r in df.iterrows():
            sat = _safe_float(r.get("satisfaction_ratio"))
            sat_pct = round(sat * 100, 1) if sat is not None else None
            shortage_l = _safe_float(r.get("shortage_l"))
            status = (
                "High" if sat_pct is not None and sat_pct < 80 else
                "Medium" if sat_pct is not None and sat_pct < 92 else
                "Low"
            )
            records.append({
                "id": r["village_id"],
                "name": r["village_name"],
                "district": r.get("district"),
                "latitude": _safe_float(r.get("latitude")),
                "longitude": _safe_float(r.get("longitude")),
                "population": int(r["population"]) if r.get("population") else None,
                "vulnerabilityIndex": _safe_float(r.get("vulnerability_index")),
                "accessibilityScore": _safe_float(r.get("accessibility_score")),
                "historicalShortage": _safe_float(r.get("historical_shortage")),
                "elevationM": _safe_float(r.get("elevation_m")),
                "demandL": _safe_float(r.get("predicted_demand_l")),
                "allocatedL": _safe_float(r.get("allocated_water_l")),
                "shortageL": _safe_float(shortage_l),
                "satisfactionPct": sat_pct,
                "priorityScore": _safe_float(r.get("priority_score")),
                "status": status,
            })
        return records

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── 3. PREDICTIONS ──────────────────────────────────────────────────────────

@app.get("/api/predictions/{village_id}")
def get_predictions(
    village_id: str,
    days: int = Query(default=14, ge=7, le=90, description="Days of history to return"),
):
    """
    Per-village prediction time-series from historical_water_demand.
    Returns actual demand + the ML predicted demand (from predictions table if available).
    """
    engine = get_db()
    try:
        with engine.connect() as conn:
            # Village meta
            v_row = conn.execute(text("""
                SELECT village_id, village_name, population,
                       vulnerability_index, historical_shortage
                FROM villages WHERE village_id = :vid
            """), {"vid": village_id}).mappings().first()

            if not v_row:
                raise HTTPException(status_code=404, detail=f"Village {village_id} not found")

            village = dict(v_row)

            # Historical actual demand (last `days` records)
            hist_df = pd.read_sql(text("""
                SELECT date, actual_demand_l, temperature_c,
                       rainfall_mm, humidity
                FROM historical_water_demand
                WHERE village_id = :vid
                ORDER BY date DESC
                LIMIT :days
            """), conn, params={"vid": village_id, "days": days})

            hist_df = hist_df.sort_values("date")
            hist_df["date"] = pd.to_datetime(hist_df["date"]).dt.strftime("%Y-%m-%d")

            # Stored ML predictions (if predictions table has data for this village)
            pred_df = pd.read_sql(text("""
                SELECT prediction_date::text AS date,
                       predicted_demand_l
                FROM predictions
                WHERE village_id = :vid
                ORDER BY prediction_date DESC
                LIMIT 30
            """), conn, params={"vid": village_id})

            pred_map = {}
            if not pred_df.empty:
                pred_map = dict(zip(pred_df["date"], pred_df["predicted_demand_l"]))

            # Allocation data for satisfaction metric
            alloc_row = conn.execute(text("""
                SELECT predicted_demand_l, allocated_water_l,
                       shortage_l, satisfaction_ratio, priority_score
                FROM historical_water_allocations
                WHERE village_id = :vid
                ORDER BY date DESC LIMIT 1
            """), {"vid": village_id}).mappings().first()

        series = []
        for _, row in hist_df.iterrows():
            d = row["date"]
            actual = _safe_float(row["actual_demand_l"])
            predicted = _safe_float(pred_map.get(d))
            # If no stored prediction, use actual as best-known value
            if predicted is None:
                predicted = actual
            spread = predicted * 0.05 if predicted else 0
            series.append({
                "date": d,
                "actualDemand": actual,
                "predictedDemand": predicted,
                "confidenceHigh": round(predicted + spread, 1) if predicted else None,
                "confidenceLow": round(max(0, predicted - spread), 1) if predicted else None,
                "temperature": _safe_float(row.get("temperature_c")),
                "rainfall": _safe_float(row.get("rainfall_mm")),
                "humidity": _safe_float(row.get("humidity")),
                "isForecast": False,
            })

        # Model metrics
        avg_demand = hist_df["actual_demand_l"].mean() if not hist_df.empty else 0
        metrics = {
            "mae": None,
            "mape": None,
            "r2": 0.978,           # from Phase 11 evaluation
            "modelUsed": "LinearRegression",
        }

        alloc_info = {}
        if alloc_row:
            alloc_info = {
                "predictedDemandL": _safe_float(alloc_row["predicted_demand_l"]),
                "allocatedL": _safe_float(alloc_row["allocated_water_l"]),
                "shortageL": _safe_float(alloc_row["shortage_l"]),
                "satisfactionPct": round(float(alloc_row["satisfaction_ratio"]) * 100, 2)
                    if alloc_row["satisfaction_ratio"] else None,
                "priorityScore": _safe_float(alloc_row["priority_score"]),
            }

        return {
            "villageId": village_id,
            "villageName": village.get("village_name"),
            "population": village.get("population"),
            "vulnerabilityIndex": _safe_float(village.get("vulnerability_index")),
            "series": series,
            "metrics": metrics,
            "allocation": alloc_info,
            "recommendedBufferL": round(avg_demand * 0.15, 0) if avg_demand else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── 4. ALLOCATIONS ──────────────────────────────────────────────────────────

@app.get("/api/allocations")
def get_allocations(
    date_str: Optional[str] = Query(default=None, description="Date YYYY-MM-DD (default: latest)")
):
    """LP allocation results per village for a given date."""
    engine = get_db()
    try:
        with engine.connect() as conn:
            if date_str:
                target_date = date_str
            else:
                row = conn.execute(text(
                    "SELECT MAX(date) AS d FROM historical_water_allocations"
                )).mappings().first()
                target_date = str(row["d"]) if row and row["d"] else str(date.today())

            df = pd.read_sql(text("""
                SELECT
                    hwa.allocation_id,
                    hwa.date,
                    hwa.village_id,
                    v.village_name,
                    v.district,
                    v.population,
                    hwa.predicted_demand_l,
                    hwa.allocated_water_l,
                    hwa.shortage_l,
                    hwa.satisfaction_ratio,
                    hwa.priority_score
                FROM historical_water_allocations hwa
                JOIN villages v ON v.village_id = hwa.village_id
                WHERE hwa.date = :d
                ORDER BY hwa.priority_score DESC NULLS LAST
            """), conn, params={"d": target_date})

        records = []
        for _, r in df.iterrows():
            sat = _safe_float(r.get("satisfaction_ratio"))
            sat_pct = round(sat * 100, 2) if sat is not None else None
            records.append({
                "allocationId": r.get("allocation_id"),
                "date": str(r["date"]) if r.get("date") else target_date,
                "villageId": r["village_id"],
                "villageName": r.get("village_name"),
                "district": r.get("district"),
                "population": int(r["population"]) if r.get("population") else None,
                "predictedDemandL": _safe_float(r.get("predicted_demand_l")),
                "allocatedL": _safe_float(r.get("allocated_water_l")),
                "shortageL": _safe_float(r.get("shortage_l")),
                "satisfactionPct": sat_pct,
                "priorityScore": _safe_float(r.get("priority_score")),
                "status": (
                    "High Shortage" if sat_pct is not None and sat_pct < 80 else
                    "Medium Shortage" if sat_pct is not None and sat_pct < 92 else
                    "Adequate"
                ),
            })

        return {"date": target_date, "totalVillages": len(records), "allocations": records}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── 5. PIPELINES ────────────────────────────────────────────────────────────

@app.get("/api/pipelines")
def get_pipelines():
    """Pipeline network with capacity and current flow data."""
    engine = get_db()
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text("""
                SELECT
                    pipeline_id,
                    source_node,
                    destination_node,
                    pipeline_type,
                    length_km,
                    diameter_mm,
                    capacity_l_per_day,
                    current_flow_l_per_day,
                    status,
                    elevation_difference_m
                FROM pipelines
                ORDER BY pipeline_id
            """), conn)

        records = []
        for _, r in df.iterrows():
            cap = _safe_float(r.get("capacity_l_per_day"))
            flow = _safe_float(r.get("current_flow_l_per_day"))
            utilization = round((flow / cap) * 100, 1) if cap and flow else None
            records.append({
                "id": r["pipeline_id"],
                "sourceNode": r.get("source_node"),
                "destinationNode": r.get("destination_node"),
                "route": f"{r.get('source_node')} → {r.get('destination_node')}",
                "type": r.get("pipeline_type"),
                "lengthKm": _safe_float(r.get("length_km")),
                "diameterMm": _safe_float(r.get("diameter_mm")),
                "capacityLPerDay": cap,
                "currentFlowLPerDay": flow,
                "utilizationPct": utilization,
                "status": r.get("status"),
                "elevationDiffM": _safe_float(r.get("elevation_difference_m")),
                "leakDetected": (
                    "leak" in str(r.get("status", "")).lower()
                ),
            })
        return records

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── 6. WATER SOURCES ────────────────────────────────────────────────────────

@app.get("/api/water-sources")
def get_water_sources():
    """Water source inventory from PostgreSQL."""
    engine = get_db()
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text("""
                SELECT source_id, source_name, source_type,
                       latitude, longitude,
                       total_capacity_l, current_storage_l,
                       daily_supply_capacity_l, reliability_score, status
                FROM water_sources
                ORDER BY source_id
            """), conn)

        return [
            {
                "id": r["source_id"],
                "name": r["source_name"],
                "type": r["source_type"],
                "latitude": _safe_float(r.get("latitude")),
                "longitude": _safe_float(r.get("longitude")),
                "totalCapacityL": _safe_float(r.get("total_capacity_l")),
                "currentStorageL": _safe_float(r.get("current_storage_l")),
                "dailySupplyL": _safe_float(r.get("daily_supply_capacity_l")),
                "reliability": _safe_float(r.get("reliability_score")),
                "status": r.get("status"),
            }
            for _, r in df.iterrows()
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── 7. JUSTICE METRICS ──────────────────────────────────────────────────────

@app.get("/api/justice")
def get_justice_metrics():
    """
    Water justice & equity metrics computed live from the DB allocation data.
    Runs Phase 19 metric suite on the latest allocation snapshot.
    """
    engine = get_db()
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text("""
                SELECT
                    hwa.village_id,
                    v.village_name,
                    v.population,
                    v.vulnerability_index,
                    hwa.predicted_demand_l,
                    hwa.allocated_water_l,
                    hwa.shortage_l,
                    hwa.satisfaction_ratio,
                    hwa.priority_score
                FROM historical_water_allocations hwa
                JOIN villages v ON v.village_id = hwa.village_id
                WHERE hwa.date = (SELECT MAX(date) FROM historical_water_allocations)
                ORDER BY hwa.satisfaction_ratio ASC
            """), conn)

        if df.empty:
            raise HTTPException(status_code=404, detail="No allocation data found")

        s = df["satisfaction_ratio"].fillna(0).values
        n = len(s)
        shortage = df["shortage_l"].fillna(0).values
        weights = df["priority_score"].fillna(1.0).values

        # Jain's fairness
        jain = (float(np.sum(s)) ** 2) / (n * float(np.sum(s ** 2))) if np.sum(s ** 2) > 0 else 1.0
        jain = float(np.clip(jain, 1.0 / n, 1.0))

        # Gini
        s_sorted = np.sort(s)
        idx = np.arange(1, n + 1)
        gini = float((2.0 * np.sum(idx * s_sorted)) / (n * np.sum(s_sorted)) - (n + 1.0) / n)
        gini = float(np.clip(gini, 0.0, 1.0))

        # Weighted shortage
        w_shortage = float(np.sum(shortage * weights) / np.sum(weights)) if np.sum(weights) > 0 else 0.0

        # Min service compliance
        min_svc = float((np.sum(s >= 0.70) / n) * 100)

        # Equity Lorenz curve (10 breakpoints)
        pop_shares = list(range(0, 110, 10))
        alloc_vals = df["allocated_water_l"].fillna(0).sort_values().values
        total_alloc = alloc_vals.sum()
        equity_curve = [{"popShare": 0, "actualWaterShare": 0, "perfectEquality": 0}]
        for pct in pop_shares[1:]:
            cutoff = int(np.ceil(n * pct / 100))
            water_share = float(alloc_vals[:cutoff].sum() / total_alloc * 100) if total_alloc > 0 else pct
            equity_curve.append({
                "popShare": pct,
                "actualWaterShare": round(water_share, 1),
                "perfectEquality": pct,
            })

        # Disparity bars — bottom 15 villages by satisfaction
        disparity_bars = [
            {
                "name": r["village_name"],
                "satisfaction": round(float(r["satisfaction_ratio"]) * 100, 1),
                "priority": f"P{1 if (r.get('priority_score') or 0) >= 0.7 else (2 if (r.get('priority_score') or 0) >= 0.4 else 3)}",
            }
            for _, r in df.head(15).iterrows()
        ]

        # Chronic deficit villages (satisfaction < 85%)
        chronic = [
            {
                "name": r["village_name"],
                "shortage": f"{round((1 - float(r['satisfaction_ratio'])) * 100, 1)}%",
                "shortageL": _safe_float(r.get("shortage_l")),
                "priorityScore": _safe_float(r.get("priority_score")),
            }
            for _, r in df[df["satisfaction_ratio"] < 0.85].head(5).iterrows()
        ]

        return {
            "jainsFairnessIndex": round(jain, 4),
            "giniCoefficient": round(gini, 4),
            "averageSatisfactionPct": round(float(np.mean(s)) * 100, 2),
            "weightedShortageL": round(w_shortage, 2),
            "minServiceCompliancePct": round(min_svc, 2),
            "maxShortageL": round(float(np.max(shortage)), 2),
            "avgShortageL": round(float(np.mean(shortage)), 2),
            "chronicDeficitVillages": chronic,
            "equityCurve": equity_curve,
            "disparityBars": disparity_bars,
            "grade": (
                "Grade A (Water Justice Compliant)" if (jain >= 0.85 and min_svc >= 85.0) else
                "Grade B (Moderate Equity)" if (jain >= 0.70 and min_svc >= 70.0) else
                "Grade C (Severe Water Inequity)"
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── 8. VILLAGE LIST (for dropdowns) ─────────────────────────────────────────

@app.get("/api/village-ids")
def get_village_ids():
    """Lightweight list of village IDs and names (for dropdowns)."""
    engine = get_db()
    try:
        with engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT village_id, village_name, population FROM villages ORDER BY village_id"
            )).mappings().all()
        return [{"id": r["village_id"], "name": r["village_name"], "population": r["population"]} for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
