"""
Water Availability
============================
For every source:

    Current storage + Expected inflow - Reserved - Expected loss = Available storage

Because the storage reservoirs are huge (billions of litres) compared with
daily village demand (millions of litres), storage alone never limits supply.
What a source can actually hand over in ONE DAY is limited by its
`daily_supply_capacity_l`. So:

    Deliverable today = min(Available storage, Daily supply capacity)

Checklist
    15.1  Calculate source availability
    15.2  Calculate total available water
    15.3  Calculate predicted total demand
    15.4  Calculate overall shortage  =  max(0, Demand - Available)

Outputs feed Phase 16 (LP):  S_s = source deliverable,  D_i = village demand.

Run with:   python -m src.optimization.water_availability
"""

import pandas as pd
from pathlib import Path
from sqlalchemy import text

from src.database.connection import get_engine

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "synthetic"

LOOKBACK_DAYS = 7          # days used to estimate expected inflow / loss
DEMAND_BASIS = "upper"     # "point" = expected demand, "upper" = 90% conservative


# ------------------------------------------------------------------
#  Data loading (PostgreSQL first, CSV fallback - same style as Phase 13)
# ------------------------------------------------------------------

def load_sources(engine=None):
    try:
        return pd.read_sql("SELECT * FROM water_sources", engine)
    except Exception as e:
        print(f"[WARN] water_sources: DB fallback to CSV ({e})")
        return pd.read_csv(DATA_DIR / "4_water_source_dataset.csv")


def load_availability_history(engine=None):
    try:
        df = pd.read_sql("SELECT * FROM water_availability", engine)
    except Exception as e:
        print(f"[WARN] water_availability: DB fallback to CSV ({e})")
        df = pd.read_csv(DATA_DIR / "8_water_availability_dataset.csv")
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values(["source_id", "date"]).reset_index(drop=True)


def load_predicted_demand(engine=None):
    """
    Latest stored prediction per village (from Phase 9-11 prediction service).
    Falls back to the mean of each village's last 7 actual demands if the
    `predictions` table is missing or empty.

    Returns DataFrame: village_id, demand_point_l, demand_upper_l, demand_source
    """
    try:
        df = pd.read_sql(text("""
            SELECT DISTINCT ON (village_id)
                   village_id, prediction_date,
                   predicted_demand_l AS demand_point_l,
                   COALESCE(upper_demand_l, predicted_demand_l) AS demand_upper_l
            FROM predictions
            WHERE prediction_date = (SELECT MAX(prediction_date) FROM predictions)
            ORDER BY village_id, created_at DESC
        """), engine)
        if not df.empty:
            df["demand_source"] = "predictions table"
            return df[["village_id", "demand_point_l", "demand_upper_l", "demand_source"]]
        print("[WARN] predictions table is empty - using recent actual demand.")
    except Exception as e:
        print(f"[WARN] predictions unavailable ({e}) - using recent actual demand.")

    try:
        hist = pd.read_sql(text(
            "SELECT village_id, date, actual_demand_l FROM historical_water_demand"
        ), engine)
        hist["date"] = pd.to_datetime(hist["date"])
    except Exception:
        hist = pd.read_csv(DATA_DIR / "2_historical_water_demand_dataset.csv")
        hist["date"] = pd.to_datetime(hist["date"], dayfirst=True)

    hist = hist.sort_values(["village_id", "date"])
    base = (hist.groupby("village_id").tail(7)
                .groupby("village_id")["actual_demand_l"].mean()
                .reset_index(name="demand_point_l"))
    base["demand_upper_l"] = base["demand_point_l"]
    base["demand_source"] = "7-day average (fallback)"
    return base


# ------------------------------------------------------------------
#  15.1  Source availability
# ------------------------------------------------------------------

def calculate_source_availability(sources, history,
                                  lookback_days=LOOKBACK_DAYS,
                                  availability_factor=1.0,
                                  capacity_change_pct=0.0):
    """
    availability_factor  : 1.0 = normal. 0.7 = only 70% of water is available.
    capacity_change_pct  : e.g. -25 reduces daily supply capacity by 25%.
    (Both default to 'no change'; they exist so Phase 23 scenarios can reuse this.)
    """
    rows = []
    for _, src in sources.iterrows():
        sid = src["source_id"]
        h = history[history["source_id"] == sid].sort_values("date")
        if h.empty:
            print(f"[WARN] No availability history for {sid} - skipped.")
            continue

        last = h.iloc[-1]
        recent = h.tail(lookback_days)

        # Closing storage of the latest day = storage at the start of tomorrow
        current_storage = (last["initial_storage_l"] + last["inflow_l"]
                           - last["outflow_l"] - last["loss_l"])
        expected_inflow = recent["inflow_l"].mean()
        expected_loss = recent["loss_l"].mean()
        reserved = last["reserved_water_l"]

        # Core Phase-15 formula (+ losses, consistent with the dataset)
        available_storage = max(
            0.0, current_storage + expected_inflow - reserved - expected_loss
        )

        daily_capacity = src["daily_supply_capacity_l"] * (1 + capacity_change_pct / 100)
        is_active = str(src.get("status", "Active")).strip().lower() == "active"

        deliverable = min(available_storage, daily_capacity) * availability_factor
        if not is_active:
            deliverable = 0.0

        rows.append({
            "source_id": sid,
            "source_name": src["source_name"],
            "status": src.get("status", "Active"),
            "current_storage_l": current_storage,
            "expected_inflow_l": expected_inflow,
            "reserved_l": reserved,
            "expected_loss_l": expected_loss,
            "available_storage_l": available_storage,
            "daily_capacity_l": daily_capacity,
            "deliverable_l_per_day": deliverable,
            "binding_limit": "storage" if available_storage < daily_capacity
                             else "daily capacity",
        })

    return pd.DataFrame(rows)


