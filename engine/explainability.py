from dataclasses import dataclass

from engine.backtracking import (
    BacktrackingResult,
    assignment_to_cargo_assignments,
)
from engine.constraints import (
    validate_loading_plan,
)
from engine.csp import AeroLoadCSP
from engine.local_search import LocalSearchResult


@dataclass
class ExplanationItem:
    """
    One human-readable explanation produced
    by the AeroLoad-AI reasoning layer.
    """

    category: str
    status: str
    message: str


@dataclass
class ExplanationReport:
    """
    Complete explainability report for a loading plan.
    """

    safe: bool
    items: list[ExplanationItem]


def explain_loading_plan(
    csp: AeroLoadCSP,
    assignment: dict[str, str],
) -> ExplanationReport:
    """
    Generate human-readable explanations for
    a complete cargo loading plan.
    """

    items: list[ExplanationItem] = []

    cargo_assignments = (
        assignment_to_cargo_assignments(
            csp,
            assignment,
        )
    )

    safety_report = validate_loading_plan(
        csp.aircraft,
        cargo_assignments,
    )

    # -----------------------------------------
    # Bay-capacity explanations
    # -----------------------------------------

    for cargo_id, bay_id in assignment.items():
        cargo = csp.get_cargo(
            cargo_id
        )

        bay = csp.get_bay(
            bay_id
        )

        if cargo.weight_kg <= bay.max_weight_kg:
            items.append(
                ExplanationItem(
                    category="Bay Capacity",
                    status="PASS",
                    message=(
                        f"{cargo_id} ({cargo.weight_kg:.1f} kg) "
                        f"is within {bay_id}'s "
                        f"{bay.max_weight_kg:.1f} kg capacity."
                    ),
                )
            )
        else:
            items.append(
                ExplanationItem(
                    category="Bay Capacity",
                    status="FAIL",
                    message=(
                        f"{cargo_id} exceeds "
                        f"{bay_id}'s weight capacity."
                    ),
                )
            )

    # -----------------------------------------
    # Hazard-separation explanations
    # -----------------------------------------

    cargo_ids = list(
        assignment.keys()
    )

    for i in range(len(cargo_ids)):
        for j in range(
            i + 1,
            len(cargo_ids),
        ):
            first_id = cargo_ids[i]
            second_id = cargo_ids[j]

            first_cargo = csp.get_cargo(
                first_id
            )

            second_cargo = csp.get_cargo(
                second_id
            )

            incompatible = (
                csp.knowledge_base.are_incompatible(
                    first_cargo.hazard_class,
                    second_cargo.hazard_class,
                )
            )

            if not incompatible:
                continue

            first_bay = csp.get_bay(
                assignment[first_id]
            )

            second_bay = csp.get_bay(
                assignment[second_id]
            )

            adjacent = (
                second_bay.bay_id
                in first_bay.adjacent_bays
            )

            if adjacent:
                items.append(
                    ExplanationItem(
                        category="Hazard Separation",
                        status="FAIL",
                        message=(
                            f"{first_id} and {second_id} "
                            f"contain incompatible hazard classes "
                            f"and occupy adjacent bays "
                            f"{first_bay.bay_id} and "
                            f"{second_bay.bay_id}."
                        ),
                    )
                )
            else:
                items.append(
                    ExplanationItem(
                        category="Hazard Separation",
                        status="PASS",
                        message=(
                            f"{first_id} and {second_id} "
                            f"have incompatible hazard classes "
                            f"but are safely separated in "
                            f"{first_bay.bay_id} and "
                            f"{second_bay.bay_id}."
                        ),
                    )
                )

    # -----------------------------------------
    # Payload explanation
    # -----------------------------------------

    payload_status = (
        "PASS"
        if safety_report.total_payload_kg
        <= csp.aircraft.max_payload_kg
        else "FAIL"
    )

    items.append(
        ExplanationItem(
            category="Total Payload",
            status=payload_status,
            message=(
                f"Total payload is "
                f"{safety_report.total_payload_kg:.1f} kg "
                f"against a maximum of "
                f"{csp.aircraft.max_payload_kg:.1f} kg."
            ),
        )
    )

    # -----------------------------------------
    # CG explanation
    # -----------------------------------------

    cg_inside = (
        csp.aircraft.cg_min_m
        <= safety_report.cg_m
        <= csp.aircraft.cg_max_m
    )

    items.append(
        ExplanationItem(
            category="Center of Gravity",
            status=(
                "PASS"
                if cg_inside
                else "FAIL"
            ),
            message=(
                f"Aircraft CG is "
                f"{safety_report.cg_m:.3f} m. "
                f"Permitted envelope is "
                f"[{csp.aircraft.cg_min_m:.3f}, "
                f"{csp.aircraft.cg_max_m:.3f}] m."
            ),
        )
    )

    # -----------------------------------------
    # Lateral-balance explanation
    # -----------------------------------------

    balance_inside = (
        safety_report.lateral_imbalance_kg
        <= csp.aircraft.lateral_imbalance_limit_kg
    )

    items.append(
        ExplanationItem(
            category="Lateral Balance",
            status=(
                "PASS"
                if balance_inside
                else "FAIL"
            ),
            message=(
                f"Lateral imbalance is "
                f"{safety_report.lateral_imbalance_kg:.1f} kg "
                f"against a limit of "
                f"{csp.aircraft.lateral_imbalance_limit_kg:.1f} kg."
            ),
        )
    )

    return ExplanationReport(
        safe=safety_report.safe,
        items=items,
    )


