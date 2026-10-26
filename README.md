# QoS-Aware Intelligent Traffic Routing and Network Management System

A Python-based simulation and network management system demonstrating Quality of Service (QoS) traffic routing, multi-constraint path optimization, and dynamic resource management with an interactive Streamlit web dashboard.

---

## 1. Project Overview and Objectives

Traditional computer network routing protocols (such as unweighted RIP or standard hop-count Dijkstra) route packets along the shortest path based exclusively on the minimum number of hops. While simple, hop-count routing is oblivious to link latency, available capacity, queuing congestion, and packet loss. Under real-world network traffic, this frequently routes latency-sensitive traffic through congested bottlenecks, degrading user experience and violating application Service Level Agreements (SLAs).

The **QoS-Aware Intelligent Traffic Routing and Network Management System** addresses this problem by implementing a multi-criteria decision engine that evaluates network paths across multiple QoS dimensions.

### Core Objectives:
1. **Network Modeling**: Model a network topology with configurable link attributes (bandwidth, delay, congestion, packet loss, and operational state).
2. **Algorithm Comparison**: Directly compare unweighted Baseline Shortest-Hop Routing against QoS-Aware Multi-Metric Routing.
3. **Application-Specific QoS (SLA Compliance)**: Evaluate route feasibility against diverse application traffic profiles (Voice/VoIP, Video Streaming, and Bulk Data).
4. **Fault Tolerance and Dynamic Adaptation**: Demonstrate how QoS routing dynamically routes around link congestion and physical link failures while baseline routing remains blind or suboptimal.
5. **Interactive Visualization**: Provide a web dashboard built with Streamlit and Plotly for real-time scenario simulation, topology inspection, and manual link property editing.

---

## 2. Technologies Used and Rationale

| Technology | Version | Rationale & Role in Project |
| :--- | :--- | :--- |
| **Python** | `>=3.10` | Core programming language offering strong typing, clean dataclass definitions, and rich scientific library support. |
| **NetworkX** | `>=3.0` | High-performance graph manipulation library used for network topology modeling, path discovery (`all_simple_paths`), active subgraph extraction, and shortest-path computation. |
| **Streamlit** | `>=1.30.0` | Reactive web dashboard framework enabling real-time simulation controls, session state management (`st.session_state`), and interactive user controls without frontend boilerplate. |
| **Plotly** | `>=5.0.0` | Interactive graphing library delivering custom 2D network topology maps with color-coded paths, interactive hover cards, and 2x2 comparative bar chart grids. |
| **Pytest** | `>=7.0` | Robust testing framework providing parameterized test execution, strict numerical assertions, and complete coverage across unit and integration suites. |

---

## 3. Project Folder Structure

