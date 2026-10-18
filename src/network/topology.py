"""
Reusable Network Topology module for QoS-Aware Intelligent Traffic Routing.

Constructs, manages, and resets the predefined 7-node network topology with
rich QoS properties on each link (bandwidth, delay, congestion, loss, enabled).
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx

from src.network.link import LinkQoS

# Default endpoints
DEFAULT_SOURCE: str = "Node_1"
DEFAULT_DESTINATION: str = "Node_7"

# Predefined nodes with structural metadata and 2D layout coordinates
DEFAULT_NODES: Dict[str, Dict[str, Any]] = {
    "Node_1": {"label": "Ingress Gateway (Node 1)", "role": "ingress", "pos": (0.0, 0.5)},
    "Node_2": {"label": "Core Router Alpha (Node 2)", "role": "core", "pos": (0.3, 0.9)},
    "Node_3": {"label": "Core Router Beta (Node 3)", "role": "core", "pos": (0.3, 0.1)},
    "Node_4": {"label": "Satellite Gateway (Node 4)", "role": "gateway", "pos": (0.5, 0.5)},
    "Node_5": {"label": "Core Router Gamma (Node 5)", "role": "core", "pos": (0.7, 0.9)},
    "Node_6": {"label": "Core Router Delta (Node 6)", "role": "core", "pos": (0.7, 0.1)},
    "Node_7": {"label": "Egress Gateway (Node 7)", "role": "egress", "pos": (1.0, 0.5)},
}

# Immutable specification of default links: (u, v, bandwidth, delay, congestion, packet_loss, enabled)
DEFAULT_LINKS_SPEC: Tuple[Tuple[str, str, float, float, float, float, bool], ...] = (
    # High-speed Fiber Core (Path 1 corridor)
    ("Node_1", "Node_2", 1000.0, 5.0, 15.0, 0.10, True),
    ("Node_2", "Node_5", 1000.0, 8.0, 18.0, 0.20, True),
    ("Node_5", "Node_7", 1000.0, 5.0, 12.0, 0.10, True),
    # Low-latency Express Route (Path 2 corridor)
    ("Node_1", "Node_3", 500.0, 3.0, 10.0, 0.05, True),
    ("Node_3", "Node_6", 500.0, 4.0, 12.0, 0.05, True),
    ("Node_6", "Node_7", 500.0, 4.0, 10.0, 0.05, True),
    # Direct / Satellite Backup Route (Path 3 corridor)
    ("Node_1", "Node_4", 100.0, 30.0, 40.0, 1.50, True),
    ("Node_4", "Node_7", 100.0, 35.0, 45.0, 2.00, True),
    # Interconnection and redundancy links
    ("Node_2", "Node_3", 600.0, 4.0, 20.0, 0.10, True),
    ("Node_2", "Node_4", 200.0, 12.0, 25.0, 0.30, True),
    ("Node_3", "Node_5", 400.0, 7.0, 15.0, 0.15, True),
    ("Node_4", "Node_6", 250.0, 15.0, 30.0, 0.60, True),
    ("Node_5", "Node_6", 800.0, 6.0, 10.0, 0.10, True),
)


def build_networkx_graph() -> nx.Graph:
    """
    Constructs a raw NetworkX graph populated with fresh default nodes and QoS attributes.
    Every edge possesses bandwidth, delay, congestion, packet_loss, and enabled attributes.
    """
    G = nx.Graph()

    for node_id, attrs in DEFAULT_NODES.items():
        G.add_node(node_id, **copy.deepcopy(attrs))

    for u, v, bw, d, cong, loss, en in DEFAULT_LINKS_SPEC:
        link_qos = LinkQoS(
            bandwidth=bw,
            delay=d,
            congestion=cong,
            packet_loss=loss,
            enabled=en,
        )
        G.add_edge(u, v, **link_qos.to_dict())

    return G


_UNSET: Any = object()


class QoSNetwork:
    """
    Manages the QoS network topology, link attribute mutations, validations,
    and topology resets without corrupting default template values.
    """

    def __init__(self, graph: Optional[nx.Graph] = None) -> None:
        if graph is not None:
            self._graph = graph
        else:
            self._graph = build_networkx_graph()

    @property
    def graph(self) -> nx.Graph:
        """Underlying NetworkX Graph object."""
        return self._graph

    @property
    def nodes(self) -> List[str]:
        """List of all node IDs in the network."""
        return list(self._graph.nodes)

    @property
    def edges(self) -> List[Tuple[str, str]]:
        """List of all edges (u, v) in the network."""
        return list(self._graph.edges)

    def reset_to_default(self) -> None:
        """Reset network graph back to the clean, unmodified default topology."""
        self._graph = build_networkx_graph()

    def has_node(self, node: str) -> bool:
        """Check if node exists in network."""
        return self._graph.has_node(node)

    def has_link(self, u: str, v: str) -> bool:
        """Check if link exists between u and v."""
        return self._graph.has_edge(u, v)

    def _verify_link_exists(self, u: str, v: str) -> None:
        """Raise KeyError if link does not exist."""
        if not self._graph.has_edge(u, v):
            raise KeyError(f"Link between '{u}' and '{v}' does not exist in the network.")

    def get_link(self, u: str, v: str) -> Dict[str, Any]:
        """
        Retrieve QoS dictionary for a link.
        Raises KeyError if link does not exist.
        """
        self._verify_link_exists(u, v)
        return dict(self._graph[u][v])

    def get_link_qos(self, u: str, v: str) -> LinkQoS:
        """
        Retrieve a LinkQoS dataclass representation of the link.
        Raises KeyError if link does not exist.
        """
        self._verify_link_exists(u, v)
        return LinkQoS.from_dict(self._graph[u][v])

    def update_link(
        self,
        u: str,
        v: str,
        *,
        bandwidth: Any = _UNSET,
        delay: Any = _UNSET,
        congestion: Any = _UNSET,
        packet_loss: Any = _UNSET,
        enabled: Any = _UNSET,
    ) -> Dict[str, Any]:
        """
        Update QoS properties on an existing link with comprehensive validation.
        Any omitted property retains its current value. Explicit None or invalid
        types will trigger validation errors.

        Raises:
            KeyError: if link does not exist.
            TypeError: if a property has an invalid type.
            ValueError: if a property value falls outside valid physical ranges.
        """
        self._verify_link_exists(u, v)
        current = dict(self._graph[u][v])

        new_bandwidth = current["bandwidth"] if bandwidth is _UNSET else bandwidth
        new_delay = current["delay"] if delay is _UNSET else delay
        new_congestion = current["congestion"] if congestion is _UNSET else congestion
        new_packet_loss = current["packet_loss"] if packet_loss is _UNSET else packet_loss
        new_enabled = current["enabled"] if enabled is _UNSET else enabled

        # Validate by constructing a LinkQoS instance
        validated_qos = LinkQoS(
            bandwidth=new_bandwidth,
            delay=new_delay,
            congestion=new_congestion,
            packet_loss=new_packet_loss,
            enabled=new_enabled,
        )

        # Apply to NetworkX edge
        self._graph[u][v].update(validated_qos.to_dict())
        return self.get_link(u, v)

    def set_link_state(self, u: str, v: str, enabled: bool) -> None:
        """Enable or disable a link."""
        self.update_link(u, v, enabled=enabled)

    def disable_link(self, u: str, v: str) -> None:
        """Mark a link as disabled (unavailable for routing)."""
        self.set_link_state(u, v, enabled=False)

    def enable_link(self, u: str, v: str) -> None:
        """Mark a link as enabled."""
        self.set_link_state(u, v, enabled=True)

    def is_link_enabled(self, u: str, v: str) -> bool:
        """Check if link is currently enabled."""
        self._verify_link_exists(u, v)
        return bool(self._graph[u][v].get("enabled", True))

    def get_available_bandwidth(self, u: str, v: str) -> float:
        """
        Returns available bandwidth in Mbps, accounting for congestion.
        Returns 0.0 if the link is disabled or fully congested.
        """
        link_qos = self.get_link_qos(u, v)
        return link_qos.available_bandwidth

    def get_active_graph(self) -> nx.Graph:
        """
        Returns an independent NetworkX subgraph containing only currently enabled links.
        Nodes remain intact to preserve topological identity.
        """
        active_g = nx.Graph()
        for node, data in self._graph.nodes(data=True):
            active_g.add_node(node, **copy.deepcopy(data))

        for u, v, data in self._graph.edges(data=True):
            if data.get("enabled", True):
                active_g.add_edge(u, v, **copy.deepcopy(data))

        return active_g

    def find_all_paths(
        self,
        source: str = DEFAULT_SOURCE,
        target: str = DEFAULT_DESTINATION,
        active_only: bool = True,
    ) -> List[List[str]]:
        """
        Find all simple (loop-free) paths between source and target nodes.

        Args:
            source: Starting node ID.
            target: Destination node ID.
            active_only: If True, considers only enabled links.
        """
        if not self.has_node(source):
            raise KeyError(f"Source node '{source}' not in network.")
        if not self.has_node(target):
            raise KeyError(f"Target node '{target}' not in network.")

        g = self.get_active_graph() if active_only else self._graph
        try:
            return list(nx.all_simple_paths(g, source=source, target=target))
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    def get_all_links_qos(self) -> List[Dict[str, Any]]:
        """Return list of all links with their endpoints and QoS parameters."""
        links = []
        for u, v, data in self._graph.edges(data=True):
            entry = {
                "source": u,
                "target": v,
                "bandwidth": data["bandwidth"],
                "delay": data["delay"],
                "congestion": data["congestion"],
                "packet_loss": data["packet_loss"],
                "enabled": data["enabled"],
                "available_bandwidth": self.get_available_bandwidth(u, v),
            }
            links.append(entry)
        return links

    def get_summary(self) -> Dict[str, Any]:
        """Provides high-level topological statistics of the network."""
        total_links = self._graph.number_of_edges()
        active_links = sum(
            1 for _, _, data in self._graph.edges(data=True) if data.get("enabled", True)
        )
        return {
            "node_count": self._graph.number_of_nodes(),
            "total_links": total_links,
            "active_links": active_links,
            "disabled_links": total_links - active_links,
            "nodes": list(self._graph.nodes),
            "default_source": DEFAULT_SOURCE,
            "default_destination": DEFAULT_DESTINATION,
        }


def create_default_topology() -> QoSNetwork:
    """
    Construct and return a brand-new QoSNetwork instance initialized with
    the default 7-node network and default QoS link attributes.
    Modifying this instance will never affect subsequent calls.
    """
    return QoSNetwork()


def reset_topology(network: QoSNetwork) -> QoSNetwork:
    """
    Reset the given QoSNetwork instance back to its pristine default state.
    Returns the reset instance.
    """
    network.reset_to_default()
    return network
