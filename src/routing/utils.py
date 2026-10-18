"""
Shared routing utilities for metric calculations and graph extraction.
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Tuple, Union

import networkx as nx

from src.network.topology import QoSNetwork


def resolve_active_graph(network: Union[QoSNetwork, nx.Graph]) -> nx.Graph:
    """
    Extracts an active NetworkX graph excluding disabled links.
    Supports either a QoSNetwork instance or a raw NetworkX graph.
    """
    if isinstance(network, QoSNetwork):
        return network.get_active_graph()
    elif isinstance(network, nx.Graph):
        active_g = nx.Graph()
        for node, data in network.nodes(data=True):
            active_g.add_node(node, **copy.deepcopy(data))
        for u, v, data in network.edges(data=True):
            if data.get("enabled", True):
                active_g.add_edge(u, v, **copy.deepcopy(data))
        return active_g
    else:
        raise TypeError(
            f"Expected QoSNetwork or nx.Graph, got {type(network).__name__}."
        )


def compute_link_cost(
    link_data: Dict[str, Any],
    congestion_weight: float = 50.0,
) -> float:
    """
    Computes QoS link cost: delay + congestion_weight * (congestion / 100).
    The congestion_weight parameter defaults to 50.0.
    """
    delay = float(link_data.get("delay", 0.0))
    congestion = float(link_data.get("congestion", 0.0))
    return delay + float(congestion_weight) * (congestion / 100.0)


def compile_route_metrics(
    active_graph: nx.Graph,
    route: List[str],
    congestion_weight: float = 50.0,
) -> Tuple[List[Dict[str, Any]], float, float, float]:
    """
    Extracts per-link details and aggregate metrics along an ordered route.

    Returns:
        (link_details, total_cost, total_delay, bottleneck_bandwidth)
    """
    if len(route) <= 1:
        return [], 0.0, 0.0, 0.0

    link_details: List[Dict[str, Any]] = []
    total_cost = 0.0
    total_delay = 0.0
    bottleneck_bw = float("inf")

    for u, v in zip(route[:-1], route[1:]):
        edge_data = active_graph[u][v]
        bw = float(edge_data.get("bandwidth", 0.0))
        d = float(edge_data.get("delay", 0.0))
        cong = float(edge_data.get("congestion", 0.0))
        loss = float(edge_data.get("packet_loss", 0.0))
        cost = compute_link_cost(edge_data, congestion_weight=congestion_weight)

        link_details.append(
            {
                "from": u,
                "to": v,
                "bandwidth": bw,
                "delay": d,
                "congestion": cong,
                "packet_loss": loss,
                "cost": round(cost, 4),
            }
        )

        total_cost += cost
        total_delay += d
        if bw < bottleneck_bw:
            bottleneck_bw = bw

    bottleneck_result = bottleneck_bw if bottleneck_bw != float("inf") else 0.0
    return link_details, round(total_cost, 4), round(total_delay, 4), round(bottleneck_result, 2)