```
.
├── requirements.txt            # Project dependencies (networkx, pytest, streamlit, plotly)
├── README.md                   # Comprehensive system documentation & user manual
├── app.py                      # Interactive Streamlit web dashboard
├── docs/
│   ├── TECHNICAL_DESIGN.md     # In-depth technical architecture, lifecycle & mathematical models
│   ├── TEST_RESULTS.md         # Automated test verification results and execution logs
│   └── pytest_run.log          # Raw console log output from pytest execution
├── screenshots/                # Real dashboard demonstration captures
│   ├── normal_voip_metrics.png
│   ├── bulk_data_topology.png
│   ├── bulk_data_metrics.png
│   ├── network_congestion_topology.png
│   └── network_congestion_metrics.png
├── src/
│   ├── __init__.py
│   ├── network/                # Network Topology & Link QoS Modeling
│   │   ├── __init__.py         # Re-exports: LinkQoS, QoSNetwork, create_default_topology
│   │   ├── link.py             # LinkQoS dataclass, validation rules, derived metrics
│   │   └── topology.py         # QoSNetwork graph manager, immutable specs, resets
│   ├── routing/                # Routing Algorithms & Decision Engine
│   │   ├── __init__.py         # Re-exports: RouteResult, find_baseline_route, find_qos_route
│   │   ├── models.py           # RouteResult dataclass
│   │   ├── utils.py            # Cost calculation formula and route metric compilation
│   │   ├── baseline.py         # Baseline shortest-path (minimum-hop) routing
│   │   └── qos_aware.py        # QoS-aware lowest-cost routing with bandwidth feasibility
│   ├── simulation/             # Traffic Profiles, QoS Metrics & Scenarios
│   │   ├── __init__.py         # Re-exports: TrafficProfile, metrics, comparison, scenarios
│   │   ├── traffic_profiles.py # Voice (VoIP), Video Streaming, Bulk Data definitions
│   │   ├── metrics.py          # E2E delay, bottleneck capacity, throughput, loss, congestion
│   │   ├── comparison.py       # Dual-routing comparison and SLA compliance evaluation
│   │   └── scenarios.py        # Reproducible scenarios (Normal, Congestion, Link Failure)
│   └── visualization/          # Plotly Visualizations & Interactive Maps
│       ├── __init__.py         # Re-exports: create_topology_figure, create_comparison_metrics_chart
│       └── plots.py            # Fixed 2D topology visualizer & comparative subplot charts
└── tests/
    ├── __init__.py
    ├── test_topology.py        # Network topology & LinkQoS unit tests (24 tests)
    ├── test_routing.py         # Baseline & QoS-aware algorithm tests (14 tests)
    ├── test_metrics.py         # Performance calculations & profiles tests (17 tests)
    ├── test_scenarios.py       # Scenario execution & isolation tests (7 tests)
    ├── test_ui.py              # Visualization helper tests (5 tests)
    └── test_integration.py     # End-to-end integration workflows (6 tests)
```

---

## 4. Installation and Execution Procedure

### Prerequisites
- **Python**: `>=3.10` (Tested and verified on Python `3.11.9`)
- **Package Manager**: `pip`

### Step 1: Clone or Open the Repository
Open a terminal (PowerShell on Windows, or Bash on Linux/macOS) in the project root directory.

### Step 2: Set Up a Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\activate
```

**On Linux / macOS (Bash):**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Required Dependencies
Upgrade `pip` and install the declared packages from `requirements.txt`:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Run the Automated Test Suite
Verify that all unit and integration tests pass before launching the dashboard:
```bash
pytest -v
```
*(All 73 tests should pass. See [`docs/TEST_RESULTS.md`](docs/TEST_RESULTS.md) for full execution logs).*

### Step 5: Launch the Interactive Dashboard
Launch the Streamlit web application using the exact command:
```bash
streamlit run app.py
```

### Step 6: Access the Dashboard in Your Browser
Once started, Streamlit will serve the application locally. Open your web browser and navigate to:
**`http://localhost:8501`**

*(If port 8501 is already in use, Streamlit will automatically increment to `http://localhost:8502` or display the active URL in your terminal).*

---

## 5. Automated Testing and Verification

The project includes an extensive automated test suite consisting of **73 tests** across 6 test modules, verifying complete system correctness, algorithmic determinism, and UI graph generation.

### Run Automated Tests:
```powershell
pytest -v
```

### Verified Test Run Results:
- **Execution Date**: October 26, 2026
- **Test Framework**: `pytest 9.1.1` on Python `3.11.9`
- **Result**: **73 passed, 0 failed** in 0.58s
- **Detailed Verification Report**: See [`docs/TEST_RESULTS.md`](docs/TEST_RESULTS.md) for full module-by-module analysis and execution logs.

### Test Suite Breakdown:
- **`tests/test_topology.py` (24 tests)**: Verifies node count, link property ranges, dataclass validations, undirected graph symmetry, mutation safety, network reset functionality, and disabled link handling.
- **`tests/test_routing.py` (14 tests)**: Validates baseline minimum-hop selection, QoS-aware cost minimization, bandwidth feasibility pruning, deterministic tie-breaking, and partitioned destination handling.
- **`tests/test_metrics.py` (17 tests)**: Confirms arithmetic accuracy of end-to-end delay, bottleneck bandwidth, capacity-bounded throughput, independent packet loss multiplication, and SLA compliance flags.
- **`tests/test_scenarios.py` (7 tests)**: Verifies deterministic execution of Normal, Congestion, and Link Failure scenarios, ensuring full scenario isolation.
- **`tests/test_ui.py` (5 tests)**: Tests Plotly graph construction, edge coloring, disabled link styling, and metric chart rendering.
- **`tests/test_integration.py` (6 tests)**: End-to-end workflow tests verifying scenario transitions, dynamic route shifts, fault rerouting, manual link editing, endpoint switching, and metric consistency.

