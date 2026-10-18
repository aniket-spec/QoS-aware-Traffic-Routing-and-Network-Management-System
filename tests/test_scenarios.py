"""
Unit tests for Phase 4: Reproducible Network Scenarios.
"""

import pytest

from src.network.topology import (
    DEFAULT_DESTINATION,
    DEFAULT_SOURCE,
    create_default_topology,
)
from src.simulation.scenarios import (
    DEFAULT_CONGESTED_LINKS,
    DEFAULT_FAILED_LINK,
    ScenarioResult,
    load_congestion_scenario,
    load_link_failure_scenario,
    load_normal_scenario,
)
from src.simulation.traffic_profiles import get_traffic_profile


class TestScenarioExecution:
    """Tests loading and executing predefined simulation scenarios."""

    def test_load_normal_scenario(self):
        """Requirement: Normal scenario loads successfully and preserves default conditions."""
        scenario = load_normal_scenario("voip")

        assert isinstance(scenario, ScenarioResult)
        assert scenario.scenario_name == "Scenario A: Normal Network"
        assert scenario.results_before is None
        assert scenario.results_after.profile.name == "voip"
        assert scenario.network.number_of_nodes() == 7 if hasattr(scenario.network, "number_of_nodes") else len(scenario.network.nodes) == 7

        # In default network for voip:
        # Baseline picks Node_1 -> Node_4 -> Node_7 (2 hops)
        # QoS picks Node_1 -> Node_3 -> Node_6 -> Node_7 (3 hops)
        assert scenario.results_after.baseline.route == ["Node_1", "Node_4", "Node_7"]
        assert scenario.results_after.qos_aware.route == ["Node_1", "Node_3", "Node_6", "Node_7"]
        assert scenario.results_after.baseline.is_viable is False  # Delay violates VoIP SLA
        assert scenario.results_after.qos_aware.is_viable is True

    def test_load_congestion_scenario_shifts_qos_route(self):
        """Requirement: Congestion changes link properties and influences QoS route selection."""
        scenario = load_congestion_scenario("voip")

        assert scenario.scenario_name == "Scenario B: Network Congestion"
        assert scenario.results_before is not None

        # Verify link congestion changed on the network instance
        for (u, v), expected_cong in DEFAULT_CONGESTED_LINKS.items():
            assert scenario.network.get_link(u, v)["congestion"] == expected_cong

        # Before congestion: QoS route was Node_1 -> Node_3 -> Node_6 -> Node_7
        assert scenario.results_before.qos_aware.route == ["Node_1", "Node_3", "Node_6", "Node_7"]
        assert pytest.approx(scenario.results_before.qos_aware.route_cost, rel=1e-3) == 27.0

        # After congestion on (1,3) and (3,6):
        # QoS route intelligently diverts to Fiber Core: Node_1 -> Node_2 -> Node_5 -> Node_7
        assert scenario.results_after.qos_aware.route == ["Node_1", "Node_2", "Node_5", "Node_7"]
        assert scenario.route_changed_qos is True

        # Baseline ignores congestion and remains on Node_1 -> Node_4 -> Node_7
        assert scenario.results_after.baseline.route == scenario.results_before.baseline.route
        assert scenario.route_changed_baseline is False

    def test_load_link_failure_scenario_reroutes_traffic(self):
        """Requirement: Link failure disables intended link and recalculates routes correctly."""
        # Default failed link is ("Node_3", "Node_6") on the preferred QoS corridor
        scenario = load_link_failure_scenario("voip", failed_link=DEFAULT_FAILED_LINK)

        assert scenario.scenario_name == "Scenario C: Link Failure"
        assert scenario.results_before is not None

        # Verify failed link is disabled in the network
        u, v = DEFAULT_FAILED_LINK
        assert scenario.network.is_link_enabled(u, v) is False
        assert not scenario.network.get_active_graph().has_edge(u, v)

        # Before failure: QoS used the failed link
        assert scenario.results_before.qos_aware.route == ["Node_1", "Node_3", "Node_6", "Node_7"]

        # After failure: QoS reroutes around the failure via cross-link (Node_3 -> Node_5)
        assert scenario.results_after.qos_aware.found is True
        assert scenario.results_after.qos_aware.route != scenario.results_before.qos_aware.route
        assert scenario.route_changed_qos is True
        # Verify disabled link is not traversed by either algorithm
        for u_hop, v_hop in zip(scenario.results_after.qos_aware.route[:-1], scenario.results_after.qos_aware.route[1:]):
            assert {u_hop, v_hop} != {u, v}

    def test_baseline_link_failure_scenario(self):
        """Test disabling link on baseline's preferred path (Node_1, Node_4)."""
        scenario = load_link_failure_scenario("voip", failed_link=("Node_1", "Node_4"))

        # Before failure: Baseline route was Node_1 -> Node_4 -> Node_7 (2 hops)
        assert scenario.results_before.baseline.route == ["Node_1", "Node_4", "Node_7"]

        # After failure: Baseline must reroute to a 3-hop path
        assert scenario.results_after.baseline.route != ["Node_1", "Node_4", "Node_7"]
        assert scenario.results_after.baseline.hop_count == 3
        assert scenario.route_changed_baseline is True


class TestScenarioIsolation:
    """Tests ensuring each scenario starts from an independent network without cross-contamination."""

    def test_scenario_isolation(self):
        """Requirement: Resetting or running one scenario does not contaminate another."""
        # Run congestion scenario which heavily modifies links
        scen_cong = load_congestion_scenario("voip")
        assert scen_cong.network.get_link("Node_1", "Node_3")["congestion"] == 85.0

        # Run link failure scenario which disables links
        scen_fail = load_link_failure_scenario("voip")
        assert scen_fail.network.is_link_enabled("Node_3", "Node_6") is False

        # Now run normal scenario: it must be completely pristine
        scen_norm = load_normal_scenario("voip")
        assert scen_norm.network.get_link("Node_1", "Node_3")["congestion"] == 10.0
        assert scen_norm.network.is_link_enabled("Node_3", "Node_6") is True

        # Fresh default topology is also completely unaffected
        clean_net = create_default_topology()
        assert clean_net.get_link("Node_1", "Node_3")["congestion"] == 10.0
        assert clean_net.is_link_enabled("Node_3", "Node_6") is True

    def test_custom_congestion_and_profiles(self):
        """Scenarios accept custom congested link values and custom profiles."""
        custom_links = {("Node_1", "Node_2"): 95.0}
        scen = load_congestion_scenario("video", congested_links=custom_links)
        assert scen.network.get_link("Node_1", "Node_2")["congestion"] == 95.0
        assert scen.profile.name == "video"

    def test_scenario_result_to_dict(self):
        """ScenarioResult provides complete dictionary representation."""
        scen = load_congestion_scenario("voip")
        data = scen.to_dict()

        assert isinstance(data, dict)
        assert "scenario_name" in data
        assert "description" in data
        assert "profile" in data
        assert "results_after" in data
        assert "results_before" in data
        assert data["route_changed_qos"] is True
