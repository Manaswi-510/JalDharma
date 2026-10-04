"""
Jal Dharma AI - Phase 21: Scenario Reports & Analysis Exporter
==============================================================
Generates comparative research reports, sensitivity summaries,
and database-ready datasets for PostgreSQL insertion (Phase 21)
and Streamlit dashboard consumption (Phase 22 & 23).
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import pandas as pd

from src.simulation.scenarios import run_all_scenarios

BASE_DIR = Path(__file__).resolve().parent.parent.parent
OUTPUTS_DIR = BASE_DIR / "outputs" / "simulation"


def generate_scenario_comparison_report() -> Dict[str, Any]:
    """
    Run all scenarios and generate an executive analytical report
    summarizing water resilience across climate and infrastructure shocks.
    """
    scorecard_df, all_alloc_df, all_pipe_df = run_all_scenarios()

    # Identify most severe crisis
    worst_fulfillment_idx = scorecard_df["fulfillment_rate_pct"].idxmin()
    worst_scenario = scorecard_df.loc[worst_fulfillment_idx, "scenario_name"]
    worst_rate = scorecard_df.loc[worst_fulfillment_idx, "fulfillment_rate_pct"]

    # Identify best fairness
    best_jain_idx = scorecard_df["jains_fairness_index"].idxmax()
    best_jain_scn = scorecard_df.loc[best_jain_idx, "scenario_name"]
    best_jain = scorecard_df.loc[best_jain_idx, "jains_fairness_index"]

    report: Dict[str, Any] = {
        "title": "Jal Dharma AI - Scenario Stress-Testing & Water Justice Report",
        "total_scenarios_evaluated": int(len(scorecard_df)),
        "executive_summary": {
            "most_vulnerable_regime": f"{worst_scenario} (Overall fulfillment dropped to {worst_rate}%)",
            "highest_fairness_regime": f"{best_jain_scn} (Jain's index reached {best_jain:.4f})",
        },
        "scenarios": scorecard_df.to_dict(orient="records"),
    }

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    report_file = OUTPUTS_DIR / "scenario_analysis_report.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=4)

    return report


def export_scenario_results() -> None:
    """Run and export all scenario datasets to CSV and JSON."""
    generate_scenario_comparison_report()


if __name__ == "__main__":
    rep = generate_scenario_comparison_report()
    print("\n[INFO] Generated scenario analysis report successfully.")
    print("Executive Summary:", rep["executive_summary"])
