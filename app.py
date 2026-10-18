"""
Streamlit Web Dashboard for QoS-Aware Intelligent Traffic Routing
and Network Resource Management System.
"""

from __future__ import annotations

import streamlit as st

from src.network.topology import (
    DEFAULT_DESTINATION,
    DEFAULT_SOURCE,
    create_default_topology,
)
from src.simulation.comparison import (
    SimulationComparisonResult,
    compare_routing_for_profile,
)
from src.simulation.scenarios import (
    ScenarioResult,
    load_congestion_scenario,
    load_link_failure_scenario,
    load_normal_scenario,
)
from src.simulation.traffic_profiles import (
    DEFAULT_PROFILES,
    TrafficProfile,
    get_traffic_profile,
    list_traffic_profiles,
)
from src.visualization.plots import (
    create_comparison_metrics_chart,
    create_topology_figure,
)

# Page configuration
st.set_page_config(
    page_title="QoS-Aware Traffic Routing System",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)


def init_session_state() -> None:
    """Initialize stateful attributes in Streamlit session state."""
    if "scenario_name" not in st.session_state:
        st.session_state.scenario_name = "Normal Network"
    if "profile_key" not in st.session_state:
        st.session_state.profile_key = "voip"
    if "source_node" not in st.session_state:
        st.session_state.source_node = DEFAULT_SOURCE
    if "destination_node" not in st.session_state:
        st.session_state.destination_node = DEFAULT_DESTINATION
    if "active_network" not in st.session_state:
        # Load default scenario initially
        scen = load_normal_scenario("voip")
        st.session_state.active_network = scen.network
        st.session_state.scenario_result = scen
        st.session_state.comparison_result = scen.results_after


def load_selected_scenario(scenario_name: str, profile_key: str, src: str, dst: str) -> None:
    """Loads the chosen predefined scenario on a fresh network instance."""
    if scenario_name == "Normal Network":
        res = load_normal_scenario(profile=profile_key, source=src, destination=dst)
    elif scenario_name == "Network Congestion":
        res = load_congestion_scenario(profile=profile_key, source=src, destination=dst)
    elif scenario_name == "Link Failure":
        res = load_link_failure_scenario(profile=profile_key, source=src, destination=dst)
    else:
        res = load_normal_scenario(profile=profile_key, source=src, destination=dst)

    st.session_state.active_network = res.network
    st.session_state.scenario_result = res
    st.session_state.comparison_result = res.results_after


