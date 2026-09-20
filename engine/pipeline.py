from dataclasses import dataclass

from engine.backtracking import (
    BacktrackingResult,
    smart_backtracking_search,
)
from engine.csp import AeroLoadCSP
from engine.explainability import (
    ExplanationItem,
    ExplanationReport,
    explain_loading_plan,
    explain_optimization,
)
from engine.local_search import (
    LocalSearchResult,
    optimize_loading_plan,
)


@dataclass
class AeroLoadAnalysisResult:
    """
    Unified result returned by the complete
    AeroLoad-AI reasoning pipeline.
    """

    solved: bool
    optimized: bool
    safe: bool

    solver_result: BacktrackingResult

    optimization_result: LocalSearchResult | None

    loading_explanation: ExplanationReport | None

    optimization_explanations: list[ExplanationItem]

    final_assignment: dict[str, str] | None

    message: str


def analyze_loading_problem(
    csp: AeroLoadCSP,
    *,
    optimize: bool = True,
    max_optimization_iterations: int = 50,
) -> AeroLoadAnalysisResult:
    """
    Run the complete AeroLoad-AI pipeline.

    Pipeline:
        1. AC-3 + MRV + LCV + backtracking
        2. Aircraft safety validation
        3. Optional local-search optimization
        4. Human-readable explainability

    Returns one structured result suitable
    for CLI, GUI and future report generation.
    """

    solver_result = smart_backtracking_search(
        csp
    )

    initial_assignment = (
        solver_result.assignment
    )

    if initial_assignment is None:
        return AeroLoadAnalysisResult(
            solved=False,
            optimized=False,
            safe=False,
            solver_result=solver_result,
            optimization_result=None,
            loading_explanation=None,
            optimization_explanations=[],
            final_assignment=None,
            message=(
                "No safe loading solution could "
                "be found for the current cargo set."
            ),
        )

    # -------------------------------------------------
    # Optimization disabled
    # -------------------------------------------------

    if not optimize:
        loading_explanation = (
            explain_loading_plan(
                csp,
                initial_assignment,
            )
        )

        return AeroLoadAnalysisResult(
            solved=True,
            optimized=False,
            safe=loading_explanation.safe,
            solver_result=solver_result,
            optimization_result=None,
            loading_explanation=(
                loading_explanation
            ),
            optimization_explanations=[],
            final_assignment=(
                initial_assignment.copy()
            ),
            message=(
                "A safe loading solution was found."
            ),
        )

    # -------------------------------------------------
    # Local-search optimization
    # -------------------------------------------------

    optimization_result = (
        optimize_loading_plan(
            csp,
            initial_assignment,
            max_iterations=(
                max_optimization_iterations
            ),
        )
    )

    final_assignment = (
        optimization_result
        .best_assignment
        .copy()
    )

    loading_explanation = (
        explain_loading_plan(
            csp,
            final_assignment,
        )
    )

    optimization_explanations = (
        explain_optimization(
            optimization_result
        )
    )

    return AeroLoadAnalysisResult(
        solved=True,
        optimized=(
            optimization_result.improved
        ),
        safe=loading_explanation.safe,
        solver_result=solver_result,
        optimization_result=(
            optimization_result
        ),
        loading_explanation=(
            loading_explanation
        ),
        optimization_explanations=(
            optimization_explanations
        ),
        final_assignment=(
            final_assignment
        ),
        message=(
            "A safe loading solution was found "
            "and evaluated by the optimization "
            "and explainability pipeline."
        ),
    )