import pytest
from engine.heuristics import (
    order_domain_values_lcv,
    select_unassigned_variable_mrv,
)
from engine.aircraft import load_aircraft_from_json
from engine.cargo import load_cargo_from_csv
from engine.csp import AeroLoadCSP

from engine.knowledge_base import load_hazard_rules

def test_lcv_returns_only_consistent_values():
    csp = make_csp()

    assignment = {
        "P1": "B1"
    }

    ordered = order_domain_values_lcv(
        csp,
        "P2",
        assignment,
    )

    assert "B1" not in ordered

    for bay_id in ordered:
        assert csp.is_consistent(
            "P2",
            bay_id,
            assignment,
        )


def test_lcv_returns_domain_values():
    csp = make_csp()

    ordered = order_domain_values_lcv(
        csp,
        "P1",
        {},
    )

    assert len(ordered) > 0

    for bay_id in ordered:
        assert bay_id in csp.domains["P1"]


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


def test_mrv_returns_unassigned_variable():
    csp = make_csp()

    assignment = {
        "P1": "B1"
    }

    selected = select_unassigned_variable_mrv(
        csp,
        assignment,
    )

    assert selected != "P1"


def test_mrv_returns_valid_cargo_id():
    csp = make_csp()

    selected = select_unassigned_variable_mrv(
        csp,
        {},
    )

    cargo_ids = {
        cargo.cargo_id
        for cargo in csp.cargo_items
    }

    assert selected in cargo_ids


def test_mrv_raises_when_everything_is_assigned():
    csp = make_csp()

    assignment = {
        cargo.cargo_id: csp.domains[cargo.cargo_id][0]
        for cargo in csp.cargo_items
    }

    with pytest.raises(
        ValueError,
        match="No unassigned variables remain"
    ):
        select_unassigned_variable_mrv(
            csp,
            assignment,
        )