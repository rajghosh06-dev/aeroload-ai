from engine.ac3 import ac3
from engine.aircraft import load_aircraft_from_json
from engine.backtracking import (
    BacktrackingResult,
    basic_backtracking_search,
    mrv_backtracking_search,
    mrv_lcv_backtracking_search,
    smart_backtracking_search,
)
from engine.cargo import load_cargo_from_csv
from engine.csp import AeroLoadCSP
from engine.knowledge_base import load_hazard_rules


def create_benchmark_csp() -> AeroLoadCSP:
    """
    Create a deliberately constrained CSP used
    to demonstrate constraint propagation.

    The normal aircraft/cargo data is preserved.
    Only the CSP domains are restricted.
    """

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

    csp.domains = {
        "P1": ["B1"],
        "P2": ["B1", "B2"],
        "P3": ["B2", "B3"],
        "P4": ["B3", "B4"],
        "P5": ["B4", "B8"],
        "P6": ["B7", "B8"],
    }

    return csp


def print_solver_row(
    name: str,
    result: BacktrackingResult,
) -> None:
    print(
        f"{name:<30}"
        f"{result.nodes_explored:>10}"
        f"{result.backtracks:>15}"
    )


csp = create_benchmark_csp()


print()
print("=" * 65)
print("AeroLoad-AI — Constrained CSP Benchmark")
print("=" * 65)


print()
print("Initial Domains")
print("-" * 40)

for cargo_id, domain in csp.domains.items():
    print(
        f"{cargo_id}: {domain}"
    )


ac3_result = ac3(
    csp
)


print()
print("Domains After AC-3")
print("-" * 40)

for cargo_id, domain in ac3_result.domains.items():
    print(
        f"{cargo_id}: {domain}"
    )


initial_values = sum(
    len(domain)
    for domain in csp.domains.values()
)

final_values = sum(
    len(domain)
    for domain in ac3_result.domains.values()
)


print()
print("AC-3 Propagation Statistics")
print("-" * 40)

print(
    f"Initial values : "
    f"{initial_values}"
)

print(
    f"Final values   : "
    f"{final_values}"
)

print(
    f"Values pruned  : "
    f"{ac3_result.values_pruned}"
)

print(
    f"Arcs processed : "
    f"{ac3_result.arcs_processed}"
)

print(
    f"Consistent     : "
    f"{ac3_result.consistent}"
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
print("=" * 65)
print("Solver Benchmark")
print("=" * 65)

print(
    f"{'Algorithm':<30}"
    f"{'Nodes':>10}"
    f"{'Backtracks':>15}"
)

print("-" * 65)

print_solver_row(
    "Basic Backtracking",
    basic_result,
)

print_solver_row(
    "Backtracking + MRV",
    mrv_result,
)

print_solver_row(
    "MRV + LCV",
    mrv_lcv_result,
)

print_solver_row(
    "AC-3 + MRV + LCV",
    smart_result,
)


print()
print("Smart Solver Result")
print("-" * 40)

assignment = smart_result.assignment

if assignment is None:
    print("No solution found.")

else:
    for cargo_id, bay_id in assignment.items():
        print(
            f"{cargo_id} -> {bay_id}"
        )

    report = smart_result.safety_report

    if report is not None:
        print()

        print(
            f"Final CG      : "
            f"{report.cg_m:.3f} m"
        )

        print(
            f"Imbalance     : "
            f"{report.lateral_imbalance_kg:.1f} kg"
        )

        print(
            f"Safe          : "
            f"{report.safe}"
        )