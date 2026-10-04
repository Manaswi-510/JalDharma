"""
Unit Tests for Phase 21: Scenario Simulations and Stress Testing
"""

import unittest
import pandas as pd
from src.simulation.scenarios import (
    SimulationScenario,
    get_predefined_scenarios,
    simulate_scenario,
    run_all_scenarios,
)
from src.simulation.reports import generate_scenario_comparison_report


class TestPhase21Simulation(unittest.TestCase):

    def test_get_predefined_scenarios(self):
        scenarios = get_predefined_scenarios()
        self.assertGreaterEqual(len(scenarios), 5)
        scenario_ids = [s.scenario_id for s in scenarios]
        self.assertIn("SCN_01", scenario_ids)
        self.assertIn("SCN_04", scenario_ids)

    def test_simulate_baseline_scenario(self):
        baseline = SimulationScenario(
            scenario_id="SCN_TEST",
            scenario_name="Test Baseline",
            water_availability_percent=100.0,
            population_change_percent=0.0,
        )
        res = simulate_scenario(baseline)
        self.assertIn("metrics", res)
        self.assertIn("village_allocations", res)
        self.assertIn("pipeline_flows", res)

        # Baseline should achieve 100% fulfillment
        self.assertAlmostEqual(res["metrics"]["fulfillment_rate_pct"], 100.0, places=1)
        self.assertEqual(len(res["village_allocations"]), 45)

    def test_simulate_pipeline_failure(self):
        failure_scn = SimulationScenario(
            scenario_id="SCN_FAIL_TEST",
            scenario_name="Pipeline Failure Test",
            water_availability_percent=100.0,
            failed_pipeline_ids=["PIPE_001"],
        )
        res = simulate_scenario(failure_scn)
        pipes_df = res["pipeline_flows"]
        pipe_1 = pipes_df[pipes_df["pipeline_id"] == "PIPE_001"].iloc[0]

        # PIPE_001 must have 0 flow and Failed status
        self.assertEqual(pipe_1["flow_l_per_day"], 0.0)
        self.assertEqual(pipe_1["network_status"], "Failed / Ruptured")

    def test_run_all_scenarios_and_report(self):
        scorecard, allocs, pipes = run_all_scenarios()
        self.assertGreaterEqual(len(scorecard), 5)
        self.assertGreater(len(allocs), 100)
        self.assertGreater(len(pipes), 100)

        report = generate_scenario_comparison_report()
        self.assertIn("executive_summary", report)


if __name__ == "__main__":
    unittest.main()
