import json
from dataclasses import dataclass
from pathlib import Path

from engine.models import HazardClass


@dataclass
class HazardKnowledgeBase:
    """
    Stores simplified cargo separation rules used by AeroLoad-AI.
    """

    incompatible_pairs: set[frozenset[HazardClass]]

    def are_incompatible(
        self,
        first: HazardClass,
        second: HazardClass,
    ) -> bool:
        """
        Return True when two separation classes are incompatible.
        """

        pair = frozenset((first, second))

        return pair in self.incompatible_pairs


def load_hazard_rules(
    file_path: str | Path,
) -> HazardKnowledgeBase:
    """
    Load simplified hazard compatibility rules from JSON.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Hazard rule file not found: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    incompatible_pairs: set[
        frozenset[HazardClass]
    ] = set()

    for first, second in data["incompatible_pairs"]:
        incompatible_pairs.add(
            frozenset(
                (
                    HazardClass(first),
                    HazardClass(second),
                )
            )
        )

    return HazardKnowledgeBase(
        incompatible_pairs=incompatible_pairs
    )