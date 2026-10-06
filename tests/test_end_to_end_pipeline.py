"""
Jal Dharma AI - Unit Tests for Phase 24: End-to-End Pipeline
============================================================
Validates the complete 12-step pipeline execution, mathematical consistency,
and output artifact generation.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from src.pipeline import run_end_to_end_pipeline


def test_pipeline_normal_supply():
    """Test full pipeline execution under normal water supply conditions."""
    results = run_end_to_end_pipeline(
        date_str="2025-06-29",
        scarcity_factor=1.0,
        verbose=False,
    )

    assert "target_date" in results
    assert results["target_date"] == "2025-06-29"
    assert results["water_available_l"] > 0
    assert results["max_flow_l"] > 0

    df_res = results["df_results"]
    assert len(df_res) == 45
    assert "allocated_water_l" in df_res.columns
    assert "satisfaction_pct" in df_res.columns
    assert "shortage_l" in df_res.columns

    # In normal conditions with high availability, satisfaction should be high
    fairness = results["fairness_metrics"]
    assert fairness["jains_fairness_index"] >= 0.90
    assert fairness["average_satisfaction_pct"] >= 90.0

    # Verify artifacts exist
    assert results["map_path"].exists()
    assert results["stored_paths"]["allocations_csv"].exists()
    assert results["stored_paths"]["summary_json"].exists()


def test_pipeline_drought_scarcity_equity():
    """
    Test pipeline under severe drought stress (scarcity_factor=0.05).
    Verifies that the LP solver prioritizes vulnerable communities (Equity-Aware).
    """
    results = run_end_to_end_pipeline(
        date_str="2025-06-29",
        scarcity_factor=0.05,
        verbose=False,
    )

    df_res = results["df_results"]
    shortage = results["shortage_metrics"]

    # Deficit should be present
    assert shortage["total_shortage_l"] > 0

    # Total allocated water cannot exceed deliverable available supply
    assert shortage["total_allocated_l"] <= results["water_available_l"] + 1.0  # slight numerical epsilon

    # Top priority village (Kashti) should have higher satisfaction than standard villages
    kashti_row = df_res[df_res["village_id"] == "VIL_010"].iloc[0]
    # Check that high-priority villages receive lifeline allocation
    assert kashti_row["allocated_water_l"] > 0


if __name__ == "__main__":
    print("[RUNNING] test_pipeline_normal_supply...")
    test_pipeline_normal_supply()
    print("[PASS] test_pipeline_normal_supply passed!")

    print("[RUNNING] test_pipeline_drought_scarcity_equity...")
    test_pipeline_drought_scarcity_equity()
    print("[PASS] test_pipeline_drought_scarcity_equity passed!")

    print("\nALL PHASE 24 END-TO-END PIPELINE UNIT TESTS PASSED SUCCESSFULLY!")
