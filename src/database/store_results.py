"""
Jal Dharma AI
PHASE 21: Store Results in PostgreSQL
======================================
Stores allocation and pipeline flow results from Phases 16-20 directly
into PostgreSQL tables.

Schema Requirements (Phase 21):
-------------------------------
1. allocations:
     - allocation_id       SERIAL PRIMARY KEY
     - date                DATE NOT NULL
     - village_id          VARCHAR(50) NOT NULL
     - predicted_demand    DOUBLE PRECISION NOT NULL
     - allocated_water     DOUBLE PRECISION NOT NULL
     - shortage            DOUBLE PRECISION NOT NULL
     - satisfaction_ratio  DOUBLE PRECISION NOT NULL
     - priority_score      DOUBLE PRECISION NOT NULL
     - strategy            VARCHAR(50) (e.g. 'Equity-Aware', 'Proportional', 'Max-Flow')
     - created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP

2. pipeline_flows:
     - flow_id             SERIAL PRIMARY KEY
     - pipeline_id         VARCHAR(50) NOT NULL
     - date                DATE NOT NULL
     - flow                DOUBLE PRECISION NOT NULL
     - capacity            DOUBLE PRECISION NOT NULL
     - utilization         DOUBLE PRECISION NOT NULL
     - strategy            VARCHAR(50)
     - created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP

Run with:
    python -m src.database.store_results
"""

import sys
from pathlib import Path
from datetime import date

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from sqlalchemy import text

from src.database.connection import get_engine

BASE_DIR = Path(__file__).resolve().parent.parent.parent
OUTPUTS_DIR = BASE_DIR / "outputs"


# =========================================================================
# STEP 21.1: CREATE TABLES
# =========================================================================

