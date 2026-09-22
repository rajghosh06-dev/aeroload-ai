"""Adapters between Streamlit widgets and AeroLoad domain objects."""

from __future__ import annotations

from dataclasses import replace

import pandas as pd

from engine.aircraft import Aircraft
from engine.models import CargoCategory, CargoItem, HazardClass

MANIFEST_COLUMNS = ["cargo_id", "name", "weight_kg", "category", "hazard_class", "priority"]


def cargo_rows(cargo_items: list[CargoItem]) -> list[dict[str, object]]:
    """Convert cargo objects to rows suitable for ``st.data_editor``."""
    return [
        {"cargo_id": item.cargo_id, "name": item.name, "weight_kg": item.weight_kg,
         "category": item.category.value, "hazard_class": item.hazard_class.value,
         "priority": item.priority}
        for item in cargo_items
    ]


def normalise_rows(rows: object) -> list[dict[str, object]]:
    frame = pd.DataFrame(rows).reindex(columns=MANIFEST_COLUMNS)
    return frame.where(pd.notna(frame), "").to_dict("records")


def reorder_rows(rows: object, ordered_labels: list[str]) -> list[dict[str, object]]:
    """Return manifest rows in the order emitted by the drag-and-drop control."""
    normalised = normalise_rows(rows)
    labels = [f"{index + 1:02d} | {row['cargo_id']} - {row['name']}" for index, row in enumerate(normalised)]
    by_label = dict(zip(labels, normalised, strict=True))
    if len(ordered_labels) != len(labels) or set(ordered_labels) != set(labels):
        return normalised
    return [by_label[label] for label in ordered_labels]


def manifest_from_rows(rows: object, allow_empty: bool = False) -> tuple[list[CargoItem], list[str]]:
    """Validate editor rows and build fresh ``CargoItem`` objects."""
    items: list[CargoItem] = []
    errors: list[str] = []
    seen: set[str] = set()
    for index, row in enumerate(normalise_rows(rows), start=1):
        if not any(str(value).strip() for value in row.values()):
            continue
        cargo_id = str(row["cargo_id"]).strip()
        normalized_id = cargo_id.casefold()
        if not cargo_id:
            errors.append(f"Row {index}: cargo ID is required.")
            continue
        if normalized_id in seen:
            errors.append(f"Row {index}: cargo ID '{cargo_id}' is duplicated.")
            continue
        seen.add(normalized_id)
        try:
            priority_value = float(row["priority"])
            if not priority_value.is_integer():
                raise ValueError("priority must be a whole number.")
            items.append(CargoItem(
                cargo_id=cargo_id,
                name=str(row["name"]).strip(),
                weight_kg=float(row["weight_kg"]),
                category=CargoCategory(str(row["category"])),
                hazard_class=HazardClass(str(row["hazard_class"])),
                priority=int(priority_value),
            ))
        except (TypeError, ValueError) as error:
            errors.append(f"Row {index}: {error}")
    if not items and not errors and not allow_empty:
        errors.append("Add at least one cargo item before running the solver.")
    return items, errors


def validate_manifest_for_aircraft(items: list[CargoItem], aircraft: Aircraft) -> list[str]:
    """Return actionable preflight errors before invoking the CSP solver."""
    errors: list[str] = []
    if not items:
        return []
    if len(items) > len(aircraft.bays):
        errors.append(f"The manifest has {len(items)} items but the aircraft has only {len(aircraft.bays)} cargo bays.")
    payload = sum(item.weight_kg for item in items)
    if payload > aircraft.max_payload_kg:
        errors.append(f"Manifest payload is {payload:,.0f} kg, exceeding the configured limit of {aircraft.max_payload_kg:,.0f} kg.")
    largest_bay = max(bay.max_weight_kg for bay in aircraft.bays)
    for item in items:
        if item.weight_kg > largest_bay:
            errors.append(f"{item.cargo_id} weighs {item.weight_kg:,.0f} kg; no bay can accept more than {largest_bay:,.0f} kg.")
    return errors


def empty_manifest_rows() -> list[dict[str, object]]:
    """Return an empty list of manifest rows."""
    return []


def manifest_csv(rows: object) -> bytes:
    return pd.DataFrame(normalise_rows(rows), columns=MANIFEST_COLUMNS).to_csv(index=False).encode("utf-8")


def import_manifest(uploaded: object) -> tuple[list[dict[str, object]], list[str]]:
    try:
        frame = pd.read_csv(uploaded)
    except Exception as error:
        return [], [f"Could not read the CSV: {error}"]
    missing = [column for column in MANIFEST_COLUMNS if column not in frame.columns]
    if missing:
        return [], ["CSV is missing required columns: " + ", ".join(missing)]
    rows = normalise_rows(frame)
    _, errors = manifest_from_rows(rows)
    return rows, errors


def configured_aircraft(base: Aircraft, *, max_payload_kg: float, cg_min_m: float,
                        cg_max_m: float, target_cg_m: float,
                        lateral_imbalance_limit_kg: float) -> Aircraft:
    """Return an in-memory aircraft configuration; JSON remains untouched."""
    return replace(base, max_payload_kg=float(max_payload_kg), cg_min_m=float(cg_min_m),
                   cg_max_m=float(cg_max_m), target_cg_m=float(target_cg_m),
                   lateral_imbalance_limit_kg=float(lateral_imbalance_limit_kg))
