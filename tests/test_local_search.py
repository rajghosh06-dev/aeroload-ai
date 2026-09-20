import pytest

from engine.aircraft import (
    load_aircraft_from_json,
)
from engine.backtracking import (
    smart_backtracking_search,
)
from engine.cargo import (
    load_cargo_from_csv,
)
from engine.csp import AeroLoadCSP
from engine.knowledge_base import (
    load_hazard_rules,
)
from engine.local_search import (
    generate_neighbors,
    is_complete_assignment_valid,
    optimize_loading_plan,
)


def make_csp() -> AeroLoadCSP:
    aircraft = load_aircraft_from_json(
        "data/aircraft.json"
    )

    cargo_items = load_cargo_from_csv(
        "data/sample_cargo.csv"
    )

    knowledge = load_hazard_rules(
        "data/hazard_rules.json"
    )

    return AeroLoadCSP(
        aircraft=aircraft,
        cargo_items=cargo_items,
        knowledge_base=knowledge,
    )


def get_initial_solution(
    csp: AeroLoadCSP,
) -> dict[str, str]:
    result = smart_backtracking_search(
        csp
    )

    assert result.assignment is not None

    return result.assignment


def test_smart_solution_is_valid_for_optimizer():
    csp = make_csp()

    assignment = get_initial_solution(
        csp
    )

    assert is_complete_assignment_valid(
        csp,
        assignment,
    )


def test_local_search_generates_valid_neighbors():
    csp = make_csp()

    assignment = get_initial_solution(
        csp
    )

    neighbors = generate_neighbors(
        csp,
        assignment,
    )

    assert len(neighbors) > 0

    for neighbor in neighbors:
        assert is_complete_assignment_valid(
            csp,
            neighbor,
        )


def test_local_search_preserves_safety():
    csp = make_csp()

    assignment = get_initial_solution(
        csp
    )

    result = optimize_loading_plan(
        csp,
        assignment,
    )

    assert result.safety_report.safe is True


def test_local_search_does_not_worsen_score():
    csp = make_csp()

    assignment = get_initial_solution(
        csp
    )

    result = optimize_loading_plan(
        csp,
        assignment,
    )

    assert (
        result.final_quality.score
        <= result.initial_quality.score
    )


def test_local_search_improves_cg_deviation():
    csp = make_csp()

    assignment = get_initial_solution(
        csp
    )

    result = optimize_loading_plan(
        csp,
        assignment,
    )

    assert (
        result.final_quality.cg_deviation_m
        < result.initial_quality.cg_deviation_m
    )


def test_local_search_does_not_modify_input():
    csp = make_csp()

    assignment = get_initial_solution(
        csp
    )

    original = assignment.copy()

    optimize_loading_plan(
        csp,
        assignment,
    )

    assert assignment == original


def test_local_search_records_statistics():
    csp = make_csp()

    assignment = get_initial_solution(
        csp
    )

    result = optimize_loading_plan(
        csp,
        assignment,
    )

    assert result.iterations > 0
    assert result.candidates_evaluated > 0
    assert result.improvements >= 1


def test_invalid_initial_assignment_is_rejected():
    csp = make_csp()

    invalid_assignment = {
        "P1": "B1",
        "P2": "B1",
        "P3": "B3",
        "P4": "B4",
        "P5": "B7",
        "P6": "B8",
    }

    with pytest.raises(
        ValueError,
        match="complete and safe",
    ):
        optimize_loading_plan(
            csp,
            invalid_assignment,
        )

def test_local_search_records_optimization_steps():
    csp = make_csp()

    assignment = get_initial_solution(
        csp
    )

    result = optimize_loading_plan(
        csp,
        assignment,
    )

    assert len(result.steps) == result.improvements


def test_each_optimization_step_improves_score():
    csp = make_csp()

    assignment = get_initial_solution(
        csp
    )

    result = optimize_loading_plan(
        csp,
        assignment,
    )

    for step in result.steps:
        assert (
            step.score_after
            < step.score_before
        )


def test_optimization_step_has_description():
    csp = make_csp()

    assignment = get_initial_solution(
        csp
    )

    result = optimize_loading_plan(
        csp,
        assignment,
    )

    assert len(result.steps) > 0

    for step in result.steps:
        assert step.move_type in {
            "MOVE",
            "SWAP",
            "MULTI",
        }

        assert step.description.strip()