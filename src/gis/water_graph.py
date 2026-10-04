"""
Phase 13: GIS Network -> Graph (PostGIS -> NetworkX Graph Algorithms)
=====================================================================
Loads the water network from PostgreSQL and builds a weighted directed
graph with pipeline capacities, source capacities, and runs connectivity
and flow analysis.

Checklist:
  13.1  Create NetworkX DiGraph
  13.2  Add nodes  (sources, tanks, villages)
  13.3  Add edges  (pipelines)
  13.4  Add pipeline capacities as edge weights
  13.5  Add source capacities as node attributes
  13.6  Test connectivity  (reachability, shortest path, max-flow)
"""

import pandas as pd
import networkx as nx
from sqlalchemy import text
from pathlib import Path
from src.database.connection import get_engine

BASE_DIR   = Path(__file__).resolve().parent.parent.parent
DATA_DIR   = BASE_DIR / "data" / "synthetic"


# ─────────────────────────────────────────────
#  Data loading
# ─────────────────────────────────────────────

def load_data(engine):
    try:
        villages  = pd.read_sql("SELECT * FROM villages",        engine)
        sources   = pd.read_sql("SELECT * FROM water_sources",   engine)
        tanks     = pd.read_sql("SELECT * FROM tanks_reservoirs",engine)
        pipelines = pd.read_sql("SELECT * FROM pipelines",       engine)
        print("[INFO] Data loaded from PostgreSQL.")
    except Exception as e:
        print(f"[WARN] DB fallback to CSV: {e}")
        villages  = pd.read_csv(DATA_DIR / "1_village_dataset.csv")
        sources   = pd.read_csv(DATA_DIR / "4_water_source_dataset.csv")
        tanks     = pd.read_csv(DATA_DIR / "6_tank_reservoir_dataset.csv")
        pipelines = pd.read_csv(DATA_DIR / "5_pipeline_water_network_dataset.csv")
    return villages, sources, tanks, pipelines


# ─────────────────────────────────────────────
#  13.1  Create NetworkX DiGraph
# ─────────────────────────────────────────────

def build_graph(villages, sources, tanks, pipelines) -> nx.DiGraph:
    """
    Build a weighted directed graph:
        Node  = source / tank / village
        Edge  = pipeline  (weight = capacity_l_per_day)
    """
    G = nx.DiGraph()

    # ── 13.2  Add nodes ────────────────────────────────────────────

    # Sources  (13.5: source capacity as node attribute)
    for _, r in sources.iterrows():
        G.add_node(
            r["source_id"],
            label       = r["source_name"],
            node_type   = "source",
            lat         = r["latitude"],
            lon         = r["longitude"],
            # 13.5 — capacity attributes
            total_capacity_l        = r["total_capacity_l"],
            daily_supply_capacity_l = r["daily_supply_capacity_l"],
            current_storage_l       = r["current_storage_l"],
            reliability_score       = r["reliability_score"],
            status                  = r["status"],
        )

    # Tanks
    for _, r in tanks.iterrows():
        G.add_node(
            r["tank_id"],
            label             = r["tank_name"],
            node_type         = "tank",
            lat               = r["latitude"],
            lon               = r["longitude"],
            capacity_l        = r["capacity_l"],
            current_storage_l = r["current_storage_l"],
            inflow_capacity_l = r["inflow_capacity_l"],
            outflow_capacity_l= r["outflow_capacity_l"],
            status            = r["status"],
        )

    # Villages
    for _, r in villages.iterrows():
        G.add_node(
            r["village_id"],
            label          = r["village_name"],
            node_type      = "village",
            lat            = r["latitude"],
            lon            = r["longitude"],
            population     = r["population"],
            vulnerability  = r.get("vulnerability_index", 0.5),
        )

    # ── 13.3 + 13.4  Add edges with pipeline capacity weights ──────

    skipped = 0
    for _, r in pipelines.iterrows():
        src  = r["source_node"]
        dst  = r["destination_node"]
        if src not in G.nodes or dst not in G.nodes:
            skipped += 1
            continue
        G.add_edge(
            src, dst,
            pipeline_id          = r["pipeline_id"],
            # 13.4 — capacity as the primary edge weight
            capacity             = r["capacity_l_per_day"],   # L/day
            capacity_ml          = r["capacity_l_per_day"] / 1_000_000,  # ML/day
            current_flow_l       = r["current_flow_l_per_day"],
            length_km            = r["length_km"],
            diameter_mm          = r["diameter_mm"],
            pipeline_type        = r["pipeline_type"],
            status               = r.get("status", "Working"),
            # NetworkX max-flow uses "capacity" key by default ↑
        )

    print(f"[INFO] Graph built: {G.number_of_nodes()} nodes, "
          f"{G.number_of_edges()} edges  ({skipped} edges skipped — unknown nodes)")
    return G


