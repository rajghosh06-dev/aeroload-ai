from engine.ac3 import ac3
from engine.aircraft import load_aircraft_from_json
from engine.backtracking import (
    basic_backtracking_search,
    smart_backtracking_search,
)
from engine.cargo import load_cargo_from_csv
from engine.csp import AeroLoadCSP
from engine.knowledge_base import load_hazard_rules


def make_benchmark_csp() -> AeroLoadCSP:
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


def test_benchmark_ac3_prunes_values():
    csp = make_benchmark_csp()

    result = ac3(csp)

    assert result.consistent is True
    assert result.values_pruned > 0


def test_benchmark_domains_become_singletons():
    csp = make_benchmark_csp()

    result = ac3(csp)

    assert result.domains["P1"] == ["B1"]
    assert result.domains["P2"] == ["B2"]
    assert result.domains["P3"] == ["B3"]
    assert result.domains["P4"] == ["B4"]
    assert result.domains["P5"] == ["B8"]
    assert result.domains["P6"] == ["B7"]


def test_benchmark_smart_solver_finds_solution():
    csp = make_benchmark_csp()

    result = smart_backtracking_search(
        csp
    )

    assert result.solved is True
    assert result.assignment is not None
    assert result.safety_report is not None
    assert result.safety_report.safe is True


def test_benchmark_smart_solver_uses_ac3():
    csp = make_benchmark_csp()

    result = smart_backtracking_search(
        csp
    )

    assert result.ac3_values_pruned > 0
    assert result.ac3_arcs_processed > 0


def test_benchmark_smart_search_not_worse_than_basic():
    basic_csp = make_benchmark_csp()
    smart_csp = make_benchmark_csp()

    basic = basic_backtracking_search(
        basic_csp
    )

    smart = smart_backtracking_search(
        smart_csp
    )

    assert (
        smart.nodes_explored
        <= basic.nodes_explored
    )