"""
QoS-Aware Intelligent Routing Algorithm.

Evaluates feasible paths in the active network topology and selects the route
with the lowest cumulative QoS cost:

    link_cost = delay + congestion_weight * (congestion / 100)

Bandwidth serves as a strict feasibility constraint: every link along a candidate
path must have bandwidth >= min_bandwidth.

Ties between equal-cost routes are resolved deterministically by fewest hops,
followed by lexicographical node sequence.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Union

import networkx as nx

from src.network.topology import QoSNetwork
from src.routing.models import RouteResult
from src.routing.utils import (
    compile_route_metrics,
    compute_link_cost,
    resolve_active_graph,
)

ALGORITHM_NAME = "QoS-Aware Routing"
DEFAULT_CONGESTION_WEIGHT = 50.0


def find_qos_route(
    network: Union[QoSNetwork, nx.Graph],
    source: str,
    destination: str,
    *,
    min_bandwidth: float = 0.0,
    congestion_weight: float = DEFAULT_CONGESTION_WEIGHT,
) -> RouteResult:
    """
    Finds the optimal path meeting bandwidth feasibility with the lowest QoS cost.

    Args:
        network: QoSNetwork instance or raw NetworkX graph.
        source: Node ID where traffic originates.
        destination: Node ID where traffic terminates.
        min_bandwidth: Minimum link bandwidth threshold in Mbps (default: 0.0).
        congestion_weight: Configurable coefficient weighting congestion vs delay (default: 50.0).

    Returns:
        RouteResult containing the optimal route, total cost, metrics, and explanation.

    Raises:
        ValueError: If min_bandwidth or congestion_weight are negative.
    """
    if min_bandwidth < 0:
        raise ValueError(f"min_bandwidth must be non-negative (>= 0 Mbps), got {min_bandwidth}")
    if congestion_weight < 0:
        raise ValueError(f"congestion_weight must be non-negative (>= 0), got {congestion_weight}")

    active_graph = resolve_active_graph(network)

    # 1. Validate node existence
    if not active_graph.has_node(source):
        return RouteResult(
            algorithm=ALGORITHM_NAME,
            source=source,
            destination=destination,
            route=[],
            hop_count=0,
            cost=None,
            found=False,
            explanation=f"Source node '{source}' does not exist in the network.",
        )

    if not active_graph.has_node(destination):
        return RouteResult(
            algorithm=ALGORITHM_NAME,
            source=source,
            destination=destination,
            route=[],
            hop_count=0,
            cost=None,
            found=False,
            explanation=f"Destination node '{destination}' does not exist in the network.",
        )

    # 2. Check for identical source and destination
    if source == destination:
        return RouteResult(
            algorithm=ALGORITHM_NAME,
            source=source,
            destination=destination,
            route=[source],
            hop_count=0,
            cost=0.0,
            found=True,
            explanation=f"Source and destination are identical ('{source}'). No hops required.",
            total_delay=0.0,
            bottleneck_bandwidth=0.0,
        )

    # 3. Discover all active simple paths between source and destination
    try:
        all_paths: List[List[str]] = list(
            nx.all_simple_paths(active_graph, source=source, target=destination)
        )
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        all_paths = []

    if not all_paths:
        return RouteResult(
            algorithm=ALGORITHM_NAME,
            source=source,
            destination=destination,
            route=[],
            hop_count=0,
            cost=None,
            found=False,
            explanation=f"No active path exists between '{source}' and '{destination}'.",
        )

    # 4. Evaluate feasibility and compute QoS cost for each candidate path
    feasible_candidates: List[Dict[str, Any]] = []

    for path in all_paths:
        is_feasible = True
        path_cost = 0.0

        for u, v in zip(path[:-1], path[1:]):
            edge_data = active_graph[u][v]
            link_bw = float(edge_data.get("bandwidth", 0.0))

            # Feasibility condition: every link bandwidth >= min_bandwidth
            if link_bw < min_bandwidth:
                is_feasible = False
                break

            path_cost += compute_link_cost(edge_data, congestion_weight=congestion_weight)

        if is_feasible:
            feasible_candidates.append(
                {
                    "path": path,
                    "cost": path_cost,
                    "hop_count": len(path) - 1,
                }
            )

    # 5. Handle case where paths exist but none meet the bandwidth threshold
    if not feasible_candidates:
        return RouteResult(
            algorithm=ALGORITHM_NAME,
            source=source,
            destination=destination,
            route=[],
            hop_count=0,
            cost=None,
            found=False,
            explanation=(
                f"Paths exist between '{source}' and '{destination}', but none satisfy the "
                f"minimum bandwidth requirement of {min_bandwidth} Mbps."
            ),
        )

    # 6. Select the feasible candidate with the lowest cost (deterministic tie-breaking)
    # Order by: 1) lowest cost, 2) fewest hops, 3) lexicographical path tuple
    feasible_candidates.sort(
        key=lambda item: (
            round(item["cost"], 6),
            item["hop_count"],
            tuple(item["path"]),
        )
    )

    best_candidate = feasible_candidates[0]
    selected_path = best_candidate["path"]
    hop_count = best_candidate["hop_count"]

    # 7. Compile detailed link information and aggregate metrics
    link_details, total_cost, total_delay, bottleneck_bw = compile_route_metrics(
        active_graph, selected_path, congestion_weight=congestion_weight
    )

    path_display = " -> ".join(selected_path)
    tie_note = (
        f" (tie-broken among {len(feasible_candidates)} feasible candidates)"
        if len(feasible_candidates) > 1 and round(feasible_candidates[1]["cost"], 6) == round(best_candidate["cost"], 6)
        else ""
    )
    explanation = (
        f"QoS-aware routing selected route with cost {total_cost:.2f} "
        f"({hop_count} hops, bottleneck bandwidth {bottleneck_bw} Mbps, "
        f"min constraint {min_bandwidth} Mbps): {path_display}{tie_note}."
    )

    return RouteResult(
        algorithm=ALGORITHM_NAME,
        source=source,
        destination=destination,
        route=selected_path,
        hop_count=hop_count,
        cost=total_cost,
        found=True,
        explanation=explanation,
        link_details=link_details,
        total_delay=total_delay,
        bottleneck_bandwidth=bottleneck_bw,
    )
