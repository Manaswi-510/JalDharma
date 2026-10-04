import folium
import pandas as pd
import networkx as nx
from pathlib import Path
from src.database.connection import get_engine

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "synthetic"
OUTPUT_DIR = BASE_DIR / "outputs" / "maps"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_network_data():
    """Loads all spatial network entities from PostgreSQL or CSV fallback."""
    try:
        engine = get_engine()
        villages = pd.read_sql("SELECT * FROM villages", engine)
        sources = pd.read_sql("SELECT * FROM water_sources", engine)
        tanks = pd.read_sql("SELECT * FROM tanks_reservoirs", engine)
        pipelines = pd.read_sql("SELECT * FROM pipelines", engine)
        print("[INFO] Network data loaded from PostgreSQL.")
    except Exception as e:
        print(f"[WARN] Failed to load from PostgreSQL ({e}), falling back to CSV.")
        villages = pd.read_csv(DATA_DIR / "1_village_dataset.csv")
        sources = pd.read_csv(DATA_DIR / "4_water_source_dataset.csv")
        tanks = pd.read_csv(DATA_DIR / "6_tank_reservoir_dataset.csv")
        pipelines = pd.read_csv(DATA_DIR / "5_pipeline_water_network_dataset.csv")
        
    return villages, sources, tanks, pipelines

def build_network_graph(villages, sources, tanks, pipelines):
    """Phase 8.1 - 8.4: Builds and validates network connectivity."""
    G = nx.DiGraph()
    
    # 8.1 Add Sources
    for _, row in sources.iterrows():
        G.add_node(
            row["source_id"], 
            name=row["source_name"], 
            type="source",
            lat=row["latitude"], 
            lon=row["longitude"],
            capacity=row["total_capacity_l"]
        )
        
    # 8.2 Add Tanks
    for _, row in tanks.iterrows():
        G.add_node(
            row["tank_id"], 
            name=row["tank_name"], 
            type="tank",
            lat=row["latitude"], 
            lon=row["longitude"],
            capacity=row["capacity_l"]
        )
        
    # 8.3 Add Villages
    for _, row in villages.iterrows():
        G.add_node(
            row["village_id"], 
            name=row["village_name"], 
            type="village",
            lat=row["latitude"], 
            lon=row["longitude"],
            population=row["population"],
            vulnerability=row.get("vulnerability_index", 0.5)
        )
        
    # 8.4 Add Pipelines
    for _, row in pipelines.iterrows():
        G.add_edge(
            row["source_node"], 
            row["destination_node"], 
            pipeline_id=row["pipeline_id"],
            capacity=row["capacity_l_per_day"],
            length_km=row["length_km"],
            status=row.get("status", "Working")
        )
        
    return G

def verify_network_connectivity(G, villages, sources):
    """Phase 8.5 & 8.6: Verifies connections and flags disconnected villages."""
    print("\n--- Phase 8.5 & 8.6: Network Connectivity Verification ---")
    print(f"Total Nodes: {G.number_of_nodes()} (Sources: {len(sources)}, Tanks: 5, Villages: {len(villages)})")
    print(f"Total Pipelines (Edges): {G.number_of_edges()}")
    
    source_ids = set(sources["source_id"])
    village_ids = set(villages["village_id"])
    
    reachable_villages = set()
    for s in source_ids:
        if s in G:
            descendants = nx.descendants(G, s)
            reachable_villages.update(descendants.intersection(village_ids))
            
    disconnected = village_ids - reachable_villages
    if disconnected:
        print(f"[WARNING] Found {len(disconnected)} disconnected village(s): {disconnected}")
    else:
        print(f"[OK] All {len(village_ids)} villages are fully connected to at least one water source!")
        
    return disconnected

def visualize_network(G, villages, sources, tanks, pipelines):
    """Phase 8.7: Creates an interactive Folium map visualization."""
    center_lat = villages["latitude"].mean()
    center_lon = villages["longitude"].mean()
    
    m = folium.Map(
        location=[center_lat, center_lon], 
        zoom_start=10, 
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri &mdash; Source: Esri, DeLorme, NAVTEQ, USGS"
    )
    
    # 1. Add Pipelines (Edges)
    for u, v, data in G.edges(data=True):
        if u in G.nodes and v in G.nodes:
            p1 = [G.nodes[u]["lat"], G.nodes[u]["lon"]]
            p2 = [G.nodes[v]["lat"], G.nodes[v]["lon"]]
            
            cap_mld = data['capacity'] / 1_000_000
            popup_html = f"""
            <b>Pipeline:</b> {data['pipeline_id']}<br>
            <b>From:</b> {u} &rarr; <b>To:</b> {v}<br>
            <b>Capacity:</b> {cap_mld:.1f} M Litres/day<br>
            <b>Length:</b> {data['length_km']} km<br>
            <b>Status:</b> {data['status']}
            """
            
            folium.PolyLine(
                locations=[p1, p2],
                color="#1E88E5",
                weight=3,
                opacity=0.75,
                tooltip=f"Pipeline {data['pipeline_id']} ({cap_mld:.1f} ML/day)",
                popup=popup_html
            ).add_to(m)
            
    # 2. Add Sources (Blue markers)
    for s_id, node in G.nodes(data=True):
        if node.get("type") == "source":
            folium.Marker(
                location=[node["lat"], node["lon"]],
                popup=f"<b>Water Source:</b> {node['name']}<br><b>Capacity:</b> {node['capacity']/1e9:.1f} Billion Litres",
                tooltip=f"Source: {node['name']}",
                icon=folium.Icon(color="darkblue", icon="tint", prefix="fa")
            ).add_to(m)
            
    # 3. Add Tanks (Green markers)
    for t_id, node in G.nodes(data=True):
        if node.get("type") == "tank":
            folium.Marker(
                location=[node["lat"], node["lon"]],
                popup=f"<b>Storage Tank:</b> {node['name']}<br><b>Capacity:</b> {node['capacity']/1e6:.1f} M Litres",
                tooltip=f"Tank: {node['name']}",
                icon=folium.Icon(color="green", icon="database", prefix="fa")
            ).add_to(m)
            
    # 4. Add Villages (Red/Orange Circle Markers)
    for v_id, node in G.nodes(data=True):
        if node.get("type") == "village":
            vuln = node.get("vulnerability", 0.5)
            color = "#E53935" if vuln > 0.6 else "#FB8C00" if vuln > 0.4 else "#43A047"
            
            folium.CircleMarker(
                location=[node["lat"], node["lon"]],
                radius=6,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.8,
                popup=f"<b>Village:</b> {node['name']} ({v_id})<br><b>Population:</b> {node.get('population', 'N/A')}<br><b>Vulnerability Score:</b> {vuln:.2f}",
                tooltip=f"{node['name']} (Pop: {node.get('population', 'N/A')})"
            ).add_to(m)
            
    map_path = OUTPUT_DIR / "water_network_map.html"
    m.save(str(map_path))
    print(f"[SUCCESS] Interactive network map saved to:\n   {map_path}")
    return map_path

def main():
    villages, sources, tanks, pipelines = load_network_data()
    G = build_network_graph(villages, sources, tanks, pipelines)
    verify_network_connectivity(G, villages, sources)
    visualize_network(G, villages, sources, tanks, pipelines)
    print("\n[SUCCESS] Phase 8 Complete: GIS Water Network Built, Connected & Visualized!")

if __name__ == "__main__":
    main()
