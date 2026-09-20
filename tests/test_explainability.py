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
from engine.explainability import (
    explain_loading_plan,
    explain_optimization,
)
from engine.knowledge_base import (
    load_hazard_rules,
)
from engine.local_search import (
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


def get_optimized_result():
    csp = make_csp()

    solver_result = smart_backtracking_search(
        csp
    )

    assert solver_result.assignment is not None

    optimization_result = optimize_loading_plan(
        csp,
        solver_result.assignment,
    )

    return csp, optimization_result


def test_loading_explanation_reports_safe_plan():
    csp, result = get_optimized_result()

    report = explain_loading_plan(
        csp,
        result.best_assignment,
    )

    assert report.safe is True
    assert len(report.items) > 0


def test_loading_explanation_contains_cg():
    csp, result = get_optimized_result()

    report = explain_loading_plan(
        csp,
        result.best_assignment,
    )

    categories = {
        item.category
        for item in report.items
    }

    assert "Center of Gravity" in categories


def test_loading_explanation_contains_balance():
    csp, result = get_optimized_result()

    report = explain_loading_plan(
        csp,
        result.best_assignment,
    )

    categories = {
        item.category
        for item in report.items
    }

    assert "Lateral Balance" in categories


def test_optimization_explanation_created():
    _, result = get_optimized_result()

    items = explain_optimization(
        result
    )

    assert len(items) > 0


def test_optimization_explanation_mentions_improvement():
    _, result = get_optimized_result()

    items = explain_optimization(
        result
    )

    statuses = {
        item.status
        for item in items
    }

    assert "IMPROVED" in statuses


def test_optimization_steps_are_explained():
    _, result = get_optimized_result()

    items = explain_optimization(
        result
    )

    step_items = [
        item
        for item in items
        if item.category == "Optimization Step"
    ]

    assert len(step_items) == result.improvements