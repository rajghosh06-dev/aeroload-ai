# Classical AI Foundations

AeroLoad-AI is built strictly upon classical Artificial Intelligence techniques from the B.Tech curriculum (Russell & Norvig, *Artificial Intelligence: A Modern Approach*, Units I and II).

---

## 1. Constraint Satisfaction Problem (CSP)

A CSP represents a problem as three components:
$$\mathcal{P} = \langle X, D, C \rangle$$

- **Variables ($X$)**: The cargo packages to be assigned.
- **Domains ($D$)**: The available aircraft cargo bays. Each variable $X_i$ initially has domain $D(X_i) = \{ B_1, B_2, \dots, B_8 \}$.
- **Constraints ($C$)**:
  - *Unary Constraint*: Cargo weight must not exceed bay capacity: $W(X_i) \le C_{\max}(B_j)$.
  - *Binary Constraint 1 (Exclusivity)*: At most one cargo package per bay: $\text{bay}(X_i) \neq \text{bay}(X_j)$.
  - *Binary Constraint 2 (Hazard Separation)*: Incompatible hazardous cargo cannot occupy adjacent bays:
    $$\text{Incompatible}(Haz(X_i), Haz(X_j)) \implies \text{bay}(X_j) \notin Adj(\text{bay}(X_i))$$

---

## 2. AC-3 (Arc Consistency Algorithm #3)

AC-3 pre-prunes unviable bay choices from variable domains before search begins:
- An arc $(X_i, X_j)$ is **consistent** if for every bay in $D(X_i)$, there exists at least one legal bay in $D(X_j)$.
- If a bay in $D(X_i)$ leaves no valid option for $X_j$, that bay is removed from $D(X_i)$.
- AC-3 propagates removals across all related arcs. If any domain becomes empty (domain wipeout), the problem is immediately recognized as unsatisfiable without branching.

---

## 3. Backtracking Search Heuristics

AeroLoad-AI uses depth-first recursive backtracking guided by two standard heuristics:

### MRV (Minimum Remaining Values Heuristic)
- **What it does**: Variable ordering — chooses which unassigned cargo item to place next.
- **Principle**: *Fail-First*. Selects the variable with the fewest remaining legal bay choices ($|D_{\text{legal}}(X)|$).
- **Why it helps**: Prunes unviable branches at the shallowest possible depth.

### LCV (Least Constraining Value Heuristic)
- **What it does**: Value ordering — chooses which candidate bay to attempt first for the selected cargo item.
- **Principle**: *Fail-Last*. Orders bays by how few options they eliminate for other unassigned cargo.
- **Why it helps**: Maximizes the likelihood of finding a complete solution on the first search path.

---

## 4. Hill-Climbing Local Search

Once a safe, feasible assignment is found by backtracking, local search refines its aerodynamic quality:
- **Objective Function**:
  $$\text{score} = |\text{CG} - \text{TargetCG}| + 0.25 \times \left( \frac{\text{LateralImbalance}}{\text{LateralLimit}} \right)$$
  *(Lower score is better).*
- **Neighborhood Operators**:
  - `MOVE`: Transfer one cargo item to an unoccupied bay.
  - `SWAP`: Exchange bay assignments between two cargo items.
- **Algorithm**: Best-improvement hill climbing. Evaluates all valid neighbors, greedily picks the candidate with strictly lower score, and stops when no neighbor improves (local optimum).
