from engine.ac3 import ac3
from engine.aircraft import load_aircraft_from_json
from engine.cargo import load_cargo_from_csv
from engine.csp import AeroLoadCSP
from engine.knowledge_base import load_hazard_rules


aircraft = load_aircraft_from_json(
    "data/aircraft.json"
)

cargo_items = load_cargo_from_csv(
    "data/sample_cargo.csv"
)

knowledge = load_hazard_rules(
    "data/hazard_rules.json"
)

csp = AeroLoadCSP(
    aircraft=aircraft,
    cargo_items=cargo_items,
    knowledge_base=knowledge,
)


initial_values = sum(
    len(values)
    for values in csp.domains.values()
)

result = ac3(csp)

final_values = sum(
    len(values)
    for values in result.domains.values()
)


print()
print("=" * 50)
print("AeroLoad-AI — AC-3 Constraint Propagation")
print("=" * 50)

print(
    f"Consistent            : "
    f"{result.consistent}"
)

print(
    f"Initial domain values : "
    f"{initial_values}"
)

print(
    f"Final domain values   : "
    f"{final_values}"
)

print(
    f"Values pruned         : "
    f"{result.values_pruned}"
)

print(
    f"Arcs processed        : "
    f"{result.arcs_processed}"
)


print()
print("Domains after AC-3")
print("-" * 50)

for cargo_id, values in result.domains.items():
    print(
        f"{cargo_id}: {values}"
    )


print()
print("-" * 50)

if result.values_pruned == 0:
    print(
        "No values were pruned because the current "
        "domains remain arc-consistent."
    )
else:
    print(
        f"AC-3 removed {result.values_pruned} "
        f"unsupported domain value(s)."
    )