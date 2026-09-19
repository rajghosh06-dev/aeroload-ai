from engine.knowledge_base import load_hazard_rules
from engine.models import HazardClass


def test_hazard_rules_load():
    knowledge = load_hazard_rules(
        "data/hazard_rules.json"
    )

    assert len(knowledge.incompatible_pairs) > 0


def test_lithium_flammable_are_incompatible():
    knowledge = load_hazard_rules(
        "data/hazard_rules.json"
    )

    assert knowledge.are_incompatible(
        HazardClass.LITHIUM_BATTERY,
        HazardClass.FLAMMABLE,
    )


def test_flammable_lithium_is_symmetric():
    knowledge = load_hazard_rules(
        "data/hazard_rules.json"
    )

    assert knowledge.are_incompatible(
        HazardClass.FLAMMABLE,
        HazardClass.LITHIUM_BATTERY,
    )


def test_general_none_classes_are_compatible():
    knowledge = load_hazard_rules(
        "data/hazard_rules.json"
    )

    assert not knowledge.are_incompatible(
        HazardClass.NONE,
        HazardClass.LITHIUM_BATTERY,
    )


def test_toxic_food_are_incompatible():
    knowledge = load_hazard_rules(
        "data/hazard_rules.json"
    )

    assert knowledge.are_incompatible(
        HazardClass.TOXIC,
        HazardClass.FOOD,
    )