# ─────────────────────────────────────────────
#  13.6  Connectivity & graph-algorithm tests
# ─────────────────────────────────────────────

def test_connectivity(G: nx.DiGraph, sources, villages):
    """
    13.6a  Reachability — which villages can be reached from each source?
    """
    print("\n" + "=" * 55)
    print("  13.6a  Reachability (source -> villages)")
    print("=" * 55)

    source_ids  = [r["source_id"]  for _, r in sources.iterrows()]
    village_ids = set(r["village_id"] for _, r in villages.iterrows())

    all_reachable = set()
    for sid in source_ids:
        desc = nx.descendants(G, sid)
        reachable_villages = desc & village_ids
        all_reachable |= reachable_villages
        src_name = G.nodes[sid]["label"]
        cap_b    = G.nodes[sid]["total_capacity_l"] / 1e9
        print(f"\n  Source: {src_name} ({sid})")
        print(f"    Total capacity  : {cap_b:.2f} Billion L")
        print(f"    Reachable nodes : {len(desc)}")
        print(f"    Villages served : {len(reachable_villages)}")

    disconnected = village_ids - all_reachable
    print(f"\n  Total reachable villages : {len(all_reachable)} / {len(village_ids)}")
    if disconnected:
        print(f"  [WARN] Disconnected      : {disconnected}")
    else:
        print("  [OK] All villages are reachable from at least one source.")


def test_shortest_path(G: nx.DiGraph):
    """
    13.6b  Shortest path by pipeline length (km).
           Find the shortest distance path from each source to every village.
    """
    print("\n" + "=" * 55)
    print("  13.6b  Shortest Path by Pipeline Length (km)")
    print("=" * 55)

    sources  = [n for n, d in G.nodes(data=True) if d["node_type"] == "source"]
    villages = [n for n, d in G.nodes(data=True) if d["node_type"] == "village"]

    # Show the 5 shortest source->village paths overall
    all_paths = []
    for src in sources:
        try:
            lengths = nx.single_source_dijkstra_path_length(
                G, src, weight="length_km"
            )
            for vid, dist in lengths.items():
                if vid in villages:
                    all_paths.append((dist, src, vid))
        except nx.NetworkXError:
            pass

    all_paths.sort()
    print("\n  Top 5 shortest source -> village paths:")
    print(f"  {'Distance':>10}  {'Source':<12}  {'Village'}")
    print("  " + "-" * 48)
    for dist, src, vid in all_paths[:5]:
        s_name = G.nodes[src]["label"]
        v_name = G.nodes[vid]["label"]
        print(f"  {dist:>8.2f} km  {src:<12}  {v_name} ({vid})")

    print("\n  Top 5 longest source -> village paths:")
    print(f"  {'Distance':>10}  {'Source':<12}  {'Village'}")
    print("  " + "-" * 48)
    for dist, src, vid in all_paths[-5:][::-1]:
        s_name = G.nodes[src]["label"]
        v_name = G.nodes[vid]["label"]
        print(f"  {dist:>8.2f} km  {src:<12}  {v_name} ({vid})")


def test_max_flow(G: nx.DiGraph):
    """
    13.6c  Maximum Flow — how much total water can flow from
           a super-source (all sources combined) to a super-sink
           (all villages combined)?
    Uses NetworkX's Edmonds-Karp max-flow algorithm.
    """
    print("\n" + "=" * 55)
    print("  13.6c  Maximum Flow (Edmonds-Karp)")
    print("=" * 55)

    # Build a copy with a super-source and super-sink
    H = G.copy()
    SUPER_SOURCE = "__SUPER_SOURCE__"
    SUPER_SINK   = "__SUPER_SINK__"
    H.add_node(SUPER_SOURCE)
    H.add_node(SUPER_SINK)

    sources  = [n for n, d in G.nodes(data=True) if d["node_type"] == "source"]
    villages = [n for n, d in G.nodes(data=True) if d["node_type"] == "village"]

    # Super-source -> each real source (capacity = source daily_supply_capacity_l)
    for sid in sources:
        cap = G.nodes[sid].get("daily_supply_capacity_l", 0)
        H.add_edge(SUPER_SOURCE, sid, capacity=cap)

    # Each village -> super-sink (capacity = effectively unlimited)
    for vid in villages:
        H.add_edge(vid, SUPER_SINK, capacity=float("inf"))

    flow_value, flow_dict = nx.maximum_flow(
        H, SUPER_SOURCE, SUPER_SINK, capacity="capacity"
    )

    print(f"\n  Max flow (network capacity): {flow_value:>15,.0f} L/day")
    print(f"                            = {flow_value/1e6:>12,.2f} ML/day")
    print(f"                            = {flow_value/1e9:>12,.4f} BL/day")

    print("\n  Flow from each source:")
    for sid in sources:
        f = flow_dict[SUPER_SOURCE].get(sid, 0)
        print(f"    {G.nodes[sid]['label']:<35} {f:>15,.0f} L/day")


