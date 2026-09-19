from engine.models import BaySide, CargoAssignment


def calculate_total_payload(
    assignments: list[CargoAssignment]
) -> float:
    """
    Calculate the total assigned cargo weight.
    """

    return sum(
        assignment.cargo.weight_kg
        for assignment in assignments
    )


def calculate_total_moment(
    assignments: list[CargoAssignment]
) -> float:
    """
    Calculate total longitudinal moment.

    Moment = weight × longitudinal arm
    """

    return sum(
        assignment.cargo.weight_kg
        * assignment.bay.longitudinal_arm_m
        for assignment in assignments
    )


def calculate_cg(
    assignments: list[CargoAssignment]
) -> float:
    """
    Calculate longitudinal cargo center of gravity.

    CG = total moment / total payload
    """

    total_payload = calculate_total_payload(
        assignments
    )

    if total_payload == 0:
        raise ValueError(
            "Cannot calculate CG with zero total payload."
        )

    total_moment = calculate_total_moment(
        assignments
    )

    return total_moment / total_payload


def calculate_side_weights(
    assignments: list[CargoAssignment]
) -> tuple[float, float]:
    """
    Calculate total cargo weight on the left and right sides.
    """

    left_weight = 0.0
    right_weight = 0.0

    for assignment in assignments:
        if assignment.bay.side == BaySide.LEFT:
            left_weight += assignment.cargo.weight_kg

        elif assignment.bay.side == BaySide.RIGHT:
            right_weight += assignment.cargo.weight_kg

    return left_weight, right_weight


def calculate_lateral_imbalance(
    assignments: list[CargoAssignment]
) -> float:
    """
    Return absolute left/right cargo weight imbalance.
    """

    left_weight, right_weight = calculate_side_weights(
        assignments
    )

    return abs(left_weight - right_weight)