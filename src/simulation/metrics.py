"""
Performance metrics evaluation for network routes and traffic profiles.

Implements standard QoS calculations:
1. End-to-End Delay (sum of link delays in ms).
2. Bottleneck Bandwidth (minimum link capacity in Mbps).
3. Estimated Throughput (min of offered traffic rate and bottleneck capacity in Mbps).
4. End-to-End Packet Loss (independent probability product model, returned as percentage).
5. Average Link Congestion (arithmetic mean of link congestion percentages).
6. Route Cost (reused directly from the routing algorithm results).

Note on Throughput: The estimated throughput is an idealized link-capacity model
(min(offered, bottleneck)), not a dynamic TCP congestion-window or packet-level simulation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.routing.models import RouteResult
from src.simulation.traffic_profiles import TrafficProfile


def calculate_end_to_end_delay(link_details: List[Dict[str, Any]]) -> float:
    """
    Computes total one-way propagation delay in milliseconds.
    Sums configured delays of all links along the route.
    """
    if not link_details:
        return 0.0
    return round(sum(float(link.get("delay", 0.0)) for link in link_details), 4)


def calculate_bottleneck_bandwidth(link_details: List[Dict[str, Any]]) -> float:
    """
    Finds the bottleneck (minimum) bandwidth among all links along the route in Mbps.
    Returns 0.0 if the route has no links.
    """
    if not link_details:
        return 0.0
    return round(min(float(link.get("bandwidth", 0.0)) for link in link_details), 2)


def calculate_estimated_throughput(
    offered_traffic_rate: float,
    bottleneck_bandwidth: float,
) -> float:
    """
    Calculates estimated throughput in Mbps using capacity bounding:
        estimated_throughput = min(offered_traffic_rate, bottleneck_bandwidth)

    Note: This represents available capacity upper-bound, not a dynamic TCP simulation.
    """
    if bottleneck_bandwidth <= 0.0 or offered_traffic_rate <= 0.0:
        return 0.0
    return round(min(float(offered_traffic_rate), float(bottleneck_bandwidth)), 2)


def calculate_end_to_end_loss(link_details: List[Dict[str, Any]]) -> float:
    """
    Computes cumulative packet loss percentage across the route,
    treating each link as an independent loss probability event:

        end_to_end_loss = 1.0 - product(1.0 - (loss_percent / 100))

    Returns:
        Loss percentage in [0.0%, 100.0%].
    """
    if not link_details:
        return 0.0

    survival_prob = 1.0
    for link in link_details:
        loss_pct = float(link.get("packet_loss", 0.0))
        loss_prob = max(0.0, min(1.0, loss_pct / 100.0))
        survival_prob *= 1.0 - loss_prob

    e2e_loss_prob = max(0.0, 1.0 - survival_prob)
    return round(e2e_loss_prob * 100.0, 4)


def calculate_average_congestion(link_details: List[Dict[str, Any]]) -> float:
    """
    Calculates the arithmetic mean of congestion percentages across links in the route.
    Represents average link congestion along this path, not total network utilization.
    """
    if not link_details:
        return 0.0
    total_cong = sum(float(link.get("congestion", 0.0)) for link in link_details)
    return round(total_cong / len(link_details), 2)


@dataclass
class RoutePerformance:
    """
    Structured performance report for a route evaluated against a traffic profile.
    """

    algorithm: str
    source: str
    destination: str
    route: List[str]
    hop_count: int
    found: bool
    end_to_end_delay: float
    bottleneck_bandwidth: float
    offered_traffic_rate: float
    estimated_throughput: float
    packet_loss_percentage: float
    average_congestion: float
    route_cost: Optional[float]
    meets_bandwidth_requirement: bool
    meets_delay_requirement: Optional[bool]
    delay_threshold: Optional[float]
    bandwidth_threshold: float
    is_viable: bool
    explanation: str
    link_details: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert performance report to a dictionary for display or API use."""
        return {
            "algorithm": self.algorithm,
            "source": self.source,
            "destination": self.destination,
            "route": list(self.route),
            "hop_count": self.hop_count,
            "found": self.found,
            "end_to_end_delay_ms": self.end_to_end_delay,
            "bottleneck_bandwidth_mbps": self.bottleneck_bandwidth,
            "offered_traffic_rate_mbps": self.offered_traffic_rate,
            "estimated_throughput_mbps": self.estimated_throughput,
            "packet_loss_percentage": self.packet_loss_percentage,
            "average_congestion_percentage": self.average_congestion,
            "route_cost": self.route_cost,
            "meets_bandwidth_requirement": self.meets_bandwidth_requirement,
            "meets_delay_requirement": self.meets_delay_requirement,
            "delay_threshold_ms": self.delay_threshold,
            "bandwidth_threshold_mbps": self.bandwidth_threshold,
            "is_viable": self.is_viable,
            "explanation": self.explanation,
            "link_details": self.link_details,
        }


