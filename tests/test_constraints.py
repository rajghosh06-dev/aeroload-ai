from engine.aircraft import load_aircraft_from_json
from engine.constraints import (
    validate_bay_capacity,
    validate_cg_envelope,
    validate_lateral_balance,
    validate_loading_plan,
    validate_total_payload,
)
from engine.models import (
    BaySide,
    CargoAssignment,
    CargoBay,
    CargoItem,
)


def test_valid_bay_capacity():
    cargo = CargoItem(
        cargo_id="P1",
        name="Test Cargo",
        weight_kg=400,
    )

    bay = CargoBay(
        bay_id="B1",
        max_weight_kg=600,
        longitudinal_arm_m=0.0,
        side=BaySide.LEFT,
        row=1,
    )

    result = validate_bay_capacity(
        CargoAssignment(cargo=cargo, bay=bay)
    )

    assert result.valid is True


def test_bay_overload():
    cargo = CargoItem(
        cargo_id="P1",
        name="Heavy Cargo",
        weight_kg=700,
    )

    bay = CargoBay(
        bay_id="B1",
        max_weight_kg=600,
        longitudinal_arm_m=0.0,
        side=BaySide.LEFT,
        row=1,
    )

    result = validate_bay_capacity(
        CargoAssignment(cargo=cargo, bay=bay)
    )

    assert result.valid is False


def test_known_unsafe_cg_plan():
    aircraft = load_aircraft_from_json(
        "data/aircraft.json"
    )

    assignments = [
        CargoAssignment(
            CargoItem("P1", "Cargo 1", 500),
            aircraft.require_bay("B1"),
        ),
        CargoAssignment(
            CargoItem("P2", "Cargo 2", 500),
            aircraft.require_bay("B2"),
        ),
    ]

    result = validate_cg_envelope(
        aircraft,
        assignments,
    )

    assert result.valid is False


def test_known_safe_cg_plan():
    aircraft = load_aircraft_from_json(
        "data/aircraft.json"
    )

    assignments = [
        CargoAssignment(
            CargoItem("P1", "Cargo 1", 300),
            aircraft.require_bay("B1"),
        ),
        CargoAssignment(
            CargoItem("P2", "Cargo 2", 300),
            aircraft.require_bay("B8"),
        ),
    ]

    result = validate_cg_envelope(
        aircraft,
        assignments,
    )

    assert result.valid is True


def test_lateral_balance_failure():
    aircraft = load_aircraft_from_json(
        "data/aircraft.json"
    )

    assignments = [
        CargoAssignment(
            CargoItem("P1", "Cargo 1", 500),
            aircraft.require_bay("B1"),
        ),
        CargoAssignment(
            CargoItem("P2", "Cargo 2", 100),
            aircraft.require_bay("B2"),
        ),
    ]

    result = validate_lateral_balance(
        aircraft,
        assignments,
    )

    assert result.valid is False


def test_complete_safe_loading_plan():
    aircraft = load_aircraft_from_json(
        "data/aircraft.json"
    )

    assignments = [
        CargoAssignment(
            CargoItem("P1", "Cargo 1", 300),
            aircraft.require_bay("B1"),
        ),
        CargoAssignment(
            CargoItem("P2", "Cargo 2", 300),
            aircraft.require_bay("B2"),
        ),
        CargoAssignment(
            CargoItem("P3", "Cargo 3", 300),
            aircraft.require_bay("B7"),
        ),
        CargoAssignment(
            CargoItem("P4", "Cargo 4", 300),
            aircraft.require_bay("B8"),
        ),
    ]

    report = validate_loading_plan(
        aircraft,
        assignments,
    )

    assert report.safe is True
    assert report.cg_m == 0.0
    assert report.lateral_imbalance_kg == 0.0