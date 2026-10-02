# Verification & Testing Methodology

AeroLoad-AI has been locally validated using a 127-test Pytest regression suite. The development test source files are maintained locally by the project developer and are intentionally excluded from the public deployment repository.

The test suite provides 100% pass-rate confidence across the classical AI reasoning engines, flight-mechanics calculations, safety constraint validation, and user interface state lifecycles.

---

## Local Developer Verification Command

For local developer environments where the automated verification suite is present, execute the following command from the project root:

```powershell
conda run -n aeroload python -m pytest -q
```

All 127 automated tests complete in under 1 second.

---

## Verification Scope & Coverage

### 1. Classical AI Algorithms & Constraint Satisfaction
- **Arc Consistency (AC-3)**: Verifies arc queue initialization, revision logic, domain value pruning, and domain wipeout detection.
- **Search Heuristics (MRV & LCV)**: Validates Minimum Remaining Values (MRV) fail-first variable selection and Least Constraining Value (LCV) value ordering.
- **Backtracking Search**: Tests basic backtracking, MRV backtracking, MRV+LCV backtracking, and the integrated solver pipeline.
- **Local Search Optimization**: Tests neighborhood generation (`MOVE`, `SWAP`), strict score improvement, and local optimum termination.
- **Optimization Scoring**: Verifies solution quality score calculation, target CG balance penalty, and step tracking.
- **CSP Problem Definition**: Tests CSP variable/domain initialization, unary capacity filtering, and binary compatibility checks.

### 2. Physical & Flight-Mechanics Calculations
- **Center of Gravity & Balance**: Verifies total payload, longitudinal moment, center of gravity equation, and lateral port/starboard balance calculations.
- **Aircraft Model & Envelopes**: Tests airframe JSON loading, bay specifications, and structural weight envelopes.
- **Cargo Manifest Validation**: Tests manifest parsing, category validation, and weight limits.
- **Safety Constraints & Reports**: Tests hard safety constraint checkers and overall `SafetyReport` generation.

### 3. Knowledge Representation & Explainability
- **Knowledge Base Reasoning**: Verifies symmetric incompatibility queries and O(1) set lookups for hazardous cargo separation.
- **Explainability (XAI)**: Tests natural-language explanations for bay capacity, hazard separation, and balance trade-offs.

### 4. Integration, Planning & UI State Management
- **Unified Pipeline**: Tests end-to-end problem analysis with and without local search optimization.
- **End-to-End Execution**: Verifies full pipeline execution from raw manifest to final verified loading plan.
- **Interactive Planning Modes**: Tests manual assignment validation, AI-assisted domain analysis, and legal/blocked bay classification.
- **UI State Lifecycles**: Verifies manifest editing, drag-and-drop ordering, aircraft configuration isolation, and workspace reset lifecycles.
- **Performance Benchmarks**: Benchmarks ensuring rapid convergence under normal cargo loads (<10 ms).
- **Data Models**: Tests data model instantiation, enumerations, and serialization.
