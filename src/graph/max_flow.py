import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import networkx as nx
from sqlalchemy import text

from src.database.connection import engine


# ============================================================
# SPECIAL NETWORK NODES
# ============================================================

SUPER_SOURCE = "WATER_SOURCE"
SUPER_SINK = "DEMAND_SINK"


# ============================================================
# 1. LOAD PIPELINE NETWORK
# ============================================================

def load_pipeline_network():

    query = text("""
        SELECT
            pipeline_id,
            source_node AS from_node,
            destination_node AS to_node,
            capacity_l_per_day AS capacity_liters,
            status
        FROM public.pipelines
        WHERE LOWER(status) IN ('working', 'operational', '1')
          AND capacity_l_per_day IS NOT NULL
          AND capacity_l_per_day > 0
        ORDER BY pipeline_id;
    """)

    with engine.connect() as connection:

        result = connection.execute(query)

        return result.fetchall()


# ============================================================
# 2. LOAD WATER SOURCES
# ============================================================

def load_water_sources():

    query = text("""
        SELECT
            source_id,
            daily_supply_capacity_l AS capacity_liters,
            current_storage_l AS current_storage_liters
        FROM public.water_sources
        WHERE daily_supply_capacity_l IS NOT NULL
          AND daily_supply_capacity_l > 0
        ORDER BY source_id;
    """)

    with engine.connect() as connection:

        result = connection.execute(query)

        return result.fetchall()


# ============================================================
# 3. LOAD VILLAGE WATER DEMANDS
# ============================================================

def load_village_demands():

    query = text("""
        SELECT DISTINCT ON (village_id)
            village_id,
            actual_demand_l
        FROM public.historical_water_demand
        WHERE actual_demand_l IS NOT NULL
          AND actual_demand_l > 0
        ORDER BY village_id, date DESC;
    """)

    with engine.connect() as connection:

        result = connection.execute(query)

        return result.fetchall()


# ============================================================
# 4. BUILD COMPLETE FLOW NETWORK
# ============================================================

def build_flow_network():

    G = nx.DiGraph()

    # --------------------------------------------------------
    # Add real pipeline network
    # --------------------------------------------------------

    pipelines = load_pipeline_network()

    for pipeline in pipelines:

        pipeline_id = pipeline[0]
        from_node = pipeline[1]
        to_node = pipeline[2]
        capacity = float(pipeline[3])

        G.add_edge(
            from_node,
            to_node,
            capacity=capacity,
            pipeline_id=pipeline_id
        )

    # --------------------------------------------------------
    # Add super source → water sources
    # --------------------------------------------------------

    sources = load_water_sources()

    for source in sources:

        source_id = source[0]
        source_capacity = float(source[1])

        G.add_edge(
            SUPER_SOURCE,
            source_id,
            capacity=source_capacity,
            pipeline_id=f"SOURCE_{source_id}"
        )

    # --------------------------------------------------------
    # Add villages → super sink
    # --------------------------------------------------------

    village_demands = load_village_demands()

    for village in village_demands:

        village_id = village[0]
        demand = float(village[1])

        G.add_edge(
            village_id,
            SUPER_SINK,
            capacity=demand,
            pipeline_id=f"DEMAND_{village_id}"
        )

    return G


# ============================================================
# 5. CALCULATE MAXIMUM FLOW
# ============================================================

def calculate_max_flow(G):

    flow_value, flow_dict = nx.maximum_flow(
        G,
        SUPER_SOURCE,
        SUPER_SINK
    )

    return flow_value, flow_dict


# ============================================================
# 6. RECORD FLOW THROUGH EVERY REAL PIPELINE
# ============================================================

def record_pipeline_flows(G, flow_dict):

    print("\n======================================")
    print("PIPELINE FLOW REPORT")
    print("======================================")

    pipeline_results = []

    for from_node, to_node, data in G.edges(data=True):

        pipeline_id = data.get("pipeline_id")

        # Ignore artificial source edges
        if pipeline_id and pipeline_id.startswith("SOURCE_"):
            continue

        # Ignore artificial demand edges
        if pipeline_id and pipeline_id.startswith("DEMAND_"):
            continue

        if not pipeline_id:
            continue

        capacity = float(data["capacity"])

        actual_flow = float(
            flow_dict
            .get(from_node, {})
            .get(to_node, 0)
        )

        # Calculate utilization
        if capacity > 0:

            utilization = (
                actual_flow / capacity
            ) * 100

        else:

            utilization = 0

        pipeline_results.append(
            {
                "pipeline_id": pipeline_id,
                "from_node": from_node,
                "to_node": to_node,
                "capacity": capacity,
                "flow": actual_flow,
                "utilization": utilization
            }
        )

        print(
            f"{pipeline_id:10s} | "
            f"{from_node:10s} -> {to_node:10s} | "
            f"Capacity: {capacity:12,.0f} | "
            f"Flow: {actual_flow:12,.2f} | "
            f"Utilization: {utilization:6.2f}%"
        )

    return pipeline_results


# ============================================================
# 7. BOTTLENECK ANALYSIS
# ============================================================

