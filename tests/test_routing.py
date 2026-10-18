"""
Comprehensive unit tests for Phase 2: Baseline Shortest-Path & QoS-Aware Routing.
"""

import networkx as nx
import pytest

from src.network.topology import (
    DEFAULT_DESTINATION,
    DEFAULT_SOURCE,
    create_default_topology,
)
from src.routing import (
    BASELINE_ALGORITHM_NAME,
    QOS_ALGORITHM_NAME,
    find_baseline_route,
    find_qos_route,
)


def create_triangle_test_graph() -> nx.Graph:
    """
    Constructs a simple 3-node test graph:
        A ---> B (1 hop, high congestion: 90%, delay: 10, bw: 100)
        A ---> C ---> B (2 hops, zero congestion: 0%, delay: 5 each, bw: 100)
    """
    g = nx.Graph()
    g.add_node("A")
    g.add_node("B")
    g.add_node("C")

    # Direct 1-hop path with high congestion
    g.add_edge("A", "B", bandwidth=100.0, delay=10.0, congestion=90.0, packet_loss=0.0, enabled=True)
    # 2-hop detour with crystal clean links
    g.add_edge("A", "C", bandwidth=100.0, delay=5.0, congestion=0.0, packet_loss=0.0, enabled=True)
    g.add_edge("C", "B", bandwidth=100.0, delay=5.0, congestion=0.0, packet_loss=0.0, enabled=True)
    return g


def create_bandwidth_test_graph() -> nx.Graph:
    """
    Constructs a graph with two alternative paths of different bandwidth capacities:
        Path 1: A -> B (bw: 50 Mbps, delay: 5 ms, congestion: 0%) -> Low cost, Low capacity
        Path 2: A -> C -> B (bw: 500 Mbps, delay: 20 ms, congestion: 0%) -> Higher cost, High capacity
    """
    g = nx.Graph()
    g.add_node("A")
    g.add_node("B")
    g.add_node("C")

    g.add_edge("A", "B", bandwidth=50.0, delay=5.0, congestion=0.0, packet_loss=0.0, enabled=True)
    g.add_edge("A", "C", bandwidth=500.0, delay=10.0, congestion=0.0, packet_loss=0.0, enabled=True)
    g.add_edge("C", "B", bandwidth=500.0, delay=10.0, congestion=0.0, packet_loss=0.0, enabled=True)
    return g


def create_equal_cost_test_graph() -> nx.Graph:
    """
    Constructs a diamond topology where two routes have identical hops and identical cost:
        Route 1: A -> B -> D (2 hops, cost = 10 + 10 = 20)
        Route 2: A -> C -> D (2 hops, cost = 10 + 10 = 20)
    """
    g = nx.Graph()
    for n in ["A", "B", "C", "D"]:
        g.add_node(n)

    g.add_edge("A", "B", bandwidth=100.0, delay=10.0, congestion=0.0, packet_loss=0.0, enabled=True)
    g.add_edge("B", "D", bandwidth=100.0, delay=10.0, congestion=0.0, packet_loss=0.0, enabled=True)
    g.add_edge("A", "C", bandwidth=100.0, delay=10.0, congestion=0.0, packet_loss=0.0, enabled=True)
    g.add_edge("C", "D", bandwidth=100.0, delay=10.0, congestion=0.0, packet_loss=0.0, enabled=True)
    return g


def create_weight_sensitivity_test_graph() -> nx.Graph:
    """
    Constructs two competing paths sensitive to the congestion coefficient:
        Path 1: High delay (15 ms), Low congestion (10%)
        Path 2: Low delay (5 ms), High congestion (50%)
    """
    g = nx.Graph()
    for n in ["S", "X", "Y", "D"]:
        g.add_node(n)

    # Path 1: S -> X -> D
    g.add_edge("S", "X", bandwidth=200.0, delay=7.5, congestion=10.0, packet_loss=0.0, enabled=True)
    g.add_edge("X", "D", bandwidth=200.0, delay=7.5, congestion=10.0, packet_loss=0.0, enabled=True)

    # Path 2: S -> Y -> D
    g.add_edge("S", "Y", bandwidth=200.0, delay=2.5, congestion=50.0, packet_loss=0.0, enabled=True)
    g.add_edge("Y", "D", bandwidth=200.0, delay=2.5, congestion=50.0, packet_loss=0.0, enabled=True)
    return g


