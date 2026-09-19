from engine.csp import AeroLoadCSP


def select_unassigned_variable_mrv(
    csp: AeroLoadCSP,
    assignment: dict[str, str],
) -> str:
    """
    Select an unassigned cargo item using the
    Minimum Remaining Values (MRV) heuristic.

    MRV chooses the cargo item that currently has
    the fewest legal bay choices.
    """

    unassigned = [
        cargo.cargo_id
        for cargo in csp.cargo_items
        if cargo.cargo_id not in assignment
    ]

    if not unassigned:
        raise ValueError(
            "No unassigned variables remain."
        )

    def legal_value_count(
        cargo_id: str,
    ) -> int:
        """
        Count how many bay values are currently legal
        for the given cargo item.
        """

        count = 0

        for bay_id in csp.domains[cargo_id]:
            if csp.is_consistent(
                cargo_id,
                bay_id,
                assignment,
            ):
                count += 1

        return count

    return min(
        unassigned,
        key=legal_value_count,
    )
def order_domain_values_lcv(
    csp: AeroLoadCSP,
    cargo_id: str,
    assignment: dict[str, str],
) -> list[str]:
    """
    Order candidate bay values using the
    Least Constraining Value (LCV) heuristic.

    Values that eliminate fewer legal choices
    for other unassigned cargo items are tried first.
    """

    candidate_bays = [
        bay_id
        for bay_id in csp.domains[cargo_id]
        if csp.is_consistent(
            cargo_id,
            bay_id,
            assignment,
        )
    ]

    def elimination_count(
        bay_id: str,
    ) -> int:
        temporary_assignment = assignment.copy()
        temporary_assignment[cargo_id] = bay_id

        eliminated = 0

        for other_cargo in csp.cargo_items:
            other_id = other_cargo.cargo_id

            if other_id in temporary_assignment:
                continue

            for other_bay_id in csp.domains[other_id]:
                before_valid = csp.is_consistent(
                    other_id,
                    other_bay_id,
                    assignment,
                )

                after_valid = csp.is_consistent(
                    other_id,
                    other_bay_id,
                    temporary_assignment,
                )

                if before_valid and not after_valid:
                    eliminated += 1

        return eliminated

    return sorted(
        candidate_bays,
        key=elimination_count,
    )