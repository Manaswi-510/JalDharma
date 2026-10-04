"""
Phase 8.7 - GeoPandas & Plotly Visualizations
Generates:
  1. A static spatial map (PNG) using GeoPandas + Matplotlib
  2. An interactive network graph (HTML) using Plotly
"""

import pandas as pd
import geopandas as gpd
import networkx as nx
import plotly.graph_objects as go
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for saving PNGs
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from shapely.geometry import Point, LineString
from shapely import wkt
from pathlib import Path
from src.database.connection import get_engine

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "synthetic"
OUTPUT_DIR = BASE_DIR / "outputs" / "maps"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------------ #
#  Data Loading                                                       #
# ------------------------------------------------------------------ #

def load_data():
    """Load spatial data from PostgreSQL (fallback to CSV)."""
    try:
        engine = get_engine()
        villages = pd.read_sql("SELECT * FROM villages", engine)
        sources = pd.read_sql("SELECT * FROM water_sources", engine)
        tanks = pd.read_sql("SELECT * FROM tanks_reservoirs", engine)
        pipelines = pd.read_sql("SELECT * FROM pipelines", engine)
        print("[INFO] Data loaded from PostgreSQL.")
    except Exception as e:
        print(f"[WARN] DB fallback to CSV ({e})")
        villages = pd.read_csv(DATA_DIR / "1_village_dataset.csv")
        sources = pd.read_csv(DATA_DIR / "4_water_source_dataset.csv")
        tanks = pd.read_csv(DATA_DIR / "6_tank_reservoir_dataset.csv")
        pipelines = pd.read_csv(DATA_DIR / "5_pipeline_water_network_dataset.csv")

    return villages, sources, tanks, pipelines


# ------------------------------------------------------------------ #
#  1. GeoPandas Static Map (PNG)                                       #
# ------------------------------------------------------------------ #

