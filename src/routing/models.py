"""
Result models for network routing algorithms.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RouteResult:
    """
    Standardized, consistent result structure returned by all routing algorithms.

    Attributes:
        algorithm: Name of the algorithm (e.g. 'Baseline Shortest Path', 'QoS-Aware Routing').
        source: Source node identifier.
        destination: Destination node identifier.
        route: Ordered list of node IDs defining the chosen path (e.g. ['Node_1', 'Node_4', 'Node_7']).
        hop_count: Number of link transitions (0 if identical or no route).
        cost: Calculated QoS route cost, or None if no valid route was found.
        found: True if a valid feasible route was found, False otherwise.
        explanation: Human-readable narrative detailing why this route was selected or why it failed.
        link_details: List of per-hop link metrics along the chosen route.
        total_delay: Sum of one-way delays (ms) along the path.
        bottleneck_bandwidth: Minimum link capacity (Mbps) along the path.
    """

    algorithm: str
    source: str
    destination: str
    route: List[str]
    hop_count: int
    cost: Optional[float]
    found: bool
    explanation: str
    link_details: List[Dict[str, Any]] = field(default_factory=list)
    total_delay: float = 0.0
    bottleneck_bandwidth: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert the routing result into a serializable dictionary."""
        return {
            "algorithm": self.algorithm,
            "source": self.source,
            "destination": self.destination,
            "route": list(self.route),
            "hop_count": self.hop_count,
            "cost": self.cost,
            "found": self.found,
            "explanation": self.explanation,
            "total_delay": self.total_delay,
            "bottleneck_bandwidth": self.bottleneck_bandwidth,
            "link_details": self.link_details,
        }
