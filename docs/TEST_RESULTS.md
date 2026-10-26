# Automated Test Results and Verification Report

**Project Title**: QoS-Aware Intelligent Traffic Routing and Network Management System  
**Execution Date**: October 26, 2026  
**Test Framework**: Pytest 9.1.1 (pluggy 1.6.0)  
**Execution Environment**:
- **Operating System**: Microsoft Windows (win32, 64-bit AMD64)
- **Python Version**: 3.11.9 (`C:\Users\ADMIN\AppData\Local\Programs\Python\Python311\python.exe`)
- **Key Dependencies**: `networkx>=3.0`, `streamlit>=1.30.0`, `plotly>=5.0.0`, `pytest>=7.0`
- **Working Directory**: Project Root (`QoS-aware-Traffic-Routing-and-Network-Management-System`)

---

## 1. Test Execution Command and Summary

### Command:
```powershell
pytest -v
```

### Result Summary:
- **Total Tests Collected**: 73
- **Passed**: 73
- **Failed**: 0
- **Skipped**: 0
- **Warnings / Errors**: 0
- **Execution Time**: ~0.58 seconds
- **Overall Exit Code**: 0 (Success)

A raw execution log of this test run is captured in [docs/pytest_run.log](file:///c:/Users/ADMIN/Desktop/QoS-aware-Traffic-Routing-and-Network-Management-System/QoS-aware-Traffic-Routing-and-Network-Management-System/docs/pytest_run.log).

---

## 2. Test Suite Breakdown by Module

| Test Module | Tests | Status | Scope and Functional Coverage |
| :--- | :---: | :---: | :--- |
| **`tests/test_topology.py`** | 24 | **24 Passed** | Node counts, graph coordinates, bidirectional link symmetry, `LinkQoS` validations (bounds checking on bandwidth, delay, congestion, loss), immutability of topology blueprints, link mutation safety, network reset functionality, and disabled link exclusion from active subgraphs. |
| **`tests/test_routing.py`** | 14 | **14 Passed** | Baseline minimum-hop Dijkstra path selection, QoS multi-constraint lowest-cost routing, bandwidth feasibility filtering (pruning paths failing minimum capacity), disabled link exclusion, congestion coefficient ($\alpha$) responsiveness, deterministic tie-breaking, and unreachable destination handling. |
| **`tests/test_metrics.py`** | 17 | **17 Passed** | Mathematical accuracy of end-to-end delay summation, bottleneck link bandwidth computation, capacity-bounded throughput calculation ($\min(\text{offered}, \text{bottleneck})$), independent multi-hop packet loss multiplication, average congestion calculation, traffic profile SLA compliance flags, and serialization to dictionaries. |
| **`tests/test_scenarios.py`** | 7 | **7 Passed** | Deterministic initialization and execution of Normal, Congestion, and Link Failure scenarios; verification that QoS routing dynamically shifts traffic corridors under impairment while baseline routing remains fixed or fails; scenario state isolation across sequential invocations. |
| **`tests/test_ui.py`** | 5 | **5 Passed** | Plotly 2D graph construction, color coding of active routes (Green for QoS, Blue for Baseline), disabled link rendering styles, hover card data generation, and 2x2 comparison metric bar chart rendering. |
| **`tests/test_integration.py`** | 6 | **6 Passed** | Full end-to-end integration workflows simulating realistic user journeys: scenario transitions, live link property edits, custom source/destination endpoint switching, fault recovery, and visualization/metric synchronicity. |

---

## 3. Detailed Test Case Verification Matrix

### 3.1 Network Topology & Link Modeling (`tests/test_topology.py`)
- `TestTopologyCreation::test_node_count_and_endpoints`: PASSED — Validates 7 nodes (`Node_1` to `Node_7`) with correct ingress and egress designations.
- `TestTopologyCreation::test_node_metadata`: PASSED — Validates 2D planar coordinate mappings for all nodes.
- `TestTopologyCreation::test_multiple_alternative_paths_exist`: PASSED — Verifies multiple simple paths connect `Node_1` to `Node_7`.
- `TestTopologyCreation::test_raw_networkx_graph_builder`: PASSED — Ensures underlying NetworkX `Graph` contains 13 undirected edges.
- `TestLinkProperties::test_all_links_have_required_properties`: PASSED — Asserts all links have non-null bandwidth, delay, congestion, and packet loss attributes.
- `TestLinkProperties::test_available_bandwidth_calculation`: PASSED — Asserts residual capacity is computed accurately.
- `TestLinkProperties::test_link_qos_dataclass_properties`: PASSED — Verifies dataclass integrity and attribute access.
- `TestLinkMutationsAndIsolation::test_update_single_and_multiple_properties`: PASSED — Asserts atomic link updates behave correctly.
- `TestLinkMutationsAndIsolation::test_default_scenario_isolation`: PASSED — Asserts mutations do not contaminate default scenario templates.
- `TestLinkMutationsAndIsolation::test_reset_network_restores_default`: PASSED — Confirms `reset_network()` restores original specifications.
- `TestInvalidValuesHandling::test_invalid_bandwidth`: PASSED — Validates `ValueError` upon non-positive bandwidth.
- `TestInvalidValuesHandling::test_invalid_delay`: PASSED — Validates `ValueError` upon negative delay.
- `TestInvalidValuesHandling::test_invalid_congestion`: PASSED — Validates bounds checking ($0.0 \le \text{congestion} \le 100.0$).
- `TestInvalidValuesHandling::test_invalid_packet_loss`: PASSED — Validates bounds checking ($0.0 \le \text{packet\_loss} \le 100.0$).
- `TestInvalidValuesHandling::test_invalid_enabled_type`: PASSED — Validates boolean type enforcement on link operational state.
- `TestInvalidValuesHandling::test_nonexistent_link_and_node`: PASSED — Asserts `KeyError` on queries for invalid endpoints.
- `TestDisabledLinksHandling::test_disable_and_enable_link`: PASSED — Confirms state toggling between active and disabled.
- `TestDisabledLinksHandling::test_active_graph_excludes_disabled_edges`: PASSED — Confirms active graph drops severed links.
- `TestDisabledLinksHandling::test_paths_exclude_disabled_links`: PASSED — Confirms path discovery never traverses disabled links.
- `TestDisabledLinksHandling::test_summary_reflects_disabled_count`: PASSED — Confirms summary metrics track inactive link counts.
- `TestDisabledLinksHandling::test_undirected_link_symmetry`: PASSED — Asserts bidirectional symmetry for $(u, v)$ and $(v, u)$.
- `TestDisabledLinksHandling::test_all_links_qos_retrieval`: PASSED — Confirms dictionary extraction of all link instances.
- `TestDisabledLinksHandling::test_complete_partition_returns_no_paths`: PASSED — Asserts empty path collection when network is partitioned.
- `TestDisabledLinksHandling::test_link_qos_serialization_and_copy`: PASSED — Verifies deepcopy isolation and serialization.

### 3.2 Routing Algorithms (`tests/test_routing.py`)
- `TestBaselineRouting::test_baseline_selects_minimum_hop_route`: PASSED — Baseline selects the 2-hop route (`Node_1-Node_4-Node_7`).
- `TestBaselineRouting::test_baseline_ignores_congestion`: PASSED — Baseline remains on 2-hop route despite high congestion.
- `TestBaselineRouting::test_baseline_ignores_disabled_links`: PASSED — Baseline properly avoids disabled links.
- `TestQoSAwareRouting::test_qos_selects_lowest_total_cost`: PASSED — QoS selects lowest combined delay and congestion cost.
- `TestQoSAwareRouting::test_qos_selects_different_route_from_baseline`: PASSED — Demonstrates QoS selects the 3-hop express path over the 2-hop satellite path.
- `TestQoSAwareRouting::test_bandwidth_requirement_excludes_infeasible_paths`: PASSED — Paths failing minimum capacity are pruned.
- `TestQoSAwareRouting::test_disabled_links_are_never_used`: PASSED — Disabled links strictly avoided during QoS evaluation.
- `TestQoSAwareRouting::test_configured_cost_coefficient_affects_selection`: PASSED — Verifies sensitivity to the $\alpha$ congestion parameter.
- `TestEdgeCasesAndRobustness::test_unreachable_destination`: PASSED — Returns empty route result when path is partitioned.
- `TestEdgeCasesAndRobustness::test_identical_source_and_destination`: PASSED — Handles single-node zero-cost loopback case cleanly.
- `TestEdgeCasesAndRobustness::test_invalid_nodes_handling`: PASSED — Gracefully catches invalid node identifiers.
- `TestEdgeCasesAndRobustness::test_equal_cost_routes_resolved_deterministically`: PASSED — Resolves equal-cost ties deterministically.
- `TestEdgeCasesAndRobustness::test_negative_parameters_raise_value_error`: PASSED — Flags invalid cost coefficients.
- `TestEdgeCasesAndRobustness::test_route_result_to_dict`: PASSED — Verifies dictionary representation of route outcomes.

### 3.3 Performance Metrics & SLA Evaluation (`tests/test_metrics.py`)
- `TestMetricCalculations::test_delay_calculation`: PASSED — Verifies $\sum \text{delay}(e)$.
- `TestMetricCalculations::test_bottleneck_bandwidth`: PASSED — Verifies $\min \text{bandwidth}(e)$.
- `TestMetricCalculations::test_estimated_throughput_offered_below_bottleneck`: PASSED — Verifies $\text{Throughput} = \text{Offered}$ when demand is less than bottleneck capacity.
- `TestMetricCalculations::test_estimated_throughput_bottleneck_below_offered`: PASSED — Verifies $\text{Throughput} = \text{Bottleneck}$ when capacity constrains demand.
- `TestMetricCalculations::test_estimated_throughput_zero_or_negative`: PASSED — Bounded at 0.0 Mbps.
- `TestMetricCalculations::test_zero_packet_loss`: PASSED — Zero loss yields 0.0% end-to-end loss.
- `TestMetricCalculations::test_end_to_end_loss_across_multiple_links`: PASSED — Verifies $(1 - \prod(1 - l_i))$.
- `TestMetricCalculations::test_average_congestion`: PASSED — Arithmetic mean across path hops.
- `TestTrafficProfiles::test_default_profiles_exist_and_configured`: PASSED — Confirms VoIP, Video, and Bulk Data specifications.
- `TestTrafficProfiles::test_custom_profile_validation`: PASSED — Confirms custom profile instantiation.
- `TestTrafficProfiles::test_unknown_profile_raises_key_error`: PASSED — Unknown profiles raise `KeyError`.
- `TestIntegrationAndEvaluation::test_delay_requirement_evaluation`: PASSED — Accurate flag asserting $\text{Delay} \le \text{SLA}$.
- `TestIntegrationAndEvaluation::test_compare_routing_for_profile_voip`: PASSED — Full dual comparison for VoIP.
- `TestIntegrationAndEvaluation::test_compare_routing_for_profile_video`: PASSED — Full dual comparison for Video.
- `TestIntegrationAndEvaluation::test_compare_routing_unreachable_destination`: PASSED — Graceful fallback comparison when target unreachable.
- `TestIntegrationAndEvaluation::test_compare_routing_identical_source_destination`: PASSED — Single node comparison.
- `TestIntegrationAndEvaluation::test_serialization_to_dict`: PASSED — Complete metric dictionary export.

### 3.4 Scenarios & UI Visualizations (`tests/test_scenarios.py`, `tests/test_ui.py`)
- `TestScenarioExecution::test_load_normal_scenario`: PASSED — Pristine network routes correctly.
- `TestScenarioExecution::test_load_congestion_scenario_shifts_qos_route`: PASSED — Injected congestion triggers dynamic route shift.
- `TestScenarioExecution::test_load_link_failure_scenario_reroutes_traffic`: PASSED — Link failure triggers rerouting via cross link.
- `TestScenarioExecution::test_baseline_link_failure_scenario`: PASSED — Asserts baseline isolation.
- `TestScenarioIsolation::test_scenario_isolation`: PASSED — Sequential scenario loadings do not leak link edits.
- `TestScenarioIsolation::test_custom_congestion_and_profiles`: PASSED — Configured congestion weights evaluated.
- `TestScenarioIsolation::test_scenario_result_to_dict`: PASSED — Scenario result export integrity.
- `TestVisualizationHelpers::test_get_route_edge_set`: PASSED — Edge tuple sets correctly extracted.
- `TestVisualizationHelpers::test_create_topology_figure`: PASSED — Plotly figure successfully built.
- `TestVisualizationHelpers::test_create_topology_figure_with_disabled_links`: PASSED — Disabled links rendered with dashed grey style.
- `TestVisualizationHelpers::test_create_comparison_metrics_chart`: PASSED — 2x2 subplot bar charts accurately constructed.
- `TestVisualizationHelpers::test_create_comparison_metrics_chart_no_route`: PASSED — Empty comparison visual handles gracefully.

### 3.5 End-to-End Workflows (`tests/test_integration.py`)
- `test_normal_network_workflow`: PASSED — Verifies complete baseline vs. QoS comparative cycle under Normal conditions.
- `test_congestion_workflow_and_route_shift`: PASSED — Confirms dynamic migration of QoS path from `Node_1-Node_3-Node_6-Node_7` to `Node_1-Node_2-Node_5-Node_7` under congestion.
- `test_link_failure_workflow_and_adaptation`: PASSED — Confirms automatic rerouting around severed link `Node_3-Node_6` via `Node_3-Node_5`.
- `test_manual_link_modification_and_recalculation`: PASSED — Confirms dynamic recalculation following interactive link edits.
- `test_source_destination_switching`: PASSED — Confirms arbitrary source/destination pair path calculations.
- `test_metrics_and_charts_consistency`: PASSED — Confirms metric numbers synchronize identically with chart data structures.

---

## 4. Environment Limitations and Notes

1. **Simulation Scope**: This project is a software-defined graph network simulation implemented with NetworkX. It is not an inline physical router or live SDN OpenFlow/P4 controller and does not inject or transmit raw network frames over physical network cards.
2. **Configured Telemetry**: Network metrics (link delay, congestion, and packet loss) represent deterministic and user-configured inputs for evaluation purposes rather than telemetry polled from physical hardware sensors.
3. **Throughput Approximation**: Throughput values represent theoretical upper bounds derived from offered application traffic rates and bottleneck link bandwidth: $\min(\text{Offered}, \text{Bottleneck})$.
