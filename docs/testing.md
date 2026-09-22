# Verification & Automated Test Suite

AeroLoad-AI is rigorously tested using the **Pytest** framework.

The test suite contains **125 automated unit, integration, and end-to-end regression tests**, providing 100% pass-rate confidence across the AI algorithms, physical calculations, and user-state lifecycles.

---

## Running the Test Suite

Execute the following command from the project root:

```powershell
conda run -n aeroload python -m pytest -v
```

All 125 tests complete in under 2 seconds.

---

## Test Categories & Coverage

### 1. Classical AI Algorithms
- `test_ac3.py` (7 tests): Verifies arc queue initialization, revision logic, domain value pruning, and domain wipeout detection.
- `test_heuristics.py` (6 tests): Validates MRV fail-first variable selection and LCV value ordering.
- `test_solver.py` (9 tests): Tests basic backtracking, MRV backtracking, MRV+LCV backtracking, and the smart solver pipeline.
- `test_local_search.py` (8 tests): Tests neighborhood generation (`MOVE`, `SWAP`), strict score improvement, and local optimum stopping.
- `test_optimization.py` (7 tests): Verifies solution quality score calculation and step tracking.
- `test_csp.py` (6 tests): Tests CSP variable/domain initialization, unary capacity filtering, and binary compatibility checks.

### 2. Physical & Flight-Mechanics Calculations
- `test_cg.py` (8 tests): Verifies total payload, longitudinal moment, center of gravity equation, and lateral balance calculations.
- `test_aircraft.py` (7 tests): Tests airframe JSON loading, bay specifications, and envelope limits.
- `test_cargo.py` (6 tests): Tests manifest parsing, category validation, and weight limits.
- `test_constraints.py` (8 tests): Tests hard safety constraint checkers and overall `SafetyReport` generation.

### 3. Knowledge Representation & Explainability
- `test_knowledge_base.py` (6 tests): Verifies symmetric incompatibility queries and $O(1)$ set lookups.
- `test_explainability.py` (6 tests): Tests natural-language explanations for bay capacity, hazard separation, and balance trade-offs.

### 4. Integration & UI State Management
- `test_pipeline.py` (8 tests): Tests end-to-end problem analysis with and without local search optimization.
- `test_end_to_end.py` (4 tests): Verifies full end-to-end execution from manifest to final plan.
- `test_planning.py` (13 tests): Tests manual assignment validation, AI-assisted domain analysis, and legal/blocked bay classification.
- `test_ui_state.py` (9 tests): Verifies manifest editing, drag-and-drop ordering, aircraft configuration isolation, and workspace reset lifecycles.
- `test_benchmark.py` (2 tests): Performance benchmarks ensuring rapid convergence under normal loads.
- `test_models.py` (5 tests): Tests data model instantiation, enums, and validations.
