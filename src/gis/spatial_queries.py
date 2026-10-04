import pandas as pd
from sqlalchemy import text
from src.database.connection import get_engine

def setup_postgis_geometries():
    """Adds PostGIS geometry columns and spatial indexes to existing tables."""
    engine = get_engine()
    
    queries = [
        "CREATE EXTENSION IF NOT EXISTS postgis;",
        "ALTER TABLE villages ADD COLUMN IF NOT EXISTS geom geometry(Point, 4326);",
        "UPDATE villages SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326) WHERE geom IS NULL;",
        "ALTER TABLE water_sources ADD COLUMN IF NOT EXISTS geom geometry(Point, 4326);",
        "UPDATE water_sources SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326) WHERE geom IS NULL;",
        "ALTER TABLE tanks_reservoirs ADD COLUMN IF NOT EXISTS geom geometry(Point, 4326);",
        "UPDATE tanks_reservoirs SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326) WHERE geom IS NULL;",
        "ALTER TABLE pipelines ADD COLUMN IF NOT EXISTS geom geometry(LineString, 4326);",
        "UPDATE pipelines SET geom = ST_GeomFromText(geometry, 4326) WHERE geom IS NULL AND geometry IS NOT NULL;",
        "CREATE INDEX IF NOT EXISTS idx_villages_geom ON villages USING GIST(geom);",
        "CREATE INDEX IF NOT EXISTS idx_water_sources_geom ON water_sources USING GIST(geom);",
        "CREATE INDEX IF NOT EXISTS idx_pipelines_geom ON pipelines USING GIST(geom);"
    ]
    
    with engine.begin() as conn:
        for q in queries:
            conn.execute(text(q))
    print("[SUCCESS] PostGIS geometry columns and spatial indexes created.")

def find_villages_within_distance(radius_km=30):
    """Phase 7.5 & 7.6: Finds villages within radius_km of any water source."""
    engine = get_engine()
    sql = text("""
        SELECT 
            v.village_id,
            v.village_name,
            s.source_name,
            ROUND((ST_Distance(v.geom::geography, s.geom::geography) / 1000)::numeric, 2) AS distance_km
        FROM villages v
        CROSS JOIN water_sources s
        WHERE ST_DWithin(v.geom::geography, s.geom::geography, :radius_m)
        ORDER BY distance_km;
    """)
    df = pd.read_sql(sql, engine, params={"radius_m": radius_km * 1000})
    return df

def get_nearest_sources_for_villages():
    """Phase 7.7: Spatial join to find nearest water source for every village."""
    engine = get_engine()
    sql = text("""
        SELECT DISTINCT ON (v.village_id)
            v.village_id,
            v.village_name,
            v.district,
            s.source_id AS nearest_source_id,
            s.source_name AS nearest_source_name,
            ROUND((ST_Distance(v.geom::geography, s.geom::geography) / 1000)::numeric, 2) AS distance_km
        FROM villages v
        CROSS JOIN water_sources s
        ORDER BY v.village_id, ST_Distance(v.geom::geography, s.geom::geography);
    """)
    df = pd.read_sql(sql, engine)
    return df

if __name__ == "__main__":
    setup_postgis_geometries()
    print("\n--- Testing Spatial Queries (Phase 7.5 - 7.7) ---")
    nearest_df = get_nearest_sources_for_villages()
    print(f"\nNearest sources for {len(nearest_df)} villages (sample):")
    print(nearest_df.head(10).to_string(index=False))
