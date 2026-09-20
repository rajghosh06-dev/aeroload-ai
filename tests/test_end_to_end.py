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


def test_end_to_end_pipeline_is_safe():
    csp = make_csp()

    result = analyze_loading_problem(
        csp
    )

    assert result.solved is True
    assert result.safe is True
    assert result.final_assignment is not None


def test_end_to_end_assigns_every_cargo():
    csp = make_csp()

    result = analyze_loading_problem(
        csp
    )

    assert result.final_assignment is not None

    assert len(
        result.final_assignment
    ) == len(
        csp.cargo_items
    )


def test_end_to_end_uses_unique_bays():
    csp = make_csp()

    result = analyze_loading_problem(
        csp
    )

    assert result.final_assignment is not None

    bays = list(
        result.final_assignment.values()
    )

    assert len(bays) == len(
        set(bays)
    )


def test_end_to_end_reaches_target_cg():
    csp = make_csp()

    result = analyze_loading_problem(
        csp
    )

    assert (
        result.optimization_result
        is not None
    )

    final_quality = (
        result.optimization_result
        .final_quality
    )

    assert abs(
        final_quality.cg_m
        - csp.aircraft.target_cg_m
    ) < 1e-9


def test_end_to_end_improves_quality_score():
    csp = make_csp()

    result = analyze_loading_problem(
        csp
    )

    assert (
        result.optimization_result
        is not None
    )

    optimization = (
        result.optimization_result
    )

    assert (
        optimization.final_quality.score
        < optimization.initial_quality.score
    )


def test_end_to_end_has_explanations():
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

    assert len(
        result.optimization_explanations
    ) > 0


def test_end_to_end_has_solver_audit_data():
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

    assert (
        result.optimization_result
        is not None
    )

    assert (
        result.optimization_result
        .candidates_evaluated
        > 0
    )