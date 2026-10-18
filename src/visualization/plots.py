"""
Plotly visualization functions for network topology and comparative performance charts.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Set, Tuple

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.network.topology import DEFAULT_NODES, QoSNetwork
from src.simulation.metrics import RoutePerformance

# Visual color palette
COLOR_NORMAL_LINK = "#94a3b8"     # Neutral slate for unselected links
COLOR_DISABLED_LINK = "#ef4444"   # Red dashed for disabled links
COLOR_BASELINE = "#2563eb"        # Vibrant blue for baseline route
COLOR_QOS = "#10b981"             # Emerald green for QoS-aware route
COLOR_SHARED = "#8b5cf6"          # Purple for links shared by both routes
COLOR_NODE_CORE = "#1e293b"       # Dark slate for core routers
COLOR_NODE_SOURCE = "#3b82f6"     # Blue for source
COLOR_NODE_DEST = "#ec4899"       # Pink for destination
COLOR_NODE_GATEWAY = "#f59e0b"    # Amber for gateways


def _get_route_edge_set(route: List[str]) -> Set[Tuple[str, str]]:
    """Convert an ordered route into a set of undirected edge tuples."""
    edge_set: Set[Tuple[str, str]] = set()
    if len(route) < 2:
        return edge_set
    for u, v in zip(route[:-1], route[1:]):
        edge_set.add((min(u, v), max(u, v)))
    return edge_set


def create_topology_figure(
    network: QoSNetwork,
    baseline_route: Optional[List[str]] = None,
    qos_route: Optional[List[str]] = None,
    source: Optional[str] = None,
    destination: Optional[str] = None,
) -> go.Figure:
    """
    Renders an interactive 2D topology map using Plotly.

    Args:
        network: Active QoSNetwork instance.
        baseline_route: Ordered list of nodes selected by baseline algorithm.
        qos_route: Ordered list of nodes selected by QoS-aware algorithm.
        source: Selected source node identifier.
        destination: Selected destination node identifier.

    Returns:
        Plotly Figure displaying nodes, links, statuses, and highlighted routes.
    """
    fig = go.Figure()

    baseline_edges = _get_route_edge_set(baseline_route or [])
    qos_edges = _get_route_edge_set(qos_route or [])

    # Predefined 2D layout coordinates
    node_coords: Dict[str, Tuple[float, float]] = {
        n: DEFAULT_NODES[n]["pos"] for n in network.nodes if n in DEFAULT_NODES
    }

    # Tracking sets for distinct legend entries
    added_legends: Set[str] = set()

    edge_hover_x: List[float] = []
    edge_hover_y: List[float] = []
    edge_hover_text: List[str] = []

    background_links: List[Tuple[Any, ...]] = []
    route_links: List[Tuple[Any, ...]] = []

    # 1. Categorize links into background vs active routes
    for u, v, data in network.graph.edges(data=True):
        if u not in node_coords or v not in node_coords:
            continue

        x0, y0 = node_coords[u]
        x1, y1 = node_coords[v]
        norm_pair = (min(u, v), max(u, v))

        is_enabled = data.get("enabled", True)
        in_baseline = norm_pair in baseline_edges
        in_qos = norm_pair in qos_edges

        bw = data.get("bandwidth", 0.0)
        delay = data.get("delay", 0.0)
        cong = data.get("congestion", 0.0)
        loss = data.get("packet_loss", 0.0)

        status_str = "ENABLED" if is_enabled else "DISABLED"
        hover_info = (
            f"<b>Link: {u} &lt;--&gt; {v}</b><br>"
            f"Status: <b>{status_str}</b><br>"
            f"Bandwidth: <b>{bw} Mbps</b><br>"
            f"Delay: <b>{delay} ms</b><br>"
            f"Congestion: <b>{cong}%</b><br>"
            f"Packet Loss: <b>{loss}%</b>"
        )
        edge_hover_x.append((x0 + x1) / 2.0)
        edge_hover_y.append((y0 + y1) / 2.0)
        edge_hover_text.append(hover_info)

        # Style determination
        if not is_enabled:
            item = (x0, y0, x1, y1, COLOR_DISABLED_LINK, 3.0, "dash", "Disabled Link")
            background_links.append(item)
        elif in_baseline and in_qos:
            item = (x0, y0, x1, y1, COLOR_SHARED, 6.0, "solid", "Shared by Both Routes")
            route_links.append(item)
        elif in_qos:
            item = (x0, y0, x1, y1, COLOR_QOS, 5.0, "solid", "QoS-Aware Route")
            route_links.append(item)
        elif in_baseline:
            item = (x0, y0, x1, y1, COLOR_BASELINE, 5.0, "solid", "Baseline Route")
            route_links.append(item)
        else:
            item = (x0, y0, x1, y1, COLOR_NORMAL_LINK, 2.0, "solid", "Active Link")
            background_links.append(item)

    # Draw background links first, then draw active route links in foreground
    for x0, y0, x1, y1, line_color, line_width, line_dash, legend_group in background_links + route_links:
        show_legend = legend_group not in added_legends
        if show_legend:
            added_legends.add(legend_group)

        fig.add_trace(
            go.Scatter(
                x=[x0, x1],
                y=[y0, y1],
                mode="lines",
                line=dict(color=line_color, width=line_width, dash=line_dash),
                name=legend_group,
                legendgroup=legend_group,
                showlegend=show_legend,
                hoverinfo="none",
            )
        )

    # 2. Transparent Midpoint Hover Trace for Links
    fig.add_trace(
        go.Scatter(
            x=edge_hover_x,
            y=edge_hover_y,
            mode="markers",
            marker=dict(size=14, color="rgba(0,0,0,0)"),
            hoverinfo="text",
            hovertext=edge_hover_text,
            showlegend=False,
        )
    )

    # 3. Draw Nodes
    node_x: List[float] = []
    node_y: List[float] = []
    node_text: List[str] = []
    node_hover: List[str] = []
    node_colors: List[str] = []
    node_line_colors: List[str] = []

    for node_id in network.nodes:
        if node_id not in node_coords:
            continue
        x, y = node_coords[node_id]
        meta = DEFAULT_NODES.get(node_id, {})
        role = meta.get("role", "core")
        label = meta.get("label", node_id)

        node_x.append(x)
        node_y.append(y)
        node_text.append(node_id)

        # Highlighting source / destination
        if node_id == source and node_id == destination:
            color = "#a855f7"  # Distinctive purple for loopback
            line_col = "#ffffff"
            role_display = "SOURCE & DESTINATION (LOOPBACK)"
        elif node_id == source:
            color = COLOR_NODE_SOURCE
            line_col = "#ffffff"
            role_display = "SOURCE / INGRESS"
        elif node_id == destination:
            color = COLOR_NODE_DEST
            line_col = "#ffffff"
            role_display = "DESTINATION / EGRESS"
        elif role == "gateway":
            color = COLOR_NODE_GATEWAY
            line_col = "#ffffff"
            role_display = "GATEWAY"
        else:
            color = COLOR_NODE_CORE
            line_col = "#94a3b8"
            role_display = "CORE ROUTER"

        node_colors.append(color)
        node_line_colors.append(line_col)

        neighbors = list(network.graph.neighbors(node_id))
        active_deg = sum(1 for nb in neighbors if network.is_link_enabled(node_id, nb))

        node_hover.append(
            f"<b>{node_id}</b> ({label})<br>"
            f"Role: <b>{role_display}</b><br>"
            f"Active Degree: <b>{active_deg} link(s)</b>"
        )

    fig.add_trace(
        go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            text=node_text,
            textposition="top center",
            textfont=dict(size=12, color="#0f172a", family="Inter, sans-serif"),
            marker=dict(
                size=32,
                color=node_colors,
                line=dict(color=node_line_colors, width=2.5),
            ),
            hoverinfo="text",
            hovertext=node_hover,
            name="Network Nodes",
            showlegend=False,
        )
    )

    fig.update_layout(
        title=dict(
            text="Network Topology & Active Path Traversal",
            x=0.5,
            xanchor="center",
            font=dict(size=16),
        ),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.12, 1.12]),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            range=[-0.12, 1.12],
            scaleanchor="x",
            scaleratio=1,
        ),
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5,
            font=dict(size=11),
        ),
        plot_bgcolor="#f8fafc",
        paper_bgcolor="#ffffff",
        height=480,
    )

    return fig


def create_comparison_metrics_chart(
    baseline: RoutePerformance,
    qos: RoutePerformance,
) -> go.Figure:
    """
    Renders a 2x2 grid of bar charts comparing Baseline vs QoS-Aware performance:
    1. End-to-End Delay (ms) - Lower is better
    2. Bottleneck Bandwidth (Mbps) - Higher is better
    3. Estimated Throughput (Mbps) - Higher is better
    4. End-to-End Packet Loss (%) - Lower is better
    """
    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "End-to-End Delay (ms) [Lower is better]",
            "Bottleneck Bandwidth (Mbps) [Higher is better]",
            "Estimated Throughput (Mbps) [Higher is better]",
            "Packet Loss (%) [Lower is better]",
        ),
        vertical_spacing=0.25,
        horizontal_spacing=0.15,
    )

    categories = ["Baseline", "QoS-Aware"]
    bar_colors = [COLOR_BASELINE, COLOR_QOS]

    # Metrics values
    delay_vals = [
        baseline.end_to_end_delay if baseline.found else 0.0,
        qos.end_to_end_delay if qos.found else 0.0,
    ]
    delay_texts = [
        f"{baseline.end_to_end_delay:.1f} ms" if baseline.found else "No Route",
        f"{qos.end_to_end_delay:.1f} ms" if qos.found else "No Route",
    ]

    bw_vals = [
        baseline.bottleneck_bandwidth if baseline.found else 0.0,
        qos.bottleneck_bandwidth if qos.found else 0.0,
    ]
    bw_texts = [
        f"{baseline.bottleneck_bandwidth:.0f} M" if baseline.found else "No Route",
        f"{qos.bottleneck_bandwidth:.0f} M" if qos.found else "No Route",
    ]

    tp_vals = [
        baseline.estimated_throughput if baseline.found else 0.0,
        qos.estimated_throughput if qos.found else 0.0,
    ]
    tp_texts = [
        f"{baseline.estimated_throughput:.1f} M" if baseline.found else "No Route",
        f"{qos.estimated_throughput:.1f} M" if qos.found else "No Route",
    ]

    loss_vals = [
        baseline.packet_loss_percentage if baseline.found else 0.0,
        qos.packet_loss_percentage if qos.found else 0.0,
    ]
    loss_texts = [
        f"{baseline.packet_loss_percentage:.2f}%" if baseline.found else "No Route",
        f"{qos.packet_loss_percentage:.2f}%" if qos.found else "No Route",
    ]

    # Subplot 1: Delay
    fig.add_trace(
        go.Bar(
            x=categories,
            y=delay_vals,
            text=delay_texts,
            textposition="auto",
            marker_color=bar_colors,
            showlegend=False,
        ),
        row=1,
        col=1,
    )

    # Subplot 2: Bottleneck Bandwidth
    fig.add_trace(
        go.Bar(
            x=categories,
            y=bw_vals,
            text=bw_texts,
            textposition="auto",
            marker_color=bar_colors,
            showlegend=False,
        ),
        row=1,
        col=2,
    )

    # Subplot 3: Estimated Throughput
    fig.add_trace(
        go.Bar(
            x=categories,
            y=tp_vals,
            text=tp_texts,
            textposition="auto",
            marker_color=bar_colors,
            showlegend=False,
        ),
        row=2,
        col=1,
    )

    # Subplot 4: Packet Loss
    fig.add_trace(
        go.Bar(
            x=categories,
            y=loss_vals,
            text=loss_texts,
            textposition="auto",
            marker_color=bar_colors,
            showlegend=False,
        ),
        row=2,
        col=2,
    )

    fig.update_layout(
        height=420,
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor="#f8fafc",
        paper_bgcolor="#ffffff",
    )

    return fig
