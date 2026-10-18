"""
Unit tests for QoS-Aware Network Topology, Link Properties, Mutations, and Resetting.
"""

import pytest

from src.network.link import LinkQoS
from src.network.topology import (
    DEFAULT_DESTINATION,
    DEFAULT_NODES,
    DEFAULT_SOURCE,
    QoSNetwork,
    build_networkx_graph,
    create_default_topology,
    reset_topology,
)


class TestTopologyCreation:
    """Tests topology construction and predefined network characteristics."""

    def test_node_count_and_endpoints(self):
        net = create_default_topology()
        # Node count requirement: approximately 6–8 nodes (here: 7)
        assert 6 <= len(net.nodes) <= 8
        assert len(net.nodes) == 7

        # Source and destination endpoints exist
        assert net.has_node(DEFAULT_SOURCE)
        assert net.has_node(DEFAULT_DESTINATION)
        for node_id in DEFAULT_NODES:
            assert net.has_node(node_id)

    def test_node_metadata(self):
        net = create_default_topology()
        for node_id, expected_data in DEFAULT_NODES.items():
            node_attrs = net.graph.nodes[node_id]
            assert "role" in node_attrs
            assert "pos" in node_attrs
            assert node_attrs["role"] == expected_data["role"]
            assert node_attrs["pos"] == expected_data["pos"]

    def test_multiple_alternative_paths_exist(self):
        net = create_default_topology()
        paths = net.find_all_paths(DEFAULT_SOURCE, DEFAULT_DESTINATION)
        # Network must provide multiple alternative paths between source and destination
        assert len(paths) >= 3
        # Check that at least 3 distinct paths start with source and end at destination
        for path in paths:
            assert path[0] == DEFAULT_SOURCE
            assert path[-1] == DEFAULT_DESTINATION

    def test_raw_networkx_graph_builder(self):
        g = build_networkx_graph()
        assert g.number_of_nodes() == 7
        assert g.number_of_edges() == 13
        assert g.has_edge("Node_1", "Node_2")


class TestLinkProperties:
    """Tests link QoS attributes, types, and domains."""

    def test_all_links_have_required_properties(self):
        net = create_default_topology()
        required_keys = {"bandwidth", "delay", "congestion", "packet_loss", "enabled"}

        for u, v in net.edges:
            link_data = net.get_link(u, v)
            assert required_keys.issubset(link_data.keys()), f"Link ({u}, {v}) missing keys"

            # Domain checks
            assert isinstance(link_data["bandwidth"], (int, float))
            assert link_data["bandwidth"] > 0

            assert isinstance(link_data["delay"], (int, float))
            assert link_data["delay"] >= 0

            assert isinstance(link_data["congestion"], (int, float))
            assert 0.0 <= link_data["congestion"] <= 100.0

            assert isinstance(link_data["packet_loss"], (int, float))
            assert 0.0 <= link_data["packet_loss"] <= 100.0

            assert isinstance(link_data["enabled"], bool)
            assert link_data["enabled"] is True

    def test_available_bandwidth_calculation(self):
        net = create_default_topology()
        link_qos = net.get_link_qos("Node_1", "Node_2")
        # 1000 Mbps with 15% congestion = 850 Mbps
        expected_available = 1000.0 * (1.0 - 0.15)
        assert pytest.approx(link_qos.available_bandwidth, rel=1e-3) == expected_available
        assert pytest.approx(net.get_available_bandwidth("Node_1", "Node_2"), rel=1e-3) == expected_available

    def test_link_qos_dataclass_properties(self):
        qos = LinkQoS(bandwidth=100.0, delay=10.0, congestion=25.0, packet_loss=1.0, enabled=True)
        assert pytest.approx(qos.packet_loss_probability) == 0.01
        assert pytest.approx(qos.available_bandwidth) == 75.0
        assert qos.effective_delay == 10.0

        qos_disabled = LinkQoS(bandwidth=100.0, delay=10.0, congestion=25.0, packet_loss=1.0, enabled=False)
        assert qos_disabled.available_bandwidth == 0.0
        assert qos_disabled.effective_delay == float("inf")


