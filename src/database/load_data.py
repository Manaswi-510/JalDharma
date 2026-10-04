import pandas as pd
from pathlib import Path
from sqlalchemy import text
from src.database.connection import get_engine, test_connection

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "synthetic"
SCHEMA_FILE = BASE_DIR / "src" / "database" / "schema.sql"

TABLES_ORDER = [
    "scenario_simulation",
    "water_quality",
    "water_availability",
    "historical_water_allocations",
    "historical_water_demand",
    "weather",
    "pipelines",
    "tanks_reservoirs",
    "water_sources",
    "villages",
]

def recreate_tables_if_empty(engine):
    """Drops and recreates tables to guarantee proper schema."""
    print("Recreating tables to ensure accurate schema...")
    with engine.begin() as conn:
        for t in TABLES_ORDER:
            conn.execute(text(f"DROP TABLE IF EXISTS {t} CASCADE;"))

    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    with engine.begin() as conn:
        statements = [stmt.strip() for stmt in schema_sql.split(";") if stmt.strip()]
        for stmt in statements:
            conn.execute(text(stmt))
    print("All tables created successfully.")

def load_data(engine):
    """Loads all synthetic CSVs into PostgreSQL tables."""
    print("\nLoading synthetic datasets into PostgreSQL...")

    # 1. Villages
    village_file = DATA_DIR / "1_village_dataset.csv"
    if village_file.exists():
        df_village = pd.read_csv(village_file)
        df_village.to_sql("villages", engine, if_exists="append", index=False)
        print(f" Loaded {len(df_village)} rows into 'villages'")

    # 2. Water Sources
    source_file = DATA_DIR / "4_water_source_dataset.csv"
    if source_file.exists():
        df_source = pd.read_csv(source_file)
        df_source.to_sql("water_sources", engine, if_exists="append", index=False)
        print(f" Loaded {len(df_source)} rows into 'water_sources'")

    # 3. Tanks
    tank_file = DATA_DIR / "6_tank_reservoir_dataset.csv"
    if tank_file.exists():
        df_tank = pd.read_csv(tank_file)
        df_tank.to_sql("tanks_reservoirs", engine, if_exists="append", index=False)
        print(f" Loaded {len(df_tank)} rows into 'tanks_reservoirs'")

    # 4. Pipelines
    pipeline_file = DATA_DIR / "5_pipeline_water_network_dataset.csv"
    if pipeline_file.exists():
        df_pipe = pd.read_csv(pipeline_file)
        df_pipe.to_sql("pipelines", engine, if_exists="append", index=False)
        print(f" Loaded {len(df_pipe)} rows into 'pipelines'")

    # 5. Weather
    weather_file = DATA_DIR / "3_weather_dataset.csv"
    if weather_file.exists():
        df_weather = pd.read_csv(weather_file)
        df_weather["date"] = pd.to_datetime(df_weather["date"], format="%Y-%m-%d")
        df_weather.to_sql("weather", engine, if_exists="append", index=False)
        print(f" Loaded {len(df_weather)} rows into 'weather'")

    # 6. Historical Demand
    demand_file = DATA_DIR / "2_historical_water_demand_dataset.csv"
    if demand_file.exists():
        df_demand = pd.read_csv(demand_file)
        df_demand["date"] = pd.to_datetime(df_demand["date"], format="%d-%m-%Y")
        df_demand.to_sql("historical_water_demand", engine, if_exists="append", index=False, chunksize=1000)
        print(f" Loaded {len(df_demand)} rows into 'historical_water_demand'")

    # 7. Historical Allocations
    alloc_file = DATA_DIR / "7_historical_water_allocation_dataset.csv"
    if alloc_file.exists():
        df_alloc = pd.read_csv(alloc_file)
        df_alloc["date"] = pd.to_datetime(df_alloc["date"], format="%Y-%m-%d")
        df_alloc.to_sql("historical_water_allocations", engine, if_exists="append", index=False, chunksize=1000)
        print(f" Loaded {len(df_alloc)} rows into 'historical_water_allocations'")

    # 8. Water Availability
    avail_file = DATA_DIR / "8_water_availability_dataset.csv"
    if avail_file.exists():
        df_avail = pd.read_csv(avail_file)
        df_avail["date"] = pd.to_datetime(df_avail["date"], format="%Y-%m-%d")
        df_avail.to_sql("water_availability", engine, if_exists="append", index=False, chunksize=1000)
        print(f" Loaded {len(df_avail)} rows into 'water_availability'")

    # 9. Water Quality
    quality_file = DATA_DIR / "9_water_quality_dataset.csv"
    if quality_file.exists():
        df_quality = pd.read_csv(quality_file)
        df_quality["date"] = pd.to_datetime(df_quality["date"], format="%Y-%m-%d")
        df_quality.to_sql("water_quality", engine, if_exists="append", index=False)
        print(f" Loaded {len(df_quality)} rows into 'water_quality'")

    # 10. Scenario Simulation
    scenario_file = DATA_DIR / "11_scenario_simulation_dataset.csv"
    if scenario_file.exists():
        df_scen = pd.read_csv(scenario_file)
        df_scen.to_sql("scenario_simulation", engine, if_exists="append", index=False)
        print(f" Loaded {len(df_scen)} rows into 'scenario_simulation'")

def populate_geometry(engine):
    """Populate PostGIS geometry columns from latitude/longitude after CSV load."""
    print("\nPopulating PostGIS geometry columns...")
    with engine.begin() as conn:
        # Villages (Point)
        conn.execute(text(
            "UPDATE villages SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326) "
            "WHERE geom IS NULL AND longitude IS NOT NULL AND latitude IS NOT NULL"
        ))
        print("  [OK] villages.geom populated")

        # Water Sources (Point)
        conn.execute(text(
            "UPDATE water_sources SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326) "
            "WHERE geom IS NULL AND longitude IS NOT NULL AND latitude IS NOT NULL"
        ))
        print("  [OK] water_sources.geom populated")

        # Tanks / Reservoirs (Point)
        conn.execute(text(
            "UPDATE tanks_reservoirs SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326) "
            "WHERE geom IS NULL AND longitude IS NOT NULL AND latitude IS NOT NULL"
        ))
        print("  [OK] tanks_reservoirs.geom populated")

        # Pipelines (LineString from WKT text in 'geometry' column)
        conn.execute(text(
            "UPDATE pipelines SET geom = ST_GeomFromText(geometry, 4326) "
            "WHERE geom IS NULL AND geometry IS NOT NULL"
        ))
        print("  [OK] pipelines.geom populated")

def main():
    if not test_connection():
        print("Cannot proceed with data loading because the database connection failed.")
        return

    engine = get_engine()
    recreate_tables_if_empty(engine)
    load_data(engine)
    populate_geometry(engine)
    print("\n[SUCCESS] Phase 6 & 7 Complete: PostgreSQL + PostGIS database 'jal_dharma' is fully loaded!")

if __name__ == "__main__":
    main()