def main() -> None:
    init_session_state()

    # --- Section A: Project Overview ---
    st.title("🌐 QoS-Aware Intelligent Traffic Routing System")
    st.markdown(
        """
        An interactive network simulation demonstrating how **Quality of Service (QoS) routing** 
        dynamically optimizes path selection based on bandwidth, delay, congestion, and packet loss, 
        compared against unweighted **Baseline shortest-path (hop-count)** routing.
        """
    )

    # --- Section B: Simulation Controls (Sidebar) ---
    with st.sidebar:
        st.header("🎛️ Simulation Controls")

        # Scenario Selection
        scenario_options = ["Normal Network", "Network Congestion", "Link Failure"]
        selected_scenario = st.selectbox(
            "Predefined Scenario",
            scenario_options,
            index=scenario_options.index(st.session_state.scenario_name),
            help="Choose a benchmark network scenario to demonstrate routing behavior.",
        )

        # Traffic Profile Selection
        profiles = list_traffic_profiles()
        profile_keys = list(profiles.keys())
        profile_labels = [profiles[k].display_name for k in profile_keys]
        selected_idx = profile_keys.index(st.session_state.profile_key)

        selected_profile_label = st.selectbox(
            "Application Traffic Profile",
            profile_labels,
            index=selected_idx,
            help="Select the application traffic class with its associated bandwidth & delay SLAs.",
        )
        selected_profile_key = profile_keys[profile_labels.index(selected_profile_label)]
        active_profile = profiles[selected_profile_key]

        st.caption(
            f"**SLA Thresholds**: Min Capacity = `{active_profile.min_bandwidth} Mbps` | "
            f"Max Delay = `{active_profile.max_acceptable_delay or 'None'} ms` | "
            f"Offered Rate = `{active_profile.offered_traffic_rate} Mbps`"
        )

        st.divider()

        # Endpoints selection
        all_nodes = list(st.session_state.active_network.nodes)
        src_idx = all_nodes.index(st.session_state.source_node) if st.session_state.source_node in all_nodes else 0
        dst_idx = all_nodes.index(st.session_state.destination_node) if st.session_state.destination_node in all_nodes else len(all_nodes) - 1

        selected_src = st.selectbox("Source (Ingress Node)", all_nodes, index=src_idx)
        selected_dst = st.selectbox("Destination (Egress Node)", all_nodes, index=dst_idx)

        st.divider()

        col_btn1, col_btn2 = st.columns(2)
        run_sim = col_btn1.button("▶️ Run Simulation", use_container_width=True, type="primary")
        reset_sim = col_btn2.button("🔄 Reset Scenario", use_container_width=True)

        if reset_sim:
            load_selected_scenario(selected_scenario, selected_profile_key, selected_src, selected_dst)
            st.session_state.scenario_name = selected_scenario
            st.session_state.profile_key = selected_profile_key
            st.session_state.source_node = selected_src
            st.session_state.destination_node = selected_dst
            st.rerun()

        scenario_changed = selected_scenario != st.session_state.scenario_name
        profile_changed = selected_profile_key != st.session_state.profile_key
        endpoints_changed = (selected_src != st.session_state.source_node or selected_dst != st.session_state.destination_node)

        if run_sim or scenario_changed or profile_changed or endpoints_changed:
            if scenario_changed or profile_changed or (endpoints_changed and selected_scenario != "Normal Network"):
                load_selected_scenario(selected_scenario, selected_profile_key, selected_src, selected_dst)
            else:
                comp = compare_routing_for_profile(
                    st.session_state.active_network,
                    selected_src,
                    selected_dst,
                    active_profile,
                )
                st.session_state.comparison_result = comp
                if hasattr(st.session_state, "scenario_result") and st.session_state.scenario_result:
                    st.session_state.scenario_result.results_after = comp

            st.session_state.scenario_name = selected_scenario
            st.session_state.profile_key = selected_profile_key
            st.session_state.source_node = selected_src
            st.session_state.destination_node = selected_dst
            st.rerun()

    # Current results references
    comp_result: SimulationComparisonResult = st.session_state.comparison_result
    baseline_perf = comp_result.baseline
    qos_perf = comp_result.qos_aware
    active_net: QoSNetwork = st.session_state.active_network

    # Warning for identical nodes
    if selected_src == selected_dst:
        st.info(f"ℹ️ Source and Destination are both **{selected_src}**. Internal loopback path requires 0 hops.")

    # --- Section C: Network Topology Visualization ---
    st.subheader("🗺️ Network Topology & Active Path Traversal")
    fig_topo = create_topology_figure(
        network=active_net,
        baseline_route=baseline_perf.route,
        qos_route=qos_perf.route,
        source=selected_src,
        destination=selected_dst,
    )
    st.plotly_chart(fig_topo, use_container_width=True)

    # Narrative verdict banner
    if comp_result.recommended_algorithm == qos_perf.algorithm:
        st.success(f"💡 **Evaluation Verdict:** {comp_result.summary}")
    elif comp_result.recommended_algorithm == baseline_perf.algorithm:
        st.warning(f"💡 **Evaluation Verdict:** {comp_result.summary}")
    else:
        st.info(f"💡 **Evaluation Verdict:** {comp_result.summary}")

    # --- Section D: Performance Comparison (Side-by-Side) ---
    st.subheader("📊 Performance Comparison: Baseline vs QoS-Aware")
    col_base, col_qos = st.columns(2)

    with col_base:
        st.markdown(f"### 🔵 {baseline_perf.algorithm}")
        st.caption("Pure hop-count optimization (ignores delay & congestion)")
        if baseline_perf.found:
            st.markdown(f"**Route:** `{' -> '.join(baseline_perf.route)}`")
            c1, c2, c3 = st.columns(3)
            c1.metric("Hop Count", f"{baseline_perf.hop_count} hops")
            c2.metric("End-to-End Delay", f"{baseline_perf.end_to_end_delay} ms")
            c3.metric("Bottleneck Capacity", f"{baseline_perf.bottleneck_bandwidth} Mbps")

            c4, c5, c6 = st.columns(3)
            c4.metric("Throughput", f"{baseline_perf.estimated_throughput} Mbps")
            c5.metric("Packet Loss", f"{baseline_perf.packet_loss_percentage}%")
            c6.metric("Avg Congestion", f"{baseline_perf.average_congestion}%")

            sla_status = "✅ Met" if baseline_perf.meets_delay_requirement is not False else f"❌ Violated (> {active_profile.max_acceptable_delay} ms)"
            st.markdown(f"**Delay SLA Status:** {sla_status}")
            st.markdown(f"**Overall Viability:** {'✅ Viable' if baseline_perf.is_viable else '❌ Infeasible / SLA Degraded'}")
        else:
            st.error("No active path could be found by the Baseline algorithm.")

    with col_qos:
        st.markdown(f"### 🟢 {qos_perf.algorithm}")
        st.caption("Cost-minimizing with strict bandwidth feasibility constraint")
        if qos_perf.found:
            st.markdown(f"**Route:** `{' -> '.join(qos_perf.route)}`")
            c1, c2, c3 = st.columns(3)
            c1.metric("Hop Count", f"{qos_perf.hop_count} hops")
            c2.metric("End-to-End Delay", f"{qos_perf.end_to_end_delay} ms")
            c3.metric("Bottleneck Capacity", f"{qos_perf.bottleneck_bandwidth} Mbps")

            c4, c5, c6 = st.columns(3)
            c4.metric("Throughput", f"{qos_perf.estimated_throughput} Mbps")
            c5.metric("Packet Loss", f"{qos_perf.packet_loss_percentage}%")
            c6.metric("Avg Congestion", f"{qos_perf.average_congestion}%")

            sla_status = "✅ Met" if qos_perf.meets_delay_requirement is not False else f"❌ Violated (> {active_profile.max_acceptable_delay} ms)"
            st.markdown(f"**Delay SLA Status:** {sla_status} (QoS Cost: `{qos_perf.route_cost}`)")
            st.markdown(f"**Overall Viability:** {'✅ Viable' if qos_perf.is_viable else '❌ Infeasible / SLA Degraded'}")
        else:
            st.error("No feasible path meets QoS constraints (e.g., minimum bandwidth requirement).")

    # --- Section E: Comparative Charts ---
    st.subheader("📈 Metric Comparison Charts")
    fig_charts = create_comparison_metrics_chart(baseline_perf, qos_perf)
    st.plotly_chart(fig_charts, use_container_width=True)

    # --- Section F: Scenario Comparison (Before vs After) ---
    scen_res: ScenarioResult = st.session_state.scenario_result
    if scen_res.results_before is not None:
        st.subheader("🔬 Scenario Impact: Before vs After Network Modification")
        st.markdown(f"**Experiment:** {scen_res.description}")

        col_bef, col_aft = st.columns(2)
        with col_bef:
            st.markdown("#### ⏳ Baseline Network (Before Changes)")
            b_bef = scen_res.results_before.baseline
            q_bef = scen_res.results_before.qos_aware
            st.write(f"- **Baseline Route**: `{' -> '.join(b_bef.route)}` (Delay: {b_bef.end_to_end_delay} ms, Cost: {b_bef.route_cost})")
            st.write(f"- **QoS-Aware Route**: `{' -> '.join(q_bef.route)}` (Delay: {q_bef.end_to_end_delay} ms, Cost: {q_bef.route_cost})")

        with col_aft:
            st.markdown("#### ⚡ Modified Network (After Changes)")
            b_aft = scen_res.results_after.baseline
            q_aft = scen_res.results_after.qos_aware
            st.write(f"- **Baseline Route**: `{' -> '.join(b_aft.route)}` (Delay: {b_aft.end_to_end_delay} ms, Cost: {b_aft.route_cost})")
            st.write(f"- **QoS-Aware Route**: `{' -> '.join(q_aft.route)}` (Delay: {q_aft.end_to_end_delay} ms, Cost: {q_aft.route_cost})")

        st.info(
            f"**Route Adaptations Observed:** "
            f"QoS Route Changed: **{'YES' if scen_res.route_changed_qos else 'NO'}** | "
            f"Baseline Route Changed: **{'YES' if scen_res.route_changed_baseline else 'NO'}**"
        )

    # --- Section G: Optional Manual Link Controls ---
    with st.expander("⚙️ Manual Link Property Editor & Fault Injection"):
        st.markdown(
            "Fine-tune individual link attributes or simulate targeted link failures on the active network."
        )

        all_edges = [f"{u} <-> {v}" for u, v in sorted(active_net.edges)]
        selected_link_str = st.selectbox("Select Network Link to Modify", all_edges)
        u_sel, v_sel = [x.strip() for x in selected_link_str.split("<->")]

        link_data = active_net.get_link(u_sel, v_sel)

        col_l1, col_l2, col_l3 = st.columns(3)
        new_bw = col_l1.number_input(
            "Bandwidth (Mbps)",
            min_value=1.0,
            max_value=2000.0,
            value=float(link_data["bandwidth"]),
            step=50.0,
            key=f"bw_{u_sel}_{v_sel}",
        )
        new_delay = col_l2.number_input(
            "Delay (ms)",
            min_value=0.0,
            max_value=500.0,
            value=float(link_data["delay"]),
            step=1.0,
            key=f"delay_{u_sel}_{v_sel}",
        )
        new_cong = col_l3.number_input(
            "Congestion (%)",
            min_value=0.0,
            max_value=100.0,
            value=float(link_data["congestion"]),
            step=5.0,
            key=f"cong_{u_sel}_{v_sel}",
        )

        col_l4, col_l5 = st.columns(2)
        new_loss = col_l4.number_input(
            "Packet Loss (%)",
            min_value=0.0,
            max_value=100.0,
            value=float(link_data["packet_loss"]),
            step=0.1,
            key=f"loss_{u_sel}_{v_sel}",
        )
        new_enabled = col_l5.checkbox(
            "Link Operational State (Enabled)",
            value=bool(link_data["enabled"]),
            key=f"en_{u_sel}_{v_sel}",
            help="Uncheck to simulate link cut/failure.",
        )

        col_up1, col_up2 = st.columns(2)
        if col_up1.button("💾 Apply Link Changes", use_container_width=True):
            active_net.update_link(
                u_sel,
                v_sel,
                bandwidth=new_bw,
                delay=new_delay,
                congestion=new_cong,
                packet_loss=new_loss,
                enabled=new_enabled,
            )
            # Re-evaluate
            new_comp = compare_routing_for_profile(
                active_net,
                selected_src,
                selected_dst,
                active_profile,
            )
            st.session_state.comparison_result = new_comp
            if hasattr(st.session_state, "scenario_result") and st.session_state.scenario_result:
                st.session_state.scenario_result.results_after = new_comp
            st.success(f"Link {u_sel} <-> {v_sel} updated successfully!")
            st.rerun()

        if col_up2.button("↩️ Revert to Scenario Defaults", use_container_width=True):
            load_selected_scenario(selected_scenario, selected_profile_key, selected_src, selected_dst)
            st.rerun()


if __name__ == "__main__":
    main()
