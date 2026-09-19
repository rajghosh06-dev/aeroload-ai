from dataclasses import dataclass, field
from enum import Enum

class CargoCategory(str, Enum):
    """
    High-level Categoru of a cargo item.
    """
    GENERAL = "General"
    FRAGILE = "Fragile"
    FOOD = "Food"
    HAZARDOUS = "Hazardous"

class HazardClass(str, Enum):
    """
    Simplified hazard classification used by Aeroload AI.
    This is an educational classification and is not intended to replace official ICAO/IATA dangerous-goods regulations.
    """
    NONE = "None"
    LITHIUM_BATTERY = "Lithium Battery"
    FLAMMABLE = "Flammable"
    TOXIC = "Toxic"
    BIOHAZARD = "Biohazard"
    OXIDIZER = "Oxidizer"
    FOOD = "Food"

class BaySide(str, Enum):
    """
    Physical side of the aircraft cargo bay.
    """
    LEFT = "Left"
    RIGHT = "Right"
    CENTER = "Center"

@dataclass
class CargoItem:
    """
    Represents one cargo pallet/package handled by AeroLoad-AI.
    """

    cargo_id: str
    name: str
    weight_kg: float

    category: CargoCategory = CargoCategory.GENERAL
    hazard_class: HazardClass = HazardClass.NONE

    priority: int = 1

    def __post_init__(self):
        if not self.cargo_id.strip():
            raise ValueError("Cargo ID cannot be empty.")

        if not self.name.strip():
            raise ValueError("Cargo name cannot be empty.")

        if self.weight_kg <= 0:
            raise ValueError("Cargo weight must be greater than 0 kg.")

        if self.priority < 1:
            raise ValueError("Cargo priority must be at least 1.")

@dataclass
class CargoBay:
    """
    Represents one aircraft cargo bay.
    """

    bay_id: str
    max_weight_kg: float

    longitudinal_arm_m: float
    side: BaySide

    row: int

    adjacent_bays: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.bay_id.strip():
            raise ValueError("Bay ID cannot be empty.")

        if self.max_weight_kg <= 0:
            raise ValueError(
                "Maximum bay weight must be greater than 0 kg."
            )

        if self.row < 1:
            raise ValueError("Bay row must be at least 1.")

@dataclass
class CargoAssignment:
    """
    Represents the placement of one cargo item into one cargo bay.
    """

    cargo: CargoItem
    bay: CargoBay