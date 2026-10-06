"""
Jal Dharma AI
=============
Main Application Entry Point • Phase 24: End-to-End Pipeline

Combines all system modules into a unified workflow:
  The user selects:
      Date (e.g. "2025-06-29")
  System performs:
      1. Load historical data
      ↓
      2. Predict demand (Phase 11 Linear Regression)
      ↓
      3. Get current water availability (Phase 15 Hydro-Informatics)
      ↓
      4. Load GIS network (Phase 8 Spatial Topology)
      ↓
      5. Build graph (Phase 8 & 16 NetworkX DiGraph)
      ↓
      6. Calculate max-flow (Phase 16 Network Throughput)
      ↓
      7. Run equity-aware LP (Phase 16-20 SciPy HiGHS Solver with Phase 18 Weights)
      ↓
      8. Calculate shortage (Deficit analysis & Satisfaction S_i = A_i / D_i)
      ↓
      9. Calculate fairness (Phase 19 Jain's Index, Gini, Hoover, Weighted Shortage)
      ↓
      10. Store results (CSV, JSON, Dashboard live sync, PostgreSQL bridge)
      ↓
      11. Update GIS (Dynamic Folium HTML map with shortage color-coding)
      ↓
      12. Display dashboard (Terminal Executive Cockpit + Web Dashboard sync)

Run with:
    python main.py
    python main.py --date 2025-06-29
    python main.py --date 2025-06-29 --scarcity 0.70
"""

import argparse
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import run_end_to_end_pipeline


def main():
    parser = argparse.ArgumentParser(
        description="Jal Dharma AI - End-to-End Water Management Pipeline (Phase 24)"
    )
    parser.add_argument(
        "--date",
        type=str,
        default="2025-06-29",
        help="Target allocation date (YYYY-MM-DD). Default: 2025-06-29",
    )
    parser.add_argument(
        "--scarcity",
        type=float,
        default=1.0,
        help="Supply scarcity factor (e.g. 0.70 for 30%% drought). Default: 1.0 (Normal Supply)",
    )
    args = parser.parse_args()

    # Execute the complete 12-step end-to-end pipeline
    results = run_end_to_end_pipeline(
        date_str=args.date,
        scarcity_factor=args.scarcity,
        verbose=True,
    )

    return results


if __name__ == "__main__":
    main()