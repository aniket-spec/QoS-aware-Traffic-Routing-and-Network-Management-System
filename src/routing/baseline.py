"""
Baseline Shortest-Path Routing Algorithm (Hop-Count Based).

Finds the route with the minimum number of hops using NetworkX.
Disabled links are strictly excluded from consideration.
Congestion, delay, and QoS cost do not influence route selection.
Equal hop-count paths are resolved using deterministic lexicographical tie-breaking.
"""

from __future__ import annotations

from typing import List, Union

import networkx as nx

from src.network.topology import QoSNetwork
from src.routing.models import RouteResult
from src.routing.utils import compile_route_metrics, resolve_active_graph

ALGORITHM_NAME = "Baseline Shortest Path"


def find_baseline_route(
    network: Union[QoSNetwork, nx.Graph],
    source: str,
    destination: str,
) -> RouteResult:
    """
    Computes the shortest path based purely on hop count (fewest links).

    Args:
        network: QoSNetwork instance or raw NetworkX graph.
        source: Node ID where traffic originates.
        destination: Node ID where traffic terminates.

    Returns:
        RouteResult containing the chosen route, hop count, metrics, and explanation.
    """
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

    # 3. Search for shortest (minimum-hop) paths in the active graph
    try:
        # nx.all_shortest_paths finds all paths achieving the minimal unweighted length
        shortest_paths: List[List[str]] = list(
            nx.all_shortest_paths(active_graph, source=source, target=destination)
        )
    except (nx.NetworkXNoPath, nx.NodeNotFound):
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

    if not shortest_paths:
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

    # 4. Deterministic tie-breaking if multiple shortest paths exist
    # Sort candidate paths lexicographically by node sequence
    shortest_paths.sort(key=lambda path: tuple(path))
    selected_path = shortest_paths[0]
    hop_count = len(selected_path) - 1

    # 5. Compute informational metrics from the selected route
    # (Metrics are calculated for observation and comparison, not used for selection)
    link_details, total_cost, total_delay, bottleneck_bw = compile_route_metrics(
        active_graph, selected_path
    )

    path_display = " -> ".join(selected_path)
    tie_note = f" (tie-broken among {len(shortest_paths)} equal-hop candidate paths)" if len(shortest_paths) > 1 else ""
    explanation = (
        f"Baseline shortest-path selected route with {hop_count} hop(s): {path_display}{tie_note}."
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
