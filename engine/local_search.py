from dataclasses import dataclass

from engine.backtracking import (
    assignment_to_cargo_assignments,
)
from engine.constraints import (
    SafetyReport,
    validate_loading_plan,
)
from engine.csp import AeroLoadCSP
from engine.optimization import (
    SolutionQuality,
    evaluate_solution_quality,
)


@dataclass
class OptimizationStep:
    """
    Records one accepted local-search improvement.
    """

    iteration: int

    move_type: str
    description: str

    score_before: float
    score_after: float

    cg_before_m: float
    cg_after_m: float

    imbalance_before_kg: float
    imbalance_after_kg: float


@dataclass
class LocalSearchResult:
    """
    Result produced by the AeroLoad-AI
    local-search optimizer.
    """

    initial_assignment: dict[str, str]
    best_assignment: dict[str, str]

    initial_quality: SolutionQuality
    final_quality: SolutionQuality

    safety_report: SafetyReport

    iterations: int
    candidates_evaluated: int
    improvements: int

    steps: list[OptimizationStep]

    @property
    def improved(self) -> bool:
        """
        Return True when the optimizer produced
        a lower solution-quality score.
        """

        return (
            self.final_quality.score
            < self.initial_quality.score
        )


def describe_assignment_change(
    before: dict[str, str],
    after: dict[str, str],
) -> tuple[str, str]:
    """
    Describe the difference between two assignments.

    Returns:
        A tuple containing:
        (move_type, description)
    """

    changed = [
        cargo_id
        for cargo_id in before
        if before[cargo_id] != after[cargo_id]
    ]

    if len(changed) == 1:
        cargo_id = changed[0]

        return (
            "MOVE",
            (
                f"{cargo_id}: "
                f"{before[cargo_id]} -> "
                f"{after[cargo_id]}"
            ),
        )

    if len(changed) == 2:
        first_id = changed[0]
        second_id = changed[1]

        if (
            before[first_id] == after[second_id]
            and before[second_id] == after[first_id]
        ):
            return (
                "SWAP",
                (
                    f"{first_id}: "
                    f"{before[first_id]} -> "
                    f"{after[first_id]}, "
                    f"{second_id}: "
                    f"{before[second_id]} -> "
                    f"{after[second_id]}"
                ),
            )

    return (
        "MULTI",
        ", ".join(
            (
                f"{cargo_id}: "
                f"{before[cargo_id]} -> "
                f"{after[cargo_id]}"
            )
            for cargo_id in changed
        ),
    )


def is_complete_assignment_valid(
    csp: AeroLoadCSP,
    assignment: dict[str, str],
) -> bool:
    """
    Check whether a complete cargo assignment satisfies
    both CSP placement constraints and aircraft-level
    safety constraints.
    """

    # Every cargo item must be assigned.
    if len(assignment) != len(csp.cargo_items):
        return False

    cargo_ids = {
        cargo.cargo_id
        for cargo in csp.cargo_items
    }

    if set(assignment.keys()) != cargo_ids:
        return False

    # No bay may contain more than one cargo item.
    assigned_bays = list(
        assignment.values()
    )

    if len(assigned_bays) != len(
        set(assigned_bays)
    ):
        return False

    # Every selected bay must belong to
    # the cargo's legal domain.
    for cargo_id, bay_id in assignment.items():
        if bay_id not in csp.domains[cargo_id]:
            return False

    # Check all pairwise CSP constraints.
    cargo_id_list = list(
        assignment.keys()
    )

    for i in range(len(cargo_id_list)):
        for j in range(
            i + 1,
            len(cargo_id_list),
        ):
            first_id = cargo_id_list[i]
            second_id = cargo_id_list[j]

            if not csp.are_pairwise_compatible(
                first_id,
                assignment[first_id],
                second_id,
                assignment[second_id],
            ):
                return False

    # Check global aircraft constraints:
    # payload, CG envelope, lateral balance, etc.
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

    return safety_report.safe