class TestLinkMutationsAndIsolation:
    """Tests modifying link attributes and ensuring default scenario remains uncorrupted."""

    def test_update_single_and_multiple_properties(self):
        net = create_default_topology()

        # Update bandwidth only
        net.update_link("Node_1", "Node_2", bandwidth=750.0)
        link = net.get_link("Node_1", "Node_2")
        assert link["bandwidth"] == 750.0
        assert link["delay"] == 5.0  # untouched

        # Update multiple properties
        net.update_link("Node_1", "Node_2", delay=12.5, congestion=40.0, packet_loss=0.8)
        updated = net.get_link("Node_1", "Node_2")
        assert updated["bandwidth"] == 750.0
        assert updated["delay"] == 12.5
        assert updated["congestion"] == 40.0
        assert updated["packet_loss"] == 0.8
        assert updated["enabled"] is True

    def test_default_scenario_isolation(self):
        net1 = create_default_topology()
        net1.update_link("Node_1", "Node_2", bandwidth=9999.0, delay=99.0, congestion=99.0)

        # Fresh network must retain original default values
        net2 = create_default_topology()
        link_default = net2.get_link("Node_1", "Node_2")
        assert link_default["bandwidth"] == 1000.0
        assert link_default["delay"] == 5.0
        assert link_default["congestion"] == 15.0

    def test_reset_network_restores_default(self):
        net = create_default_topology()

        # Mutate several links
        net.update_link("Node_1", "Node_2", bandwidth=25.0, congestion=90.0)
        net.disable_link("Node_1", "Node_3")
        net.update_link("Node_6", "Node_7", delay=200.0)

        # Verify mutated
        assert net.get_link("Node_1", "Node_2")["bandwidth"] == 25.0
        assert net.is_link_enabled("Node_1", "Node_3") is False

        # Reset using instance method
        net.reset_to_default()
        assert net.get_link("Node_1", "Node_2")["bandwidth"] == 1000.0
        assert net.get_link("Node_1", "Node_2")["congestion"] == 15.0
        assert net.is_link_enabled("Node_1", "Node_3") is True
        assert net.get_link("Node_6", "Node_7")["delay"] == 4.0

        # Reset using functional helper reset_topology
        net.disable_link("Node_5", "Node_7")
        assert net.is_link_enabled("Node_5", "Node_7") is False
        reset_topology(net)
        assert net.is_link_enabled("Node_5", "Node_7") is True


class TestInvalidValuesHandling:
    """Tests domain validation and sensible error handling."""

    def test_invalid_bandwidth(self):
        net = create_default_topology()
        with pytest.raises(ValueError, match="bandwidth must be positive"):
            net.update_link("Node_1", "Node_2", bandwidth=0)

        with pytest.raises(ValueError, match="bandwidth must be positive"):
            net.update_link("Node_1", "Node_2", bandwidth=-50)

        with pytest.raises(TypeError, match="bandwidth must be a numeric value"):
            net.update_link("Node_1", "Node_2", bandwidth="fast")

        with pytest.raises(TypeError, match="bandwidth must be a numeric value"):
            net.update_link("Node_1", "Node_2", bandwidth=True)

    def test_invalid_delay(self):
        net = create_default_topology()
        with pytest.raises(ValueError, match="delay must be non-negative"):
            net.update_link("Node_1", "Node_2", delay=-1.0)

        with pytest.raises(TypeError, match="delay must be a numeric value"):
            net.update_link("Node_1", "Node_2", delay=None)

    def test_invalid_congestion(self):
        net = create_default_topology()
        with pytest.raises(ValueError, match="congestion must be between 0.0% and 100.0%"):
            net.update_link("Node_1", "Node_2", congestion=-0.1)

        with pytest.raises(ValueError, match="congestion must be between 0.0% and 100.0%"):
            net.update_link("Node_1", "Node_2", congestion=100.1)

    def test_invalid_packet_loss(self):
        net = create_default_topology()
        with pytest.raises(ValueError, match="packet_loss must be between 0.0% and 100.0%"):
            net.update_link("Node_1", "Node_2", packet_loss=-1.0)

        with pytest.raises(ValueError, match="packet_loss must be between 0.0% and 100.0%"):
            net.update_link("Node_1", "Node_2", packet_loss=105.0)

    def test_invalid_enabled_type(self):
        net = create_default_topology()
        with pytest.raises(TypeError, match="enabled must be a boolean"):
            net.update_link("Node_1", "Node_2", enabled="yes")

    def test_nonexistent_link_and_node(self):
        net = create_default_topology()
        with pytest.raises(KeyError, match="Link between 'Node_1' and 'NonExistent' does not exist"):
            net.get_link("Node_1", "NonExistent")

        with pytest.raises(KeyError, match="Link between 'Node_1' and 'NonExistent' does not exist"):
            net.update_link("Node_1", "NonExistent", bandwidth=100)

        with pytest.raises(KeyError, match="Source node 'UnknownNode' not in network"):
            net.find_all_paths("UnknownNode", DEFAULT_DESTINATION)