class TestBaselineRouting:
    """Tests for Algorithm A: Baseline shortest-path routing."""

    def test_baseline_selects_minimum_hop_route(self):
        """Requirement 1: Baseline routing selects a minimum-hop route."""
        net = create_default_topology()
        # In default topology, Node_1 -> Node_4 -> Node_7 has only 2 hops
        result = find_baseline_route(net, DEFAULT_SOURCE, DEFAULT_DESTINATION)

        assert result.found is True
        assert result.algorithm == BASELINE_ALGORITHM_NAME
        assert result.route == ["Node_1", "Node_4", "Node_7"]
        assert result.hop_count == 2
        assert len(result.link_details) == 2

    def test_baseline_ignores_congestion(self):
        """Requirement 2: Baseline routing ignores congestion when selecting a route."""
        g = create_triangle_test_graph()
        # Direct A -> B is 90% congested, but has 1 hop vs 2 hops for A -> C -> B
        result = find_baseline_route(g, "A", "B")

        assert result.found is True
        assert result.route == ["A", "B"]
        assert result.hop_count == 1
        # Direct path cost was high due to congestion, but baseline picked it regardless
        assert result.link_details[0]["congestion"] == 90.0

    def test_baseline_ignores_disabled_links(self):
        """Requirement 6: Disabled links are never used."""
        net = create_default_topology()
        # Disable direct 2-hop link Node_1 -> Node_4
        net.disable_link("Node_1", "Node_4")

        result = find_baseline_route(net, DEFAULT_SOURCE, DEFAULT_DESTINATION)
        assert result.found is True
        # Must reroute to a 3-hop path
        assert result.hop_count == 3
        assert "Node_4" not in result.route or result.route != ["Node_1", "Node_4", "Node_7"]
        for detail in result.link_details:
            assert detail["from"] != "Node_1" or detail["to"] != "Node_4"


