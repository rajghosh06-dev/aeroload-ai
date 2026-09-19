from dataclasses import dataclass

from engine.aircraft import Aircraft
from engine.cg import (
    calculate_cg,
    calculate_lateral_imbalance,
    calculate_total_payload,
)
from engine.models import CargoAssignment


@dataclass
class ValidationResult:
    """
    Stores the outcome of a safety validation check.
    """

    valid: bool
    message: str


def validate_bay_capacity(
    assignment: CargoAssignment
) -> ValidationResult:
    """
    Check whether cargo exceeds the bay weight limit.
    """

    cargo_weight = assignment.cargo.weight_kg
    bay_limit = assignment.bay.max_weight_kg

    if cargo_weight > bay_limit:
        return ValidationResult(
            valid=False,
            message=(
                f"{assignment.cargo.cargo_id} exceeds "
                f"{assignment.bay.bay_id} capacity: "
                f"{cargo_weight:.1f} kg > "
                f"{bay_limit:.1f} kg."
            ),
        )

    return ValidationResult(
        valid=True,
        message=(
            f"{assignment.cargo.cargo_id} is within "
            f"{assignment.bay.bay_id} capacity."
        ),
    )


def validate_total_payload(
    aircraft: Aircraft,
    assignments: list[CargoAssignment],
) -> ValidationResult:
    """
    Check total payload against aircraft limit.
    """

    payload = calculate_total_payload(assignments)

    if payload > aircraft.max_payload_kg:
        return ValidationResult(
            valid=False,
            message=(
                f"Aircraft payload exceeded: "
                f"{payload:.1f} kg > "
                f"{aircraft.max_payload_kg:.1f} kg."
            ),
        )

    return ValidationResult(
        valid=True,
        message=(
            f"Total payload is within aircraft limit: "
            f"{payload:.1f} kg."
        ),
    )


def validate_cg_envelope(
    aircraft: Aircraft,
    assignments: list[CargoAssignment],
) -> ValidationResult:
    """
    Check whether calculated CG is inside the safe range.
    """

    cg = calculate_cg(assignments)

    if not aircraft.cg_min_m <= cg <= aircraft.cg_max_m:
        return ValidationResult(
            valid=False,
            message=(
                f"CG out of limits: {cg:.3f} m. "
                f"Allowed range is "
                f"{aircraft.cg_min_m:.3f} m to "
                f"{aircraft.cg_max_m:.3f} m."
            ),
        )

    return ValidationResult(
        valid=True,
        message=(
            f"CG is within safe limits: "
            f"{cg:.3f} m."
        ),
    )


def validate_lateral_balance(
    aircraft: Aircraft,
    assignments: list[CargoAssignment],
) -> ValidationResult:
    """
    Check left/right cargo imbalance.
    """

    imbalance = calculate_lateral_imbalance(
        assignments
    )

    if imbalance > aircraft.lateral_imbalance_limit_kg:
        return ValidationResult(
            valid=False,
            message=(
                f"Lateral imbalance too high: "
                f"{imbalance:.1f} kg > "
                f"{aircraft.lateral_imbalance_limit_kg:.1f} kg."
            ),
        )

    return ValidationResult(
        valid=True,
        message=(
            f"Lateral imbalance is acceptable: "
            f"{imbalance:.1f} kg."
        ),
    )

@dataclass
class SafetyReport:
    """
    Overall safety status for a cargo loading plan.
    """

    safe: bool
    cg_m: float
    total_payload_kg: float
    lateral_imbalance_kg: float
    checks: list[ValidationResult]


def validate_loading_plan(
    aircraft: Aircraft,
    assignments: list[CargoAssignment],
) -> SafetyReport:
    """
    Run all Phase 2 safety checks.
    """

    checks: list[ValidationResult] = []

    for assignment in assignments:
        checks.append(
            validate_bay_capacity(assignment)
        )

    checks.append(
        validate_total_payload(
            aircraft,
            assignments,
        )
    )

    checks.append(
        validate_cg_envelope(
            aircraft,
            assignments,
        )
    )

    checks.append(
        validate_lateral_balance(
            aircraft,
            assignments,
        )
    )

    return SafetyReport(
        safe=all(check.valid for check in checks),
        cg_m=calculate_cg(assignments),
        total_payload_kg=calculate_total_payload(
            assignments
        ),
        lateral_imbalance_kg=(
            calculate_lateral_imbalance(assignments)
        ),
        checks=checks,
    )