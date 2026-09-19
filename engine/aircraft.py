import json
from dataclasses import dataclass
from pathlib import Path

from engine.models import BaySide, CargoBay

from dataclasses import dataclass

from engine.models import CargoBay


@dataclass
class Aircraft:
    """
    Represents an aircraft configuration used by AeroLoad-AI.
    """

    aircraft_id: str
    name: str

    max_payload_kg: float

    cg_min_m: float
    cg_max_m: float
    target_cg_m: float

    lateral_imbalance_limit_kg: float

    bays: list[CargoBay]

    def __post_init__(self):
        if not self.aircraft_id.strip():
            raise ValueError("Aircraft ID cannot be empty.")

        if not self.name.strip():
            raise ValueError("Aircraft name cannot be empty.")

        if self.max_payload_kg <= 0:
            raise ValueError(
                "Maximum aircraft payload must be greater than 0 kg."
            )

        if self.cg_min_m >= self.cg_max_m:
            raise ValueError(
                "Minimum CG must be smaller than maximum CG."
            )

        if not self.cg_min_m <= self.target_cg_m <= self.cg_max_m:
            raise ValueError(
                "Target CG must lie inside the permitted CG range."
            )

        if self.lateral_imbalance_limit_kg < 0:
            raise ValueError(
                "Lateral imbalance limit cannot be negative."
            )

        if not self.bays:
            raise ValueError(
                "Aircraft must contain at least one cargo bay."
            )

    def get_bay(self, bay_id: str) -> CargoBay | None:
        """
        Find a cargo bay by ID.
        """

        for bay in self.bays:
            if bay.bay_id == bay_id:
                return bay

        return None

def load_aircraft_from_json(file_path: str | Path) -> Aircraft:
    """
    Load an aircraft configuration from a JSON file.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Aircraft configuration file not found: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    bays = []

    for bay_data in data["bays"]:
        bay = CargoBay(
            bay_id=bay_data["bay_id"],
            max_weight_kg=float(bay_data["max_weight_kg"]),
            longitudinal_arm_m=float(
                bay_data["longitudinal_arm_m"]
            ),
            side=BaySide(bay_data["side"]),
            row=int(bay_data["row"]),
            adjacent_bays=bay_data.get(
                "adjacent_bays",
                []
            ),
        )

        bays.append(bay)

    cg_limits = data["cg_limits"]

    aircraft = Aircraft(
        aircraft_id=data["aircraft_id"],
        name=data["name"],
        max_payload_kg=float(data["max_payload_kg"]),
        cg_min_m=float(cg_limits["minimum_m"]),
        cg_max_m=float(cg_limits["maximum_m"]),
        target_cg_m=float(cg_limits["target_m"]),
        lateral_imbalance_limit_kg=float(
            data["lateral_imbalance_limit_kg"]
        ),
        bays=bays,
    )

    return aircraft