"""Interactive and AI-assisted planning logic for AeroLoad-AI."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from engine.aircraft import Aircraft
from engine.cg import calculate_cg, calculate_lateral_imbalance, calculate_total_payload
from engine.constraints import SafetyReport, validate_loading_plan
from engine.csp import AeroLoadCSP
from engine.knowledge_base import HazardKnowledgeBase
from engine.models import CargoAssignment, CargoItem


class BayOptionStatus(str, Enum):
    """Classification of an aircraft cargo bay for a candidate cargo item."""

    LEGAL = "LEGAL"
    ILLEGAL = "ILLEGAL"
    OCCUPIED = "OCCUPIED"


@dataclass
class BayOption:
    """Evaluation of one cargo bay for a specific cargo item."""

    bay_id: str
    status: BayOptionStatus
    reason: str
    css_class: str


@dataclass
class CargoDomainAnalysis:
    """CSP domain analysis showing consistent and blocked bay values."""

    cargo_id: str
    domain_size: int
    legal_bays: list[str]
    blocked_bays: dict[str, str]
    bay_options: dict[str, BayOption]


@dataclass
class ManualPlanStatus:
    """Status and physical summary of a manual cargo loading plan."""

    is_complete: bool
    assigned_count: int
    total_count: int
    occupied_bays: int
    total_bays: int
    is_valid: bool
    message: str
    violations: list[str]
    safety_report: SafetyReport | None = None
    cg_preview: float | None = None
    imbalance_preview: float | None = None
    payload_kg: float = 0.0


def evaluate_bay_options(
    csp: AeroLoadCSP,
    cargo_id: str,
    current_assignments: dict[str, str],
) -> CargoDomainAnalysis:
    """
    Evaluate every aircraft bay for the specified cargo item in the context
    of the current partial manual assignment.

    Demonstrates CSP variable-domain consistency:
    - Unary constraint: cargo weight <= bay capacity
    - Binary constraint 1: bay must not already be occupied
    - Binary constraint 2: adjacent bays must not hold hazard-incompatible cargo
    """
    cargo = csp.get_cargo(cargo_id)
    bay_options: dict[str, BayOption] = {}
    legal_bays: list[str] = []
    blocked_bays: dict[str, str] = {}

    for bay in csp.aircraft.bays:
        bay_id = bay.bay_id

        # Check if bay is occupied
        occupied_by: str | None = None
        for assigned_cargo_id, assigned_bay_id in current_assignments.items():
            if assigned_bay_id == bay_id:
                occupied_by = assigned_cargo_id
                break

        if occupied_by is not None:
            if occupied_by == cargo_id:
                reason = "Currently assigned to this bay"
            else:
                reason = f"Occupied by {occupied_by}"
            bay_options[bay_id] = BayOption(
                bay_id=bay_id,
                status=BayOptionStatus.OCCUPIED,
                reason=reason,
                css_class="bay-occupied",
            )
            blocked_bays[bay_id] = reason
            continue

        # Check unary capacity constraint (is bay in initial CSP domain?)
        if bay_id not in csp.domains.get(cargo_id, []):
            reason = (
                f"Weight ({cargo.weight_kg:,.0f} kg) exceeds "
                f"bay capacity ({bay.max_weight_kg:,.0f} kg)"
            )
            bay_options[bay_id] = BayOption(
                bay_id=bay_id,
                status=BayOptionStatus.ILLEGAL,
                reason=reason,
                css_class="bay-illegal",
            )
            blocked_bays[bay_id] = reason
            continue

        # Check binary constraints with all other currently assigned cargo
        hazard_conflict = False
        conflict_reason = ""

        for other_id, other_bay_id in current_assignments.items():
            if other_id == cargo_id:
                continue

            other_cargo = csp.get_cargo(other_id)
            other_bay = csp.get_bay(other_bay_id)

            if csp.knowledge_base.are_incompatible(
                cargo.hazard_class, other_cargo.hazard_class
            ) and (other_bay.bay_id in bay.adjacent_bays):
                hazard_conflict = True
                conflict_reason = (
                    f"{cargo.hazard_class.value} conflicts with "
                    f"{other_cargo.hazard_class.value} ({other_id}) in adjacent {other_bay_id}"
                )
                break

        if hazard_conflict:
            bay_options[bay_id] = BayOption(
                bay_id=bay_id,
                status=BayOptionStatus.ILLEGAL,
                reason=conflict_reason,
                css_class="bay-illegal",
            )
            blocked_bays[bay_id] = conflict_reason
        else:
            reason = "Placement valid; no constraint conflict"
            bay_options[bay_id] = BayOption(
                bay_id=bay_id,
                status=BayOptionStatus.LEGAL,
                reason=reason,
                css_class="bay-legal",
            )
            legal_bays.append(bay_id)

    return CargoDomainAnalysis(
        cargo_id=cargo_id,
        domain_size=len(legal_bays),
        legal_bays=legal_bays,
        blocked_bays=blocked_bays,
        bay_options=bay_options,
    )


def validate_manual_plan(
    aircraft: Aircraft,
    cargo_items: list[CargoItem],
    manual_assignments: dict[str, str],
    knowledge_base: HazardKnowledgeBase,
) -> ManualPlanStatus:
    """
    Validate a manual cargo loading plan.

    Distinguishes between:
    - Incomplete plan: validates individual bay capacities and hazard separation
      without falsely failing whole-aircraft CG limits.
    - Complete plan: validates all aircraft limits (payload, CG envelope, lateral imbalance,
      bay capacities, hazard separation).
    """
    cargo_by_id = {item.cargo_id: item for item in cargo_items}
    total_count = len(cargo_items)
    assigned_count = len(manual_assignments)
    total_bays = len(aircraft.bays)
    occupied_bays = len(set(manual_assignments.values()))

    violations: list[str] = []
    assignments: list[CargoAssignment] = []

    # 1. Validate assigned items exist and check bay capacity
    for cargo_id, bay_id in manual_assignments.items():
        cargo = cargo_by_id.get(cargo_id)
        bay = aircraft.get_bay(bay_id)

        if cargo is None:
            violations.append(f"Cargo '{cargo_id}' does not exist in manifest.")
            continue
        if bay is None:
            violations.append(f"Bay '{bay_id}' does not exist in aircraft.")
            continue

        if cargo.weight_kg > bay.max_weight_kg:
            violations.append(
                f"{cargo.cargo_id} ({cargo.weight_kg:,.0f} kg) exceeds "
                f"{bay.bay_id} capacity ({bay.max_weight_kg:,.0f} kg)."
            )

        assignments.append(CargoAssignment(cargo=cargo, bay=bay))

    # 2. Validate bay exclusivity (no shared bays)
    seen_bays: set[str] = set()
    for cargo_id, bay_id in manual_assignments.items():
        if bay_id in seen_bays:
            violations.append(f"Multiple cargo items assigned to bay {bay_id}.")
        seen_bays.add(bay_id)

    # 3. Validate hazard separation on currently placed items
    placed_ids = list(manual_assignments.keys())
    for i in range(len(placed_ids)):
        for j in range(i + 1, len(placed_ids)):
            id_a, id_b = placed_ids[i], placed_ids[j]
            cargo_a, cargo_b = cargo_by_id.get(id_a), cargo_by_id.get(id_b)
            if not cargo_a or not cargo_b:
                continue

            if knowledge_base.are_incompatible(cargo_a.hazard_class, cargo_b.hazard_class):
                bay_a = aircraft.get_bay(manual_assignments[id_a])
                bay_b = aircraft.get_bay(manual_assignments[id_b])
                if bay_a and bay_b and (bay_b.bay_id in bay_a.adjacent_bays):
                    violations.append(
                        f"Hazard separation violation: {cargo_a.cargo_id} ({cargo_a.hazard_class.value}) in {bay_a.bay_id} "
                        f"is adjacent to {cargo_b.cargo_id} ({cargo_b.hazard_class.value}) in {bay_b.bay_id}."
                    )

    payload_kg = calculate_total_payload(assignments) if assignments else 0.0

    # 4. Check whether plan is complete
    is_complete = total_count > 0 and assigned_count == total_count

    if is_complete:
        # Full validation through standard safety report
        safety_report = validate_loading_plan(aircraft, assignments)
        for check in safety_report.checks:
            if not check.valid and check.message not in violations:
                violations.append(check.message)

        is_safe = safety_report.safe and len(violations) == 0
        return ManualPlanStatus(
            is_complete=True,
            assigned_count=assigned_count,
            total_count=total_count,
            occupied_bays=occupied_bays,
            total_bays=total_bays,
            is_valid=is_safe,
            message=(
                "Complete manual plan passes all simulation safety checks."
                if is_safe
                else f"Complete manual plan violates aircraft safety constraints ({len(violations)} issue{'s' if len(violations) != 1 else ''})."
            ),
            violations=violations,
            safety_report=safety_report,
            cg_preview=safety_report.cg_m,
            imbalance_preview=safety_report.lateral_imbalance_kg,
            payload_kg=payload_kg,
        )

    # Incomplete plan
    cg_preview: float | None = None
    imbalance_preview: float | None = None
    if assignments and payload_kg > 0:
        try:
            cg_preview = calculate_cg(assignments)
            imbalance_preview = calculate_lateral_imbalance(assignments)
        except ValueError:
            pass

    is_valid = len(violations) == 0
    if not is_valid:
        message = f"Violations detected ({len(violations)} constraint issue{'s' if len(violations) != 1 else ''})."
    elif assigned_count == 0:
        message = "No cargo placed yet. Select cargo to begin manual planning."
    else:
        message = f"Current placements are constraint-consistent ({assigned_count}/{total_count} assigned)."

    return ManualPlanStatus(
        is_complete=False,
        assigned_count=assigned_count,
        total_count=total_count,
        occupied_bays=occupied_bays,
        total_bays=total_bays,
        is_valid=is_valid,
        message=message,
        violations=violations,
        safety_report=None,
        cg_preview=cg_preview,
        imbalance_preview=imbalance_preview,
        payload_kg=payload_kg,
    )


def reconcile_manual_assignments(
    manual_assignments: dict[str, str],
    current_cargo_ids: set[str],
    current_bay_ids: set[str],
) -> dict[str, str]:
    """
    Remove any manual assignments referencing cargo items or bays
    that no longer exist after scenario edits.
    """
    return {
        cargo_id: bay_id
        for cargo_id, bay_id in manual_assignments.items()
        if cargo_id in current_cargo_ids and bay_id in current_bay_ids
    }


def assign_cargo_manually(
    manual_assignments: dict[str, str],
    cargo_id: str,
    bay_id: str,
) -> dict[str, str]:
    """
    Assign a cargo item to a bay, displacing any other cargo already in that bay.
    """
    updated = manual_assignments.copy()
    # If another cargo is in this bay, displace it
    for other_id, assigned_bay in list(updated.items()):
        if assigned_bay == bay_id and other_id != cargo_id:
            del updated[other_id]

    updated[cargo_id] = bay_id
    return updated


def unassign_cargo_manually(
    manual_assignments: dict[str, str],
    cargo_id: str,
) -> dict[str, str]:
    """Unassign one cargo item from its currently placed bay."""
    updated = manual_assignments.copy()
    updated.pop(cargo_id, None)
    return updated


def clear_manual_assignments() -> dict[str, str]:
    """Reset all manual placements."""
    return {}
