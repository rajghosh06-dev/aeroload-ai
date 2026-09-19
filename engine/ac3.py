from collections import deque
from dataclasses import dataclass

from engine.csp import AeroLoadCSP


@dataclass
class AC3Result:
    """
    Result produced by AC-3 constraint propagation.
    """

    consistent: bool

    domains: dict[str, list[str]]

    values_pruned: int
    arcs_processed: int


def revise(
    csp: AeroLoadCSP,
    domains: dict[str, list[str]],
    xi: str,
    xj: str,
) -> int:
    """
    Revise Xi's domain with respect to Xj.

    A value is removed from Xi when no value
    remaining in Xj satisfies the binary
    constraints between Xi and Xj.

    Returns:
        Number of values removed.
    """

    removed_values: list[str] = []

    for value_i in domains[xi]:
        supported = False

        for value_j in domains[xj]:
            if csp.are_pairwise_compatible(
                xi,
                value_i,
                xj,
                value_j,
            ):
                supported = True
                break

        if not supported:
            removed_values.append(
                value_i
            )

    for value in removed_values:
        domains[xi].remove(
            value
        )

    return len(
        removed_values
    )


def ac3(
    csp: AeroLoadCSP,
) -> AC3Result:
    """
    Apply AC-3 constraint propagation.

    The original CSP domains are not modified.
    AC-3 operates on a copy and returns the
    resulting domains.
    """

    domains = {
        cargo_id: values.copy()
        for cargo_id, values
        in csp.domains.items()
    }

    variables = list(
        domains.keys()
    )

    queue: deque[
        tuple[str, str]
    ] = deque(
        (xi, xj)
        for xi in variables
        for xj in variables
        if xi != xj
    )

    values_pruned = 0
    arcs_processed = 0

    while queue:
        xi, xj = queue.popleft()

        arcs_processed += 1

        removed = revise(
            csp,
            domains,
            xi,
            xj,
        )

        if removed > 0:
            values_pruned += removed

            # Domain wipe-out:
            # CSP is inconsistent.
            if not domains[xi]:
                return AC3Result(
                    consistent=False,
                    domains=domains,
                    values_pruned=values_pruned,
                    arcs_processed=arcs_processed,
                )

            # Xi changed, so every incoming
            # relationship Xk -> Xi must
            # be reconsidered.
            for xk in variables:
                if (
                    xk != xi
                    and xk != xj
                ):
                    queue.append(
                        (xk, xi)
                    )

    return AC3Result(
        consistent=True,
        domains=domains,
        values_pruned=values_pruned,
        arcs_processed=arcs_processed,
    )