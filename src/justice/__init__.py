"""
Jal Dharma AI - Water Justice & Equity Package
==============================================
Phases 18, 19 & 20 implementation for Person B:
- Phase 18: Village Priority & Vulnerability Scoring Methodology
- Phase 19: Water Justice & Fairness Metrics (Jain's Index, Gini, Hoover, Shortage Analysis)
- Phase 20: Allocation Strategy Comparison (Proportional vs Max-Flow vs Equity-Aware)
"""

from src.justice.priority import (
    calculate_priority_scores,
    run_priority_sensitivity_analysis,
    DEFAULT_WEIGHTS,
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
from src.justice.comparison import (
    solve_proportional,
    solve_max_flow,
    solve_equity_aware,
    run_allocation_comparison,
)

__all__ = [
    "calculate_priority_scores",
    "run_priority_sensitivity_analysis",
    "DEFAULT_WEIGHTS",
    "calculate_satisfaction_ratios",
    "average_satisfaction_ratio",
    "maximum_shortage",
    "average_shortage",
    "weighted_shortage",
    "jains_fairness_index",
    "gini_coefficient",
    "hoover_index",
    "percentage_minimum_service_level",
    "calculate_all_fairness_metrics",
    "solve_proportional",
    "solve_max_flow",
    "solve_equity_aware",
    "run_allocation_comparison",
]
