from engine.aircraft import load_aircraft_from_json
from engine.backtracking import (
    assignment_to_cargo_assignments,
    basic_backtracking_search,
    mrv_backtracking_search,
    mrv_lcv_backtracking_search,
    smart_backtracking_search,
)
from engine.cargo import load_cargo_from_csv
from engine.constraints import validate_loading_plan
from engine.csp import AeroLoadCSP
from engine.knowledge_base import load_hazard_rules

def test_mrv_lcv_backtracking_finds_solution():
    csp = make_csp()

    result = mrv_lcv_backtracking_search(csp)

    assert result.solved is True
    assert result.assignment is not None


def test_mrv_lcv_solution_is_safe():
    csp = make_csp()

    result = mrv_lcv_backtracking_search(csp)

    assert result.safety_report is not None
    assert result.safety_report.safe is True


def test_mrv_lcv_assigns_all_cargo():
    csp = make_csp()

    result = mrv_lcv_backtracking_search(csp)

    assert result.assignment is not None

    assert len(result.assignment) == len(
        csp.cargo_items
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


def test_assignment_conversion():
    csp = make_csp()

    assignment = {
        "P1": "B1",
        "P2": "B3",
    }

    converted = assignment_to_cargo_assignments(
        csp,
        assignment,
    )

    assert len(converted) == 2

    assert converted[0].cargo.cargo_id == "P1"
    assert converted[0].bay.bay_id == "B1"


def test_basic_backtracking_finds_solution():
    csp = make_csp()

    result = basic_backtracking_search(csp)

    assert result.solved is True
    assert result.assignment is not None


def test_basic_backtracking_assigns_all_cargo():
    csp = make_csp()

    result = basic_backtracking_search(csp)

    assert result.assignment is not None

    assert len(result.assignment) == len(
        csp.cargo_items
    )


def test_backtracking_solution_has_unique_bays():
    csp = make_csp()

    result = basic_backtracking_search(csp)

    assert result.assignment is not None

    assigned_bays = list(
        result.assignment.values()
    )

    assert len(assigned_bays) == len(
        set(assigned_bays)
    )


def test_backtracking_solution_is_safe():
    csp = make_csp()

    result = basic_backtracking_search(csp)

    assert result.assignment is not None

    assignments = assignment_to_cargo_assignments(
        csp,
        result.assignment,
    )

    report = validate_loading_plan(
        csp.aircraft,
        assignments,
    )

    assert report.safe is True


def test_basic_solver_statistics_are_recorded():
    csp = make_csp()

    result = basic_backtracking_search(csp)

    assert result.nodes_explored > 0
    assert result.backtracks >= 0


def test_mrv_backtracking_finds_solution():
    csp = make_csp()

    result = mrv_backtracking_search(csp)

    assert result.solved is True
    assert result.assignment is not None


def test_mrv_solution_assigns_all_cargo():
    csp = make_csp()

    result = mrv_backtracking_search(csp)

    assert result.assignment is not None

    assert len(result.assignment) == len(
        csp.cargo_items
    )


def test_mrv_solution_has_unique_bays():
    csp = make_csp()

    result = mrv_backtracking_search(csp)

    assert result.assignment is not None

    assigned_bays = list(
        result.assignment.values()
    )

    assert len(assigned_bays) == len(
        set(assigned_bays)
    )


def test_mrv_solution_is_safe():
    csp = make_csp()

    result = mrv_backtracking_search(csp)

    assert result.safety_report is not None
    assert result.safety_report.safe is True


def test_mrv_solver_statistics_are_recorded():
    csp = make_csp()

    result = mrv_backtracking_search(csp)

    assert result.nodes_explored > 0
    assert result.backtracks >= 0

def test_smart_solver_finds_solution():
    csp = make_csp()

    result = smart_backtracking_search(csp)

    assert result.solved is True
    assert result.assignment is not None


def test_smart_solver_assigns_all_cargo():
    csp = make_csp()

    result = smart_backtracking_search(csp)

    assert result.assignment is not None

    assert len(result.assignment) == len(
        csp.cargo_items
    )


def test_smart_solver_solution_is_safe():
    csp = make_csp()

    result = smart_backtracking_search(csp)

    assert result.safety_report is not None
    assert result.safety_report.safe is True


def test_smart_solver_records_ac3_statistics():
    csp = make_csp()

    result = smart_backtracking_search(csp)

    assert result.ac3_arcs_processed > 0
    assert result.ac3_values_pruned >= 0


def test_smart_solver_does_not_modify_original_domains():
    csp = make_csp()

    original_domains = {
        cargo_id: values.copy()
        for cargo_id, values
        in csp.domains.items()
    }

    smart_backtracking_search(csp)

    assert csp.domains == original_domains

def test_smart_solver_detects_ac3_inconsistency():
    csp = make_csp()

    csp.domains["P1"] = ["B1"]
    csp.domains["P2"] = ["B1"]

    result = smart_backtracking_search(csp)

    assert result.solved is False
    assert result.assignment is None
    assert result.nodes_explored == 0