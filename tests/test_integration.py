"""
Comprehensive integration tests verifying end-to-end simulation workflows,
scenario transitions, manual link modifications, and metric integrity.
"""

import pytest

from src.network.topology import DEFAULT_DESTINATION, DEFAULT_SOURCE, create_default_topology
from src.simulation.comparison import compare_routing_for_profile
from src.simulation.scenarios import (
    DEFAULT_CONGESTED_LINKS,
    DEFAULT_FAILED_LINK,
    load_congestion_scenario,
    load_link_failure_scenario,
    load_normal_scenario,
)
from src.simulation.traffic_profiles import get_traffic_profile
from src.visualization.plots import create_comparison_metrics_chart, create_topology_figure


class TestEndToEndIntegration:
    """Verifies complete end-to-end application behaviors."""

    def test_normal_network_workflow(self):
        """Verify normal network routing, SLA compliance, and topology visualization."""
        scen = load_normal_scenario("voip")
        assert scen.results_after.baseline.found is True
        assert scen.results_after.qos_aware.found is True

        # Baseline picks 2 hops (Node_1 -> Node_4 -> Node_7) with 65 ms delay (violating 30 ms SLA)
        assert scen.results_after.baseline.hop_count == 2
        assert scen.results_after.baseline.meets_delay_requirement is False
        assert scen.results_after.baseline.is_viable is False

        # QoS-aware picks 3 hops (Node_1 -> Node_3 -> Node_6 -> Node_7) with 11 ms delay (compliant)
        assert scen.results_after.qos_aware.hop_count == 3
        assert scen.results_after.qos_aware.meets_delay_requirement is True
        assert scen.results_after.qos_aware.is_viable is True

        # Verify figure generation matches
        fig = create_topology_figure(
            scen.network,
            scen.results_after.baseline.route,
            scen.results_after.qos_aware.route,
            DEFAULT_SOURCE,
            DEFAULT_DESTINATION,
        )
        assert len(fig.data) >= 3

    def test_congestion_workflow_and_route_shift(self):
        """Verify congestion scenario changes properties, triggers QoS shift, leaves baseline unchanged."""
        scen = load_congestion_scenario("voip")

        # Verify link congestion applied
        for (u, v), cong_val in DEFAULT_CONGESTED_LINKS.items():
            assert scen.network.get_link(u, v)["congestion"] == cong_val

        # QoS route shifted from (1-3-6-7) to Fiber Core (1-2-5-7)
        assert scen.route_changed_qos is True
        assert scen.results_before.qos_aware.route == ["Node_1", "Node_3", "Node_6", "Node_7"]
        assert scen.results_after.qos_aware.route == ["Node_1", "Node_2", "Node_5", "Node_7"]

        # Baseline route remained strictly on hop-count objective (1-4-7)
        assert scen.route_changed_baseline is False
        assert scen.results_after.baseline.route == ["Node_1", "Node_4", "Node_7"]

    def test_link_failure_workflow_and_adaptation(self):
        """Verify link failure disables link and both algorithms route around it."""
        u, v = DEFAULT_FAILED_LINK
        scen = load_link_failure_scenario("voip", failed_link=(u, v))

        assert scen.network.is_link_enabled(u, v) is False
        # Neither algorithm traverses the severed link
        for r in [scen.results_after.baseline.route, scen.results_after.qos_aware.route]:
            edges = set(zip(r[:-1], r[1:]))
            assert (u, v) not in edges and (v, u) not in edges

        # Alternative route was found for QoS
        assert scen.results_after.qos_aware.found is True
        assert scen.route_changed_qos is True

    def test_manual_link_modification_and_recalculation(self):
        """Verify modifying link properties on active network updates comparison results."""
        net = create_default_topology()
        voip = get_traffic_profile("voip")

        # Initial comparison
        res1 = compare_routing_for_profile(net, DEFAULT_SOURCE, DEFAULT_DESTINATION, voip)
        assert res1.qos_aware.route == ["Node_1", "Node_3", "Node_6", "Node_7"]

        # Manually congest Node_1-Node_3 to 95%
        net.update_link("Node_1", "Node_3", congestion=95.0)
        net.update_link("Node_3", "Node_6", congestion=95.0)

        # Recalculate
        res2 = compare_routing_for_profile(net, DEFAULT_SOURCE, DEFAULT_DESTINATION, voip)
        assert res2.qos_aware.route == ["Node_1", "Node_2", "Node_5", "Node_7"]

        # Reverting to default restores original route
        net.reset_to_default()
        res3 = compare_routing_for_profile(net, DEFAULT_SOURCE, DEFAULT_DESTINATION, voip)
        assert res3.qos_aware.route == ["Node_1", "Node_3", "Node_6", "Node_7"]

    def test_source_destination_switching(self):
        """Verify changing source and destination recalculates routes and handles unreachability."""
        net = create_default_topology()
        voip = get_traffic_profile("voip")

        # Route between intermediate nodes Node_2 -> Node_6
        res_mid = compare_routing_for_profile(net, "Node_2", "Node_6", voip)
        assert res_mid.baseline.found is True
        assert res_mid.baseline.route[0] == "Node_2"
        assert res_mid.baseline.route[-1] == "Node_6"

        # Disconnected node test
        for nb in list(net.graph.neighbors("Node_7")):
            net.disable_link("Node_7", nb)

        res_unreach = compare_routing_for_profile(net, DEFAULT_SOURCE, DEFAULT_DESTINATION, voip)
        assert res_unreach.baseline.found is False
        assert res_unreach.qos_aware.found is False
        assert "No active path exists" in res_unreach.baseline.explanation

        # Charts handle missing routes safely
        fig = create_comparison_metrics_chart(res_unreach.baseline, res_unreach.qos_aware)
        assert len(fig.data) == 4

    def test_metrics_and_charts_consistency(self):
        """Verify calculated performance metrics match chart values and cost formulas."""
        net = create_default_topology()
        voip = get_traffic_profile("voip")
        comp = compare_routing_for_profile(net, DEFAULT_SOURCE, DEFAULT_DESTINATION, voip)

        # Baseline
        assert comp.baseline.end_to_end_delay == sum(link["delay"] for link in comp.baseline.link_details)
        assert comp.baseline.bottleneck_bandwidth == min(link["bandwidth"] for link in comp.baseline.link_details)
        assert comp.baseline.estimated_throughput == min(voip.offered_traffic_rate, comp.baseline.bottleneck_bandwidth)

        # QoS-aware
        assert comp.qos_aware.end_to_end_delay == sum(link["delay"] for link in comp.qos_aware.link_details)
        assert comp.qos_aware.bottleneck_bandwidth == min(link["bandwidth"] for link in comp.qos_aware.link_details)
        assert comp.qos_aware.route_cost == sum(link["cost"] for link in comp.qos_aware.link_details)
