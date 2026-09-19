import csv
from pathlib import Path

from engine.models import (
    CargoCategory,
    CargoItem,
    HazardClass,
)


def load_cargo_from_csv(
    file_path: str | Path
) -> list[CargoItem]:
    """
    Load cargo items from a CSV file.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Cargo data file not found: {path}"
        )

    cargo_items = []

    with path.open(
        "r",
        encoding="utf-8",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:
            cargo = CargoItem(
                cargo_id=row["cargo_id"],
                name=row["name"],
                weight_kg=float(row["weight_kg"]),
                category=CargoCategory(
                    row["category"]
                ),
                hazard_class=HazardClass(
                    row["hazard_class"]
                ),
                priority=int(row["priority"]),
            )

            cargo_items.append(cargo)

    return cargo_items