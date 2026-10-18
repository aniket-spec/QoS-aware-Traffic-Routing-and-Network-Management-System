"""
Simulation package for performance metrics, traffic profiles, and scenarios.
"""

from src.simulation.comparison import SimulationComparisonResult, compare_routing_for_profile
from src.simulation.metrics import (
    RoutePerformance,
    calculate_average_congestion,
    calculate_bottleneck_bandwidth,
    calculate_end_to_end_delay,
    calculate_end_to_end_loss,
    calculate_estimated_throughput,
    evaluate_route_performance,
)
from src.simulation.scenarios import (
    ScenarioResult,
    load_congestion_scenario,
    load_link_failure_scenario,
    load_normal_scenario,
)
from src.simulation.traffic_profiles import (
    DEFAULT_PROFILES,
    TrafficProfile,
    get_traffic_profile,
    list_traffic_profiles,
)

__all__ = [
    "TrafficProfile",
    "DEFAULT_PROFILES",
    "get_traffic_profile",
    "list_traffic_profiles",
    "RoutePerformance",
    "calculate_end_to_end_delay",
    "calculate_bottleneck_bandwidth",
    "calculate_estimated_throughput",
    "calculate_end_to_end_loss",
    "calculate_average_congestion",
    "evaluate_route_performance",
    "SimulationComparisonResult",
    "compare_routing_for_profile",
    "ScenarioResult",
    "load_normal_scenario",
    "load_congestion_scenario",
    "load_link_failure_scenario",
]