# ------------------------------------------------------------------
#  15.2 / 15.3 / 15.4
# ------------------------------------------------------------------

def calculate_total_available(source_df):
    return float(source_df["deliverable_l_per_day"].sum())


def calculate_total_demand(demand_df, basis=DEMAND_BASIS):
    col = "demand_upper_l" if basis == "upper" else "demand_point_l"
    return float(demand_df[col].sum())


def calculate_shortage(total_demand, total_available):
    """Shortage = max(0, Demand - Available)."""
    shortage = max(0.0, total_demand - total_available)
    pct = (shortage / total_demand * 100) if total_demand > 0 else 0.0
    return shortage, pct


# ------------------------------------------------------------------
#  Orchestration
# ------------------------------------------------------------------

def run_water_availability(engine=None, demand_basis=DEMAND_BASIS,
                           availability_factor=1.0, capacity_change_pct=0.0,
                           verbose=True):
    if engine is None:
        engine = get_engine()

    sources = load_sources(engine)
    history = load_availability_history(engine)
    demand_df = load_predicted_demand(engine)

    source_df = calculate_source_availability(
        sources, history,
        availability_factor=availability_factor,
        capacity_change_pct=capacity_change_pct,
    )
    total_available = calculate_total_available(source_df)
    total_demand = calculate_total_demand(demand_df, demand_basis)
    shortage, shortage_pct = calculate_shortage(total_demand, total_available)

    result = {
        "source_availability": source_df,
        "village_demand": demand_df,
        "total_available_l": total_available,
        "total_demand_l": total_demand,
        "shortage_l": shortage,
        "shortage_pct": shortage_pct,
        "coverage_ratio": min(1.0, total_available / total_demand) if total_demand else 1.0,
        "demand_basis": demand_basis,
    }
    if verbose:
        print_report(result)
    return result


def print_report(r):
    print("\n" + "=" * 66)
    print("  PHASE 15 - WATER AVAILABILITY")
    print("=" * 66)

    print("\n  15.1  Source availability")
    for _, s in r["source_availability"].iterrows():
        print(f"\n  {s['source_name']} ({s['source_id']})  [{s['status']}]")
        print(f"    Current storage        : {s['current_storage_l']/1e9:>12,.3f} B L")
        print(f"    + Expected inflow/day  : {s['expected_inflow_l']/1e6:>12,.2f} ML")
        print(f"    - Reserved             : {s['reserved_l']/1e9:>12,.3f} B L")
        print(f"    - Expected loss/day    : {s['expected_loss_l']/1e6:>12,.2f} ML")
        print(f"    = Available storage    : {s['available_storage_l']/1e9:>12,.3f} B L")
        print(f"    Daily supply capacity  : {s['daily_capacity_l']/1e6:>12,.2f} ML/day")
        print(f"    Deliverable today      : {s['deliverable_l_per_day']/1e6:>12,.2f} ML/day"
              f"   (limited by {s['binding_limit']})")

    print("\n  15.2  Total available water (deliverable per day)")
    print(f"    {r['total_available_l']:>16,.0f} L/day  ({r['total_available_l']/1e6:,.2f} ML/day)")

    d = r["village_demand"]
    print(f"\n  15.3  Predicted total demand  [{r['demand_basis']}; source: {d['demand_source'].iloc[0]}]")
    print(f"    Villages               : {len(d)}")
    print(f"    Total demand           : {r['total_demand_l']:>16,.0f} L/day  ({r['total_demand_l']/1e6:,.2f} ML/day)")

    print("\n  15.4  Overall shortage = max(0, Demand - Available)")
    print(f"    Shortage               : {r['shortage_l']:>16,.0f} L/day  ({r['shortage_pct']:.2f}% of demand)")
    print(f"    Demand coverage        : {r['coverage_ratio']*100:.1f}%")
    if r["shortage_l"] == 0:
        print("    [OK] Source water is sufficient. Any shortfall in later phases")
        print("         will come from pipeline bottlenecks, not from the sources.")
    else:
        print("    [WARN] Sources cannot meet total demand - allocation must prioritise.")
    print("=" * 66)


if __name__ == "__main__":
    run_water_availability()
    print("\n[SUCCESS] water availability & shortage calculated!")