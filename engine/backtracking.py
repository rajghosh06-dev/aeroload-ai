from dataclasses import dataclass
from engine.ac3 import ac3
from engine.constraints import (
    SafetyReport,
    validate_loading_plan,
)
from engine.csp import AeroLoadCSP
from engine.heuristics import (
    order_domain_values_lcv,
    select_unassigned_variable_mrv,
)
from engine.models import CargoAssignment


@dataclass
class BacktrackingResult:
    """
    Result returned by an AeroLoad-AI search solver.
    """

    assignment: dict[str, str] | None
    safety_report: SafetyReport | None

    nodes_explored: int
    backtracks: int

    ac3_values_pruned: int = 0
    ac3_arcs_processed: int = 0

    @property
    def solved(self) -> bool:
        return self.assignment is not None


def assignment_to_cargo_assignments(
    csp: AeroLoadCSP,
    assignment: dict[str, str],
) -> list[CargoAssignment]:
    """
    Convert a CSP assignment into CargoAssignment
    objects understood by the aircraft safety engine.
    """

    result: list[CargoAssignment] = []

    for cargo_id, bay_id in assignment.items():
        result.append(
            CargoAssignment(
                cargo=csp.get_cargo(cargo_id),
                bay=csp.get_bay(bay_id),
            )
        )

    return result


def basic_backtracking_search(
    csp: AeroLoadCSP,
) -> BacktrackingResult:
    """
    Solve AeroLoadCSP using basic recursive
    backtracking.

    Variable order:
        Original cargo input order.

    Value order:
        Original bay-domain order.

    No MRV, LCV or AC-3 is used.
    """

    assignment: dict[str, str] = {}

    nodes_explored = 0
    backtracks = 0

    variables = [
        cargo.cargo_id
        for cargo in csp.cargo_items
    ]

    def backtrack() -> tuple[
        dict[str, str] | None,
        SafetyReport | None,
    ]:
        nonlocal nodes_explored
        nonlocal backtracks

        # Complete assignment reached.
        if len(assignment) == len(variables):
            cargo_assignments = (
                assignment_to_cargo_assignments(
                    csp,
                    assignment,
                )
            )

            safety_report = validate_loading_plan(
                csp.aircraft,
                cargo_assignments,
            )

            if safety_report.safe:
                return (
                    assignment.copy(),
                    safety_report,
                )

            backtracks += 1

            return None, None

        # Basic strategy:
        # choose next variable in original order.
        cargo_id = variables[len(assignment)]

        for bay_id in csp.domains[cargo_id]:
            nodes_explored += 1

            if csp.is_consistent(
                cargo_id,
                bay_id,
                assignment,
            ):
                assignment[cargo_id] = bay_id

                solution, report = backtrack()

                if solution is not None:
                    return solution, report

                del assignment[cargo_id]

        backtracks += 1

        return None, None

    solution, report = backtrack()

    return BacktrackingResult(
        assignment=solution,
        safety_report=report,
        nodes_explored=nodes_explored,
        backtracks=backtracks,
    )


def mrv_backtracking_search(
    csp: AeroLoadCSP,
) -> BacktrackingResult:
    """
    Solve AeroLoadCSP using recursive backtracking
    with the Minimum Remaining Values (MRV)
    variable-selection heuristic.
    """

    assignment: dict[str, str] = {}

    nodes_explored = 0
    backtracks = 0

    def backtrack() -> tuple[
        dict[str, str] | None,
        SafetyReport | None,
    ]:
        nonlocal nodes_explored
        nonlocal backtracks

        # Complete assignment reached.
        if len(assignment) == len(csp.cargo_items):
            cargo_assignments = (
                assignment_to_cargo_assignments(
                    csp,
                    assignment,
                )
            )

            safety_report = validate_loading_plan(
                csp.aircraft,
                cargo_assignments,
            )

            if safety_report.safe:
                return (
                    assignment.copy(),
                    safety_report,
                )

            backtracks += 1

            return None, None

        # MRV chooses the currently most
        # constrained unassigned variable.
        cargo_id = select_unassigned_variable_mrv(
            csp,
            assignment,
        )

        for bay_id in csp.domains[cargo_id]:
            nodes_explored += 1

            if csp.is_consistent(
                cargo_id,
                bay_id,
                assignment,
            ):
                assignment[cargo_id] = bay_id

                solution, report = backtrack()

                if solution is not None:
                    return solution, report

                del assignment[cargo_id]

        backtracks += 1

        return None, None

    solution, report = backtrack()

    return BacktrackingResult(
        assignment=solution,
        safety_report=report,
        nodes_explored=nodes_explored,
        backtracks=backtracks,
    )