def test_graph_stats(G: nx.DiGraph):
    """13.6d  General graph statistics."""
    print("\n" + "=" * 55)
    print("  13.6d  Graph Statistics")
    print("=" * 55)

    sources  = [n for n, d in G.nodes(data=True) if d["node_type"] == "source"]
    tanks    = [n for n, d in G.nodes(data=True) if d["node_type"] == "tank"]
    villages = [n for n, d in G.nodes(data=True) if d["node_type"] == "village"]

    # Total pipeline capacity
    total_cap = sum(d.get("capacity", 0) for _, _, d in G.edges(data=True))
    total_len = sum(d.get("length_km", 0) for _, _, d in G.edges(data=True))

    # Total source capacity
    total_src_cap = sum(
        G.nodes[n].get("daily_supply_capacity_l", 0) for n in sources
    )

    print(f"\n  Nodes               : {G.number_of_nodes()}")
    print(f"    Sources           : {len(sources)}")
    print(f"    Tanks             : {len(tanks)}")
    print(f"    Villages          : {len(villages)}")
    print(f"  Edges (pipelines)   : {G.number_of_edges()}")
    print(f"  Total pipeline len  : {total_len:,.1f} km")
    print(f"  Total pipe capacity : {total_cap:>15,.0f} L/day  ({total_cap/1e6:.2f} ML/day)")
    print(f"  Total source supply : {total_src_cap:>15,.0f} L/day  ({total_src_cap/1e6:.2f} ML/day)")

    # Average edges per node
    avg_deg = G.number_of_edges() / max(G.number_of_nodes(), 1)
    print(f"  Avg edges/node      : {avg_deg:.2f}")

    # Weakly connected components
    wcc = list(nx.weakly_connected_components(G))
    print(f"  Connected components: {len(wcc)}")
    if len(wcc) > 1:
        sizes = sorted([len(c) for c in wcc], reverse=True)
        print(f"    Component sizes   : {sizes}")


# -----------------------------------------
#  Plotly Interactive Visualisation
# -----------------------------------------

