from engine.aircraft import load_aircraft_from_json
from engine.cargo import load_cargo_from_csv
from engine.csp import AeroLoadCSP
from engine.knowledge_base import load_hazard_rules
from engine.models import CargoItem


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


def test_csp_variables_created():
    csp = make_csp()

    assert len(csp.cargo_items) == 6


def test_domains_created_for_every_cargo():
    csp = make_csp()

    assert len(csp.domains) == 6

    for cargo in csp.cargo_items:
        assert cargo.cargo_id in csp.domains


def test_normal_cargo_has_valid_domain():
    csp = make_csp()

    assert "B1" in csp.domains["P1"]


def test_heavy_cargo_domain_is_filtered():
    aircraft = load_aircraft_from_json(
        "data/aircraft.json"
    )

    knowledge = load_hazard_rules(
        "data/hazard_rules.json"
    )

    heavy_cargo = CargoItem(
        cargo_id="PX",
        name="Heavy Test Cargo",
        weight_kg=625,
    )

    csp = AeroLoadCSP(
        aircraft=aircraft,
        cargo_items=[heavy_cargo],
        knowledge_base=knowledge,
    )

    assert "B1" not in csp.domains["PX"]
    assert "B2" not in csp.domains["PX"]

    assert "B3" in csp.domains["PX"]
    assert "B4" in csp.domains["PX"]


def test_same_bay_cannot_be_used_twice():
    csp = make_csp()

    assignment = {
        "P1": "B1"
    }

    assert not csp.is_consistent(
        "P2",
        "B1",
        assignment,
    )


def test_lithium_and_flammable_cannot_be_adjacent():
    csp = make_csp()

    assignment = {
        "P2": "B3"
    }

    assert not csp.is_consistent(
        "P3",
        "B4",
        assignment,
    )


def test_lithium_and_flammable_can_be_separated():
    csp = make_csp()

    assignment = {
        "P2": "B1"
    }

    assert csp.is_consistent(
        "P3",
        "B8",
        assignment,
    )


def test_overweight_cargo_is_not_consistent():
    aircraft = load_aircraft_from_json(
        "data/aircraft.json"
    )

    knowledge = load_hazard_rules(
        "data/hazard_rules.json"
    )

    heavy_cargo = CargoItem(
        cargo_id="PX",
        name="Heavy Cargo",
        weight_kg=625,
    )

    csp = AeroLoadCSP(
        aircraft=aircraft,
        cargo_items=[heavy_cargo],
        knowledge_base=knowledge,
    )

    assert not csp.is_consistent(
        "PX",
        "B1",
        {},
    )


def test_toxic_and_food_cannot_be_adjacent():
    csp = make_csp()

    # P6 = Toxic
    # P4 = Food
    assignment = {
        "P6": "B3"
    }

    assert not csp.is_consistent(
        "P4",
        "B4",
        assignment,
    )


def test_pairwise_same_bay_is_invalid():
    csp = make_csp()

    assert not csp.are_pairwise_compatible(
        "P1",
        "B1",
        "P2",
        "B1",
    )


def test_pairwise_hazard_conflict_is_invalid():
    csp = make_csp()

    # P2 = Lithium Battery
    # P3 = Flammable
    # B3 and B4 are adjacent.
    assert not csp.are_pairwise_compatible(
        "P2",
        "B3",
        "P3",
        "B4",
    )


def test_pairwise_separated_hazard_is_valid():
    csp = make_csp()

    assert csp.are_pairwise_compatible(
        "P2",
        "B1",
        "P3",
        "B8",
    )