# Simplified Hazard Knowledge Base

AeroLoad-AI incorporates a **rule-based structured knowledge representation** system (Russell & Norvig, Unit III: Knowledge & Reasoning) that stores dangerous-goods separation rules separately from the search algorithms.

---

## 1. Separation of Knowledge from Inference

In classical AI, domain rules should not be hardcoded inside search loops. Instead, domain knowledge is declared in an external knowledge base (`data/hazard_rules.json`) and queried through clean interfaces (`engine/knowledge_base.py`).

This architecture allows hazard rules to be modified, extended, or replaced without altering the CSP solver, AC-3 propagator, or local-search engine.

---

## 2. Incompatible Hazard Pairs

AeroLoad-AI defines 4 educational incompatibility rules inspired by general dangerous-goods separation principles:

| First Class | Second Class | Reason for Incompatibility |
| :--- | :--- | :--- |
| **Lithium Battery** | **Flammable** | Thermal runaway risk from lithium cells can ignite volatile flammable vapors. |
| **Flammable** | **Oxidizer** | Oxidizers dramatically accelerate combustion and increase fire intensity. |
| **Toxic** | **Food** | Chemical toxicity contamination risk to food supplies in adjacent compartments. |
| **Biohazard** | **Food** | Biological pathogen contamination risk to consumable goods. |

---

## 3. Knowledge Representation in Code

### Symmetric Relation
Hazard incompatibility is inherently symmetric:
$$\text{Incompatible}(A, B) \iff \text{Incompatible}(B, A)$$

### Implementation
In `engine/knowledge_base.py`:
- Incompatibility pairs are stored in a set of `frozenset[HazardClass]`.
- When querying `are_incompatible(first, second)`, the engine constructs `frozenset((first, second))` and performs a hash-set lookup.
- Query time complexity is **$O(1)$ constant time**.

### Adjacency Constraint
The CSP engine queries the knowledge base during consistency checks. If two cargo items are incompatible and their assigned bays share a boundary in `bay.adjacent_bays`, the placement is rejected.
