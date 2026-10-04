"""
Unit Tests for Phase 20: Allocation Strategy Comparison
"""

import unittest
import pandas as pd
import numpy as np

from src.justice.comparison import (
    solve_proportional,
    solve_max_flow,
    solve_equity_aware,
    run_allocation_comparison,
)


class TestPhase20AllocationComparison(unittest.TestCase):

    def test_run_allocation_comparison(self):
        summary_table, detailed_table = run_allocation_comparison(scarcity_factor=0.75)

        # Verify summary table contains required columns and rows
        self.assertIn("Proportional", summary_table.columns)
        self.assertIn("Max-Flow", summary_table.columns)
        self.assertIn("Equity-Aware", summary_table.columns)

        self.assertIn("Total Water Delivered (L)", summary_table.index)
        self.assertIn("Weighted Shortage (L)", summary_table.index)
        self.assertIn("Jain's Fairness Index", summary_table.index)
        self.assertIn("Gini Coefficient", summary_table.index)

        # Verify detailed table
        self.assertEqual(len(detailed_table), 45)
        self.assertIn("alloc_proportional_l", detailed_table.columns)
        self.assertIn("alloc_max_flow_l", detailed_table.columns)
        self.assertIn("alloc_equity_aware_l", detailed_table.columns)
        self.assertIn("sat_equity_aware", detailed_table.columns)


if __name__ == "__main__":
    unittest.main()