class TestQoSAwareRouting:
    """Tests for Algorithm B: QoS-Aware Routing."""

    def test_qos_selects_lowest_total_cost(self):
        """Requirement 3: QoS-aware routing selects the route with the lowest total cost."""
        g = create_triangle_test_graph()
        # Direct A -> B: delay 10, cong 90% => cost = 10 + 50 * 0.9 = 55.0
        # Detour A -> C -> B: delay 5+5=10, cong 0% => cost = (5+0) + (5+0) = 10.0
        result = find_qos_route(g, "A", "B", congestion_weight=50.0)

        assert result.found is True
        assert result.algorithm == QOS_ALGORITHM_NAME
        assert result.route == ["A", "C", "B"]
        assert result.hop_count == 2
        assert pytest.approx(result.cost, rel=1e-3) == 10.0

    def test_qos_selects_different_route_from_baseline(self):
        """Requirement 4: QoS-aware routing can select a different route from the baseline."""
        net = create_default_topology()

        baseline_res = find_baseline_route(net, DEFAULT_SOURCE, DEFAULT_DESTINATION)
        qos_res = find_qos_route(net, DEFAULT_SOURCE, DEFAULT_DESTINATION)

        # Baseline picks Node_1 -> Node_4 -> Node_7 (2 hops, high delay & congestion: cost > 100)
        assert baseline_res.route == ["Node_1", "Node_4", "Node_7"]
        assert baseline_res.hop_count == 2

        # QoS-aware picks Node_1 -> Node_3 -> Node_6 -> Node_7 (3 hops, low delay & congestion: cost ~ 27)
        assert qos_res.route == ["Node_1", "Node_3", "Node_6", "Node_7"]
        assert qos_res.hop_count == 3
        assert qos_res.cost < baseline_res.cost
        assert qos_res.route != baseline_res.route

    def test_bandwidth_requirement_excludes_infeasible_paths(self):
        """Requirement 5: Bandwidth requirements exclude infeasible paths."""
        g = create_bandwidth_test_graph()

        # Without bandwidth constraint, Path 1 (A -> B, cost = 5.0) is cheaper than Path 2 (A -> C -> B, cost = 20.0)
        res_unconstrained = find_qos_route(g, "A", "B", min_bandwidth=0.0)
        assert res_unconstrained.route == ["A", "B"]
        assert pytest.approx(res_unconstrained.cost, rel=1e-3) == 5.0

        # With min_bandwidth = 100 Mbps, Path 1 (50 Mbps) is disqualified; Path 2 (500 Mbps) is chosen
        res_constrained = find_qos_route(g, "A", "B", min_bandwidth=100.0)
        assert res_constrained.found is True
        assert res_constrained.route == ["A", "C", "B"]
        assert pytest.approx(res_constrained.cost, rel=1e-3) == 20.0
        assert res_constrained.bottleneck_bandwidth >= 100.0

        # With min_bandwidth = 1000 Mbps, no path is feasible
        res_infeasible = find_qos_route(g, "A", "B", min_bandwidth=1000.0)
        assert res_infeasible.found is False
        assert res_infeasible.route == []
        assert res_infeasible.cost is None
        assert "none satisfy the minimum bandwidth requirement" in res_infeasible.explanation

    def test_disabled_links_are_never_used(self):
        """Requirement 6: Disabled links are never used."""
        net = create_default_topology()
        # Normal QoS route is Node_1 -> Node_3 -> Node_6 -> Node_7
        # Disable Node_3 -> Node_6
        net.disable_link("Node_3", "Node_6")

        result = find_qos_route(net, DEFAULT_SOURCE, DEFAULT_DESTINATION)
        assert result.found is True
        # Route must adapt and avoid Node_3 -> Node_6
        for u, v in zip(result.route[:-1], result.route[1:]):
            assert not ({u, v} == {"Node_3", "Node_6"})

    def test_configured_cost_coefficient_affects_selection(self):
        """Requirement 11: Configured cost coefficient affects route selection when expected."""
        g = create_weight_sensitivity_test_graph()

        # Path 1 (S -> X -> D): delay = 15.0, congestion = 10%
        # Path 2 (S -> Y -> D): delay = 5.0, congestion = 50%

        # Low congestion weight (10.0):
        # Path 1 (S -> X -> D): (7.5 + 10 * 0.1) * 2 = 8.5 * 2 = 17.0
        # Path 2 (S -> Y -> D): (2.5 + 10 * 0.5) * 2 = 7.5 * 2 = 15.0 (Path 2 wins)
        res_low_weight = find_qos_route(g, "S", "D", congestion_weight=10.0)
        assert res_low_weight.route == ["S", "Y", "D"]
        assert pytest.approx(res_low_weight.cost, rel=1e-3) == 15.0

        # High congestion weight (100.0):
        # Path 1 (S -> X -> D): (7.5 + 100 * 0.1) * 2 = 17.5 * 2 = 35.0 (Path 1 wins)
        # Path 2 (S -> Y -> D): (2.5 + 100 * 0.5) * 2 = 52.5 * 2 = 105.0
        res_high_weight = find_qos_route(g, "S", "D", congestion_weight=100.0)
        assert res_high_weight.route == ["S", "X", "D"]
        assert pytest.approx(res_high_weight.cost, rel=1e-3) == 35.0


