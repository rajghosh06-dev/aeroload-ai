"""Unit and integration tests for AeroLoad-AI manual and AI-assisted planning logic."""

from engine.aircraft import load_aircraft_from_json
from engine.cargo import load_cargo_from_csv
from engine.csp import AeroLoadCSP
from engine.knowledge_base import load_hazard_rules
from engine.models import BaySide, CargoBay, CargoCategory, CargoItem, HazardClass
from ui.planning import (
    BayOptionStatus,
    assign_cargo_manually,
    clear_manual_assignments,
    evaluate_bay_options,
    reconcile_manual_assignments,
    unassign_cargo_manually,
    validate_manual_plan,
)
from ui.state import empty_manifest_rows, manifest_from_rows


def _get_test_data():
    aircraft = load_aircraft_from_json("data/aircraft.json")
    cargo_items = load_cargo_from_csv("data/sample_cargo.csv")
    knowledge = load_hazard_rules("data/hazard_rules.json")
    csp = AeroLoadCSP(aircraft=aircraft, cargo_items=cargo_items, knowledge_base=knowledge)
    return aircraft, cargo_items, knowledge, csp


def test_evaluate_bay_options_legal_bays():
    aircraft, cargo_items, knowledge, csp = _get_test_data()
    # P1 is General cargo, 420 kg. All bays with capacity >= 420 kg should be legal when unassigned.
    analysis = evaluate_bay_options(csp, "P1", {})
    assert analysis.cargo_id == "P1"
    assert len(analysis.legal_bays) > 0
    assert "B1" in analysis.legal_bays
    assert analysis.bay_options["B1"].status == BayOptionStatus.LEGAL


def test_evaluate_bay_options_occupied_bay():
    aircraft, cargo_items, knowledge, csp = _get_test_data()
    # P1 is assigned to B1
    current = {"P1": "B1"}
    # Evaluate P2: B1 should be OCCUPIED
    analysis = evaluate_bay_options(csp, "P2", current)
    assert analysis.bay_options["B1"].status == BayOptionStatus.OCCUPIED
    assert "Occupied by P1" in analysis.bay_options["B1"].reason


def test_evaluate_bay_options_overweight_bay():
    aircraft, cargo_items, knowledge, csp = _get_test_data()
    # Create a heavy cargo item (620 kg) - bays B1, B2, B7, B8 have max capacity 600 kg.
    heavy = CargoItem(
        cargo_id="HEAVY",
        name="Heavy Machinery",
        weight_kg=620.0,
        category=CargoCategory.GENERAL,
        hazard_class=HazardClass.NONE,
    )
    custom_csp = AeroLoadCSP(aircraft=aircraft, cargo_items=[heavy], knowledge_base=knowledge)
    analysis = evaluate_bay_options(custom_csp, "HEAVY", {})
    assert analysis.bay_options["B1"].status == BayOptionStatus.ILLEGAL
    assert "exceeds bay capacity" in analysis.bay_options["B1"].reason


def test_evaluate_bay_options_hazard_conflict():
    aircraft, cargo_items, knowledge, csp = _get_test_data()
    # P2 is Lithium Battery, P3 is Flammable
    # Place P2 in B1. B2 and B3 are adjacent to B1.
    current = {"P2": "B1"}
    analysis = evaluate_bay_options(csp, "P3", current)

    # B2 and B3 should be blocked due to hazard adjacency
    assert analysis.bay_options["B2"].status == BayOptionStatus.ILLEGAL
    assert "conflicts with" in analysis.bay_options["B2"].reason
    assert analysis.bay_options["B3"].status == BayOptionStatus.ILLEGAL

    # B7 and B8 are not adjacent to B1, so they should be LEGAL for P3
    assert analysis.bay_options["B7"].status == BayOptionStatus.LEGAL
    assert "B7" in analysis.legal_bays


def test_evaluate_bay_options_separated_incompatible_is_legal():
    aircraft, cargo_items, knowledge, csp = _get_test_data()
    # P2 is Lithium Battery in B1. P3 is Flammable in B7.
    current = {"P2": "B1"}
    analysis = evaluate_bay_options(csp, "P3", current)
    assert analysis.bay_options["B7"].status == BayOptionStatus.LEGAL


def test_validate_manual_plan_partial_valid():
    aircraft, cargo_items, knowledge, csp = _get_test_data()
    current = {"P1": "B1", "P2": "B7"}
    status = validate_manual_plan(aircraft, cargo_items, current, knowledge)
    assert status.is_complete is False
    assert status.assigned_count == 2
    assert status.total_count == len(cargo_items)
    assert status.is_valid is True
    assert len(status.violations) == 0
    assert status.payload_kg == 420.0 + 300.0