def generate_neighbors(
    csp: AeroLoadCSP,
    assignment: dict[str, str],
) -> list[dict[str, str]]:
    """
    Generate neighboring cargo arrangements.

    Two neighborhood operations are used:

    1. Move one cargo item into an empty bay.
    2. Swap the bays occupied by two cargo items.
    """

    neighbors: list[dict[str, str]] = []

    occupied_bays = set(
        assignment.values()
    )

    all_bays = [
        bay.bay_id
        for bay in csp.aircraft.bays
    ]

    empty_bays = [
        bay_id
        for bay_id in all_bays
        if bay_id not in occupied_bays
    ]

    cargo_ids = list(
        assignment.keys()
    )

    # -----------------------------------------
    # MOVE neighbors
    # -----------------------------------------

    for cargo_id in cargo_ids:
        for empty_bay_id in empty_bays:
            candidate = assignment.copy()

            candidate[cargo_id] = (
                empty_bay_id
            )

            if is_complete_assignment_valid(
                csp,
                candidate,
            ):
                neighbors.append(
                    candidate
                )

    # -----------------------------------------
    # SWAP neighbors
    # -----------------------------------------

    for i in range(len(cargo_ids)):
        for j in range(
            i + 1,
            len(cargo_ids),
        ):
            first_id = cargo_ids[i]
            second_id = cargo_ids[j]

            candidate = assignment.copy()

            first_bay = assignment[
                first_id
            ]

            second_bay = assignment[
                second_id
            ]

            candidate[first_id] = second_bay
            candidate[second_id] = first_bay

            if is_complete_assignment_valid(
                csp,
                candidate,
            ):
                neighbors.append(
                    candidate
                )

    return neighbors


def optimize_loading_plan(
    csp: AeroLoadCSP,
    initial_assignment: dict[str, str],
    max_iterations: int = 50,
) -> LocalSearchResult:
    """
    Improve an already-safe cargo loading plan using
    deterministic hill-climbing local search.

    The optimizer explores valid MOVE and SWAP
    neighbors and repeatedly chooses the candidate
    with the lowest quality score.

    Search stops when:
    - no better neighbor exists, or
    - max_iterations is reached.
    """

    if max_iterations < 1:
        raise ValueError(
            "max_iterations must be at least 1."
        )

    if not is_complete_assignment_valid(
        csp,
        initial_assignment,
    ):
        raise ValueError(
            "Initial assignment must be a complete "
            "and safe loading plan."
        )

    current_assignment = (
        initial_assignment.copy()
    )

    initial_objects = (
        assignment_to_cargo_assignments(
            csp,
            current_assignment,
        )
    )

    initial_quality = (
        evaluate_solution_quality(
            csp.aircraft,
            initial_objects,
        )
    )

    current_quality = initial_quality

    iterations = 0
    candidates_evaluated = 0
    improvements = 0

    steps: list[OptimizationStep] = []

    tolerance = 1e-12

    while iterations < max_iterations:
        iterations += 1

        neighbors = generate_neighbors(
            csp,
            current_assignment,
        )

        if not neighbors:
            break

        best_neighbor: dict[str, str] | None = None
        best_quality = current_quality

        for candidate in neighbors:
            candidates_evaluated += 1

            candidate_objects = (
                assignment_to_cargo_assignments(
                    csp,
                    candidate,
                )
            )

            candidate_quality = (
                evaluate_solution_quality(
                    csp.aircraft,
                    candidate_objects,
                )
            )

            if (
                candidate_quality.score
                < best_quality.score - tolerance
            ):
                best_neighbor = candidate
                best_quality = candidate_quality

        # Local optimum reached.
        if best_neighbor is None:
            break

        move_type, description = (
            describe_assignment_change(
                current_assignment,
                best_neighbor,
            )
        )

        step = OptimizationStep(
            iteration=iterations,
            move_type=move_type,
            description=description,

            score_before=(
                current_quality.score
            ),
            score_after=(
                best_quality.score
            ),

            cg_before_m=(
                current_quality.cg_m
            ),
            cg_after_m=(
                best_quality.cg_m
            ),

            imbalance_before_kg=(
                current_quality
                .lateral_imbalance_kg
            ),
            imbalance_after_kg=(
                best_quality
                .lateral_imbalance_kg
            ),
        )

        steps.append(
            step
        )

        current_assignment = (
            best_neighbor.copy()
        )

        current_quality = best_quality

        improvements += 1

    final_objects = (
        assignment_to_cargo_assignments(
            csp,
            current_assignment,
        )
    )

    safety_report = validate_loading_plan(
        csp.aircraft,
        final_objects,
    )

    return LocalSearchResult(
        initial_assignment=(
            initial_assignment.copy()
        ),
        best_assignment=(
            current_assignment.copy()
        ),
        initial_quality=initial_quality,
        final_quality=current_quality,
        safety_report=safety_report,
        iterations=iterations,
        candidates_evaluated=(
            candidates_evaluated
        ),
        improvements=improvements,
        steps=steps,
    )