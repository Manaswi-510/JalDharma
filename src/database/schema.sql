-- Jal Dharma AI: Database Schema
-- Phase 6: PostgreSQL Setup

-- 1. Villages Table
CREATE TABLE IF NOT EXISTS villages (
    village_id VARCHAR(50) PRIMARY KEY,
    village_name VARCHAR(150) NOT NULL,
    district VARCHAR(100),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    population INTEGER,
    households INTEGER,
    population_density DOUBLE PRECISION,
    area_km2 DOUBLE PRECISION,
    elevation_m DOUBLE PRECISION,
    vulnerability_index DOUBLE PRECISION,
    accessibility_score DOUBLE PRECISION,
    historical_shortage VARCHAR(50)
);
-- Geometry for villages (Point)
ALTER TABLE villages ADD COLUMN IF NOT EXISTS geom geometry(Point, 4326);
CREATE INDEX IF NOT EXISTS idx_villages_geom ON villages USING GIST(geom);

-- 2. Water Sources Table
CREATE TABLE IF NOT EXISTS water_sources (
    source_id VARCHAR(50) PRIMARY KEY,
    source_name VARCHAR(150),
    source_type VARCHAR(100),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    total_capacity_l DOUBLE PRECISION,
    current_storage_l DOUBLE PRECISION,
    daily_supply_capacity_l DOUBLE PRECISION,
    reliability_score DOUBLE PRECISION,
    status VARCHAR(50)
);
-- Geometry for water sources (Point)
ALTER TABLE water_sources ADD COLUMN IF NOT EXISTS geom geometry(Point, 4326);
CREATE INDEX IF NOT EXISTS idx_water_sources_geom ON water_sources USING GIST(geom);

-- 3. Tanks / Reservoirs Table
CREATE TABLE IF NOT EXISTS tanks_reservoirs (
    tank_id VARCHAR(50) PRIMARY KEY,
    tank_name VARCHAR(150),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    capacity_l DOUBLE PRECISION,
    current_storage_l DOUBLE PRECISION,
    inflow_capacity_l DOUBLE PRECISION,
    outflow_capacity_l DOUBLE PRECISION,
    status VARCHAR(50)
);
-- Geometry for tanks/reservoirs (Point)
ALTER TABLE tanks_reservoirs ADD COLUMN IF NOT EXISTS geom geometry(Point, 4326);
CREATE INDEX IF NOT EXISTS idx_tanks_reservoirs_geom ON tanks_reservoirs USING GIST(geom);

-- 4. Pipelines Table
CREATE TABLE IF NOT EXISTS pipelines (
    pipeline_id VARCHAR(50) PRIMARY KEY,
    source_node VARCHAR(50),
    destination_node VARCHAR(50),
    pipeline_type VARCHAR(100),
    length_km DOUBLE PRECISION,
    diameter_mm DOUBLE PRECISION,
    capacity_l_per_day DOUBLE PRECISION,
    current_flow_l_per_day DOUBLE PRECISION,
    status VARCHAR(50),
    elevation_difference_m DOUBLE PRECISION,
    geometry TEXT
);
-- Geometry for pipelines (LineString) – uses existing TEXT column "geometry"
ALTER TABLE pipelines ADD COLUMN IF NOT EXISTS geom geometry(LineString, 4326);
CREATE INDEX IF NOT EXISTS idx_pipelines_geom ON pipelines USING GIST(geom);

-- 5. Weather Table
CREATE TABLE IF NOT EXISTS weather (
    date DATE,
    location_id VARCHAR(50),
    temperature_c DOUBLE PRECISION,
    min_temperature_c DOUBLE PRECISION,
    max_temperature_c DOUBLE PRECISION,
    rainfall_mm DOUBLE PRECISION,
    humidity_percent DOUBLE PRECISION,
    wind_speed_kmh DOUBLE PRECISION,
    season VARCHAR(50)
);

-- 6. Historical Water Demand Table
CREATE TABLE IF NOT EXISTS historical_water_demand (
    record_id VARCHAR(50) PRIMARY KEY,
    village_id VARCHAR(50) REFERENCES villages(village_id),
    date DATE,
    population INTEGER,
    temperature_c DOUBLE PRECISION,
    rainfall_mm DOUBLE PRECISION,
    humidity DOUBLE PRECISION,
    previous_day_demand_l DOUBLE PRECISION,
    demand_7day_avg_l DOUBLE PRECISION,
    demand_30day_avg_l DOUBLE PRECISION,
    actual_demand_l DOUBLE PRECISION
);

-- 7. Historical Water Allocations Table
CREATE TABLE IF NOT EXISTS historical_water_allocations (
    allocation_id VARCHAR(50) PRIMARY KEY,
    date DATE,
    village_id VARCHAR(50) REFERENCES villages(village_id),
    predicted_demand_l DOUBLE PRECISION,
    requested_water_l DOUBLE PRECISION,
    allocated_water_l DOUBLE PRECISION,
    shortage_l DOUBLE PRECISION,
    satisfaction_ratio DOUBLE PRECISION,
    priority_score DOUBLE PRECISION
);

-- 8. Water Availability Table
CREATE TABLE IF NOT EXISTS water_availability (
    date DATE,
    source_id VARCHAR(50) REFERENCES water_sources(source_id),
    initial_storage_l DOUBLE PRECISION,
    inflow_l DOUBLE PRECISION,
    outflow_l DOUBLE PRECISION,
    reserved_water_l DOUBLE PRECISION,
    loss_l DOUBLE PRECISION,
    available_water_l DOUBLE PRECISION
);

-- 9. Water Quality Table
CREATE TABLE IF NOT EXISTS water_quality (
    source_id VARCHAR(50) REFERENCES water_sources(source_id),
    date DATE,
    ph DOUBLE PRECISION,
    turbidity_ntu DOUBLE PRECISION,
    tds_mg_l DOUBLE PRECISION,
    temperature_c DOUBLE PRECISION,
    quality_index DOUBLE PRECISION
);

-- 10. Scenario Simulation Table
CREATE TABLE IF NOT EXISTS scenario_simulation (
    scenario_id VARCHAR(50) PRIMARY KEY,
    scenario_name VARCHAR(150),
    rainfall_change_percent DOUBLE PRECISION,
    population_change_percent DOUBLE PRECISION,
    water_availability_percent DOUBLE PRECISION,
    pipeline_failure VARCHAR(20),
    failed_pipeline_id VARCHAR(50),
    source_capacity_change DOUBLE PRECISION
);
