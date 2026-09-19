import pytest

from engine.cg import (
    calculate_cg,
    calculate_lateral_imbalance,
    calculate_side_weights,
    calculate_total_moment,
    calculate_total_payload,
)
from engine.models import (
    BaySide,
    CargoAssignment,
    CargoBay,
    CargoItem,
)


def make_assignment(
    cargo_id: str,
    weight: float,
    bay_id: str,
    arm: float,
    side: BaySide,
) -> CargoAssignment:
    cargo = CargoItem(
        cargo_id=cargo_id,
        name=f"Cargo {cargo_id}",
        weight_kg=weight,
    )

    bay = CargoBay(
        bay_id=bay_id,
        max_weight_kg=1000,
        longitudinal_arm_m=arm,
        side=side,
        row=1,
    )

    return CargoAssignment(
        cargo=cargo,
        bay=bay,
    )


def test_total_payload():
    assignments = [
        make_assignment(
            "P1", 300, "B1", -3.0, BaySide.LEFT
        ),
        make_assignment(
            "P2", 200, "B2", 3.0, BaySide.RIGHT
        ),
    ]

    assert calculate_total_payload(assignments) == 500


def test_total_moment():
    assignments = [
        make_assignment(
            "P1", 300, "B1", -3.0, BaySide.LEFT
        ),
        make_assignment(
            "P2", 300, "B2", 3.0, BaySide.RIGHT
        ),
    ]

    assert calculate_total_moment(assignments) == 0


def test_centered_cg():
    assignments = [
        make_assignment(
            "P1", 300, "B1", -3.0, BaySide.LEFT
        ),
        make_assignment(
            "P2", 300, "B2", 3.0, BaySide.RIGHT
        ),
    ]

    assert calculate_cg(assignments) == pytest.approx(0.0)


def test_side_weights():
    assignments = [
        make_assignment(
            "P1", 400, "B1", -1.0, BaySide.LEFT
        ),
        make_assignment(
            "P2", 250, "B2", 1.0, BaySide.RIGHT
        ),
    ]

    left, right = calculate_side_weights(assignments)

    assert left == 400
    assert right == 250


def test_lateral_imbalance():
    assignments = [
        make_assignment(
            "P1", 400, "B1", -1.0, BaySide.LEFT
        ),
        make_assignment(
            "P2", 250, "B2", 1.0, BaySide.RIGHT
        ),
    ]

    assert calculate_lateral_imbalance(assignments) == 150


def test_zero_payload_cg_error():
    with pytest.raises(
        ValueError,
        match="Cannot calculate CG with zero total payload"
    ):
        calculate_cg([])