def evaluate_route_performance(
    route_result: RouteResult,
    profile: TrafficProfile,
) -> RoutePerformance:
    """
    Evaluates complete QoS metrics and SLA compliance for a RouteResult
    under a given TrafficProfile.

    Args:
        route_result: Output from baseline or QoS-aware routing algorithm.
        profile: The application traffic profile with SLA thresholds.

    Returns:
        RoutePerformance containing detailed performance metrics and SLA verdicts.
    """
    if not route_result.found:
        return RoutePerformance(
            algorithm=route_result.algorithm,
            source=route_result.source,
            destination=route_result.destination,
            route=[],
            hop_count=0,
            found=False,
            end_to_end_delay=0.0,
            bottleneck_bandwidth=0.0,
            offered_traffic_rate=profile.offered_traffic_rate,
            estimated_throughput=0.0,
            packet_loss_percentage=0.0,
            average_congestion=0.0,
            route_cost=None,
            meets_bandwidth_requirement=False,
            meets_delay_requirement=False if profile.max_acceptable_delay is not None else None,
            delay_threshold=profile.max_acceptable_delay,
            bandwidth_threshold=profile.min_bandwidth,
            is_viable=False,
            explanation=f"No route found: {route_result.explanation}",
            link_details=[],
        )

    # Identical source and destination (0 hops)
    if route_result.source == route_result.destination:
        return RoutePerformance(
            algorithm=route_result.algorithm,
            source=route_result.source,
            destination=route_result.destination,
            route=route_result.route,
            hop_count=0,
            found=True,
            end_to_end_delay=0.0,
            bottleneck_bandwidth=float("inf"),
            offered_traffic_rate=profile.offered_traffic_rate,
            estimated_throughput=profile.offered_traffic_rate,
            packet_loss_percentage=0.0,
            average_congestion=0.0,
            route_cost=0.0,
            meets_bandwidth_requirement=True,
            meets_delay_requirement=True,
            delay_threshold=profile.max_acceptable_delay,
            bandwidth_threshold=profile.min_bandwidth,
            is_viable=True,
            explanation=f"Source and destination are identical ('{route_result.source}'). Internal loopback.",
            link_details=[],
        )

    # Calculate individual metrics from link_details
    links = route_result.link_details
    delay = calculate_end_to_end_delay(links)
    bottleneck_bw = calculate_bottleneck_bandwidth(links)
    throughput = calculate_estimated_throughput(profile.offered_traffic_rate, bottleneck_bw)
    loss = calculate_end_to_end_loss(links)
    avg_cong = calculate_average_congestion(links)
    cost = route_result.cost

    # Evaluate compliance against profile requirements
    meets_bw = bottleneck_bw >= profile.min_bandwidth
    meets_delay: Optional[bool] = None
    if profile.max_acceptable_delay is not None:
        meets_delay = delay <= profile.max_acceptable_delay

    is_viable = meets_bw and (meets_delay is not False)

    # Formulate human-readable evaluation explanation
    status_parts = []
    if not meets_bw:
        status_parts.append(
            f"insufficient bandwidth ({bottleneck_bw} Mbps < {profile.min_bandwidth} Mbps required)"
        )
    if meets_delay is False:
        status_parts.append(
            f"exceeds delay SLA ({delay} ms > {profile.max_acceptable_delay} ms maximum)"
        )

    if not status_parts:
        compliance_text = f"Meets all {profile.display_name} requirements."
    else:
        compliance_text = f"SLA Violation: {'; '.join(status_parts)}."

    explanation = (
        f"{route_result.algorithm} path ({' -> '.join(route_result.route)}): "
        f"Delay={delay} ms, Bottleneck={bottleneck_bw} Mbps, "
        f"Throughput={throughput} Mbps, Loss={loss}%, Avg Congestion={avg_cong}%. "
        f"{compliance_text}"
    )

    return RoutePerformance(
        algorithm=route_result.algorithm,
        source=route_result.source,
        destination=route_result.destination,
        route=route_result.route,
        hop_count=route_result.hop_count,
        found=True,
        end_to_end_delay=delay,
        bottleneck_bandwidth=bottleneck_bw,
        offered_traffic_rate=profile.offered_traffic_rate,
        estimated_throughput=throughput,
        packet_loss_percentage=loss,
        average_congestion=avg_cong,
        route_cost=cost,
        meets_bandwidth_requirement=meets_bw,
        meets_delay_requirement=meets_delay,
        delay_threshold=profile.max_acceptable_delay,
        bandwidth_threshold=profile.min_bandwidth,
        is_viable=is_viable,
        explanation=explanation,
        link_details=links,
    )
