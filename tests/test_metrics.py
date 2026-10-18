"""
Unit tests for Phase 3: Performance Metrics, Traffic Profiles, and Routing Integration.
"""

import networkx as nx
import pytest

from src.network.topology import (
    DEFAULT_DESTINATION,
    DEFAULT_SOURCE,
    create_default_topology,
)
from src.routing import find_baseline_route, find_qos_route
from src.simulation.comparison import compare_routing_for_profile
from src.simulation.metrics import (
    calculate_average_congestion,
    calculate_bottleneck_bandwidth,
    calculate_end_to_end_delay,
    calculate_end_to_end_loss,
    calculate_estimated_throughput,
    evaluate_route_performance,
)
from src.simulation.traffic_profiles import (
    DEFAULT_PROFILES,
    TrafficProfile,
    get_traffic_profile,
    list_traffic_profiles,
)


class TestMetricCalculations:
    """Tests for individual performance metric calculation functions."""

    def test_delay_calculation(self):
        """Requirement: Delay calculation sums link delays along the route."""
        links = [
            {"delay": 5.0},
            {"delay": 12.5},
            {"delay": 8.2},
        ]
        assert pytest.approx(calculate_end_to_end_delay(links), rel=1e-3) == 25.7

        # Empty links
        assert calculate_end_to_end_delay([]) == 0.0

    def test_bottleneck_bandwidth(self):
        """Requirement: Bottleneck bandwidth finds minimum capacity along route."""
        links = [
            {"bandwidth": 1000.0},
            {"bandwidth": 250.0},
            {"bandwidth": 500.0},
        ]
        assert calculate_bottleneck_bandwidth(links) == 250.0

        # Empty links
        assert calculate_bottleneck_bandwidth([]) == 0.0

    def test_estimated_throughput_offered_below_bottleneck(self):
        """Requirement: Throughput when offered rate is below bottleneck."""
        offered = 20.0  # Mbps
        bottleneck = 100.0  # Mbps
        throughput = calculate_estimated_throughput(offered, bottleneck)
        assert throughput == 20.0

    def test_estimated_throughput_bottleneck_below_offered(self):
        """Requirement: Throughput when bottleneck is below offered rate."""
        offered = 150.0  # Mbps
        bottleneck = 45.0  # Mbps
        throughput = calculate_estimated_throughput(offered, bottleneck)
        assert throughput == 45.0

    def test_estimated_throughput_zero_or_negative(self):
        """Throughput with zero capacity or zero offered rate."""
        assert calculate_estimated_throughput(0.0, 100.0) == 0.0
        assert calculate_estimated_throughput(50.0, 0.0) == 0.0

    def test_zero_packet_loss(self):
        """Requirement: Single and multiple links with 0% loss yield exactly 0%."""
        links_single = [{"packet_loss": 0.0}]
        assert calculate_end_to_end_loss(links_single) == 0.0

        links_multi = [{"packet_loss": 0.0}, {"packet_loss": 0.0}, {"packet_loss": 0.0}]
        assert calculate_end_to_end_loss(links_multi) == 0.0

        # Empty links
        assert calculate_end_to_end_loss([]) == 0.0

    def test_end_to_end_loss_across_multiple_links(self):
        """
        Requirement: End-to-end loss treating each link as independent loss probability.
        Link 1: 1.0% loss (0.01) -> survival 0.99
        Link 2: 2.0% loss (0.02) -> survival 0.98
        Total survival = 0.99 * 0.98 = 0.9702
        Total loss = 1 - 0.9702 = 0.0298 = 2.98%
        """
        links = [{"packet_loss": 1.0}, {"packet_loss": 2.0}]
        loss = calculate_end_to_end_loss(links)
        assert pytest.approx(loss, rel=1e-3) == 2.98

        # Single link with 5.0%
        assert pytest.approx(calculate_end_to_end_loss([{"packet_loss": 5.0}]), rel=1e-3) == 5.0

    def test_average_congestion(self):
        """Requirement: Arithmetic mean of link congestion percentages."""
        links = [
            {"congestion": 10.0},
            {"congestion": 25.0},
            {"congestion": 40.0},
        ]
        # (10 + 25 + 40) / 3 = 25.0%
        assert pytest.approx(calculate_average_congestion(links), rel=1e-3) == 25.0

        # Empty links
        assert calculate_average_congestion([]) == 0.0


class TestTrafficProfiles:
    """Tests for traffic profile creation, configuration, and constraints."""

    def test_default_profiles_exist_and_configured(self):
        """Requirement: Three profiles: Voice (VoIP), Video streaming, Bulk data."""
        profiles = list_traffic_profiles()
        assert "voip" in profiles
        assert "video" in profiles
        assert "bulk_data" in profiles

        voip = get_traffic_profile("voip")
        assert voip.display_name == "Voice (VoIP)"
        assert voip.min_bandwidth > 0
        assert voip.max_acceptable_delay is not None
        assert voip.offered_traffic_rate > 0

        video = get_traffic_profile("video")
        assert video.display_name == "Video Streaming"
        assert video.min_bandwidth >= voip.min_bandwidth

        bulk = get_traffic_profile("bulk_data")
        assert bulk.display_name == "Bulk Data Transfer"
        assert bulk.min_bandwidth >= video.min_bandwidth

    def test_custom_profile_validation(self):
        """Validation: Negative rates or delays raise ValueError."""
        with pytest.raises(ValueError, match="min_bandwidth must be non-negative"):
            TrafficProfile("test", "Test", min_bandwidth=-1.0, offered_traffic_rate=10.0)

        with pytest.raises(ValueError, match="offered_traffic_rate must be non-negative"):
            TrafficProfile("test", "Test", min_bandwidth=10.0, offered_traffic_rate=-5.0)

        with pytest.raises(ValueError, match="max_acceptable_delay must be non-negative"):
            TrafficProfile("test", "Test", min_bandwidth=10.0, offered_traffic_rate=5.0, max_acceptable_delay=-1.0)

    def test_unknown_profile_raises_key_error(self):
        with pytest.raises(KeyError, match="Unknown traffic profile 'unknown'"):
            get_traffic_profile("unknown")