def plot_geopandas_map(villages, sources, tanks, pipelines):
    """
    Creates a publication-quality static map:
    - Villages: circles color-coded by vulnerability (red=high, orange=medium, green=low)
    - Water Sources: large blue squares
    - Tanks: green diamonds
    - Pipelines: blue lines connecting nodes
    """
    print("\n--- Generating GeoPandas Static Map ---")

    # Convert to GeoDataFrames
    gdf_villages = gpd.GeoDataFrame(
        villages,
        geometry=[Point(lon, lat) for lon, lat in zip(villages["longitude"], villages["latitude"])],
        crs="EPSG:4326"
    )

    gdf_sources = gpd.GeoDataFrame(
        sources,
        geometry=[Point(lon, lat) for lon, lat in zip(sources["longitude"], sources["latitude"])],
        crs="EPSG:4326"
    )

    gdf_tanks = gpd.GeoDataFrame(
        tanks,
        geometry=[Point(lon, lat) for lon, lat in zip(tanks["longitude"], tanks["latitude"])],
        crs="EPSG:4326"
    )

    # Build pipeline geometries from WKT or from source/dest coordinates
    pipe_geoms = []
    for _, row in pipelines.iterrows():
        if pd.notna(row.get("geometry")) and str(row["geometry"]).strip():
            try:
                pipe_geoms.append(wkt.loads(row["geometry"]))
            except Exception:
                pipe_geoms.append(None)
        else:
            pipe_geoms.append(None)

    gdf_pipelines = gpd.GeoDataFrame(
        pipelines,
        geometry=pipe_geoms,
        crs="EPSG:4326"
    )
    gdf_pipelines = gdf_pipelines[gdf_pipelines.geometry.notna()]

    # ----- Plot -----
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#16213e")

    # Pipelines (blue lines)
    if not gdf_pipelines.empty:
        gdf_pipelines.plot(ax=ax, color="#42a5f5", linewidth=1.5, alpha=0.7, zorder=1)

    # Villages (color by vulnerability)
    def vuln_color(v):
        if v > 0.6:
            return "#ef5350"   # red - high vulnerability
        elif v > 0.4:
            return "#ffa726"   # orange - medium
        else:
            return "#66bb6a"   # green - low

    village_colors = gdf_villages["vulnerability_index"].apply(vuln_color)
    gdf_villages.plot(
        ax=ax, color=village_colors, markersize=50,
        edgecolor="white", linewidth=0.5, zorder=3, alpha=0.9
    )

    # Water Sources (large blue markers)
    gdf_sources.plot(
        ax=ax, color="#1565c0", marker="s", markersize=120,
        edgecolor="white", linewidth=1.5, zorder=4
    )

    # Tanks (green diamonds)
    gdf_tanks.plot(
        ax=ax, color="#2e7d32", marker="D", markersize=90,
        edgecolor="white", linewidth=1.5, zorder=4
    )

    # Labels for sources
    for _, row in gdf_sources.iterrows():
        ax.annotate(
            row["source_name"], xy=(row["longitude"], row["latitude"]),
            fontsize=7, color="white", fontweight="bold",
            xytext=(5, 5), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="#1565c0", alpha=0.8)
        )

    # Labels for tanks
    for _, row in gdf_tanks.iterrows():
        ax.annotate(
            row["tank_name"], xy=(row["longitude"], row["latitude"]),
            fontsize=6, color="white",
            xytext=(5, -10), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="#2e7d32", alpha=0.8)
        )

    # Legend
    legend_elements = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#ef5350", markersize=10, label="Village (High Vulnerability)", linestyle="None"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#ffa726", markersize=10, label="Village (Medium Vulnerability)", linestyle="None"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#66bb6a", markersize=10, label="Village (Low Vulnerability)", linestyle="None"),
        Line2D([0], [0], marker="s", color="w", markerfacecolor="#1565c0", markersize=12, label="Water Source", linestyle="None"),
        Line2D([0], [0], marker="D", color="w", markerfacecolor="#2e7d32", markersize=10, label="Tank / Reservoir", linestyle="None"),
        Line2D([0], [0], color="#42a5f5", linewidth=2, label="Pipeline"),
    ]
    legend = ax.legend(
        handles=legend_elements, loc="lower left", fontsize=8,
        facecolor="#1a1a2e", edgecolor="#42a5f5", labelcolor="white"
    )
    legend.get_frame().set_alpha(0.9)

    ax.set_title("Jal Dharma - Water Distribution Network", fontsize=16, color="white", fontweight="bold", pad=15)
    ax.set_xlabel("Longitude", fontsize=10, color="#aaa")
    ax.set_ylabel("Latitude", fontsize=10, color="#aaa")
    ax.tick_params(colors="#888")
    for spine in ax.spines.values():
        spine.set_edgecolor("#42a5f5")

    plt.tight_layout()
    out_path = OUTPUT_DIR / "network_static_map.png"
    fig.savefig(str(out_path), dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"[OK] GeoPandas static map saved to:\n   {out_path}")
    return out_path


# ------------------------------------------------------------------ #
#  2. Plotly Interactive Network Graph (HTML)                          #
# ------------------------------------------------------------------ #

