-- Phase 7: PostGIS Spatial Configuration & Queries

-- 7.1 Enable PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;

-- 7.2 Add Geometry Column to Villages (POINT)
ALTER TABLE villages ADD COLUMN IF NOT EXISTS geom geometry(Point, 4326);
UPDATE villages 
SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
WHERE geom IS NULL;

-- 7.3 Add Geometry Column to Water Sources & Tanks (POINT)
ALTER TABLE water_sources ADD COLUMN IF NOT EXISTS geom geometry(Point, 4326);
UPDATE water_sources 
SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
WHERE geom IS NULL;

ALTER TABLE tanks_reservoirs ADD COLUMN IF NOT EXISTS geom geometry(Point, 4326);
UPDATE tanks_reservoirs 
SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
WHERE geom IS NULL;

-- 7.4 Add Geometry Column to Pipelines (LINESTRING)
ALTER TABLE pipelines ADD COLUMN IF NOT EXISTS geom geometry(LineString, 4326);
UPDATE pipelines 
SET geom = ST_GeomFromText(geometry, 4326) 
WHERE geom IS NULL AND geometry IS NOT NULL;

-- Spatial Indexes (GIST) for high-speed spatial searches
CREATE INDEX IF NOT EXISTS idx_villages_geom ON villages USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_water_sources_geom ON water_sources USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_pipelines_geom ON pipelines USING GIST(geom);

-- 7.5, 7.6, 7.7: Spatial Query Verification
-- Query: Find nearest water source and distance (in km) for each village
SELECT DISTINCT ON (v.village_id)
    v.village_id,
    v.village_name,
    s.source_name AS nearest_source,
    ROUND((ST_Distance(v.geom::geography, s.geom::geography) / 1000)::numeric, 2) AS distance_km
FROM villages v
CROSS JOIN water_sources s
ORDER BY v.village_id, ST_Distance(v.geom::geography, s.geom::geography);
