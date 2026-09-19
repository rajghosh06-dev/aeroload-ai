from engine.ac3 import ac3, revise
from engine.aircraft import load_aircraft_from_json
from engine.cargo import load_cargo_from_csv
from engine.csp import AeroLoadCSP
from engine.knowledge_base import load_hazard_rules
from engine.models import (
    CargoCategory,
    CargoItem,
    HazardClass,
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


def test_ac3_returns_consistent_result():
    csp = make_csp()

    result = ac3(
        csp
    )

    assert result.consistent is True
    assert result.arcs_processed > 0


def test_ac3_does_not_modify_original_domains():
    csp = make_csp()

    original = {
        cargo_id: values.copy()
        for cargo_id, values
        in csp.domains.items()
    }

    ac3(
        csp
    )

    assert csp.domains == original


def test_revise_removes_unsupported_same_bay_value():
    csp = make_csp()

    domains = {
        "P1": [
            "B1",
            "B2",
        ],
        "P2": [
            "B1",
        ],
    }

    removed = revise(
        csp,
        domains,
        "P1",
        "P2",
    )

    assert removed == 1

    assert domains["P1"] == [
        "B2"
    ]


def test_revise_prunes_hazard_conflict():
    aircraft = load_aircraft_from_json(
        "data/aircraft.json"
    )

    knowledge = load_hazard_rules(
        "data/hazard_rules.json"
    )

    lithium = CargoItem(
        cargo_id="PX",
        name="Lithium Test Cargo",
        weight_kg=200,
        category=CargoCategory.HAZARDOUS,
        hazard_class=(
            HazardClass.LITHIUM_BATTERY
        ),
    )

    flammable = CargoItem(
        cargo_id="PY",
        name="Flammable Test Cargo",
        weight_kg=200,
        category=CargoCategory.HAZARDOUS,
        hazard_class=(
            HazardClass.FLAMMABLE
        ),
    )

    csp = AeroLoadCSP(
        aircraft=aircraft,
        cargo_items=[
            lithium,
            flammable,
        ],
        knowledge_base=knowledge,
    )

    domains = {
        "PX": [
            "B3",
            "B8",
        ],
        "PY": [
            "B4",
        ],
    }

    removed = revise(
        csp,
        domains,
        "PX",
        "PY",
    )

    # B3 is adjacent to B4 and conflicts.
    # B8 is sufficiently separated.
    assert removed == 1

    assert domains["PX"] == [
        "B8"
    ]


def test_ac3_detects_inconsistent_domains():
    csp = make_csp()

    # Force two variables to have only
    # the exact same available bay.
    csp.domains["P1"] = [
        "B1"
    ]

    csp.domains["P2"] = [
        "B1"
    ]

    result = ac3(
        csp
    )

    assert result.consistent is False