def analyze_bottlenecks(pipeline_results):

    # --------------------------------------------------------
    # Sort by utilization
    # --------------------------------------------------------

    pipeline_results.sort(
        key=lambda x: x["utilization"],
        reverse=True
    )

    # --------------------------------------------------------
    # Top 5 most utilized pipelines
    # --------------------------------------------------------

    print("\n======================================")
    print("TOP 5 MOST UTILIZED PIPELINES")
    print("======================================")

    top_five = pipeline_results[:5]

    for index, pipeline in enumerate(top_five, start=1):

        print(
            f"{index}. "
            f"{pipeline['pipeline_id']} | "
            f"{pipeline['from_node']} -> "
            f"{pipeline['to_node']} | "
            f"Flow: {pipeline['flow']:,.2f} L/day | "
            f"Capacity: {pipeline['capacity']:,.0f} L/day | "
            f"Utilization: "
            f"{pipeline['utilization']:.2f}%"
        )

    # --------------------------------------------------------
    # Bottleneck candidates
    # --------------------------------------------------------

    bottlenecks = [
        pipeline
        for pipeline in pipeline_results
        if pipeline["utilization"] >= 80
    ]

    print("\n======================================")
    print("BOTTLENECK PIPELINES")
    print("======================================")

    if bottlenecks:

        for pipeline in bottlenecks:

            print(
                f"{pipeline['pipeline_id']} | "
                f"{pipeline['from_node']} -> "
                f"{pipeline['to_node']} | "
                f"Capacity: "
                f"{pipeline['capacity']:,.0f} L/day | "
                f"Flow: "
                f"{pipeline['flow']:,.2f} L/day | "
                f"Utilization: "
                f"{pipeline['utilization']:.2f}%"
            )

    else:

        print(
            "No pipeline is currently above "
            "80% utilization."
        )

    # --------------------------------------------------------
    # Zero-flow pipelines
    # --------------------------------------------------------

    zero_flow = [
        pipeline
        for pipeline in pipeline_results
        if pipeline["flow"] == 0
    ]

    print("\n======================================")
    print("ZERO-FLOW PIPELINES")
    print("======================================")

    print(
        f"Number of zero-flow pipelines: "
        f"{len(zero_flow)}"
    )

    for pipeline in zero_flow:

        print(
            f"{pipeline['pipeline_id']} | "
            f"{pipeline['from_node']} -> "
            f"{pipeline['to_node']} | "
            f"Capacity: "
            f"{pipeline['capacity']:,.0f} L/day"
        )

    # --------------------------------------------------------
    # Candidate bottleneck
    # --------------------------------------------------------

    print("\n======================================")
    print("BOTTLENECK ANALYSIS")
    print("======================================")

    if pipeline_results:

        candidate = pipeline_results[0]

        print(
            f"Candidate bottleneck: "
            f"{candidate['pipeline_id']}"
        )

        print(
            f"Route: "
            f"{candidate['from_node']} -> "
            f"{candidate['to_node']}"
        )

        print(
            f"Capacity: "
            f"{candidate['capacity']:,.0f} L/day"
        )

        print(
            f"Actual flow: "
            f"{candidate['flow']:,.2f} L/day"
        )

        print(
            f"Utilization: "
            f"{candidate['utilization']:.2f}%"
        )

        # Interpretation
        if candidate["utilization"] >= 80:

            print(
                "Status: HIGH UTILIZATION - "
                "potential bottleneck."
            )

        elif candidate["utilization"] >= 50:

            print(
                "Status: MODERATE UTILIZATION - "
                "monitor this pipeline."
            )

        else:

            print(
                "Status: LOW UTILIZATION - "
                "not currently a severe bottleneck."
            )


# ============================================================
# 8. MAIN PROGRAM
# ============================================================

if __name__ == "__main__":

    print("======================================")
    print("JAL-DHARMA AI - MAX FLOW MODEL")
    print("======================================")

    # --------------------------------------------------------
    # Build network
    # --------------------------------------------------------

    print("\nBuilding water network...")

    G = build_flow_network()

    print(
        f"Number of nodes: "
        f"{G.number_of_nodes()}"
    )

    print(
        f"Number of edges: "
        f"{G.number_of_edges()}"
    )

    # --------------------------------------------------------
    # Calculate maximum flow
    # --------------------------------------------------------

    print(
        "\nCalculating maximum physically "
        "deliverable water..."
    )

    max_flow, flow_dict = calculate_max_flow(G)

    # --------------------------------------------------------
    # Display maximum flow
    # --------------------------------------------------------

    print("\n======================================")
    print("MAXIMUM FLOW RESULT")
    print("======================================")

    print(
        f"Maximum water flow: "
        f"{max_flow:,.2f} L/day"
    )

    # --------------------------------------------------------
    # Record pipeline flows
    # --------------------------------------------------------

    pipeline_results = record_pipeline_flows(
        G,
        flow_dict
    )

    # --------------------------------------------------------
    # Analyze bottlenecks
    # --------------------------------------------------------

    analyze_bottlenecks(
        pipeline_results
    )

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    print("\n======================================")
    print("MAX FLOW ANALYSIS COMPLETED")
    print("======================================")