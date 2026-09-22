# ✈️ AeroLoad-AI: Aircraft Cargo Weight-and-Balance & Hazmat Placement Engine

> **Academic Project**: B.Tech 3rd Year, 1st Semester — Artificial Intelligence Project-Based Learning (AI-PBL)  
> **Curriculum Alignment**: Russell & Norvig, *Artificial Intelligence: A Modern Approach* (Units I, II, III)  
> **Test Suite**: 125 Automated Tests Passing (100% Pass Rate)

---

## 📋 Table of Contents
1. [Executive Summary & Problem Statement](#1-executive-summary--problem-statement)
2. [Strict Academic Scope & Syllabus Alignment](#2-strict-academic-scope--syllabus-alignment)
3. [System Architecture & Pipeline Flow](#3-system-architecture--pipeline-flow)
4. [Formal CSP Formulation](#4-formal-csp-formulation)
5. [Search & Constraint Satisfaction Algorithms](#5-search--constraint-satisfaction-algorithms)
6. [Local Search & Solution Quality Optimization](#6-local-search--solution-quality-optimization)
7. [Knowledge Base & Simplified Hazard Separation](#7-knowledge-base--simplified-hazard-separation)
8. [Flight Physics & Balance Calculations](#8-flight-physics--balance-calculations)
9. [Operations Console & Interaction Modes](#9-operations-console--interaction-modes)
10. [Repository Structure](#10-repository-structure)
11. [Installation & Quickstart Guide](#11-installation--quickstart-guide)
12. [Automated Verification & Test Suite](#12-automated-verification--test-suite)
13. [Demonstration Workflows & Scenarios](#13-demonstration-workflows--scenarios)
14. [Faculty Demo Script & Viva Voce Q&A](#14-faculty-demo-script--viva-voce-qa)
15. [Real-World vs. Simulation Simplifications](#15-real-world-vs-simulation-simplifications)
16. [Educational Disclaimer](#16-educational-disclaimer)
17. [Technology Stack](#17-technology-stack)
18. [Future Scope](#18-future-scope)
19. [Authors & Acknowledgments](#19-authors--acknowledgments)

---

## 1. Executive Summary & Problem Statement

Aircraft cargo loading is an assignment and optimization problem governed by discrete physical balance limits and safety considerations:
1. **Longitudinal Center of Gravity (CG)**: Must remain strictly within forward and aft limits ($[\text{CG}_{\min}, \text{CG}_{\max}]$) to maintain safe flight stability.
2. **Lateral Balance**: Weight distributed between port (left) and starboard (right) cargo bays must not exceed the allowable lateral imbalance limit.
3. **Bay Capacity Limits**: Each cargo bay has a structural maximum weight rating that cannot be exceeded.
4. **Hazardous Cargo Separation**: Incompatible hazardous items (e.g., flammable materials and oxidizers, or toxic goods and food items) must not be placed in adjacent cargo bays.

**AeroLoad-AI** solves this challenge using classical Artificial Intelligence techniques. It formulates cargo placement as a **Constraint Satisfaction Problem (CSP)**, removes unsupported bay options using **AC-3 constraint propagation**, finds safe initial assignments using **Backtracking Search with MRV and LCV heuristics**, and refines the balance quality score using **best-improvement Hill-Climbing Local Search**.

---

## 2. Strict Academic Scope & Syllabus Alignment

This project is strictly scoped to the foundational classical AI curriculum:

| Syllabus Unit | Core AI Subject Area | Implementation in AeroLoad-AI |
| :--- | :--- | :--- |
| **Unit I** | **Problem Solving & Heuristic Search** | Multi-attribute objective function balancing longitudinal CG deviation and normalized lateral imbalance; best-improvement hill-climbing local search using `MOVE` and `SWAP` neighborhood operators. |
| **Unit II** | **Constraint Satisfaction Problems (CSPs)** | Formal CSP $\langle X, D, C \rangle$, AC-3 arc consistency preprocessing, recursive backtracking search, Minimum Remaining Values (MRV) variable selection, and Least Constraining Value (LCV) value ordering. |
| **Unit III** | **Knowledge Representation & Reasoning** | Rule-based structured knowledge representation storing simplified hazard incompatibility pairs as symmetric relations; explainability layer generating human-readable validation results. |

### Academic Boundaries & Design Choices
- **Strictly Excluded**: Machine Learning, Deep Neural Networks, Large Language Models (LLMs), Reinforcement Learning (RL), and Computer Vision (CV).
- **Why CSP Instead of A\* Search?**: A\* search is primarily suited to pathfinding and graph traversal where an agent seeks a path to a goal using path costs and distance heuristics. Cargo loading is naturally an **assignment problem** involving variables, domains, and mutual constraints, so CSP techniques with constraint propagation and backtracking are more direct and effective.

---

## 3. System Architecture & Pipeline Flow

The AeroLoad-AI engine operates as a deterministic, multi-stage reasoning pipeline:

```
                  +----------------------------------------------+
                  |                 INPUT DATA                   |
                  |  - Aircraft Limits (data/aircraft.json)      |
                  |  - Cargo Manifest (data/sample_cargo.csv)    |
                  |  - Hazard Rules (data/hazard_rules.json)     |
                  +----------------------------------------------+
                                         |
                                         v
                  +----------------------------------------------+
                  |         STAGE 1: CSP FORMULATION             |
                  |  Variables X: Cargo Items                    |
                  |  Domains D: Aircraft Cargo Bays              |
                  |  Unary Filtering: Bay Weight Limits          |
                  +----------------------------------------------+
                                         |
                                         v
                  +----------------------------------------------+
                  |         STAGE 2: AC-3 ARC PROPAGATION        |
                  |  Pre-prunes unsupported bays from domains    |
                  |  Enforces arc consistency across all pairs   |
                  +----------------------------------------------+
                                         |
                                         v
                  +----------------------------------------------+
                  |    STAGE 3: BACKTRACKING SEARCH (MRV + LCV)  |
                  |  - MRV: Selects most constrained item next   |
                  |  - LCV: Orders bays by maximum flexibility   |
                  |  - Consistency check against partial plan    |
                  +----------------------------------------------+
                                         |
                                         v
                  +----------------------------------------------+
                  |     STAGE 4: SAFETY & BALANCE VALIDATION     |
                  |  - Total Payload <= Max Payload Limit        |
                  |  - Longitudinal CG in [CG_min, CG_max]       |
                  |  - Lateral Imbalance <= Roll Limit           |
                  +----------------------------------------------+
                                         |
                                         v
                  +----------------------------------------------+
                  |    STAGE 5: HILL-CLIMBING LOCAL SEARCH       |
                  |  - Evaluates valid MOVE and SWAP neighbors   |
                  |  - Minimizes CG deviation & lateral penalty  |
                  |  - Greedily selects best-improving candidate |
                  +----------------------------------------------+
                                         |
                                         v
                  +----------------------------------------------+
                  |   STAGE 6: EXPLAINABILITY & TELEMETRY UI     |
                  |  - Natural language pass/fail audit report   |
                  |  - Real-time Plotly CG & balance envelopes   |
                  |  - Interactive 3-mode Operations Console     |
                  +----------------------------------------------+
```

---

## 4. Formal CSP Formulation

AeroLoad-AI formally defines the aircraft cargo loading problem as a triple:

$$\mathcal{P} = \langle X, D, C \rangle$$

### 4.1 Variables ($X$)
Let $n$ be the number of cargo items to be loaded:
$$X = \{ x_1, x_2, \dots, x_n \}$$
Each variable $x_i$ represents a cargo item with weight $W(x_i)$, category $Cat(x_i)$, and hazard class $Haz(x_i)$.

### 4.2 Domains ($D$)
Let $m$ be the number of available aircraft cargo bays:
$$D(x_i) = \{ b_1, b_2, \dots, b_m \}, \quad \forall x_i \in X$$
Each bay $b_j$ is defined by its longitudinal arm $x(b_j)$, lateral side (Left/Right), maximum weight capacity $C_{\text{max}}(b_j)$, and physical adjacency set $Adj(b_j)$.

### 4.3 Constraints ($C$)

#### Unary Constraints
1. **Bay Weight Capacity**: A cargo item cannot exceed the weight rating of its assigned bay:
   $$\forall x_i \in X, \quad W(x_i) \le C_{\text{max}}(\text{bay}(x_i))$$
   *(Enforced during initial domain construction)*

#### Binary Constraints
2. **Exclusivity (All-Different)**: At most one cargo item may occupy any given bay:
   $$\forall x_i, x_j \in X \ (i \neq j): \quad \text{bay}(x_i) \neq \text{bay}(x_j)$$

3. **Hazard Separation**: If two cargo items have incompatible hazard classes, they must not occupy adjacent bays:
   $$\forall x_i, x_j \in X \ (i \neq j): \quad \text{Incompatible}(Haz(x_i), Haz(x_j)) \implies \text{bay}(x_j) \notin Adj(\text{bay}(x_i))$$

#### Global Aircraft Safety Constraints (Evaluated on Complete Plans)
4. **Total Payload Capacity**:
   $$\sum_{i=1}^n W(x_i) \le \text{MaxPayload}_{\text{aircraft}}$$

5. **Longitudinal Center of Gravity Envelope**:
   $$\text{CG}_{\min} \le \text{CG} \le \text{CG}_{\max}$$

6. **Lateral Balance Tolerance**:
   $$\left| \sum_{x_i \in \text{Left}} W(x_i) - \sum_{x_j \in \text{Right}} W(x_j) \right| \le \text{Limit}_{\text{lateral}}$$

---

## 5. Search & Constraint Satisfaction Algorithms

### 5.1 AC-3 (Arc Consistency Algorithm #3)
Before executing backtracking search, AC-3 eliminates values from variable domains that cannot participate in any valid binary constraint relation:
1. Initialize an arc queue $Q = \{ (x_i, x_j) \mid x_i, x_j \in X, i \neq j \}$.
2. While $Q$ is not empty:
   - Pop arc $(x_i, x_j)$.
   - For each bay $b \in D(x_i)$, check if there exists at least one bay $b' \in D(x_j)$ that satisfies all binary constraints (`are_pairwise_compatible`).
   - If no supporting value exists, remove $b$ from $D(x_i)$.
   - If $D(x_i)$ was revised, re-enqueue all incoming arcs $(x_k, x_i)$ for $k \neq j$.
3. If any domain becomes empty, the problem is immediately recognized as unsatisfiable without branching.

### 5.2 MRV (Minimum Remaining Values Heuristic)
During backtracking, variable ordering dictates which unassigned cargo item to place next:
$$\text{Next Variable} = \arg\min_{x_i \in X_{\text{unassigned}}} |D_{\text{legal}}(x_i)|$$
- **Fail-First Principle**: By choosing the cargo item that currently has the fewest legal bay choices, search detects unviable branches as early as possible.

### 5.3 LCV (Least Constraining Value Heuristic)
Once a variable $x_i$ is selected, value ordering determines which candidate bay $b \in D(x_i)$ to attempt first:
$$\text{Best Value} = \arg\min_{b \in D(x_i)} \text{CountEliminatedChoices}(b)$$
- **Fail-Last Principle**: Values that eliminate fewer legal choices for other unassigned cargo items are tried first, maximizing the chance of finding a solution on the first branch.

### 5.4 Recursive Backtracking Search
The search engine recursively assigns cargo items to bays. At each step, it checks consistency against the current partial assignment (`is_consistent`) and reverses decisions (backtracks) when a branch cannot produce a valid solution.

---

## 6. Local Search & Solution Quality Optimization

Once a safe, feasible assignment is found by the CSP solver, AeroLoad-AI executes **best-improvement Hill-Climbing Local Search** to refine the balance quality of the load plan.

### 6.1 Objective Function ($f(s)$)
The optimization evaluates the soft quality of a valid plan using:

$$\text{score} = |\text{CG} - \text{TargetCG}| + 0.25 \times \left( \frac{\text{LateralImbalance}}{\text{LateralImbalanceLimit}} \right)$$

- **Lower score is better.**
- **Longitudinal CG deviation** ($|\text{CG} - \text{TargetCG}|$) is the primary balance objective.
- **Lateral imbalance ratio** contributes a normalized penalty.
- **Tuning Parameter**: The factor **$0.25$ is a project-specific design tuning weight** chosen to balance the relative priority between longitudinal CG alignment and lateral balance. It is **not** an aviation regulatory constant.

### 6.2 Neighborhood Operators
At each iteration, the local search generates and evaluates candidates using two neighborhood operators:
1. **`MOVE(cargo, empty_bay)`**: Moves one cargo item into an unoccupied bay.
2. **`SWAP(cargo_a, cargo_b)`**: Swaps the bays occupied by two cargo items.

### 6.3 Best-Improvement Search & Termination
- Every proposed neighbor state is strictly screened against all hard constraints (`is_complete_assignment_valid`). Infeasible states are discarded.
- The algorithm greedily selects the neighbor with the lowest score that provides a strict improvement ($\text{score} < \text{current\_score} - 10^{-12}$).
- Search terminates when no neighbor yields an improvement (local optimum reached) or when `max_iterations` (default: 50) is reached.

---

## 7. Knowledge Base & Simplified Hazard Separation

AeroLoad-AI incorporates a **simplified educational hazard-separation knowledge base** inspired by general dangerous-goods segregation principles.

### 7.1 Defined Incompatible Pairs
The knowledge base (`data/hazard_rules.json`) explicitly defines 4 incompatible pairs:
1. `["Lithium Battery", "Flammable"]`
2. `["Flammable", "Oxidizer"]`
3. `["Toxic", "Food"]`
4. `["Biohazard", "Food"]`

### 7.2 Representation & Query Efficiency
- Conceptually, incompatibility is represented as a symmetric relation:
  $$\text{Incompatible}(A, B) \iff \text{Incompatible}(B, A)$$
- In the Python source (`engine/knowledge_base.py`), pairs are stored as a hash set of `frozenset[HazardClass]`.
- Pairwise compatibility checks execute in **$O(1)$ constant time**.
- This cleanly separates domain knowledge from the solver algorithms.

---

## 8. Flight Physics & Balance Calculations

All physical calculations are implemented in `engine/cg.py`:

### 8.1 Total Payload
$$\text{Total Payload} = \sum_{i=1}^n \text{Weight}_i$$

### 8.2 Total Longitudinal Moment
$$\text{Total Moment} = \sum_{i=1}^n (\text{Weight}_i \times \text{Arm}_i)$$
*(Where $\text{Arm}_i$ is the longitudinal distance of the assigned bay from the reference datum in meters).*

### 8.3 Longitudinal Center of Gravity (CG)
$$\text{CG} = \frac{\text{Total Moment}}{\text{Total Payload}} = \frac{\sum_{i=1}^n (\text{Weight}_i \times \text{Arm}_i)}{\sum_{i=1}^n \text{Weight}_i}$$

### 8.4 Side Weights & Lateral Imbalance
$$\text{Left Weight} = \sum_{b_i \in \text{Left}} \text{Weight}_i, \quad \text{Right Weight} = \sum_{b_i \in \text{Right}} \text{Weight}_i$$

$$\text{Lateral Imbalance} = |\text{Left Weight} - \text{Right Weight}|$$

---

## 9. Operations Console & Interaction Modes

The user interface provides three distinct operational modes:

```
+------------------------------------------------------------------------------------+
|  AEROLOAD-AI OPERATIONS CONSOLE                                                    |
+------------------------------------------------------------------------------------+
|  [ MODE SELECTOR ]:  (o) Auto Solve     ( ) Manual Planning     ( ) AI-Assisted    |
+------------------------------------------------------------------------------------+
```

### 9.1 Mode 1: Auto Solve
- **Purpose**: Automated end-to-end load planning.
- **Workflow**: One-click execution triggers CSP formulation $\rightarrow$ AC-3 domain reduction $\rightarrow$ MRV/LCV backtracking search $\rightarrow$ safety validation $\rightarrow$ hill-climbing optimization $\rightarrow$ explainability report.

### 9.2 Mode 2: Manual Planning
- **Purpose**: Interactive load planning for students and operators.
- **Workflow**: Select any cargo item from the manifest and manually place it into a target bay. Real-time validation checks bay capacity, hazmat adjacency, and weight envelopes, providing immediate feedback on violations.

### 9.3 Mode 3: AI-Assisted Planning
- **Purpose**: Educational CSP domain inspection.
- **Workflow**: Selecting any cargo item displays its live CSP domain:
  $$D(X_{\text{cargo}}) = \{ \text{candidate bays} \}$$
  The interactive cargo deck highlights:
  - **`✓ LEGAL CHOICE`** (Green/Cyan): Bays that satisfy all unary and binary constraints.
  - **`✕ INCOMPATIBLE`** (Red): Bays blocked with specific violation reasons (e.g., *"Adjacent to P2 (Lithium Battery) in B1"*).
  - **`OCCUPIED`** (Muted): Bays already assigned.

### 9.4 Dynamic Scenario Management
- **Add / Edit / Delete Cargo**: Dynamically modify cargo weights, categories, and hazard classes in memory.
- **CSV Import / Export**: Import custom manifests or export loading plans.
- **Clear All Cargo**: Fast reset with confirmation popover to prevent accidental data loss.
- **Pre-configured Scenario Templates**:
  - *Balanced Express Cargo* (Feasible, demonstrates trim optimization)
  - *Hazardous Incompatible* (Demonstrates dangerous-goods separation)
  - *Overweight Scenario* (Demonstrates constraint violation handling)

---

## 10. Repository Structure

```
aeroLoad-ai/
├── app.py                      # Main Streamlit application entry point
├── pipeline_demo.py            # Terminal CLI demonstration script
├── requirements.txt            # Python dependencies
├── environment.yml             # Conda environment definition
├── README.md                   # Complete system documentation
├── data/                       # Declarative JSON data and CSV manifests
│   ├── aircraft.json           # Educational training aircraft specification (ALT-8)
│   ├── hazard_rules.json       # Simplified hazard incompatibility rules
│   └── sample_cargo.csv        # Baseline cargo manifest
├── engine/                     # Core AI reasoning and physics algorithms
│   ├── ac3.py                  # AC-3 constraint propagation algorithm
│   ├── aircraft.py             # Airframe data models and loaders
│   ├── backtracking.py         # Backtracking search with MRV and LCV
│   ├── cargo.py                # Cargo data models and CSV parsers
│   ├── cg.py                   # Center of gravity & balance physics
│   ├── constraints.py          # Safety report and constraint checkers
│   ├── csp.py                  # Formal CSP problem definition
│   ├── explainability.py       # XAI natural language explanations
│   ├── heuristics.py           # MRV and LCV search heuristics
│   ├── knowledge_base.py       # Rule-based hazard reasoning
│   ├── local_search.py         # Best-improvement hill-climbing optimizer
│   ├── models.py               # Shared dataclasses and enumerations
│   ├── optimization.py         # Solution quality score calculation
│   └── pipeline.py             # Unified end-to-end analysis pipeline
├── ui/                         # Streamlit presentation and components
│   ├── aircraft_view.py        # Visual aircraft cargo deck renderer
│   ├── charts.py               # Plotly CG and lateral balance charts
│   ├── components.py           # Native HTML cards, KPIs, and badges
│   ├── dashboard.py            # Primary operations console dashboard
│   ├── docs.py                 # In-app documentation browser
│   ├── planning.py             # Manual and AI-assisted planning logic
│   ├── state.py                # Streamlit session state management
│   ├── styles.py               # Custom CSS design system
│   ├── templates.py            # Pre-configured scenario templates
│   └── theme.py                # Color palette and theme tokens
└── tests/                      # Automated test suite (125 tests)
    ├── test_ac3.py             # AC-3 algorithm verification
    ├── test_aircraft.py        # Aircraft loader and envelope tests
    ├── test_benchmark.py       # Performance and scalability tests
    ├── test_cargo.py           # Cargo parsing and validation tests
    ├── test_cg.py              # Physics formulas, moments, and balance tests
    ├── test_constraints.py     # Constraint violation tests
    ├── test_csp.py             # CSP initialization and domain tests
    ├── test_end_to_end.py      # End-to-end pipeline integration tests
    ├── test_explainability.py  # XAI explanation generation tests
    ├── test_heuristics.py      # MRV and LCV heuristic tests
    ├── test_knowledge_base.py  # Hazard KB query tests
    ├── test_local_search.py    # Hill-climbing optimizer tests
    ├── test_models.py          # Data model serialization tests
    ├── test_optimization.py    # Optimization score tracking tests
    ├── test_pipeline.py        # Analysis pipeline tests
    ├── test_planning.py        # Manual and AI-assisted planning tests
    ├── test_solver.py          # Backtracking search tests
    └── test_ui_state.py        # Session state and template tests
```

---

## 11. Installation & Quickstart Guide

### Prerequisites
- Python 3.12 (Miniconda / Anaconda recommended)
- Git

### Step 1: Clone Repository
```powershell
git clone https://github.com/rajghosh06-dev/aeroload-ai.git
cd aeroload-ai
```

### Step 2: Create & Activate Conda Environment
```powershell
conda create -n aeroload python=3.12 -y
conda activate aeroload
```

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Run Automated Tests
```powershell
conda run -n aeroload python -m pytest -q
```
*(All 125 tests should pass in under 2 seconds)*

### Step 5: Launch the Streamlit Dashboard
```powershell
conda run -n aeroload streamlit run app.py
```
Open your browser at `http://localhost:8501` (or the URL displayed in the terminal).

---

## 12. Automated Verification & Test Suite

The test suite covers the entire system with **125 automated unit, integration, and regression tests**:

| Test Module | Coverage Area |
| :--- | :--- |
| `test_ac3.py` | AC-3 arc consistency and domain reduction |
| `test_aircraft.py` | Aircraft data models and JSON loading |
| `test_benchmark.py` | Performance, runtime, and node counts |
| `test_cargo.py` | Cargo models and CSV parsing |
| `test_cg.py` | Physics formulas, moments, and lateral balance |
| `test_constraints.py` | Hard safety constraints and report generator |
| `test_csp.py` | CSP variables, domains, and unary filtering |
| `test_end_to_end.py` | Integrated pipeline execution |
| `test_explainability.py`| Natural language XAI report generation |
| `test_heuristics.py` | MRV variable and LCV value ordering |
| `test_knowledge_base.py`| Hazard rule logic and symmetric queries |
| `test_local_search.py` | Hill-climbing, MOVE and SWAP neighbors |
| `test_models.py` | Enums and data structures |
| `test_optimization.py` | Solution quality score calculation |
| `test_pipeline.py` | Full solver pipeline coordination |
| `test_planning.py` | Manual planning, AI-assistance, and domain cards |
| `test_solver.py` | Backtracking search with MRV and LCV |
| `test_ui_state.py` | Session state, manifest rows, and scenario loading |

To run the complete test suite:
```powershell
conda run -n aeroload python -m pytest -v
```

---

## 13. Demonstration Workflows & Scenarios

### Scenario A: Balanced Express Cargo (Auto Solve Mode)
1. In the sidebar, select **Load Scenario Template** $\rightarrow$ **"Balanced Express Cargo"**.
2. Note the KPI strip: 6 items, 2,000 kg total payload, 2 bays free.
3. Click **Run AeroLoad-AI** in **Auto Solve** mode.
4. Observe the results:
   - AC-3 pre-prunes unviable bays.
   - Backtracking search finds a safe solution in $<10$ ms.
   - Hill-climbing local search performs MOVE and SWAP operations to optimize the balance score.
   - Telemetry displays live Plotly figures for the CG envelope and lateral balance.

### Scenario B: Hazardous Materials Segregation (AI-Assisted Mode)
1. Load the **"Hazardous Incompatible"** scenario (contains Lithium Batteries and Flammable Liquids).
2. Switch to **AI-Assisted Planning** mode.
3. Select cargo item `P2` (Lithium Batteries) and place it in bay `B1` (Forward Port).
4. Select cargo item `P3` (Flammable Liquids).
5. Inspect the cargo deck:
   - Bays `B2` and `B3` are flagged in **Red** (`✕ INCOMPATIBLE`) with the reason: *"Adjacent to P2 (Lithium Battery) in B1"*.
   - Bays `B7` and `B8` are highlighted in **Green** (`✓ LEGAL CHOICE`).

### Scenario C: Interactive Manual Planning & Constraint Violations (Manual Mode)
1. Switch to **Manual Planning** mode.
2. Deliberately place heavy cargo items into the forward-most bays (`B1`, `B2`, `B3`).
3. Observe the immediate feedback:
   - System flags the configuration as violating constraints.
   - Violations list shows: *"CG out of limits"*.
   - Live telemetry shows the CG marker outside the permitted envelope.

---

## 14. Faculty Demo Script & Viva Voce Q&A

### Q1: Why did you formulate this as a CSP rather than using A* Search?
> **Answer**: A* is primarily suited to path/state-space search with a path-cost objective. Cargo loading is naturally an assignment problem involving variables, domains, and mutual constraints, so CSP techniques are more direct and allow us to use constraint propagation and backtracking heuristics.

### Q2: Why use Hill Climbing after Backtracking?
> **Answer**: Backtracking finds a feasible solution that satisfies all hard constraints. Hill climbing then improves its soft quality objective (centering the CG and reducing lateral imbalance) using valid MOVE and SWAP neighbors while retaining the hard constraints.

### Q3: How does the AC-3 algorithm reduce the search space before backtracking?
> **Answer**: AC-3 verifies arc consistency between pairs of variables. If assigning a cargo item to a bay leaves no compatible bay for another item, that bay is pruned from its domain before search begins, eliminating dead-end branches early.

### Q4: What is the difference between MRV and LCV heuristics?
> **Answer**:
> - **MRV (Minimum Remaining Values)** is a variable-ordering heuristic following the *fail-first principle*: it picks the unassigned cargo with the fewest remaining legal bays to detect dead ends early.
> - **LCV (Least Constraining Value)** is a value-ordering heuristic following the *fail-last principle*: once a cargo item is chosen, it tries candidate bays that leave the most options open for remaining items.

### Q5: How does the Knowledge Base handle hazmat incompatibility?
> **Answer**: The Knowledge Base stores incompatibility pairs as symmetric relations using frozensets. During constraint checks, the CSP queries the Knowledge Base in $O(1)$ time to ensure incompatible items are not placed in adjacent bays.

### Q6: Why are Machine Learning and Neural Networks not used?
> **Answer**: This problem is naturally discrete and rule-constrained, so a CSP gives us explicit, deterministic, and explainable constraint handling. Machine-learning methods are unnecessary for the current academic objective.

---

## 15. Real-World vs. Simulation Simplifications

To remain appropriate for a B.Tech 3rd-year AI curriculum, the following engineering simplifications were made:
1. **Discrete Bay Model**: Cargo is assigned to discrete bays rather than continuous geometric packing along the floor.
2. **Static CG Calculation**: CG is computed for static cargo placement without modeling in-flight fuel burn shift.
3. **Simplified Airframe**: Uses an educational training aircraft model ("ALT-8") with 8 discrete cargo bays.
4. **Simplified Hazard Rules**: Models 4 primary incompatibility pairs rather than full regulatory dangerous goods manuals.

---

## 16. Educational Disclaimer

> [!NOTE]
> **AeroLoad-AI is an educational simulation project. Aircraft parameters and hazardous-material rules are simplified for academic demonstration and must not be used for real-world flight dispatch or dangerous-goods compliance.**

---

## 17. Technology Stack

- **Core Programming Language**: Python 3.12
- **Web Application Framework**: Streamlit 1.64
- **Interactive Visualizations**: Plotly Graph Objects & Express
- **Data Structures & Numerical Operations**: NumPy, Pandas, Dataclasses
- **Automated Testing**: Pytest 9.1+
- **Styling**: Custom CSS design system with aviation operations visual tokens

---

## 18. Future Scope

1. **Multi-Leg Cargo Planning**: Cargo re-planning across multi-stop routes with en-route loading and offloading.
2. **Dynamic Fuel Burn Modeling**: Modeling fuel weight changes and center of gravity shift during flight.
3. **3D Volumetric Bin Packing**: Integration of 3D container packing algorithms inside individual bays.

---

## 19. Authors & Acknowledgments

- **Student Developer**: Raj Ghosh (B.Tech Computer Science & Engineering)
- **Institution**: College of Engineering & Technology
- **Course**: Artificial Intelligence (AI) — Project Based Learning (PBL), Semester 5 (3rd Year, 1st Semester)
- **Mentorship & Guidance**: Department of Computer Science & Engineering, Faculty AI Mentors
- **References**:
  - Stuart Russell and Peter Norvig, *Artificial Intelligence: A Modern Approach* (4th Edition).