def plot_plotly_network(villages, sources, tanks, pipelines):
    """
    Creates an interactive Plotly network graph:
    - Nodes: sources (blue), tanks (green), villages (colored by vulnerability)
    - Edges: pipelines with hover info
    """
    print("\n--- Generating Plotly Interactive Network Graph ---")

    # Build NetworkX graph for layout
    G = nx.DiGraph()

    for _, r in sources.iterrows():
        G.add_node(r["source_id"], label=r["source_name"], type="source",
                    lat=r["latitude"], lon=r["longitude"],
                    info=f"Source: {r['source_name']}<br>Capacity: {r['total_capacity_l']/1e9:.1f}B L<br>Status: {r['status']}")

    for _, r in tanks.iterrows():
        G.add_node(r["tank_id"], label=r["tank_name"], type="tank",
                    lat=r["latitude"], lon=r["longitude"],
                    info=f"Tank: {r['tank_name']}<br>Capacity: {r['capacity_l']/1e6:.1f}M L<br>Status: {r['status']}")

    for _, r in villages.iterrows():
        vuln = r.get("vulnerability_index", 0.5)
        G.add_node(r["village_id"], label=r["village_name"], type="village",
                    lat=r["latitude"], lon=r["longitude"], vulnerability=vuln,
                    info=f"Village: {r['village_name']}<br>Pop: {r['population']}<br>Vulnerability: {vuln:.2f}")

    for _, r in pipelines.iterrows():
        G.add_edge(r["source_node"], r["destination_node"],
                    pid=r["pipeline_id"],
                    info=f"Pipeline: {r['pipeline_id']}<br>Capacity: {r['capacity_l_per_day']/1e6:.1f}M L/day<br>Length: {r['length_km']} km<br>Status: {r['status']}")

    # Use geographic positions (lon, lat)
    pos = {n: (d["lon"], d["lat"]) for n, d in G.nodes(data=True) if "lon" in d}

    # ----- Edge traces -----
    edge_x, edge_y = [], []
    edge_hover = []
    for u, v, data in G.edges(data=True):
        if u in pos and v in pos:
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            edge_x += [x0, x1, None]
            edge_y += [y0, y1, None]
            # Midpoint for hover
            edge_hover.append(dict(x=(x0 + x1) / 2, y=(y0 + y1) / 2, text=data.get("info", "")))

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line=dict(width=1.5, color="#42a5f5"),
        hoverinfo="none", name="Pipelines"
    )

    # Edge midpoint hover trace
    edge_mid_trace = go.Scatter(
        x=[e["x"] for e in edge_hover],
        y=[e["y"] for e in edge_hover],
        text=[e["text"] for e in edge_hover],
        mode="markers", hoverinfo="text",
        marker=dict(size=5, color="rgba(66,165,245,0.3)"),
        name="Pipeline Info"
    )

    # ----- Node traces (separate by type for legend) -----
    def make_node_trace(node_type, color, symbol, size, name):
        nodes = [(n, d) for n, d in G.nodes(data=True) if d.get("type") == node_type and n in pos]
        return go.Scatter(
            x=[pos[n][0] for n, d in nodes],
            y=[pos[n][1] for n, d in nodes],
            text=[d.get("info", "") for n, d in nodes],
            mode="markers+text",
            textposition="top center",
            textfont=dict(size=8, color="white"),
            hoverinfo="text",
            name=name,
            marker=dict(size=size, color=color, symbol=symbol,
                        line=dict(width=1, color="white"))
        )

    source_trace = make_node_trace("source", "#1565c0", "square", 18, "Water Sources")
    tank_trace = make_node_trace("tank", "#2e7d32", "diamond", 14, "Tanks")

    # Villages with vulnerability coloring
    village_nodes = [(n, d) for n, d in G.nodes(data=True) if d.get("type") == "village" and n in pos]
    village_colors = []
    for n, d in village_nodes:
        v = d.get("vulnerability", 0.5)
        if v > 0.6:
            village_colors.append("#ef5350")
        elif v > 0.4:
            village_colors.append("#ffa726")
        else:
            village_colors.append("#66bb6a")

    village_trace = go.Scatter(
        x=[pos[n][0] for n, d in village_nodes],
        y=[pos[n][1] for n, d in village_nodes],
        text=[d.get("info", "") for n, d in village_nodes],
        mode="markers",
        hoverinfo="text",
        name="Villages",
        marker=dict(size=10, color=village_colors, symbol="circle",
                    line=dict(width=0.5, color="white"))
    )

    # ----- Layout -----
    fig = go.Figure(
        data=[edge_trace, edge_mid_trace, source_trace, tank_trace, village_trace],
        layout=go.Layout(
            title=dict(text="Jal Dharma - Interactive Water Network Graph", font=dict(size=18, color="white")),
            showlegend=True,
            legend=dict(font=dict(color="white"), bgcolor="rgba(26,26,46,0.8)"),
            hovermode="closest",
            xaxis=dict(title="Longitude", showgrid=False, color="#888", gridcolor="#333"),
            yaxis=dict(title="Latitude", showgrid=False, color="#888", gridcolor="#333", scaleanchor="x"),
            paper_bgcolor="#1a1a2e",
            plot_bgcolor="#16213e",
            margin=dict(l=40, r=40, t=60, b=40),
        )
    )

    out_path = OUTPUT_DIR / "network_plotly.html"
    fig.write_html(str(out_path))
    print(f"[OK] Plotly interactive graph saved to:\n   {out_path}")
    return out_path


# ------------------------------------------------------------------ #
#  Main                                                               #
# ------------------------------------------------------------------ #

def main():
    villages, sources, tanks, pipelines = load_data()
    plot_geopandas_map(villages, sources, tanks, pipelines)
    plot_plotly_network(villages, sources, tanks, pipelines)
    print("\n[SUCCESS] Phase 8.7 Complete: All three visualizations (Folium + GeoPandas + Plotly) are ready!")

if __name__ == "__main__":
    main()
