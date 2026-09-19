from engine.aircraft import (
    load_aircraft_from_json,
)
from engine.backtracking import (
    BacktrackingResult,
    basic_backtracking_search,
    mrv_backtracking_search,
    mrv_lcv_backtracking_search,
    smart_backtracking_search,
)
from engine.cargo import load_cargo_from_csv
from engine.csp import AeroLoadCSP
from engine.knowledge_base import (
    load_hazard_rules,
)


def print_result(
    title: str,
    result: BacktrackingResult,
) -> None:
    """
    Print a formatted solver result.
    """

    print()
    print(title)
    print("-" * len(title))

    assignment = result.assignment

    if assignment is None:
        print("No valid solution found.")
        return

    print("Solution found!")
    print()

    for cargo_id, bay_id in assignment.items():
        print(
            f"{cargo_id} -> {bay_id}"
        )

    print()

    print(
        f"Nodes explored : "
        f"{result.nodes_explored}"
    )

    print(
        f"Backtracks     : "
        f"{result.backtracks}"
    )

    report = result.safety_report

    if report is not None:
        print(
            f"Final CG       : "
            f"{report.cg_m:.3f} m"
        )

        print(
            f"Payload        : "
            f"{report.total_payload_kg:.1f} kg"
        )

        print(
            f"L/R imbalance  : "
            f"{report.lateral_imbalance_kg:.1f} kg"
        )

        print(
            f"Safe           : "
            f"{report.safe}"
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


basic_result = basic_backtracking_search(
    csp
)

mrv_result = mrv_backtracking_search(
    csp
)

mrv_lcv_result = mrv_lcv_backtracking_search(
    csp
)

smart_result = smart_backtracking_search(
    csp
)


print()
print("=" * 62)
print("AeroLoad-AI — Solver Comparison")
print("=" * 62)


print_result(
    "Basic Backtracking",
    basic_result,
)

print_result(
    "Backtracking + MRV",
    mrv_result,
)

print_result(
    "Backtracking + MRV + LCV",
    mrv_lcv_result,
)

print_result(
    "AC-3 + MRV + LCV + Backtracking",
    smart_result,
)


print()
print("AC-3 Statistics")
print("-" * 25)

print(
    f"Values pruned   : "
    f"{smart_result.ac3_values_pruned}"
)

print(
    f"Arcs processed  : "
    f"{smart_result.ac3_arcs_processed}"
)


print()
print("=" * 62)
print("Search Comparison")
print("=" * 62)

print(
    f"{'Algorithm':<35}"
    f"{'Nodes':>10}"
    f"{'Backtracks':>15}"
)

print("-" * 62)

print(
    f"{'Basic Backtracking':<35}"
    f"{basic_result.nodes_explored:>10}"
    f"{basic_result.backtracks:>15}"
)

print(
    f"{'Backtracking + MRV':<35}"
    f"{mrv_result.nodes_explored:>10}"
    f"{mrv_result.backtracks:>15}"
)

print(
    f"{'MRV + LCV':<35}"
    f"{mrv_lcv_result.nodes_explored:>10}"
    f"{mrv_lcv_result.backtracks:>15}"
)

print(
    f"{'AC-3 + MRV + LCV':<35}"
    f"{smart_result.nodes_explored:>10}"
    f"{smart_result.backtracks:>15}"
)