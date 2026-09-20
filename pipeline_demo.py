from engine.aircraft import (
    load_aircraft_from_json,
)
from engine.cargo import (
    load_cargo_from_csv,
)
from engine.csp import AeroLoadCSP
from engine.knowledge_base import (
    load_hazard_rules,
)
from engine.pipeline import (
    analyze_loading_problem,
)


aircraft = load_aircraft_from_json(
    "data/aircraft.json"
)

cargo_items = load_cargo_from_csv(
    "data/sample_cargo.csv"
)

knowledge = load_hazard_rules(
    "data/hazard_rules.json"
)

csp = AeroLoadCSP(
    aircraft=aircraft,
    cargo_items=cargo_items,
    knowledge_base=knowledge,
)


result = analyze_loading_problem(
    csp
)


print()
print("=" * 65)
print("AeroLoad-AI — Unified Analysis Pipeline")
print("=" * 65)


print()
print("Overall Status")
print("-" * 40)

print(
    f"Solved     : {result.solved}"
)

print(
    f"Optimized  : {result.optimized}"
)

print(
    f"Safe       : {result.safe}"
)

print(
    f"Message    : {result.message}"
)


print()
print("Solver Statistics")
print("-" * 40)

print(
    f"Nodes explored   : "
    f"{result.solver_result.nodes_explored}"
)

print(
    f"Backtracks       : "
    f"{result.solver_result.backtracks}"
)

print(
    f"AC-3 pruned      : "
    f"{result.solver_result.ac3_values_pruned}"
)

print(
    f"AC-3 arcs        : "
    f"{result.solver_result.ac3_arcs_processed}"
)


print()
print("Final Assignment")
print("-" * 40)

if result.final_assignment is None:
    print(
        "No final assignment available."
    )

else:
    for cargo_id, bay_id in (
        result.final_assignment.items()
    ):
        print(
            f"{cargo_id} -> {bay_id}"
        )


optimization = (
    result.optimization_result
)

if optimization is not None:
    print()
    print("Optimization")
    print("-" * 40)

    print(
        f"Initial CG       : "
        f"{optimization.initial_quality.cg_m:.3f} m"
    )

    print(
        f"Final CG         : "
        f"{optimization.final_quality.cg_m:.3f} m"
    )

    print(
        f"Initial score    : "
        f"{optimization.initial_quality.score:.4f}"
    )

    print(
        f"Final score      : "
        f"{optimization.final_quality.score:.4f}"
    )

    print(
        f"Iterations       : "
        f"{optimization.iterations}"
    )

    print(
        f"Candidates       : "
        f"{optimization.candidates_evaluated}"
    )

    print(
        f"Improvements     : "
        f"{optimization.improvements}"
    )


if result.loading_explanation is not None:
    print()
    print("Safety Explanation")
    print("-" * 40)

    for item in (
        result.loading_explanation.items
    ):
        print(
            f"[{item.status}] "
            f"{item.category}: "
            f"{item.message}"
        )


if result.optimization_explanations:
    print()
    print("Optimization Explanation")
    print("-" * 40)

    for item in (
        result.optimization_explanations
    ):
        print(
            f"[{item.status}] "
            f"{item.category}: "
            f"{item.message}"
        )