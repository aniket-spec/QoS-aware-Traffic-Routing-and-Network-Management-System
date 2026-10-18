"""
Reproducible Network Scenarios for QoS-Aware Routing and Performance Evaluation.

Implements three deterministic, student-friendly benchmark scenarios:
1. Scenario A: Normal Network (unmodified baseline topology).
2. Scenario B: Network Congestion (high congestion injected onto preferred links).
3. Scenario C: Link Failure (disabling a preferred link to demonstrate dynamic rerouting).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple, Union

from src.network.topology import (
    DEFAULT_DESTINATION,
    DEFAULT_SOURCE,
    QoSNetwork,
    create_default_topology,
)
from src.simulation.comparison import (
    SimulationComparisonResult,
    compare_routing_for_profile,
)
from src.simulation.traffic_profiles import TrafficProfile, get_traffic_profile

DEFAULT_CONGESTED_LINKS: Dict[Tuple[str, str], float] = {
    ("Node_1", "Node_3"): 85.0,
    ("Node_3", "Node_6"): 85.0,
}

DEFAULT_FAILED_LINK: Tuple[str, str] = ("Node_3", "Node_6")


@dataclass
class ScenarioResult:
    """
    Encapsulates results from executing a reproducible network scenario.

    Attributes:
        scenario_name: Name of the scenario.
        description: Explanatory text summarizing scenario purpose and conditions.
        network: The independent QoSNetwork instance used in the scenario.
        profile: The TrafficProfile applied during simulation.
        results_after: Routing and performance comparison under scenario conditions.
        results_before: Pre-change baseline comparison (for congestion/failure experiments).
        changes_applied: Dictionary detailing the network modifications applied.
    """

    scenario_name: str
    description: str
    network: QoSNetwork
    profile: TrafficProfile
    results_after: SimulationComparisonResult
    results_before: Optional[SimulationComparisonResult] = None
    changes_applied: Dict[str, Any] = field(default_factory=dict)

    @property
    def route_changed_qos(self) -> bool:
        """Returns True if the QoS-aware route changed between before and after."""
        if self.results_before is None:
            return False
        return self.results_before.qos_aware.route != self.results_after.qos_aware.route

    @property
    def route_changed_baseline(self) -> bool:
        """Returns True if the baseline route changed between before and after."""
        if self.results_before is None:
            return False
        return self.results_before.baseline.route != self.results_after.baseline.route

    def to_dict(self) -> Dict[str, Any]:
        """Convert scenario result to a dictionary representation."""
        return {
            "scenario_name": self.scenario_name,
            "description": self.description,
            "profile": self.profile.to_dict(),
            "changes_applied": self.changes_applied,
            "route_changed_qos": self.route_changed_qos,
            "route_changed_baseline": self.route_changed_baseline,
            "results_after": self.results_after.to_dict(),
            "results_before": self.results_before.to_dict() if self.results_before else None,
        }


def load_normal_scenario(
    profile: Union[TrafficProfile, str] = "voip",
    source: str = DEFAULT_SOURCE,
    destination: str = DEFAULT_DESTINATION,
) -> ScenarioResult:
    """
    Scenario A: Normal Network.

    Loads a pristine, unmodified copy of the default 7-node network and evaluates
    both baseline and QoS-aware routing for the chosen traffic profile.
    """
    resolved_profile = (
        get_traffic_profile(profile) if isinstance(profile, str) else profile
    )
    network = create_default_topology()

    comparison = compare_routing_for_profile(
        network=network,
        source=source,
        destination=destination,
        profile=resolved_profile,
    )

    description = (
        "Scenario A (Normal Network): Operates under pristine default conditions. "
        "Baseline selects the minimum-hop route, while QoS-aware routing chooses "
        "the lowest-cost corridor meeting bandwidth requirements."
    )

    return ScenarioResult(
        scenario_name="Scenario A: Normal Network",
        description=description,
        network=network,
        profile=resolved_profile,
        results_after=comparison,
        results_before=None,
        changes_applied={},
    )


def load_congestion_scenario(
    profile: Union[TrafficProfile, str] = "voip",
    congested_links: Optional[Dict[Tuple[str, str], float]] = None,
    source: str = DEFAULT_SOURCE,
    destination: str = DEFAULT_DESTINATION,
) -> ScenarioResult:
    """
    Scenario B: Network Congestion.

    1. Starts with a fresh copy of the default network.
    2. Records pre-congestion routing comparison (results_before).
    3. Injects high congestion onto specified links (defaulting to Node_1-Node_3 and Node_3-Node_6).
    4. Evaluates routing comparison post-congestion (results_after).
    5. Demonstrates how QoS-aware routing shifts traffic to less congested paths
       while baseline routing remains oblivious to link congestion.
    """
    resolved_profile = (
        get_traffic_profile(profile) if isinstance(profile, str) else profile
    )
    network = create_default_topology()

    # Step 1: Benchmark before congestion
    results_before = compare_routing_for_profile(
        network=network,
        source=source,
        destination=destination,
        profile=resolved_profile,
    )

    # Step 2: Apply congestion modifications
    links_to_modify = (
        DEFAULT_CONGESTED_LINKS if congested_links is None else congested_links
    )
    changes_record: Dict[str, Any] = {"congested_links": {}}

    for (u, v), cong_val in links_to_modify.items():
        network.update_link(u, v, congestion=cong_val)
        changes_record["congested_links"][f"{u} <-> {v}"] = cong_val

    # Step 3: Evaluate after congestion
    results_after = compare_routing_for_profile(
        network=network,
        source=source,
        destination=destination,
        profile=resolved_profile,
    )

    description = (
        "Scenario B (Network Congestion): Severe congestion is injected onto preferred "
        "corridor links. QoS-aware routing detects the rising cost penalty and shifts "
        "traffic to an alternative corridor, whereas baseline routing remains unchanged."
    )

    return ScenarioResult(
        scenario_name="Scenario B: Network Congestion",
        description=description,
        network=network,
        profile=resolved_profile,
        results_after=results_after,
        results_before=results_before,
        changes_applied=changes_record,
    )


def load_link_failure_scenario(
    profile: Union[TrafficProfile, str] = "voip",
    failed_link: Tuple[str, str] = DEFAULT_FAILED_LINK,
    source: str = DEFAULT_SOURCE,
    destination: str = DEFAULT_DESTINATION,
) -> ScenarioResult:
    """
    Scenario C: Link Failure.

    1. Starts with a fresh copy of the default network.
    2. Records pre-failure routing comparison (results_before).
    3. Disables the selected link (defaulting to Node_3-Node_6 on the preferred QoS path).
    4. Evaluates routing comparison post-failure (results_after).
    5. Demonstrates automated route adaptation around physical network breaks.
    """
    resolved_profile = (
        get_traffic_profile(profile) if isinstance(profile, str) else profile
    )
    network = create_default_topology()

    # Step 1: Benchmark before failure
    results_before = compare_routing_for_profile(
        network=network,
        source=source,
        destination=destination,
        profile=resolved_profile,
    )

    # Step 2: Disable the targeted link
    u, v = failed_link
    network.disable_link(u, v)
    changes_record = {"failed_link": f"{u} <-> {v}", "status": "disabled"}

    # Step 3: Evaluate after link failure
    results_after = compare_routing_for_profile(
        network=network,
        source=source,
        destination=destination,
        profile=resolved_profile,
    )

    description = (
        f"Scenario C (Link Failure): Link {u} <-> {v} is disabled. "
        "Both algorithms recalculate paths in the remaining active topology, "
        "demonstrating resilience and dynamic path diversion."
    )

    return ScenarioResult(
        scenario_name="Scenario C: Link Failure",
        description=description,
        network=network,
        profile=resolved_profile,
        results_after=results_after,
        results_before=results_before,
        changes_applied=changes_record,
    )
