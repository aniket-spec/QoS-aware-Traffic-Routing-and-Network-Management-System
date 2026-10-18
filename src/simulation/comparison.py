"""
Integration of routing algorithms with traffic profiles and comparative evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Union

import networkx as nx

from src.network.topology import QoSNetwork
from src.routing import find_baseline_route, find_qos_route
from src.simulation.metrics import RoutePerformance, evaluate_route_performance
from src.simulation.traffic_profiles import TrafficProfile, get_traffic_profile


@dataclass
class SimulationComparisonResult:
    """
    Comparison container contrasting Baseline and QoS-Aware routing performance
    for a given traffic profile and endpoints.
    """

    profile: TrafficProfile
    source: str
    destination: str
    baseline: RoutePerformance
    qos_aware: RoutePerformance
    summary: str
    recommended_algorithm: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert comparison result into a serializable dictionary for Streamlit."""
        return {
            "profile": self.profile.to_dict(),
            "source": self.source,
            "destination": self.destination,
            "baseline": self.baseline.to_dict(),
            "qos_aware": self.qos_aware.to_dict(),
            "summary": self.summary,
            "recommended_algorithm": self.recommended_algorithm,
        }


def compare_routing_for_profile(
    network: Union[QoSNetwork, nx.Graph],
    source: str,
    destination: str,
    profile: Union[TrafficProfile, str],
) -> SimulationComparisonResult:
    """
    Runs both routing algorithms and evaluates their performance against a traffic profile.

    1. Runs baseline routing (pure minimum-hop, unconstrained).
    2. Runs QoS-aware routing (cost-minimizing with profile.min_bandwidth feasibility).
    3. Evaluates performance metrics (delay, throughput, loss, congestion) for each route.
    4. Evaluates compliance against profile SLA thresholds (bandwidth, delay).
    5. Returns structured comparison object with narrative summary.

    Args:
        network: QoSNetwork instance or raw NetworkX graph.
        source: Source node ID.
        destination: Destination node ID.
        profile: TrafficProfile instance or string key ('voip', 'video', 'bulk_data').

    Returns:
        SimulationComparisonResult containing performance for both algorithms.
    """
    if isinstance(profile, str):
        profile_obj = get_traffic_profile(profile)
    elif isinstance(profile, TrafficProfile):
        profile_obj = profile
    else:
        raise TypeError(f"Expected TrafficProfile or str, got {type(profile).__name__}")

    # 1. Run Baseline Routing (minimum hops)
    baseline_result = find_baseline_route(network, source, destination)
    baseline_perf = evaluate_route_performance(baseline_result, profile_obj)

    # 2. Run QoS-Aware Routing (bandwidth feasibility + lowest QoS cost)
    qos_result = find_qos_route(
        network,
        source,
        destination,
        min_bandwidth=profile_obj.min_bandwidth,
    )
    qos_perf = evaluate_route_performance(qos_result, profile_obj)

    # 3. Generate comparative assessment
    recommended: Optional[str] = None
    summary_lines = []

    if not baseline_perf.found and not qos_perf.found:
        summary_lines.append(
            f"No viable route could be found by either algorithm between '{source}' and '{destination}'."
        )
    elif qos_perf.found and not baseline_perf.found:
        recommended = qos_perf.algorithm
        summary_lines.append(
            f"Only {qos_perf.algorithm} successfully established an active path."
        )
    elif baseline_perf.found and not qos_perf.found:
        # Baseline found a path, but it violated bandwidth feasibility for QoS
        recommended = baseline_perf.algorithm
        summary_lines.append(
            f"{baseline_perf.algorithm} found a route, but no route met the "
            f"{profile_obj.display_name} bandwidth requirement ({profile_obj.min_bandwidth} Mbps)."
        )
    else:
        # Both found routes: compare SLA compliance and performance
        baseline_ok = baseline_perf.is_viable
        qos_ok = qos_perf.is_viable

        if qos_ok and not baseline_ok:
            recommended = qos_perf.algorithm
            violations = []
            if not baseline_perf.meets_bandwidth_requirement:
                violations.append("bandwidth deficiency")
            if baseline_perf.meets_delay_requirement is False:
                violations.append("excessive delay")
            violation_str = " and ".join(violations)
            summary_lines.append(
                f"{qos_perf.algorithm} is strongly recommended: it satisfies all "
                f"{profile_obj.display_name} requirements, whereas {baseline_perf.algorithm} "
                f"fails due to {violation_str}."
            )
        elif baseline_ok and not qos_ok:
            recommended = baseline_perf.algorithm
            summary_lines.append(
                f"{baseline_perf.algorithm} is the only route satisfying requirements."
            )
        elif qos_ok and baseline_ok:
            recommended = qos_perf.algorithm
            delay_diff = baseline_perf.end_to_end_delay - qos_perf.end_to_end_delay
            loss_diff = baseline_perf.packet_loss_percentage - qos_perf.packet_loss_percentage
            summary_lines.append(
                f"Both algorithms provide viable routes. {qos_perf.algorithm} achieves "
                f"lower QoS cost ({qos_perf.route_cost} vs {baseline_perf.route_cost}), "
                f"with {abs(delay_diff):.1f} ms {'lower' if delay_diff >= 0 else 'higher'} delay "
                f"and {qos_perf.average_congestion}% avg congestion vs {baseline_perf.average_congestion}%."
            )
        else:
            # Neither is fully viable
            summary_lines.append(
                f"Both routes experience SLA degradation under {profile_obj.display_name} thresholds."
            )

    summary = " ".join(summary_lines)

    return SimulationComparisonResult(
        profile=profile_obj,
        source=source,
        destination=destination,
        baseline=baseline_perf,
        qos_aware=qos_perf,
        summary=summary,
        recommended_algorithm=recommended,
    )
