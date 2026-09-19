import pytest

def test_aircraft_require_existing_bay():
    aircraft = load_aircraft_from_json(
        "data/aircraft.json"
    )

    bay = aircraft.require_bay("B3")

    assert bay.bay_id == "B3"


def test_aircraft_require_missing_bay():
    aircraft = load_aircraft_from_json(
        "data/aircraft.json"
    )

    with pytest.raises(
        ValueError,
        match="Cargo bay 'B99' does not exist"
    ):
        aircraft.require_bay("B99")

from engine.aircraft import (
    load_aircraft_from_json,
)


def test_aircraft_loading():
    aircraft = load_aircraft_from_json(
        "data/aircraft.json"
    )

    assert aircraft.aircraft_id == "ALT-8"
    assert len(aircraft.bays) == 8

    assert aircraft.cg_min_m == -1.0
    assert aircraft.cg_max_m == 1.0
    assert aircraft.target_cg_m == 0.0


def test_aircraft_get_bay():
    aircraft = load_aircraft_from_json(
        "data/aircraft.json"
    )

    bay = aircraft.get_bay("B3")

    assert bay is not None
    assert bay.bay_id == "B3"