def test_validate_manual_plan_partial_conflict():
    aircraft, cargo_items, knowledge, csp = _get_test_data()
    # P2 (Lithium Battery) in B1, P3 (Flammable) in adjacent B2
    current = {"P2": "B1", "P3": "B2"}
    status = validate_manual_plan(aircraft, cargo_items, current, knowledge)
    assert status.is_valid is False
    assert len(status.violations) > 0
    assert any("Hazard separation violation" in v for v in status.violations)


def test_validate_manual_plan_complete_safe():
    aircraft, cargo_items, knowledge, csp = _get_test_data()
    # Balanced, hazard-separated full assignment
    # P1 (420kg, Gen, None) -> B4 (-1.0m, R, row 2)
    # P2 (300kg, Haz, Lithium) -> B1 (-3.0m, L, row 1)
    # P3 (280kg, Haz, Flammable) -> B8 (3.0m, R, row 4)
    # P4 (350kg, Food, Food) -> B5 (1.0m, L, row 3)
    # P5 (250kg, Fragile, None) -> B2 (-3.0m, R, row 1)
    # P6 (200kg, Haz, Toxic) -> B6 (1.0m, R, row 3) - not adjacent to B5? Wait, B5 is adjacent to B6!
    # Toxic in B6 is adjacent to Food in B5! Let's place P6 in B7 (row 4, L, arm 3.0m). B7 is adjacent to B5, B8.
    # Wait, B7 is adjacent to B5! Let's check: B5 adjacent_bays = ["B3", "B6", "B7"].
    # So B7 is adjacent to B5!
    # Let's use the auto-solver to get a known safe assignment:
    from engine.pipeline import analyze_loading_problem

    res = analyze_loading_problem(csp, optimize=True)
    assert res.solved is True
    safe_assignment = res.final_assignment

    status = validate_manual_plan(aircraft, cargo_items, safe_assignment, knowledge)
    assert status.is_complete is True
    assert status.is_valid is True
    assert status.safety_report is not None
    assert status.safety_report.safe is True


def test_validate_manual_plan_complete_unsafe():
    aircraft, cargo_items, knowledge, csp = _get_test_data()
    # Force an extreme nose-heavy assignment by placing everything forward
    # P1 (420) -> B1 (-3.0m)
    # P2 (300) -> B2 (-3.0m)
    # P3 (280) -> B3 (-1.0m)
    # P4 (350) -> B4 (-1.0m)
    # P5 (250) -> B5 (1.0m)
    # P6 (200) -> B6 (1.0m)
    extreme_front = {
        "P1": "B1",
        "P2": "B2",  # Note: P2 and P3 both in front row! P2 Lithium, P3 Flammable -> B2 and B3 adjacent -> conflict!
        "P3": "B3",
        "P4": "B4",
        "P5": "B5",
        "P6": "B6",
    }
    status = validate_manual_plan(aircraft, cargo_items, extreme_front, knowledge)
    assert status.is_complete is True
    assert status.is_valid is False
    assert len(status.violations) > 0


def test_reconcile_manual_assignments():
    manual = {"P1": "B1", "P2": "B2", "DELETED": "B3", "P3": "INVALID_BAY"}
    reconciled = reconcile_manual_assignments(manual, {"P1", "P2"}, {"B1", "B2", "B3"})
    assert "DELETED" not in reconciled
    assert "P3" not in reconciled
    assert reconciled == {"P1": "B1", "P2": "B2"}


def test_assign_and_unassign_cargo_manually():
    current = {}
    current = assign_cargo_manually(current, "P1", "B1")
    assert current == {"P1": "B1"}

    # Assigning P2 to B1 should displace P1
    current = assign_cargo_manually(current, "P2", "B1")
    assert current == {"P2": "B1"}

    # Reassigning P2 to B2
    current = assign_cargo_manually(current, "P2", "B2")
    assert current == {"P2": "B2"}

    # Unassigning P2
    current = unassign_cargo_manually(current, "P2")
    assert current == {}


def test_clear_manual_assignments():
    assert clear_manual_assignments() == {}


def test_empty_manifest_rows_and_state():
    assert empty_manifest_rows() == []
    items, errors = manifest_from_rows([], allow_empty=True)
    assert items == []
    assert errors == []