---

## 6. Default Network Topology

The system models a predefined enterprise network consisting of **7 nodes** and **13 bidirectional links** connecting `Node_1` (Ingress Gateway) to `Node_7` (Egress Gateway):

```
                     [Node_2] ------- (High-Speed Fiber) ------- [Node_5]
                    /   |    \                                   /   |   \
                   /    |     \                                 /    |    \
 (Ingress) [Node_1]     |      \                             /      |     [Node_7] (Egress)
                   \    |       \                           /       |    /
                    \   |        \                         /        |   /
                     [Node_3] ----\-- (Low-Latency Express) --/--- [Node_6]
                       \           \                         /     /
                        \           \                       /     /
                         \           --- [Node_4] ---------      /
                          \               (Satellite)           /
                           -------------------------------------
```

### Node Descriptions
- **`Node_1` (Ingress Gateway)**: Primary traffic entry point ($x=0.0, y=0.5$).
- **`Node_2` (Core Router Alpha)**: High-speed core switch ($x=0.3, y=0.9$).
- **`Node_3` (Core Router Beta)**: Low-latency express router ($x=0.3, y=0.1$).
- **`Node_4` (Satellite Gateway)**: High-delay direct satellite hop ($x=0.5, y=0.5$).
- **`Node_5` (Core Router Gamma)**: High-speed distribution router ($x=0.7, y=0.9$).
- **`Node_6` (Core Router Delta)**: Low-latency egress aggregator ($x=0.7, y=0.1$).
- **`Node_7` (Egress Gateway)**: Primary traffic exit point ($x=1.0, y=0.5$).

### Default Link Specifications

| Link $(u \leftrightarrow v)$ | Corridor / Purpose | Bandwidth | Delay | Congestion | Packet Loss | State |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `Node_1 <-> Node_2` | High-speed Fiber Core | 1000 Mbps | 5.0 ms | 15.0% | 0.10% | Enabled |
| `Node_2 <-> Node_5` | High-speed Fiber Core | 1000 Mbps | 8.0 ms | 18.0% | 0.20% | Enabled |
| `Node_5 <-> Node_7` | High-speed Fiber Core | 1000 Mbps | 5.0 ms | 12.0% | 0.10% | Enabled |
| `Node_1 <-> Node_3` | Low-Latency Express | 500 Mbps | 3.0 ms | 10.0% | 0.05% | Enabled |
| `Node_3 <-> Node_6` | Low-Latency Express | 500 Mbps | 4.0 ms | 12.0% | 0.05% | Enabled |
| `Node_6 <-> Node_7` | Low-Latency Express | 500 Mbps | 4.0 ms | 10.0% | 0.05% | Enabled |
| `Node_1 <-> Node_4` | Satellite Backup | 100 Mbps | 30.0 ms | 40.0% | 1.50% | Enabled |
| `Node_4 <-> Node_7` | Satellite Backup | 100 Mbps | 35.0 ms | 45.0% | 2.00% | Enabled |
| `Node_2 <-> Node_3` | Core Interconnect | 600 Mbps | 4.0 ms | 20.0% | 0.10% | Enabled |
| `Node_2 <-> Node_4` | Cross-Tier Link | 200 Mbps | 12.0 ms | 25.0% | 0.30% | Enabled |
| `Node_3 <-> Node_5` | Cross-Corridor Link | 400 Mbps | 7.0 ms | 15.0% | 0.15% | Enabled |
| `Node_4 <-> Node_6` | Cross-Tier Link | 250 Mbps | 15.0 ms | 30.0% | 0.60% | Enabled |
| `Node_5 <-> Node_6` | Core Interconnect | 800 Mbps | 6.0 ms | 10.0% | 0.10% | Enabled |

---

