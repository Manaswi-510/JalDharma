"""
Unit Tests for Phase 18 & Phase 19 (Water Justice & Fairness Metrics)
"""

import unittest
import numpy as np
import pandas as pd

from src.justice.priority import (
    calculate_priority_scores,
    run_priority_sensitivity_analysis,
    min_max_normalize,
)
from src.justice.metrics import (
    calculate_satisfaction_ratios,
    average_satisfaction_ratio,
    maximum_shortage,
    average_shortage,
    weighted_shortage,
    jains_fairness_index,
    gini_coefficient,
    hoover_index,
    percentage_minimum_service_level,
    calculate_all_fairness_metrics,
)


class TestPhase18Priority(unittest.TestCase):

    def setUp(self):
        self.sample_villages = pd.DataFrame([
            {
                "village_id": "VIL_001",
                "village_name": "Test Village A",
                "population": 5000,
                "vulnerability_index": 0.9,
                "accessibility_score": 0.2,
                "historical_shortage": "Critical",
            },
            {
                "village_id": "VIL_002",
                "village_name": "Test Village B",
                "population": 2000,
                "vulnerability_index": 0.3,
                "accessibility_score": 0.8,
                "historical_shortage": "Low",
            },
        ])

    def test_priority_scores_calculation(self):
        res = calculate_priority_scores(self.sample_villages)
        self.assertEqual(len(res), 2)
        self.assertIn("priority_score", res.columns)
        self.assertIn("priority_weight", res.columns)
        self.assertIn("priority_rank", res.columns)
        # Village A has high pop, high vuln, critical shortage, low access -> must have higher priority
        self.assertGreater(res.loc[res["village_id"] == "VIL_001", "priority_score"].iloc[0],
                            res.loc[res["village_id"] == "VIL_002", "priority_score"].iloc[0])
        self.assertEqual(res.loc[res["village_id"] == "VIL_001", "priority_rank"].iloc[0], 1)

    def test_sensitivity_analysis(self):
        rank_comp, _ = run_priority_sensitivity_analysis(self.sample_villages)
        self.assertEqual(len(rank_comp), 2)
        self.assertIn("Rank: Balanced (Default)", rank_comp.columns)


class TestPhase19FairnessMetrics(unittest.TestCase):

    def test_jains_fairness_index_equal(self):
        # When all allocations/satisfactions are equal, Jain's index must be exactly 1.0
        allocations = [100.0, 100.0, 100.0, 100.0]
        self.assertAlmostEqual(jains_fairness_index(allocations), 1.0, places=4)

    def test_jains_fairness_index_unequal(self):
        # 1 user gets 100, 3 users get 0 -> J = 1/4 = 0.25
        allocations = [100.0, 0.0, 0.0, 0.0]
        self.assertAlmostEqual(jains_fairness_index(allocations), 0.25, places=4)

    def test_gini_coefficient(self):
        # Perfect equality -> Gini = 0.0
        equal_vals = [50.0, 50.0, 50.0, 50.0]
        self.assertAlmostEqual(gini_coefficient(equal_vals), 0.0, places=4)

        # Unequal distribution -> Gini > 0
        unequal_vals = [10.0, 20.0, 30.0, 140.0]
        self.assertGreater(gini_coefficient(unequal_vals), 0.3)

    def test_hoover_index(self):
        equal_vals = [50.0, 50.0, 50.0]
        self.assertAlmostEqual(hoover_index(equal_vals), 0.0, places=4)

    def test_minimum_service_level(self):
        ratios = [0.8, 0.9, 0.6, 0.5]
        # 2 out of 4 are >= 0.7 (50%)
        self.assertEqual(percentage_minimum_service_level(ratios, threshold=0.7), 50.0)

    def test_calculate_all_fairness_metrics(self):
        sample_df = pd.DataFrame({
            "village_id": ["V1", "V2", "V3"],
            "predicted_demand_l": [1000.0, 2000.0, 3000.0],
            "allocated_water_l": [800.0, 1800.0, 2400.0],
            "priority_score": [0.8, 0.5, 0.3],
        })
        res = calculate_all_fairness_metrics(sample_df)
        self.assertIn("phase_19_metrics", res)
        p19 = res["phase_19_metrics"]
        self.assertIn("19.1_average_satisfaction_ratio", p19)
        self.assertIn("19.5_jains_fairness_index", p19)
        self.assertIn("19.6_gini_coefficient_satisfaction", p19)


if __name__ == "__main__":
    unittest.main()