class TestEdgeCasesAndRobustness:
    """Tests for edge cases: unreachable destinations, identical nodes, invalid inputs, tie-breaking."""

    def test_unreachable_destination(self):
        """Requirement 7: Unreachable destinations are handled correctly."""
        g = nx.Graph()
        g.add_node("Island1")
        g.add_node("Island2")  # Disconnected

        baseline_res = find_baseline_route(g, "Island1", "Island2")
        assert baseline_res.found is False
        assert baseline_res.route == []
        assert baseline_res.hop_count == 0
        assert baseline_res.cost is None
        assert "No active path exists" in baseline_res.explanation

        qos_res = find_qos_route(g, "Island1", "Island2")
        assert qos_res.found is False
        assert qos_res.route == []
        assert qos_res.cost is None
        assert "No active path exists" in qos_res.explanation

    def test_identical_source_and_destination(self):
        """Requirement 8: Identical source and destination are handled consistently."""
        net = create_default_topology()

        baseline_res = find_baseline_route(net, "Node_2", "Node_2")
        assert baseline_res.found is True
        assert baseline_res.route == ["Node_2"]
        assert baseline_res.hop_count == 0
        assert baseline_res.cost == 0.0
        assert "identical" in baseline_res.explanation.lower()

        qos_res = find_qos_route(net, "Node_2", "Node_2", min_bandwidth=500.0)
        assert qos_res.found is True
        assert qos_res.route == ["Node_2"]
        assert qos_res.hop_count == 0
        assert qos_res.cost == 0.0
        assert "identical" in qos_res.explanation.lower()

    def test_invalid_nodes_handling(self):
        """Requirement 9: Invalid nodes are handled without unhandled exceptions."""
        net = create_default_topology()

        # Non-existent source
        res_src = find_baseline_route(net, "NonExistentSource", DEFAULT_DESTINATION)
        assert res_src.found is False
        assert res_src.route == []
        assert "Source node 'NonExistentSource' does not exist" in res_src.explanation

        # Non-existent destination
        res_dst = find_qos_route(net, DEFAULT_SOURCE, "NonExistentDest")
        assert res_dst.found is False
        assert res_dst.route == []
        assert "Destination node 'NonExistentDest' does not exist" in res_dst.explanation

    def test_equal_cost_routes_resolved_deterministically(self):
        """Requirement 10: Equal-cost routes are resolved deterministically."""
        g = create_equal_cost_test_graph()
        # Candidate 1: A -> B -> D (cost = 20, hops = 2)
        # Candidate 2: A -> C -> D (cost = 20, hops = 2)
        # Tie breaker rule: lexicographical tuple('A', 'B', 'D') < tuple('A', 'C', 'D')

        # Run multiple times to verify deterministic stability
        for _ in range(5):
            baseline_res = find_baseline_route(g, "A", "D")
            assert baseline_res.route == ["A", "B", "D"]

            qos_res = find_qos_route(g, "A", "D")
            assert qos_res.route == ["A", "B", "D"]
            assert pytest.approx(qos_res.cost, rel=1e-3) == 20.0

    def test_negative_parameters_raise_value_error(self):
        """Validation: Negative min_bandwidth or negative weight raises ValueError."""
        net = create_default_topology()

        with pytest.raises(ValueError, match="min_bandwidth must be non-negative"):
            find_qos_route(net, DEFAULT_SOURCE, DEFAULT_DESTINATION, min_bandwidth=-10.0)

        with pytest.raises(ValueError, match="congestion_weight must be non-negative"):
            find_qos_route(net, DEFAULT_SOURCE, DEFAULT_DESTINATION, congestion_weight=-1.0)

    def test_route_result_to_dict(self):
        """Result structure provides serializable dictionary."""
        net = create_default_topology()
        result = find_qos_route(net, DEFAULT_SOURCE, DEFAULT_DESTINATION)
        data = result.to_dict()

        assert isinstance(data, dict)
        assert data["algorithm"] == QOS_ALGORITHM_NAME
        assert data["source"] == DEFAULT_SOURCE
        assert data["destination"] == DEFAULT_DESTINATION
        assert isinstance(data["route"], list)
        assert isinstance(data["link_details"], list)
        assert data["found"] is True