class TestDisabledLinksHandling:
    """Tests disabled link behavior, path filtering, and capacity evaluation."""

    def test_disable_and_enable_link(self):
        net = create_default_topology()
        assert net.is_link_enabled("Node_1", "Node_2") is True

        net.disable_link("Node_1", "Node_2")
        assert net.is_link_enabled("Node_1", "Node_2") is False
        assert net.get_available_bandwidth("Node_1", "Node_2") == 0.0

        net.enable_link("Node_1", "Node_2")
        assert net.is_link_enabled("Node_1", "Node_2") is True
        assert net.get_available_bandwidth("Node_1", "Node_2") > 0.0

    def test_active_graph_excludes_disabled_edges(self):
        net = create_default_topology()
        net.disable_link("Node_1", "Node_2")
        net.disable_link("Node_5", "Node_7")

        active_g = net.get_active_graph()
        assert not active_g.has_edge("Node_1", "Node_2")
        assert not active_g.has_edge("Node_5", "Node_7")
        # All nodes remain in active graph
        assert active_g.number_of_nodes() == 7
        assert active_g.number_of_edges() == net.graph.number_of_edges() - 2

    def test_paths_exclude_disabled_links(self):
        net = create_default_topology()
        # Find paths before disabling
        all_paths_before = net.find_all_paths(DEFAULT_SOURCE, DEFAULT_DESTINATION)

        # Disable Node_1 -> Node_2
        net.disable_link("Node_1", "Node_2")
        active_paths = net.find_all_paths(DEFAULT_SOURCE, DEFAULT_DESTINATION, active_only=True)

        # No active path should use the disabled link Node_1 -> Node_2
        for path in active_paths:
            assert not (path[0] == "Node_1" and path[1] == "Node_2")

        # But alternative paths still exist (e.g., via Node_3 or Node_4)
        assert len(active_paths) > 0
        assert len(active_paths) < len(all_paths_before)

    def test_summary_reflects_disabled_count(self):
        net = create_default_topology()
        summary1 = net.get_summary()
        assert summary1["disabled_links"] == 0
        assert summary1["active_links"] == summary1["total_links"]

        net.disable_link("Node_1", "Node_4")
        summary2 = net.get_summary()
        assert summary2["disabled_links"] == 1
        assert summary2["active_links"] == summary2["total_links"] - 1

    def test_undirected_link_symmetry(self):
        net = create_default_topology()
        # Edge can be queried or modified with either node order
        link_uv = net.get_link("Node_1", "Node_2")
        link_vu = net.get_link("Node_2", "Node_1")
        assert link_uv == link_vu

        net.update_link("Node_2", "Node_1", delay=9.9)
        assert net.get_link("Node_1", "Node_2")["delay"] == 9.9

    def test_all_links_qos_retrieval(self):
        net = create_default_topology()
        all_qos = net.get_all_links_qos()
        assert len(all_qos) == len(net.edges)
        for item in all_qos:
            assert "source" in item
            assert "target" in item
            assert "available_bandwidth" in item

    def test_complete_partition_returns_no_paths(self):
        net = create_default_topology()
        # All links connected to Node_1 are (Node_1, Node_2), (Node_1, Node_3), (Node_1, Node_4)
        net.disable_link("Node_1", "Node_2")
        net.disable_link("Node_1", "Node_3")
        net.disable_link("Node_1", "Node_4")

        active_paths = net.find_all_paths(DEFAULT_SOURCE, DEFAULT_DESTINATION, active_only=True)
        assert active_paths == []

    def test_link_qos_serialization_and_copy(self):
        original = LinkQoS(bandwidth=250.0, delay=14.0, congestion=30.0, packet_loss=0.5, enabled=True)
        data = original.to_dict()
        restored = LinkQoS.from_dict(data)
        assert restored == original

        cloned = original.copy()
        assert cloned == original
        cloned.bandwidth = 500.0
        assert original.bandwidth == 250.0