def mrv_lcv_backtracking_search(
    csp: AeroLoadCSP,
) -> BacktrackingResult:
    """
    Solve AeroLoadCSP using:

    - Backtracking Search
    - MRV for variable selection
    - LCV for value ordering
    """

    assignment: dict[str, str] = {}

    nodes_explored = 0
    backtracks = 0

    def backtrack() -> tuple[
        dict[str, str] | None,
        SafetyReport | None,
    ]:
        nonlocal nodes_explored
        nonlocal backtracks

        if len(assignment) == len(csp.cargo_items):
            cargo_assignments = (
                assignment_to_cargo_assignments(
                    csp,
                    assignment,
                )
            )

            safety_report = validate_loading_plan(
                csp.aircraft,
                cargo_assignments,
            )

            if safety_report.safe:
                return (
                    assignment.copy(),
                    safety_report,
                )

            backtracks += 1
            return None, None

        cargo_id = select_unassigned_variable_mrv(
            csp,
            assignment,
        )

        ordered_bays = order_domain_values_lcv(
            csp,
            cargo_id,
            assignment,
        )

        for bay_id in ordered_bays:
            nodes_explored += 1

            if csp.is_consistent(
                cargo_id,
                bay_id,
                assignment,
            ):
                assignment[cargo_id] = bay_id

                solution, report = backtrack()

                if solution is not None:
                    return solution, report

                del assignment[cargo_id]

        backtracks += 1

        return None, None

    solution, report = backtrack()

    return BacktrackingResult(
        assignment=solution,
        safety_report=report,
        nodes_explored=nodes_explored,
        backtracks=backtracks,
    )

def smart_backtracking_search(
    csp: AeroLoadCSP,
) -> BacktrackingResult:
    """
    Solve AeroLoadCSP using the complete smart pipeline:

    1. AC-3 constraint propagation
    2. MRV variable selection
    3. LCV value ordering
    4. Recursive backtracking
    5. Final aircraft safety validation

    The original CSP domains are not modified.
    """

    # -------------------------------------------------
    # Stage 1: AC-3 constraint propagation
    # -------------------------------------------------

    ac3_result = ac3(csp)

    # If AC-3 causes a domain wipe-out,
    # the CSP has no valid solution.
    if not ac3_result.consistent:
        return BacktrackingResult(
            assignment=None,
            safety_report=None,
            nodes_explored=0,
            backtracks=0,
            ac3_values_pruned=(
                ac3_result.values_pruned
            ),
            ac3_arcs_processed=(
                ac3_result.arcs_processed
            ),
        )

    # -------------------------------------------------
    # Stage 2:
    # Create a working CSP using the AC-3-pruned
    # domains, while preserving the original CSP.
    # -------------------------------------------------

    working_csp = AeroLoadCSP(
        aircraft=csp.aircraft,
        cargo_items=csp.cargo_items,
        knowledge_base=csp.knowledge_base,
    )

    working_csp.domains = {
        cargo_id: values.copy()
        for cargo_id, values
        in ac3_result.domains.items()
    }

    # -------------------------------------------------
    # Stage 3:
    # Run MRV + LCV backtracking on the
    # reduced domains.
    # -------------------------------------------------

    search_result = mrv_lcv_backtracking_search(
        working_csp
    )

    return BacktrackingResult(
        assignment=search_result.assignment,
        safety_report=search_result.safety_report,
        nodes_explored=search_result.nodes_explored,
        backtracks=search_result.backtracks,
        ac3_values_pruned=(
            ac3_result.values_pruned
        ),
        ac3_arcs_processed=(
            ac3_result.arcs_processed
        ),
    )