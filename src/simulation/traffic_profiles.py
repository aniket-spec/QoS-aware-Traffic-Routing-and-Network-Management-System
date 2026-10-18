"""
Traffic Profile models and predefined application traffic classes.

Provides configuration profiles for different network application types:
1. Voice (VoIP): Low latency, modest bandwidth requirement.
2. Video Streaming: Higher bandwidth requirement, moderate latency tolerance.
3. Bulk Data: Greater latency tolerance, configurable bandwidth requirement.

Note: Predefined numerical thresholds are illustrative demonstration settings,
not universal networking standards.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class TrafficProfile:
    """
    Configuration specification for a traffic class.

    Attributes:
        name: Internal unique profile identifier (e.g. 'voip', 'video', 'bulk_data').
        display_name: Human-friendly display label (e.g. 'Voice (VoIP)').
        min_bandwidth: Minimum acceptable link bandwidth in Mbps.
        offered_traffic_rate: Demanded transmission rate in Mbps.
        max_acceptable_delay: Maximum acceptable end-to-end delay in ms (or None).
        description: Informational explanation of traffic profile characteristics.
    """

    name: str
    display_name: str
    min_bandwidth: float
    offered_traffic_rate: float
    max_acceptable_delay: Optional[float] = None
    description: str = ""

    def __post_init__(self) -> None:
        if self.min_bandwidth < 0:
            raise ValueError(f"min_bandwidth must be non-negative (>= 0), got {self.min_bandwidth}")
        if self.offered_traffic_rate < 0:
            raise ValueError(
                f"offered_traffic_rate must be non-negative (>= 0), got {self.offered_traffic_rate}"
            )
        if self.max_acceptable_delay is not None and self.max_acceptable_delay < 0:
            raise ValueError(
                f"max_acceptable_delay must be non-negative (>= 0), got {self.max_acceptable_delay}"
            )

    def to_dict(self) -> Dict[str, object]:
        """Convert profile to a dictionary representation."""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "min_bandwidth": self.min_bandwidth,
            "offered_traffic_rate": self.offered_traffic_rate,
            "max_acceptable_delay": self.max_acceptable_delay,
            "description": self.description,
        }


# Illustrative demonstration default traffic profiles
DEFAULT_PROFILES: Dict[str, TrafficProfile] = {
    "voip": TrafficProfile(
        name="voip",
        display_name="Voice (VoIP)",
        min_bandwidth=1.0,  # 1.0 Mbps minimum link capacity
        offered_traffic_rate=0.5,  # 500 kbps constant bitrate stream
        max_acceptable_delay=30.0,  # 30 ms strict one-way latency threshold
        description=(
            "Interactive voice communication demanding ultra-low delay and "
            "minimal jitter with modest bandwidth requirements."
        ),
    ),
    "video": TrafficProfile(
        name="video",
        display_name="Video Streaming",
        min_bandwidth=25.0,  # 25.0 Mbps for high-definition video streams
        offered_traffic_rate=20.0,  # 20.0 Mbps offered transmission rate
        max_acceptable_delay=75.0,  # 75 ms latency threshold with buffer support
        description=(
            "High-definition video delivery requiring substantial sustained bandwidth "
            "and moderate delay tolerance aided by client playback buffering."
        ),
    ),
    "bulk_data": TrafficProfile(
        name="bulk_data",
        display_name="Bulk Data Transfer",
        min_bandwidth=100.0,  # 100.0 Mbps preferred minimum link speed
        offered_traffic_rate=150.0,  # 150.0 Mbps high-throughput data transfer
        max_acceptable_delay=250.0,  # 250 ms high latency tolerance
        description=(
            "Large-scale file sync, database replication, and background transfers "
            "tolerant to latency but seeking high throughput capacity."
        ),
    ),
}


def get_traffic_profile(name: str) -> TrafficProfile:
    """
    Retrieve a default traffic profile by its identifier key.

    Raises:
        KeyError: If profile name is not found in DEFAULT_PROFILES.
    """
    key = name.lower().strip()
    if key not in DEFAULT_PROFILES:
        valid_keys = ", ".join(repr(k) for k in DEFAULT_PROFILES)
        raise KeyError(f"Unknown traffic profile '{name}'. Available: {valid_keys}")
    return DEFAULT_PROFILES[key]


def list_traffic_profiles() -> Dict[str, TrafficProfile]:
    """Return a dictionary of all predefined default traffic profiles."""
    return dict(DEFAULT_PROFILES)