## 7. Baseline Shortest-Hop Routing

The **Baseline Routing Algorithm** models conventional unweighted shortest-path routing (e.g., standard RIP or unweighted OSPF):
- **Objective**: Finds the path connecting source and destination with the **minimum number of hops** (fewest intermediate links).
- **Behavior**:
  - Operates only over operational links (`enabled == True`).
  - Ignores link bandwidth, delay, congestion, and packet loss when selecting routes.
  - Resolves ties between candidate paths of equal hop count deterministically using lexicographical node ordering.
  - Evaluates informational performance metrics post-selection without allowing them to influence the routing decision.

---

## 8. QoS-Aware Intelligent Routing

The **QoS-Aware Routing Algorithm** optimizes path selection across multiple Quality of Service constraints:

### 1. Bandwidth Feasibility Constraint
A candidate path $P$ is deemed feasible **if and only if** every link along the path satisfies the traffic profile's minimum required bandwidth:
$$\forall e \in P, \quad \text{bandwidth}(e) \ge \text{min\_bandwidth}$$
Paths that fail this threshold on even a single link are eliminated from consideration.

### 2. Routing Cost Function
For all feasible paths, the total QoS cost is computed as the sum of individual link costs:
$$\text{Cost}(P) = \sum_{e \in P} \text{link\_cost}(e)$$

Where link cost balances latency against congestion penalty:
$$\text{link\_cost}(e) = \text{delay}(e) + \alpha \times \left(\frac{\text{congestion}(e)}{100}\right)$$

- $\text{delay}(e)$: Physical propagation delay across the link in milliseconds.
- $\text{congestion}(e)$: Current link utilization percentage ($0.0 \le \text{congestion} \le 100.0$).
- $\alpha$: **Configurable congestion weight coefficient** (default $\alpha = 50.0$).

### 3. Tie-Breaking and Fault Resilience
- If two feasible paths yield the exact same lowest cost, ties are broken by fewest hops, then lexicographically by node sequence.
- Disabled links (`enabled == False`) are strictly excluded during graph traversal.

---

## 9. Traffic Profiles and Performance Metrics

### Traffic Profiles (`src/simulation/traffic_profiles.py`)

| Profile | Target Application | Min Bandwidth | Offered Rate | Max Latency SLA | Description |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Voice (VoIP)** | Real-time interactive voice | 1.0 Mbps | 0.5 Mbps | 30.0 ms | Demands ultra-low delay and minimal jitter with modest bandwidth. |
| **Video Streaming** | HD video delivery | 25.0 Mbps | 20.0 Mbps | 75.0 ms | High sustained bandwidth requirement aided by client playback buffering. |
| **Bulk Data Transfer** | Large file sync & backups | 100.0 Mbps | 150.0 Mbps | 250.0 ms | Latency-tolerant; demands maximum throughput and link capacity. |

*(Note: Thresholds serve as demonstration benchmark parameters).*

### Calculated Metrics (`src/simulation/metrics.py`)

1. **End-to-End Delay**: Total propagation delay along the path:
   $$\text{Delay}_{\text{e2e}} = \sum_{e \in P} \text{delay}(e) \quad (\text{ms})$$
2. **Bottleneck Bandwidth**: Capacity of the most constrained link along the path:
   $$\text{Bottleneck} = \min_{e \in P} \text{bandwidth}(e) \quad (\text{Mbps})$$
3. **Estimated Throughput**: Upper-bound throughput determined by application demand and bottleneck capacity:
   $$\text{Throughput} = \min(\text{Offered Traffic Rate}, \text{Bottleneck Bandwidth}) \quad (\text{Mbps})$$
4. **End-to-End Packet Loss**: Cumulative loss probability modeled as independent link drop events:
   $$\text{Loss}_{\text{e2e}} = \left[1.0 - \prod_{e \in P} \left(1.0 - \frac{\text{packet\_loss}(e)}{100}\right)\right] \times 100\%$$
5. **Average Congestion**: Arithmetic mean of link utilization percentages along the path:
   $$\text{Avg Congestion} = \frac{1}{|P|} \sum_{e \in P} \text{congestion}(e) \quad (\%)$$
