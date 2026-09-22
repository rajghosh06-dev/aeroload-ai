from io import BytesIO

from engine.aircraft import load_aircraft_from_json
from ui.state import configured_aircraft, import_manifest, manifest_from_rows, reorder_rows


def test_manifest_from_rows_rejects_case_insensitive_duplicate_ids():
    rows = [
        {"cargo_id": "P1", "name": "One", "weight_kg": 100, "category": "General", "hazard_class": "None", "priority": 1},
        {"cargo_id": "p1", "name": "Two", "weight_kg": 120, "category": "General", "hazard_class": "None", "priority": 1},
    ]
    items, errors = manifest_from_rows(rows)
    assert len(items) == 1
    assert any("duplicated" in error for error in errors)


def test_configured_aircraft_is_temporary_and_does_not_mutate_base():
    base = load_aircraft_from_json("data/aircraft.json")
    configured = configured_aircraft(
        base,
        max_payload_kg=3500,
        cg_min_m=-0.8,
        cg_max_m=0.9,
        target_cg_m=0.1,
        lateral_imbalance_limit_kg=250,
    )
    assert configured.max_payload_kg == 3500
    assert configured.target_cg_m == 0.1
    assert base.max_payload_kg == 4000
    assert base.target_cg_m == 0.0
    assert configured.bays is base.bays


def test_import_manifest_reports_missing_columns():
    rows, errors = import_manifest(BytesIO(b"cargo_id,name\nP1,Box\n"))
    assert rows == []
    assert errors and "missing required columns" in errors[0]


def test_reorder_rows_uses_drag_order_without_changing_values():
    rows = [
        {"cargo_id": "P1", "name": "One", "weight_kg": 100, "category": "General", "hazard_class": "None", "priority": 1},
        {"cargo_id": "P2", "name": "Two", "weight_kg": 120, "category": "General", "hazard_class": "None", "priority": 2},
    ]
    reordered = reorder_rows(rows, ["02 | P2 - Two", "01 | P1 - One"])
    assert [row["cargo_id"] for row in reordered] == ["P2", "P1"]
    assert reordered[0]["weight_kg"] == 120
