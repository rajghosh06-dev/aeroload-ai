from dataclasses import dataclass

from engine.aircraft import Aircraft
from engine.cg import (
    calculate_cg,
    calculate_lateral_imbalance,
)
from engine.models import CargoAssignment


@dataclass
class SolutionQuality:
    """
    Describes the quality of a safe cargo loading plan.

    Lower score is better.
    """

    cg_m: float
    target_cg_m: float
    cg_deviation_m: float

    lateral_imbalance_kg: float
    imbalance_ratio: float

    score: float


def evaluate_solution_quality(
    aircraft: Aircraft,
    assignments: list[CargoAssignment],
) -> SolutionQuality:
    """
    Evaluate the soft optimization quality of
    an aircraft cargo loading plan.

    Hard safety constraints are handled elsewhere.
    This function measures how desirable a valid
    solution is.

    Lower score is better.
    """

    cg_m = calculate_cg(
        assignments
    )

    lateral_imbalance_kg = (
        calculate_lateral_imbalance(
            assignments
        )
    )

    cg_deviation_m = abs(
        cg_m - aircraft.target_cg_m
    )

    if aircraft.lateral_imbalance_limit_kg > 0:
        imbalance_ratio = (
            lateral_imbalance_kg
            / aircraft.lateral_imbalance_limit_kg
        )
    else:
        imbalance_ratio = 0.0

    score = (
        cg_deviation_m
        + 0.25 * imbalance_ratio
    )

    return SolutionQuality(
        cg_m=cg_m,
        target_cg_m=aircraft.target_cg_m,
        cg_deviation_m=cg_deviation_m,
        lateral_imbalance_kg=lateral_imbalance_kg,
        imbalance_ratio=imbalance_ratio,
        score=score,
    )