6. **SLA Compliance**: Evaluates whether path metrics satisfy $\text{Delay}_{\text{e2e}} \le \text{Max Acceptable Delay}$ and $\text{Bottleneck} \ge \text{Min Bandwidth}$.

---

## 10. Predefined Network Scenarios

The system includes three deterministic scenarios in [`src/simulation/scenarios.py`](file:///c:/Users/ADMIN/Desktop/QoS-aware-Traffic-Routing-and-Network-Management-System/QoS-aware-Traffic-Routing-and-Network-Management-System/src/simulation/scenarios.py):

### Scenario A: Normal Network (`load_normal_scenario`)
- Operates on the default, pristine 7-node network.
- **Baseline Behavior**: Selects the 2-hop Satellite route `Node_1 -> Node_4 -> Node_7` (65.0 ms delay, violating the 30.0 ms VoIP SLA).
- **QoS-Aware Behavior**: Selects the 3-hop Express route `Node_1 -> Node_3 -> Node_6 -> Node_7` (11.0 ms delay, meeting the VoIP SLA).

### Scenario B: Network Congestion (`load_congestion_scenario`)
- Injects severe congestion ($85.0\%$) onto links `(Node_1, Node_3)` and `(Node_3, Node_6)`.
- **Baseline Behavior**: Remains oblivious to congestion and stays on `Node_1 -> Node_4 -> Node_7`.
- **QoS-Aware Behavior**: Detects the cost increase on the Express route (rising to 103.5) and dynamically shifts traffic to the pristine Fiber Core corridor: `Node_1 -> Node_2 -> Node_5 -> Node_7` (cost 40.5).

### Scenario C: Link Failure (`load_link_failure_scenario`)
- Simulates an operational failure by severing link `Node_3 <-> Node_6` (`enabled = False`).
- **Baseline Behavior**: Continues routing along `Node_1 -> Node_4 -> Node_7` (as that path is unaffected).
- **QoS-Aware Behavior**: Automatically excludes the broken link and reroutes traffic via the cross-corridor link `Node_3 -> Node_5`: `Node_1 -> Node_3 -> Node_5 -> Node_7` (cost 33.5).

---

## 11. Dashboard User Guide

The Streamlit dashboard (`app.py`) provides an interactive interface for live experimentation:

```
+----------------------------------------------------------------------------------+
|  🌐 QoS-Aware Intelligent Traffic Routing System                                 |
+---------------------+------------------------------------------------------------+
| 🎛️ Simulation Controls | 🗺️ Network Topology Visualization                         |
|                     | [Plotly 2D Map: Green = QoS Route, Blue = Baseline Route]  |
| - Scenario Select   +------------------------------------------------------------+
| - Traffic Profile   | 📊 Side-by-Side Performance Comparison                     |
| - Source Node       | [KPI Metric Cards: Delay, Throughput, Loss, SLA Viability] |
| - Destination Node  +------------------------------------------------------------+
|                     | 📈 Comparative Metric Charts                               |
| [Run Simulation]    | [2x2 Bar Grid: Delay, Bottleneck, Throughput, Loss]        |
| [Reset Scenario]    +------------------------------------------------------------+
|                     | ⚙️ Manual Link Property Editor & Fault Injection           |
|                     | [Select Link, Adjust BW/Delay/Congestion/Loss, Toggle State]|
+---------------------+------------------------------------------------------------+
```

### Step-by-Step Instructions:
1. **Selecting Scenarios**: In the left sidebar, select **Normal Network**, **Network Congestion**, or **Link Failure**. Click **▶️ Run Simulation** to execute.
2. **Changing Traffic Profile**: Select **Voice (VoIP)**, **Video Streaming**, or **Bulk Data Transfer** to observe how application requirements influence route feasibility and SLA compliance badges.
3. **Changing Endpoints**: Modify the **Source Node** and **Destination Node** dropdowns to route traffic between arbitrary pairs of routers (e.g., `Node_2` to `Node_6`).
4. **Editing Links & Fault Injection**:
   - Expand the **"⚙️ Manual Link Property Editor"** at the bottom of the page.
   - Choose any link (e.g., `Node_1 <-> Node_2`).
   - Adjust bandwidth, delay, congestion, or packet loss sliders, or uncheck **Link Operational State** to disable the link.
   - Click **Apply Link Changes** to instantly observe path recalculation.
5. **Resetting the Network**: Click **🔄 Reset Scenario** in the sidebar to discard mutations and restore the default scenario state.

---

## 12. Dashboard Screenshots

The screenshots below demonstrate genuine executions of the interactive Streamlit dashboard (`http://localhost:8501`) across evaluated scenarios and traffic profiles:

### 1. Normal Network Scenario — Voice (VoIP) Profile
Demonstrates baseline shortest-path routing vs. QoS-aware routing under default conditions:
- **Baseline Shortest Path**: Traverses `Node_1 -> Node_4 -> Node_7` (2 hops) with high end-to-end delay (65.0 ms), violating the 30.0 ms VoIP latency SLA.
- **QoS-Aware Routing**: Selects the low-latency express path `Node_1 -> Node_3 -> Node_6 -> Node_7` (3 hops, 11.0 ms delay, 0.15% packet loss), satisfying all SLA requirements with a composite QoS cost of 27.0.

![Normal Network VoIP Performance Metrics](screenshots/normal_voip_metrics.png)

---

### 2. Normal Network Scenario — Bulk Data Transfer Profile
Demonstrates high-throughput, latency-tolerant routing where QoS routing prioritizes capacity over raw hop count:
- **Active Path Traversal**: Baseline traverses the direct 2-hop satellite corridor `Node_1 -> Node_4 -> Node_7` (shown in blue), while QoS routing selects `Node_1 -> Node_3 -> Node_5 -> Node_7` (shown in green).
- **Comparative Metrics**: Baseline is constrained by a 100.0 Mbps bottleneck and achieves only 100.0 Mbps throughput with 3.47% packet loss. QoS routing achieves the full offered rate of 150.0 Mbps through a 400.0 Mbps bottleneck with 0.30% packet loss and a QoS cost of 33.5.

![Bulk Data Transfer Network Topology Traversal](screenshots/bulk_data_topology.png)

![Bulk Data Transfer Comparative Performance Metrics](screenshots/bulk_data_metrics.png)

---

### 3. Network Congestion Scenario — Dynamic Traffic Shift
Demonstrates dynamic corridor migration when severe congestion (85%) is injected onto express links:
- **Active Path Traversal**: QoS-aware routing detects the elevated delay and congestion on the lower tier and automatically migrates traffic to the upper high-speed fiber backbone `Node_1 -> Node_2 -> Node_5 -> Node_7` (green line). Baseline remains fixed on the satellite link (blue line).
- **Comparative Metrics**: Baseline experiences 65.0 ms delay and 42.5% average congestion, violating SLA. QoS routing achieves 18.0 ms end-to-end delay, 1000.0 Mbps bottleneck bandwidth, and 0.40% packet loss, remaining fully viable.

![Network Congestion Dynamic Topology Traversal](screenshots/network_congestion_topology.png)

![Network Congestion Comparative Performance Metrics](screenshots/network_congestion_metrics.png)

---

## 13. Representative Routing Comparison (Verified Implementation Data)

The following table compares Baseline Shortest-Path vs. QoS-Aware Routing for **Voice (VoIP)** traffic between `Node_1` and `Node_7` under default conditions. All values have been verified against the executing codebase:

| Metric | Baseline Shortest-Path | QoS-Aware Routing | Improvement / Impact |
| :--- | :---: | :---: | :--- |
| **Selected Route** | `Node_1 -> Node_4 -> Node_7` | `Node_1 -> Node_3 -> Node_6 -> Node_7` | Chooses optimal 3-hop express corridor |
| **Hop Count** | **2 hops** | 3 hops | Baseline minimizes hops; QoS trades 1 hop for performance |
| **End-to-End Delay** | **65.0 ms** | **11.0 ms** | **83.1% reduction in latency** (11 ms vs 65 ms) |
| **Bottleneck Bandwidth** | 100.0 Mbps | 500.0 Mbps | 5x greater capacity buffer |
| **Offered Traffic Rate** | 0.5 Mbps | 0.5 Mbps | Demanded VoIP rate |
| **Estimated Throughput** | 0.5 Mbps | 0.5 Mbps | Both satisfy 0.5 Mbps offered demand |
| **Packet Loss Rate** | 3.47% | **0.15%** | **95.7% reduction in packet loss** |
| **Average Congestion** | 42.50% | **10.67%** | Avoids heavily loaded satellite corridor |
| **Routing Cost** | 107.50 | **27.00** | Lowest composite cost $(\text{delay} + 50 \times \text{congestion})$ |
| **VoIP Delay SLA ($\le 30\text{ ms}$)** | ❌ **Violated** (65.0 ms > 30.0 ms) | ✅ **Met** (11.0 ms $\le$ 30.0 ms) | Baseline fails latency SLA |
| **Overall Route Viability** | ❌ **Infeasible** | ✅ **Viable** | QoS route successfully meets all SLA constraints |

### Cost Calculation Details:
- **Baseline Route (`Node_1-Node_4-Node_7`)**:
  - Link `(Node_1, Node_4)`: $30.0 + 50.0 \times (40.0 / 100) = 50.00$
  - Link `(Node_4, Node_7)`: $35.0 + 50.0 \times (45.0 / 100) = 57.50$
  - Total Cost = $50.00 + 57.50 = \mathbf{107.50}$
- **QoS Route (`Node_1-Node_3-Node_6-Node_7`)**:
  - Link `(Node_1, Node_3)`: $3.0 + 50.0 \times (10.0 / 100) = 8.00$
  - Link `(Node_3, Node_6)`: $4.0 + 50.0 \times (12.0 / 100) = 10.00$
  - Link `(Node_6, Node_7)`: $4.0 + 50.0 \times (10.0 / 100) = 9.00$
  - Total Cost = $8.00 + 10.00 + 9.00 = \mathbf{27.00}$

---

## 14. Current Limitations and Future Improvements

### Current Limitations
1. **Graph-Based Simulation**: This system is a graph-based network simulation implemented with NetworkX, not an inline hardware router controller or physical SDN switch. It does not transmit or forward raw physical network packets.
2. **Configured Telemetry vs. Live Probing**: Link delay, congestion percentages, and packet loss are configured simulation parameters and scenario inputs rather than real-time hardware telemetry.
3. **Throughput Upper-Bound Estimation**: Throughput is mathematically estimated from offered traffic rate and bottleneck link capacity ($\min(\text{Offered Traffic Rate}, \text{Bottleneck Bandwidth})$), rather than measured from physical TCP window transfers or socket throughput.
4. **Packet Loss Independence**: Multi-hop packet loss is modeled using statistically independent Bernoulli trials without modeling correlated queue overflow bursts.
5. **Instantaneous Convergence**: Routing recalculations occur deterministically in simulation memory without distributed protocol convergence overheads, link-state advertisement propagation delays, or transient loops.
6. **Path Enumeration Scalability**: Candidate route discovery uses simple path exploration suitable for edge-to-core campus networks (7–20 nodes). High-tier carrier networks require polynomial heuristics or constrained Dijkstra variants.

### Future Improvements
- **Dynamic Packet-Level Queuing**: Integrate discrete-event simulation (e.g., SimPy) to model FIFO/Priority packet queues and jitter buffers.
- **Adaptive Reinforcement Learning**: Implement Q-learning or Multi-Agent Reinforcement Learning (MARL) to dynamically tune the congestion coefficient $\alpha$ based on real-time traffic demand.
- **Multi-Path Routing (ECMP / MPTCP)**: Extend the routing engine to split high-bandwidth flows across multiple parallel corridors simultaneously.
- **Telemetry Ingestion**: Add REST or gRPC endpoints to ingest live telemetry from physical SDN controllers (e.g., OpenFlow or P4).
- **Formal Technical Design**: Refer to [`docs/TECHNICAL_DESIGN.md`](docs/TECHNICAL_DESIGN.md) for full architecture specifications.
