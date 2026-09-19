from engine.aircraft import load_aircraft_from_json
from engine.cargo import load_cargo_from_csv
from engine.constraints import validate_loading_plan
from engine.models import CargoAssignment


aircraft = load_aircraft_from_json(
    "data/aircraft.json"
)

cargo_items = load_cargo_from_csv(
    "data/sample_cargo.csv"
)


assignments = [
    CargoAssignment(
        cargo=cargo_items[0],
        bay=aircraft.require_bay("B1"),
    ),
    CargoAssignment(
        cargo=cargo_items[1],
        bay=aircraft.require_bay("B2"),
    ),
    CargoAssignment(
        cargo=cargo_items[2],
        bay=aircraft.require_bay("B5"),
    ),
    CargoAssignment(
        cargo=cargo_items[3],
        bay=aircraft.require_bay("B6"),
    ),
    CargoAssignment(
        cargo=cargo_items[4],
        bay=aircraft.require_bay("B3"),
    ),
    CargoAssignment(
        cargo=cargo_items[5],
        bay=aircraft.require_bay("B4"),
    ),
]


report = validate_loading_plan(
    aircraft,
    assignments,
)


print("AeroLoad-AI Safety Report")
print("-" * 40)

print(
    f"Total Payload: "
    f"{report.total_payload_kg:.1f} kg"
)

print(
    f"CG: "
    f"{report.cg_m:.3f} m"
)

print(
    f"Lateral Imbalance: "
    f"{report.lateral_imbalance_kg:.1f} kg"
)

print(
    f"Overall Safe: "
    f"{report.safe}"
)

print()

print("Checks:")

for check in report.checks:
    status = "PASS" if check.valid else "FAIL"

    print(
        f"[{status}] {check.message}"
    )