def explain_optimization(
    result: LocalSearchResult,
) -> list[ExplanationItem]:
    """
    Explain how local search improved the
    loading plan.
    """

    items: list[ExplanationItem] = []

    items.append(
        ExplanationItem(
            category="Optimization",
            status=(
                "IMPROVED"
                if result.improved
                else "UNCHANGED"
            ),
            message=(
                f"Optimization score changed from "
                f"{result.initial_quality.score:.4f} "
                f"to {result.final_quality.score:.4f}."
            ),
        )
    )

    items.append(
        ExplanationItem(
            category="CG Optimization",
            status=(
                "IMPROVED"
                if (
                    result.final_quality.cg_deviation_m
                    < result.initial_quality.cg_deviation_m
                )
                else "UNCHANGED"
            ),
            message=(
                f"CG deviation from target changed from "
                f"{result.initial_quality.cg_deviation_m:.3f} m "
                f"to "
                f"{result.final_quality.cg_deviation_m:.3f} m."
            ),
        )
    )

    initial_imbalance = (
        result.initial_quality
        .lateral_imbalance_kg
    )

    final_imbalance = (
        result.final_quality
        .lateral_imbalance_kg
    )

    if final_imbalance > initial_imbalance:
        balance_status = "TRADEOFF"

        balance_message = (
            f"Lateral imbalance increased from "
            f"{initial_imbalance:.1f} kg to "
            f"{final_imbalance:.1f} kg, "
            f"but the final plan remains within "
            f"the aircraft safety limit."
        )

    elif final_imbalance < initial_imbalance:
        balance_status = "IMPROVED"

        balance_message = (
            f"Lateral imbalance improved from "
            f"{initial_imbalance:.1f} kg to "
            f"{final_imbalance:.1f} kg."
        )

    else:
        balance_status = "UNCHANGED"

        balance_message = (
            f"Lateral imbalance remained at "
            f"{final_imbalance:.1f} kg."
        )

    items.append(
        ExplanationItem(
            category="Balance Tradeoff",
            status=balance_status,
            message=balance_message,
        )
    )

    for step in result.steps:
        items.append(
            ExplanationItem(
                category="Optimization Step",
                status="ACCEPTED",
                message=(
                    f"Iteration {step.iteration}: "
                    f"{step.move_type} — "
                    f"{step.description}. "
                    f"Score improved from "
                    f"{step.score_before:.4f} "
                    f"to {step.score_after:.4f}."
                ),
            )
        )

    return items