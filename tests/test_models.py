import pytest

from engine.models import (
    BaySide,
    CargoBay,
    CargoCategory,
    CargoItem,
    HazardClass,
)


def test_valid_cargo_item():
    cargo = CargoItem(
        cargo_id="P1",
        name="Test Cargo",
        weight_kg=250,
        category=CargoCategory.GENERAL,
        hazard_class=HazardClass.NONE,
    )

    assert cargo.cargo_id == "P1"
    assert cargo.weight_kg == 250


def test_invalid_cargo_weight():
    with pytest.raises(
        ValueError,
        match="Cargo weight must be greater than 0 kg"
    ):
        CargoItem(
            cargo_id="P1",
            name="Invalid Cargo",
            weight_kg=-100,
        )


def test_valid_cargo_bay():
    bay = CargoBay(
        bay_id="B1",
        max_weight_kg=600,
        longitudinal_arm_m=-3.0,
        side=BaySide.LEFT,
        row=1,
    )

    assert bay.bay_id == "B1"
    assert bay.max_weight_kg == 600