def visualize_plotly(G: nx.DiGraph, out_dir: Path = None):
    """
    Save an interactive Plotly graph of the water network.
    - Sources  : large blue squares
    - Tanks    : green diamonds
    - Villages : circles coloured by vulnerability
    - Edges    : lines, thickness proportional to pipeline capacity
    """
    import plotly.graph_objects as go

    if out_dir is None:
        out_dir = BASE_DIR / "outputs" / "maps"
    out_dir.mkdir(parents=True, exist_ok=True)

    pos = {n: (d["lon"], d["lat"]) for n, d in G.nodes(data=True) if "lon" in d}
    max_cap = max((d.get("capacity", 1) for _, _, d in G.edges(data=True)), default=1)

    # --- Edge traces ---
    edge_traces = []
    for u, v, data in G.edges(data=True):
        if u not in pos or v not in pos:
            continue
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        cap    = data.get("capacity", 0)
        width  = 1 + 6 * (cap / max_cap)
        hover  = (
            f"Pipeline: {data.get('pipeline_id','?')}<br>"
            f"From: {G.nodes[u].get('label', u)} -> {G.nodes[v].get('label', v)}<br>"
            f"Capacity: {cap/1e6:.1f} ML/day<br>"
            f"Length: {data.get('length_km','?')} km<br>"
            f"Status: {data.get('status','?')}"
        )
        edge_traces.append(go.Scatter(
            x=[x0, x1, None], y=[y0, y1, None],
            mode="lines",
            line=dict(width=width, color="rgba(66,165,245,0.6)"),
            hoverinfo="text", text=hover,
            showlegend=False,
        ))

    # --- Node helper ---
    def node_trace(node_type, symbol, base_color, size, legend_name):
        nodes = [(n, d) for n, d in G.nodes(data=True)
                 if d.get("node_type") == node_type and n in pos]
        if not nodes:
            return None
        xs, ys, hovers, colors = [], [], [], []
        for n, d in nodes:
            xs.append(pos[n][0])
            ys.append(pos[n][1])
            if node_type == "source":
                hovers.append(
                    f"<b>Source: {d['label']}</b><br>"
                    f"Total capacity: {d.get('total_capacity_l',0)/1e9:.1f} B L<br>"
                    f"Daily supply: {d.get('daily_supply_capacity_l',0)/1e6:.1f} ML/day<br>"
                    f"Status: {d.get('status','?')}"
                )
                colors.append(base_color)
            elif node_type == "tank":
                hovers.append(
                    f"<b>Tank: {d['label']}</b><br>"
                    f"Capacity: {d.get('capacity_l',0)/1e6:.1f} ML<br>"
                    f"Inflow: {d.get('inflow_capacity_l',0)/1e6:.1f} ML/day<br>"
                    f"Status: {d.get('status','?')}"
                )
                colors.append(base_color)
            else:
                vuln = d.get("vulnerability", 0.5)
                colors.append("#ef5350" if vuln > 0.6 else "#ffa726" if vuln > 0.4 else "#66bb6a")
                hovers.append(
                    f"<b>Village: {d['label']}</b> ({n})<br>"
                    f"Population: {d.get('population','?')}<br>"
                    f"Vulnerability: {vuln:.2f}"
                )
        return go.Scatter(
            x=xs, y=ys,
            mode="markers+text" if node_type in ("source","tank") else "markers",
            text=[G.nodes[n]["label"] for n,_ in nodes] if node_type in ("source","tank") else None,
            textposition="top center",
            textfont=dict(size=8, color="white"),
            hovertext=hovers, hoverinfo="text",
            name=legend_name,
            marker=dict(
                symbol=symbol, size=size,
                color=colors if node_type=="village" else base_color,
                line=dict(width=1.5, color="white"),
            ),
        )

    src_tr = node_trace("source",  "square",  "#1565c0", 20, "Water Source")
    tnk_tr = node_trace("tank",    "diamond", "#2e7d32", 16, "Tank/Reservoir")
    vil_tr = node_trace("village", "circle",  None,      10, "Village")

    fig = go.Figure(
        data=edge_traces + [t for t in [src_tr, tnk_tr, vil_tr] if t],
        layout=go.Layout(
            title=dict(
                text="Phase 13 - Jal Dharma Water Network Graph",
                font=dict(size=20, color="white"), x=0.5,
            ),
            showlegend=True,
            legend=dict(font=dict(color="white", size=12),
                        bgcolor="rgba(26,26,46,0.85)",
                        bordercolor="#42a5f5", borderwidth=1),
            hovermode="closest",
            xaxis=dict(title="Longitude", showgrid=True, gridcolor="#1e3050",
                       color="#aaa", zeroline=False),
            yaxis=dict(title="Latitude",  showgrid=True, gridcolor="#1e3050",
                       color="#aaa", zeroline=False, scaleanchor="x"),
            paper_bgcolor="#0f0f1a",
            plot_bgcolor="#111827",
            margin=dict(l=40, r=40, t=70, b=40),
            annotations=[dict(
                text="Edge width = pipeline capacity  |  Village colour: red=high vuln, orange=medium, green=low",
                xref="paper", yref="paper", x=0.5, y=-0.06,
                showarrow=False, font=dict(size=10, color="#888"), align="center",
            )],
        )
    )

    out_path = out_dir / "graph_network_phase13.html"
    fig.write_html(str(out_path))
    print(f"\n[OK] Plotly graph saved to:\n   {out_path}")
    return out_path


# -----------------------------------------
#  Main
# -----------------------------------------

def main():
    engine = get_engine()
    villages, sources, tanks, pipelines = load_data(engine)

    G = build_graph(villages, sources, tanks, pipelines)

    test_graph_stats(G)
    test_connectivity(G, sources, villages)
    test_shortest_path(G)
    test_max_flow(G)

    visualize_plotly(G)

    print("\n[SUCCESS] Phase 13 Complete: GIS -> NetworkX Graph built, tested & visualized!")
    return G


if __name__ == "__main__":
    main()