CREATE_ALLOCATIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS allocations (
    allocation_id       SERIAL PRIMARY KEY,
    date                DATE NOT NULL,
    village_id          VARCHAR(50) NOT NULL,
    predicted_demand    DOUBLE PRECISION NOT NULL,
    allocated_water     DOUBLE PRECISION NOT NULL,
    shortage            DOUBLE PRECISION NOT NULL,
    satisfaction_ratio  DOUBLE PRECISION NOT NULL,
    priority_score      DOUBLE PRECISION NOT NULL,
    strategy            VARCHAR(50) DEFAULT 'Equity-Aware',
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_PIPELINE_FLOWS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pipeline_flows (
    flow_id             SERIAL PRIMARY KEY,
    pipeline_id         VARCHAR(50) NOT NULL,
    date                DATE NOT NULL,
    flow                DOUBLE PRECISION NOT NULL,
    capacity            DOUBLE PRECISION NOT NULL,
    utilization         DOUBLE PRECISION NOT NULL,
    strategy            VARCHAR(50) DEFAULT 'Equity-Aware',
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def ensure_tables(engine):
    """Ensure allocations and pipeline_flows tables exist with all required Phase 21 columns."""
    with engine.begin() as conn:
        # Create pipeline_flows table
        conn.execute(text(CREATE_PIPELINE_FLOWS_TABLE_SQL))

        # Check and upgrade allocations table if it was created previously with older column names
        conn.execute(text(CREATE_ALLOCATIONS_TABLE_SQL))
        
        # Add any missing Phase 21 columns if table already existed
        for col_def in [
            "ADD COLUMN IF NOT EXISTS date DATE",
            "ADD COLUMN IF NOT EXISTS predicted_demand DOUBLE PRECISION",
            "ADD COLUMN IF NOT EXISTS allocated_water DOUBLE PRECISION",
            "ADD COLUMN IF NOT EXISTS shortage DOUBLE PRECISION",
            "ADD COLUMN IF NOT EXISTS satisfaction_ratio DOUBLE PRECISION",
            "ADD COLUMN IF NOT EXISTS priority_score DOUBLE PRECISION",
            "ADD COLUMN IF NOT EXISTS strategy VARCHAR(50)",
        ]:
            try:
                conn.execute(text(f"ALTER TABLE allocations {col_def}"))
            except Exception:
                pass


# =========================================================================
# STEP 21.2: STORE ALLOCATIONS
# =========================================================================

def store_village_allocations(engine, df: pd.DataFrame, run_date: date = None):
    """
    Store village allocation rows into `allocations` table.
    Expects DataFrame with:
      village_id, predicted_demand, allocated_water, shortage, satisfaction_ratio, priority_score, strategy
    """
    if run_date is None:
        run_date = date.today()

    records = []
    for _, row in df.iterrows():
        dem = float(row.get("predicted_demand") or row.get("predicted_demand_l") or 0.0)
        alloc = float(row.get("allocated_water") or row.get("allocated_water_l") or 0.0)
        short = max(0.0, dem - alloc)
        sat = (alloc / dem) if dem > 0 else 1.0
        score = float(row.get("priority_score") or row.get("vulnerability_index") or 0.5)
        strat = str(row.get("strategy", "Equity-Aware"))

        record_date = row.get("date") or run_date
        if isinstance(record_date, str):
            record_date = pd.to_datetime(record_date).date()

        records.append({
            "date": record_date,
            "village_id": str(row["village_id"]),
            "predicted_demand": dem,
            "allocated_water": alloc,
            "shortage": short,
            "satisfaction_ratio": round(sat, 4),
            "satisfaction_pct": round(sat * 100.0, 2),
            "priority_score": round(score, 4),
            "strategy": strat,
        })

    insert_sql = text("""
        INSERT INTO allocations (
            date,
            allocation_date,
            village_id,
            predicted_demand,
            predicted_demand_l,
            allocated_water,
            allocated_water_l,
            shortage,
            shortage_l,
            satisfaction_ratio,
            satisfaction_pct,
            priority_score,
            strategy
        )
        VALUES (
            :date,
            :date,
            :village_id,
            :predicted_demand,
            :predicted_demand,
            :allocated_water,
            :allocated_water,
            :shortage,
            :shortage,
            :satisfaction_ratio,
            :satisfaction_pct,
            :priority_score,
            :strategy
        )
    """)

    with engine.begin() as conn:
        conn.execute(insert_sql, records)

    print(f"[SUCCESS] Stored {len(records)} village records into PostgreSQL `allocations` table!")
    return len(records)


# =========================================================================
# STEP 21.3: STORE PIPELINE FLOWS
# =========================================================================

def store_pipeline_flows(engine, df: pd.DataFrame, run_date: date = None, strategy: str = "Equity-Aware"):
    """
    Store pipeline flow rows into `pipeline_flows` table.
    Expects DataFrame with:
      pipeline_id, flow, capacity, utilization
    """
    if run_date is None:
        run_date = date.today()

    records = []
    for _, row in df.iterrows():
        flow_val = float(row.get("flow") or row.get("flow_l_per_day") or 0.0)
        cap_val = float(row.get("capacity") or row.get("capacity_l_per_day") or row.get("effective_capacity_l") or 0.0)
        util_val = float(row.get("utilization") or row.get("utilization_pct") or row.get("utilization_percent") or 0.0)
        strat = str(row.get("strategy") or strategy)

        record_date = row.get("date") or run_date
        if isinstance(record_date, str):
            record_date = pd.to_datetime(record_date).date()

        records.append({
            "pipeline_id": str(row["pipeline_id"]),
            "date": record_date,
            "flow": round(flow_val, 1),
            "capacity": round(cap_val, 1),
            "utilization": round(util_val, 2),
            "strategy": strat,
        })

    insert_sql = text("""
        INSERT INTO pipeline_flows (
            pipeline_id,
            date,
            flow,
            capacity,
            utilization,
            strategy
        )
        VALUES (
            :pipeline_id,
            :date,
            :flow,
            :capacity,
            :utilization,
            :strategy
        )
    """)

    with engine.begin() as conn:
        conn.execute(insert_sql, records)

    print(f"[SUCCESS] Stored {len(records)} pipeline flow records into PostgreSQL `pipeline_flows` table!")
    return len(records)


# =========================================================================
# STEP 21.4: LOAD COMPARATIVE RESULTS & STORE TO POSTGRESQL
# =========================================================================

def store_phase20_comparison_results(engine=None):
    """
    Load the comparative results from Phase 20 (Proportional, Max-Flow, Equity-Aware)
    and store all allocations and pipeline flows to PostgreSQL.
    """
    if engine is None:
        engine = get_engine()

    ensure_tables(engine)

    # 1. Load Compared Allocations from Phase 20
    comp_file = OUTPUTS_DIR / "justice" / "village_allocations_compared.csv"
    if comp_file.exists():
        df_comp = pd.read_csv(comp_file)
        today = date.today()

        # Prepare records for each of the 3 strategies
        all_alloc_records = []

        # Strategy A: Proportional
        for _, r in df_comp.iterrows():
            all_alloc_records.append({
                "date": today,
                "village_id": r["village_id"],
                "predicted_demand": r["predicted_demand_l"],
                "allocated_water": r["alloc_proportional_l"],
                "shortage": max(0.0, r["predicted_demand_l"] - r["alloc_proportional_l"]),
                "satisfaction_ratio": r["sat_proportional"],
                "priority_score": r["priority_score"],
                "strategy": "Proportional",
            })

        # Strategy B: Max-Flow
        for _, r in df_comp.iterrows():
            all_alloc_records.append({
                "date": today,
                "village_id": r["village_id"],
                "predicted_demand": r["predicted_demand_l"],
                "allocated_water": r["alloc_max_flow_l"],
                "shortage": max(0.0, r["predicted_demand_l"] - r["alloc_max_flow_l"]),
                "satisfaction_ratio": r["sat_max_flow"],
                "priority_score": r["priority_score"],
                "strategy": "Max-Flow",
            })

        # Strategy C: Equity-Aware (The flagship model)
        for _, r in df_comp.iterrows():
            all_alloc_records.append({
                "date": today,
                "village_id": r["village_id"],
                "predicted_demand": r["predicted_demand_l"],
                "allocated_water": r["alloc_equity_aware_l"],
                "shortage": max(0.0, r["predicted_demand_l"] - r["alloc_equity_aware_l"]),
                "satisfaction_ratio": r["sat_equity_aware"],
                "priority_score": r["priority_score"],
                "strategy": "Equity-Aware",
            })

        df_to_store = pd.DataFrame(all_alloc_records)
        store_village_allocations(engine, df_to_store, run_date=today)
    else:
        print(f"[WARN] {comp_file} not found. Running Phase 16 to generate allocations...")
        from src.optimization.lp_allocator import run_phase16_lp
        alloc_df, _ = run_phase16_lp(engine, store=False)
        alloc_df["predicted_demand"] = alloc_df["predicted_demand_l"]
        alloc_df["allocated_water"] = alloc_df["allocated_water_l"]
        alloc_df["shortage"] = alloc_df["shortage_l"]
        alloc_df["satisfaction_ratio"] = alloc_df["satisfaction_pct"] / 100.0
        alloc_df["priority_score"] = alloc_df["vulnerability_index"]
        alloc_df["strategy"] = "Equity-Aware"
        store_village_allocations(engine, alloc_df)

    # 2. Load Pipeline Flows
    pipe_file = OUTPUTS_DIR / "simulation" / "scenario_pipeline_flows.csv"
    if pipe_file.exists():
        df_pipes = pd.read_csv(pipe_file)
        # Filter for baseline scenario SCN_01
        if "scenario_id" in df_pipes.columns:
            df_pipes = df_pipes[df_pipes["scenario_id"] == "SCN_01"].copy()

        df_pipes["flow"] = df_pipes["flow_l_per_day"]
        df_pipes["capacity"] = df_pipes["effective_capacity_l"]
        df_pipes["utilization"] = df_pipes["utilization_percent"]
        df_pipes["strategy"] = "Equity-Aware"
        store_pipeline_flows(engine, df_pipes, run_date=date.today())
    else:
        # Fallback to LP allocator flows
        print("[INFO] Generating fresh pipeline flows from LP allocator...")
        from src.optimization.lp_allocator import run_phase16_lp
        _, flows_df = run_phase16_lp(engine, store=False)
        flows_df["flow"] = flows_df["flow_l_per_day"]
        flows_df["capacity"] = flows_df["capacity_l_per_day"]
        flows_df["utilization"] = flows_df["utilization_pct"]
        flows_df["strategy"] = "Equity-Aware"
        store_pipeline_flows(engine, flows_df, run_date=date.today())

    # 3. Print verification report
    print_verification_report(engine)


def print_verification_report(engine):
    """Query and display stored data from PostgreSQL."""
    print("\n" + "=" * 75)
    print("PHASE 21 - POSTGRESQL STORAGE VERIFICATION REPORT")
    print("=" * 75)

    with engine.connect() as conn:
        alloc_count = conn.execute(text("SELECT count(*) FROM allocations;")).scalar()
        flow_count = conn.execute(text("SELECT count(*) FROM pipeline_flows;")).scalar()

        print(f"Total Rows in `allocations`     : {alloc_count}")
        print(f"Total Rows in `pipeline_flows`  : {flow_count}")

        print("\n--- SAMPLE STORED ALLOCATIONS (Strategy = Equity-Aware) ---")
        sample_alloc = conn.execute(text("""
            SELECT 
                allocation_id,
                date,
                village_id,
                ROUND(predicted_demand::numeric, 0) AS predicted_demand,
                ROUND(allocated_water::numeric, 0) AS allocated_water,
                ROUND(shortage::numeric, 0) AS shortage,
                ROUND(satisfaction_ratio::numeric, 2) AS satisfaction_ratio,
                priority_score,
                strategy
            FROM allocations
            WHERE strategy = 'Equity-Aware'
            ORDER BY allocation_id DESC
            LIMIT 5;
        """)).mappings().fetchall()

        df_a = pd.DataFrame(sample_alloc)
        print(df_a.to_string(index=False) if not df_a.empty else "No records")

        print("\n--- SAMPLE STORED PIPELINE FLOWS ---")
        sample_flows = conn.execute(text("""
            SELECT 
                flow_id,
                pipeline_id,
                date,
                ROUND(flow::numeric, 0) AS flow,
                ROUND(capacity::numeric, 0) AS capacity,
                utilization,
                strategy
            FROM pipeline_flows
            ORDER BY flow_id DESC
            LIMIT 5;
        """)).mappings().fetchall()

        df_f = pd.DataFrame(sample_flows)
        print(df_f.to_string(index=False) if not df_f.empty else "No records")

    print("\n[SUCCESS] Phase 21 Complete: All allocations and pipeline flows stored in PostgreSQL!")


if __name__ == "__main__":
    store_phase20_comparison_results()
