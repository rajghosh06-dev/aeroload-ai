import pytest

from engine.aircraft import (
    load_aircraft_from_json,
)
from engine.models import (
    CargoAssignment,
    CargoItem,
)
from engine.optimization import (
    evaluate_solution_quality,
)


def test_centered_solution_has_zero_cg_deviation():
    aircraft = load_aircraft_from_json(
        "data/aircraft.json"
    )

    assignments = [
        CargoAssignment(
            cargo=CargoItem(
                cargo_id="PX",
                name="Cargo X",
                weight_kg=300,
            ),
            bay=aircraft.require_bay("B1"),
        ),
        CargoAssignment(
            cargo=CargoItem(
                cargo_id="PY",
                name="Cargo Y",
                weight_kg=300,
            ),
            bay=aircraft.require_bay("B8"),
        ),
    ]

    quality = evaluate_solution_quality(
        aircraft,
        assignments,
    )

    assert quality.cg_m == pytest.approx(0.0)
    assert quality.cg_deviation_m == pytest.approx(
        0.0
    )


def test_balanced_solution_has_zero_imbalance():
    aircraft = load_aircraft_from_json(
        "data/aircraft.json"
    )

    assignments = [
        CargoAssignment(
            cargo=CargoItem(
                cargo_id="PX",
                name="Cargo X",
                weight_kg=300,
            ),
            bay=aircraft.require_bay("B1"),
        ),
        CargoAssignment(
            cargo=CargoItem(
                cargo_id="PY",
                name="Cargo Y",
                weight_kg=300,
            ),
            bay=aircraft.require_bay("B2"),
        ),
    ]

    quality = evaluate_solution_quality(
        aircraft,
        assignments,
    )

    assert quality.lateral_imbalance_kg == pytest.approx(
        0.0
    )

    assert quality.imbalance_ratio == pytest.approx(
        0.0
    )


def test_better_cg_produces_lower_score():
    aircraft = load_aircraft_from_json(
        "data/aircraft.json"
    )

    poor_assignments = [
        CargoAssignment(
            cargo=CargoItem(
                cargo_id="PX",
                name="Cargo X",
                weight_kg=300,
            ),
            bay=aircraft.require_bay("B1"),
        ),
        CargoAssignment(
            cargo=CargoItem(
                cargo_id="PY",
                name="Cargo Y",
                weight_kg=300,
            ),
            bay=aircraft.require_bay("B2"),
        ),
    ]

    better_assignments = [
        CargoAssignment(
            cargo=CargoItem(
                cargo_id="PX",
                name="Cargo X",
                weight_kg=300,
            ),
            bay=aircraft.require_bay("B1"),
        ),
        CargoAssignment(
            cargo=CargoItem(
                cargo_id="PY",
                name="Cargo Y",
                weight_kg=300,
            ),
            bay=aircraft.require_bay("B8"),
        ),
    ]

    poor_quality = evaluate_solution_quality(
        aircraft,
        poor_assignments,
    )

    better_quality = evaluate_solution_quality(
        aircraft,
        better_assignments,
    )

    assert (
        better_quality.score
        < poor_quality.score
    )


def test_quality_score_is_non_negative():
    aircraft = load_aircraft_from_json(
        "data/aircraft.json"
    )

    assignments = [
        CargoAssignment(
            cargo=CargoItem(
                cargo_id="PX",
                name="Cargo X",
                weight_kg=300,
            ),
            bay=aircraft.require_bay("B1"),
        ),
        CargoAssignment(
            cargo=CargoItem(
                cargo_id="PY",
                name="Cargo Y",
                weight_kg=300,
            ),
            bay=aircraft.require_bay("B8"),
        ),
    ]

    quality = evaluate_solution_quality(
        aircraft,
        assignments,
    )

    assert quality.score >= 0.0