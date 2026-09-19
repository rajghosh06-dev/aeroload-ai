from engine.cargo import load_cargo_from_csv


def test_cargo_loading():
    cargo_items = load_cargo_from_csv(
        "data/sample_cargo.csv"
    )

    assert len(cargo_items) == 6

    first = cargo_items[0]

    assert first.cargo_id == "P1"
    assert first.weight_kg == 420
