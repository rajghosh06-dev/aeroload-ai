"""Curated classroom-sized scenario templates for the data workspace."""

from __future__ import annotations


def scenario_templates(sample_rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    """Return small, valid manifests that demonstrate different CSP behavior."""
    return {
        "Mixed training load": {
            "description": "The original six-item demonstration with general, food, fragile and hazardous cargo.",
            "rows": sample_rows,
        },
        "Relief and medical mission": {
            "description": "Priority-focused supplies with food, medical equipment and one controlled battery shipment.",
            "rows": [
                {"cargo_id": "R1", "name": "Emergency Food Packs", "weight_kg": 360.0, "category": "Food", "hazard_class": "Food", "priority": 3},
                {"cargo_id": "R2", "name": "Medical Diagnostic Kits", "weight_kg": 210.0, "category": "Fragile", "hazard_class": "None", "priority": 3},
                {"cargo_id": "R3", "name": "Portable Generator", "weight_kg": 430.0, "category": "General", "hazard_class": "None", "priority": 2},
                {"cargo_id": "R4", "name": "Battery Power Modules", "weight_kg": 260.0, "category": "Hazardous", "hazard_class": "Lithium Battery", "priority": 2},
                {"cargo_id": "R5", "name": "Shelter Equipment", "weight_kg": 390.0, "category": "General", "hazard_class": "None", "priority": 1},
            ],
        },
        "Hazmat separation exercise": {
            "description": "A compact teaching scenario designed to expose adjacency and knowledge-base constraints.",
            "rows": [
                {"cargo_id": "H1", "name": "Lithium Battery Cases", "weight_kg": 280.0, "category": "Hazardous", "hazard_class": "Lithium Battery", "priority": 2},
                {"cargo_id": "H2", "name": "Flammable Solvent Drum", "weight_kg": 240.0, "category": "Hazardous", "hazard_class": "Flammable", "priority": 2},
                {"cargo_id": "H3", "name": "Food Supply Pallet", "weight_kg": 330.0, "category": "Food", "hazard_class": "Food", "priority": 1},
                {"cargo_id": "H4", "name": "Toxic Lab Material", "weight_kg": 190.0, "category": "Hazardous", "hazard_class": "Toxic", "priority": 3},
                {"cargo_id": "H5", "name": "Protective Equipment", "weight_kg": 310.0, "category": "General", "hazard_class": "None", "priority": 2},
            ],
        },
    }
