"""
Unit tests for Streamlit UI visualization and chart generation helpers.
"""

import plotly.graph_objects as go
import pytest

from src.network.topology import DEFAULT_DESTINATION, DEFAULT_SOURCE, create_default_topology
from src.simulation.comparison import compare_routing_for_profile
from src.visualization.plots import (
    _get_route_edge_set,
    create_comparison_metrics_chart,
    create_topology_figure,
)


class TestVisualizationHelpers:
    """Tests for Plotly topology map and performance comparison charts."""

    def test_get_route_edge_set(self):
        """Test converting route nodes into undirected edge set."""
        route = ["Node_1", "Node_3", "Node_6", "Node_7"]
        edges = _get_route_edge_set(route)
        assert len(edges) == 3
        assert ("Node_1", "Node_3") in edges
        assert ("Node_3", "Node_6") in edges
        assert ("Node_6", "Node_7") in edges

        # Empty or single node route
        assert _get_route_edge_set([]) == set()
        assert _get_route_edge_set(["Node_1"]) == set()

    def test_create_topology_figure(self):
        """Test topology figure generation produces valid Plotly figure."""
        net = create_default_topology()
        baseline_route = ["Node_1", "Node_4", "Node_7"]
        qos_route = ["Node_1", "Node_3", "Node_6", "Node_7"]

        fig = create_topology_figure(
            network=net,
            baseline_route=baseline_route,
            qos_route=qos_route,
            source=DEFAULT_SOURCE,
            destination=DEFAULT_DESTINATION,
        )

        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0

        # Verify layout properties
        assert fig.layout.title.text == "Network Topology & Active Path Traversal"
        assert fig.layout.xaxis.showgrid is False
        assert fig.layout.yaxis.showgrid is False

    def test_create_topology_figure_with_disabled_links(self):
        """Test topology figure renders disabled links without errors."""
        net = create_default_topology()
        net.disable_link("Node_1", "Node_4")

        fig = create_topology_figure(
            network=net,
            baseline_route=["Node_1", "Node_2", "Node_5", "Node_7"],
            qos_route=["Node_1", "Node_3", "Node_6", "Node_7"],
        )
        assert isinstance(fig, go.Figure)

    def test_create_comparison_metrics_chart(self):
        """Test comparative bar chart generation."""
        net = create_default_topology()
        comp = compare_routing_for_profile(net, DEFAULT_SOURCE, DEFAULT_DESTINATION, "voip")

        fig = create_comparison_metrics_chart(comp.baseline, comp.qos_aware)

        assert isinstance(fig, go.Figure)
        # 4 subplots, each with 1 bar trace
        assert len(fig.data) == 4

    def test_create_comparison_metrics_chart_no_route(self):
        """Test chart handles missing routes cleanly without crashing."""
        net = create_default_topology()
        # Disconnect destination
        for nb in list(net.graph.neighbors("Node_7")):
            net.disable_link("Node_7", nb)

        comp = compare_routing_for_profile(net, DEFAULT_SOURCE, DEFAULT_DESTINATION, "voip")
        fig = create_comparison_metrics_chart(comp.baseline, comp.qos_aware)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 4
