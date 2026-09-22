# System Architecture & Module Map

AeroLoad-AI is structured into modular layers that separate the web presentation, state management, CSP reasoning engine, and physical data models.

---

## 1. Information Flow

```
                      [ User Input / CSV / Templates ]
                                     │
                                     ▼
                        [ ui/state.py & ui/dashboard.py ]
                           (State & Scenario Adapters)
                                     │
                                     ▼
                           [ engine/csp.py ]
                       (Formal CSP Formulation: X, D, C)
                                     │
                                     ▼
                           [ engine/ac3.py ]
                     (Arc Consistency Domain Pruning)
                                     │
                                     ▼
                      [ engine/backtracking.py ]
                     (MRV & LCV Backtracking Search)
                                     │
                                     ▼
                     [ engine/constraints.py & cg.py ]
                        (Safety & Physics Validation)
                                     │
                                     ▼
                      [ engine/local_search.py ]
                    (Hill-Climbing Trim Optimization)
                                     │
                                     ▼
                     [ engine/explainability.py ]
                   (Natural Language XAI Justifications)
                                     │
                                     ▼
                        [ ui/aircraft_view.py & charts.py ]
                        (Visual Deck & Plotly Telemetry)
```

---

## 2. Directory & Module Guide

### `engine/` — Classical AI & Physics Core (Pure Python)
- `models.py`: Dataclasses and enums (`CargoItem`, `CargoBay`, `HazardClass`, `CargoCategory`, `BaySide`).
- `aircraft.py`: Airframe data models and JSON loader.
- `cargo.py`: Cargo manifest models and CSV parsers.
- `knowledge_base.py`: Declarative hazard rule loader and $O(1)$ symmetric query engine.
- `cg.py`: Center of gravity, longitudinal moment, and lateral balance calculations.
- `constraints.py`: Safety constraints and `SafetyReport` generator.
- `csp.py`: Formal `AeroLoadCSP` definition with unary capacity filtering and binary compatibility checkers.
- `ac3.py`: AC-3 constraint propagation algorithm.
- `heuristics.py`: MRV variable selection and LCV value ordering.
- `backtracking.py`: Recursive search with consistency checking.
- `optimization.py`: Solution quality evaluation score ($|\text{CG} - \text{TargetCG}| + 0.25 \times \text{imbalance\_ratio}$).
- `local_search.py`: Best-improvement hill climbing with `MOVE` and `SWAP` operators.
- `explainability.py`: Natural language PASS/FAIL explanation generator.
- `pipeline.py`: Unified end-to-end analysis coordinator.

### `ui/` — Presentation & Interaction Layer (Streamlit)
- `dashboard.py`: Primary operations console, workflow orchestration, and mode views.
- `planning.py`: Manual planning validation and AI-assisted CSP domain analysis helpers.
- `aircraft_view.py`: Visual aircraft cargo deck renderer.
- `charts.py`: Plotly CG envelope and lateral roll balance figures.
- `components.py`: Reusable presentation cards, status pills, and KPI metrics.
- `state.py`: Session state adapters, CSV import/export, and row validation.
- `templates.py`: Curated scenario templates.
- `docs.py`: In-app modular documentation browser.
- `styles.py`: Custom CSS design system.
- `theme.py`: Theme tokens and color palette.
