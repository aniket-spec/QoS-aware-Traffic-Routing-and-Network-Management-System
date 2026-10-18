"""
QoS Link model and validation rules.

Each network link maintains QoS properties:
- Bandwidth (in Mbps, > 0)
- Delay (in milliseconds, >= 0)
- Congestion percentage (0.0 to 100.0%)
- Packet loss percentage (0.0 to 100.0%)
- Enabled state (boolean)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class LinkQoS:
    """Represents QoS attributes of a network link."""

    bandwidth: float
    delay: float
    congestion: float
    packet_loss: float
    enabled: bool = True

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Validate all QoS properties and enforce domain constraints."""
        # Bandwidth validation
        if isinstance(self.bandwidth, bool) or not isinstance(self.bandwidth, (int, float)):
            raise TypeError(f"bandwidth must be a numeric value, got {type(self.bandwidth).__name__}")
        if self.bandwidth <= 0:
            raise ValueError(f"bandwidth must be positive (> 0 Mbps), got {self.bandwidth}")

        # Delay validation
        if isinstance(self.delay, bool) or not isinstance(self.delay, (int, float)):
            raise TypeError(f"delay must be a numeric value, got {type(self.delay).__name__}")
        if self.delay < 0:
            raise ValueError(f"delay must be non-negative (>= 0 ms), got {self.delay}")

        # Congestion validation
        if isinstance(self.congestion, bool) or not isinstance(self.congestion, (int, float)):
            raise TypeError(f"congestion must be a numeric value, got {type(self.congestion).__name__}")
        if not (0.0 <= float(self.congestion) <= 100.0):
            raise ValueError(f"congestion must be between 0.0% and 100.0%, got {self.congestion}")

        # Packet-loss validation
        if isinstance(self.packet_loss, bool) or not isinstance(self.packet_loss, (int, float)):
            raise TypeError(f"packet_loss must be a numeric value, got {type(self.packet_loss).__name__}")
        if not (0.0 <= float(self.packet_loss) <= 100.0):
            raise ValueError(f"packet_loss must be between 0.0% and 100.0%, got {self.packet_loss}")

        # Enabled flag validation
        if not isinstance(self.enabled, bool):
            raise TypeError(f"enabled must be a boolean (True/False), got {type(self.enabled).__name__}")

    @property
    def packet_loss_probability(self) -> float:
        """Packet loss expressed as a probability in [0.0, 1.0]."""
        return float(self.packet_loss) / 100.0

    @property
    def available_bandwidth(self) -> float:
        """
        Calculates effective available bandwidth in Mbps.
        Returns 0.0 if the link is disabled or fully congested.
        """
        if not self.enabled:
            return 0.0
        free_ratio = max(0.0, 1.0 - (float(self.congestion) / 100.0))
        return float(self.bandwidth) * free_ratio

    @property
    def effective_delay(self) -> float:
        """Effective delay in ms. Returns infinity if the link is disabled."""
        if not self.enabled:
            return float("inf")
        return float(self.delay)

    def to_dict(self) -> Dict[str, Any]:
        """Convert attributes to a plain dictionary."""
        return {
            "bandwidth": float(self.bandwidth),
            "delay": float(self.delay),
            "congestion": float(self.congestion),
            "packet_loss": float(self.packet_loss),
            "enabled": bool(self.enabled),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LinkQoS:
        """Construct a LinkQoS instance from a dictionary."""
        return cls(
            bandwidth=data["bandwidth"],
            delay=data["delay"],
            congestion=data["congestion"],
            packet_loss=data["packet_loss"],
            enabled=data.get("enabled", True),
        )

    def copy(self) -> LinkQoS:
        """Create an independent copy of this link's QoS state."""
        return LinkQoS(
            bandwidth=float(self.bandwidth),
            delay=float(self.delay),
            congestion=float(self.congestion),
            packet_loss=float(self.packet_loss),
            enabled=bool(self.enabled),
        )