class TestIntegrationAndEvaluation:
    """Tests integrating routing algorithms with traffic profiles and delay evaluations."""

    def test_delay_requirement_evaluation(self):
        """Requirement: Clearly indicate when a route exceeds a profile's delay requirement."""
        net = create_default_topology()

        # Voice profile has strict max_acceptable_delay = 30.0 ms
        voip_profile = get_traffic_profile("voip")

        # Baseline route in default network is Node_1 -> Node_4 -> Node_7 (Delay: 30 + 35 = 65 ms)
        baseline_res = find_baseline_route(net, DEFAULT_SOURCE, DEFAULT_DESTINATION)
        baseline_perf = evaluate_route_performance(baseline_res, voip_profile)

        assert baseline_perf.end_to_end_delay == 65.0
        assert baseline_perf.meets_delay_requirement is False
        assert baseline_perf.is_viable is False
        assert "exceeds delay SLA" in baseline_perf.explanation

        # QoS-aware route is Node_1 -> Node_3 -> Node_6 -> Node_7 (Delay: 3 + 4 + 4 = 11 ms)
        qos_res = find_qos_route(net, DEFAULT_SOURCE, DEFAULT_DESTINATION, min_bandwidth=voip_profile.min_bandwidth)
        qos_perf = evaluate_route_performance(qos_res, voip_profile)

        assert qos_perf.end_to_end_delay == 11.0
        assert qos_perf.meets_delay_requirement is True
        assert qos_perf.is_viable is True
        assert "Meets all Voice (VoIP) requirements" in qos_perf.explanation

    def test_compare_routing_for_profile_voip(self):
        """Integration test: compare_routing_for_profile on VoIP."""
        net = create_default_topology()
        comp = compare_routing_for_profile(net, DEFAULT_SOURCE, DEFAULT_DESTINATION, "voip")

        assert comp.profile.name == "voip"
        assert comp.baseline.found is True
        assert comp.qos_aware.found is True
        # Baseline delay (65 ms) violates VoIP SLA (30 ms)
        assert comp.baseline.meets_delay_requirement is False
        assert comp.qos_aware.meets_delay_requirement is True
        # Recommended algorithm should be QoS-Aware Routing
        assert comp.recommended_algorithm == comp.qos_aware.algorithm
        assert "QoS-Aware Routing is strongly recommended" in comp.summary

    def test_compare_routing_for_profile_video(self):
        """Integration test: compare_routing_for_profile on Video Streaming."""
        net = create_default_topology()
        # Video requires 25.0 Mbps.
        # Baseline route via Node_4 has only 100 Mbps links, but delay is 65 ms (SLA is 75 ms).
        # QoS route has 500 Mbps capacity and 11 ms delay.
        comp = compare_routing_for_profile(net, DEFAULT_SOURCE, DEFAULT_DESTINATION, "video")

        assert comp.qos_aware.bottleneck_bandwidth >= 25.0
        assert comp.qos_aware.is_viable is True
        assert comp.recommended_algorithm == comp.qos_aware.algorithm

    def test_compare_routing_unreachable_destination(self):
        """Requirement: Handle invalid or unreachable routes gracefully."""
        g = nx.Graph()
        g.add_node("IsolatedA")
        g.add_node("IsolatedB")

        voip = get_traffic_profile("voip")
        comp = compare_routing_for_profile(g, "IsolatedA", "IsolatedB", voip)

        assert comp.baseline.found is False
        assert comp.qos_aware.found is False
        assert comp.baseline.end_to_end_delay == 0.0
        assert comp.baseline.estimated_throughput == 0.0
        assert comp.qos_aware.estimated_throughput == 0.0
        assert comp.recommended_algorithm is None
        assert "No viable route could be found" in comp.summary

    def test_compare_routing_identical_source_destination(self):
        """Identical source and destination (0 hops) handling."""
        net = create_default_topology()
        comp = compare_routing_for_profile(net, "Node_1", "Node_1", "voip")

        assert comp.baseline.found is True
        assert comp.qos_aware.found is True
        assert comp.baseline.end_to_end_delay == 0.0
        assert comp.baseline.hop_count == 0
        assert comp.qos_aware.hop_count == 0

    def test_serialization_to_dict(self):
        """Ensure all comparison and performance objects serialize cleanly to dict."""
        net = create_default_topology()
        comp = compare_routing_for_profile(net, DEFAULT_SOURCE, DEFAULT_DESTINATION, "bulk_data")
        data = comp.to_dict()

        assert isinstance(data, dict)
        assert "profile" in data
        assert "baseline" in data
        assert "qos_aware" in data
        assert "summary" in data
        assert data["baseline"]["algorithm"] == comp.baseline.algorithm
        assert data["qos_aware"]["bottleneck_bandwidth_mbps"] >= comp.profile.min_bandwidth
