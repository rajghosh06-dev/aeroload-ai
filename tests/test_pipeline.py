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


def test_pipeline_finds_solution():
    csp = make_csp()

    result = analyze_loading_problem(
        csp
    )

    assert result.solved is True
    assert result.final_assignment is not None


def test_pipeline_final_plan_is_safe():
    csp = make_csp()

    result = analyze_loading_problem(
        csp
    )

    assert result.safe is True


def test_pipeline_runs_optimization():
    csp = make_csp()

    result = analyze_loading_problem(
        csp
    )

    assert (
        result.optimization_result
        is not None
    )


def test_pipeline_produces_loading_explanation():
    csp = make_csp()

    result = analyze_loading_problem(
        csp
    )

    assert (
        result.loading_explanation
        is not None
    )

    assert len(
        result.loading_explanation.items
    ) > 0


def test_pipeline_produces_optimization_explanations():
    csp = make_csp()

    result = analyze_loading_problem(
        csp
    )

    assert len(
        result.optimization_explanations
    ) > 0


def test_pipeline_without_optimization():
    csp = make_csp()

    result = analyze_loading_problem(
        csp,
        optimize=False,
    )

    assert result.solved is True
    assert result.safe is True

    assert (
        result.optimization_result
        is None
    )

    assert result.optimized is False


def test_pipeline_preserves_solver_statistics():
    csp = make_csp()

    result = analyze_loading_problem(
        csp
    )

    assert (
        result.solver_result
        .nodes_explored
        > 0
    )

    assert (
        result.solver_result
        .ac3_arcs_processed
        > 0
    )


def test_pipeline_detects_unsatisfiable_problem():
    csp = make_csp()

    csp.domains["P1"] = [
        "B1"
    ]

    csp.domains["P2"] = [
        "B1"
    ]

    result = analyze_loading_problem(
        csp
    )

    assert result.solved is False
    assert result.safe is False
    assert result.final_assignment is None

    assert (
        result.optimization_result
        is None
    )