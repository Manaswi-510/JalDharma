"""
Jal Dharma AI - Scenario Simulation & Stress Testing Package
============================================================
Phases 20 & 21 implementation for Person B:
- Scenario Simulation Engine (Drought, Heatwave/Demand Surge, Pipeline Failure, Compound Crisis)
- Network Flow & Pipeline Utilization Analysis
- Scenario Comparative Scorecards & Reporting
"""

from src.simulation.scenarios import (
    simulate_scenario,
    run_all_scenarios,
    SimulationScenario,
    get_predefined_scenarios,
)
from src.simulation.reports import (
    generate_scenario_comparison_report,
    export_scenario_results,
)

__all__ = [
    "simulate_scenario",
    "run_all_scenarios",
    "SimulationScenario",
    "get_predefined_scenarios",
    "generate_scenario_comparison_report",
    "export_scenario_results",
]
