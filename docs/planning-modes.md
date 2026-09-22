# Operational Planning Modes

AeroLoad-AI offers three planning modes tailored for different use cases and learning stages.

---

## 1. Auto Solve

**"Let AeroLoad-AI generate a complete loading plan."**

### When to Use
- You want an immediate, mathematically sound load plan for the current manifest.
- You want to evaluate how the automated AI pipeline solves the problem end-to-end.

### How It Works
1. Formulates the active manifest and aircraft limits into a formal CSP.
2. Runs **AC-3 constraint propagation** to prune unsupported bay values.
3. Executes **Backtracking Search with MRV and LCV heuristics** to find a safe feasible assignment.
4. Validates the complete plan against aircraft payload, CG, and lateral balance limits.
5. If enabled in Settings, runs **Hill-Climbing Local Search** with `MOVE` and `SWAP` operators to align the CG with the Target CG.
6. Generates human-readable explainability reports and Plotly telemetry charts.

---

## 2. Manual Planning

**"Place cargo yourself and let AeroLoad-AI validate your plan."**

### When to Use
- You want hands-on experience loading an aircraft.
- You want to test how different loading decisions affect the Center of Gravity and lateral balance.

### How It Works
1. Select any cargo item from the unassigned queue or dropdown.
2. Select a target cargo bay and click **Place cargo**.
3. AeroLoad-AI immediately checks constraints:
   - Bay weight capacity
   - Bay occupancy (exclusivity)
   - Hazardous material adjacency
4. Displays live plan status:
   - **Incomplete**: Placements are consistent so far, but more cargo needs to be loaded.
   - **Complete & Safe**: All items loaded and all safety limits satisfied.
   - **Invalid**: A constraint violation has been detected.

---

## 3. AI-Assisted Planning

**"Place cargo yourself while AeroLoad-AI shows legal and blocked bays."**

### When to Use
- You want interactive guidance while learning how CSP domains work.
- You want to see *why* certain bays are blocked (e.g., due to hazardous material conflicts or capacity limits).

### How It Works
1. Select any cargo item to inspect.
2. The aircraft cargo deck updates visually:
   - **Available / Legal** (Green/Cyan): The bay satisfies all capacity and hazard constraints.
   - **Blocked** (Red): The bay violates a constraint, with an explicit reason displayed (e.g., *Adjacent to P2 (Lithium Battery) in B1*).
   - **Occupied** (Muted): The bay already contains another cargo package.
3. Click any legal bay button to place the cargo item directly.
4. Expand **Show CSP explanation** to inspect the mathematical domain representation:
   $$D(X_{\text{cargo}}) = \{ \text{legal bays} \}$$
