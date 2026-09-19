from dataclasses import dataclass, field

from engine.aircraft import Aircraft
from engine.knowledge_base import HazardKnowledgeBase
from engine.models import CargoBay, CargoItem


@dataclass
class AeroLoadCSP:
    """
    Constraint Satisfaction Problem representation
    for aircraft cargo placement.

    Variables:
        Cargo item IDs.

    Domains:
        Candidate cargo bays for each cargo item.

    Assignment:
        Mapping from cargo ID to bay ID.
    """

    aircraft: Aircraft
    cargo_items: list[CargoItem]
    knowledge_base: HazardKnowledgeBase

    domains: dict[str, list[str]] = field(
        init=False
    )

    def __post_init__(self):
        self.domains = self._build_initial_domains()

    def _build_initial_domains(
        self,
    ) -> dict[str, list[str]]:
        """
        Build initial bay domains for all cargo items.

        Bays that cannot physically support cargo weight
        are removed immediately.
        """

        domains: dict[str, list[str]] = {}

        for cargo in self.cargo_items:
            valid_bays: list[str] = []

            for bay in self.aircraft.bays:
                if cargo.weight_kg <= bay.max_weight_kg:
                    valid_bays.append(
                        bay.bay_id
                    )

            domains[cargo.cargo_id] = valid_bays

        return domains

    def get_cargo(
        self,
        cargo_id: str,
    ) -> CargoItem:
        """
        Retrieve cargo by ID.
        """

        for cargo in self.cargo_items:
            if cargo.cargo_id == cargo_id:
                return cargo

        raise ValueError(
            f"Cargo item '{cargo_id}' does not exist."
        )

    def get_bay(
        self,
        bay_id: str,
    ) -> CargoBay:
        """
        Retrieve a required aircraft cargo bay.
        """

        return self.aircraft.require_bay(
            bay_id
        )

    def are_pairwise_compatible(
        self,
        first_cargo_id: str,
        first_bay_id: str,
        second_cargo_id: str,
        second_bay_id: str,
    ) -> bool:
        """
        Check whether two hypothetical cargo-to-bay
        assignments satisfy the binary CSP constraints.

        This method is used by AC-3.

        Binary constraints currently include:
        1. Two cargo items cannot occupy the same bay.
        2. Hazard-incompatible cargo cannot occupy
           adjacent bays.
        """

        first_cargo = self.get_cargo(
            first_cargo_id
        )

        second_cargo = self.get_cargo(
            second_cargo_id
        )

        first_bay = self.get_bay(
            first_bay_id
        )

        second_bay = self.get_bay(
            second_bay_id
        )

        # Constraint 1:
        # Two cargo items cannot use the same bay.
        if first_bay_id == second_bay_id:
            return False

        # Constraint 2:
        # Hazard-incompatible cargo cannot
        # occupy adjacent bays.
        incompatible = (
            self.knowledge_base.are_incompatible(
                first_cargo.hazard_class,
                second_cargo.hazard_class,
            )
        )

        adjacent = (
            second_bay.bay_id
            in first_bay.adjacent_bays
        )

        if incompatible and adjacent:
            return False

        return True

    def is_consistent(
        self,
        cargo_id: str,
        bay_id: str,
        assignment: dict[str, str],
    ) -> bool:
        """
        Check whether assigning cargo_id to bay_id
        is consistent with the current partial assignment.
        """

        cargo = self.get_cargo(
            cargo_id
        )

        bay = self.get_bay(
            bay_id
        )

        # Constraint 1:
        # Cargo must not exceed bay capacity.
        if cargo.weight_kg > bay.max_weight_kg:
            return False

        # Constraint 2:
        # No two cargo items may occupy the same bay.
        if bay_id in assignment.values():
            return False

        # Constraint 3:
        # Hazard-incompatible cargo cannot occupy
        # adjacent bays.
        for (
            other_cargo_id,
            other_bay_id,
        ) in assignment.items():

            other_cargo = self.get_cargo(
                other_cargo_id
            )

            other_bay = self.get_bay(
                other_bay_id
            )

            incompatible = (
                self.knowledge_base.are_incompatible(
                    cargo.hazard_class,
                    other_cargo.hazard_class,
                )
            )

            adjacent = (
                other_bay.bay_id
                in bay.adjacent_bays
            )

            if incompatible and adjacent:
                return False

        return True