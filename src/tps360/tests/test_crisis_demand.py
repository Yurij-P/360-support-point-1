from decimal import Decimal

from tps360.simulation.services.crisis_demand import estimate_demand, resource_gap


def test_deterministic() -> None:
    a = estimate_demand("wildfire", 10000, 2.0, 1.0)
    b = estimate_demand("wildfire", 10000, 2.0, 1.0)
    assert a == b


def test_family_classification() -> None:
    assert "fire_trucks" in estimate_demand("structural_fire", 5000, 1.0)
    assert "backup_generators" in estimate_demand("blackout", 5000, 1.0)
    assert "decontamination_units" in estimate_demand("chemical_release", 5000, 1.0)
    assert "medical_personnel" in estimate_demand("epidemic", 5000, 1.0)
    # unknown hazard -> generic
    assert "personnel" in estimate_demand("some_unknown_hazard", 5000, 1.0)


def test_scales_with_radius_and_population() -> None:
    small = estimate_demand("wildfire", 5000, 1.0)["fire_trucks"]
    big_radius = estimate_demand("wildfire", 5000, 4.0)["fire_trucks"]
    assert big_radius > small

    few = estimate_demand("missile_strike", 2000, 1.0)["medical_personnel"]
    many = estimate_demand("missile_strike", 50000, 1.0)["medical_personnel"]
    assert many > few


def test_resource_gap_shortfall_only() -> None:
    demand = {"fire_trucks": Decimal("6"), "fuel_liters": Decimal("2000")}
    available = {"fire_trucks": Decimal("4"), "fuel_liters": Decimal("5000")}
    gap = resource_gap(demand, available)
    assert gap == {"fire_trucks": Decimal("2")}  # fuel is covered, omitted


def test_resource_gap_missing_resource_is_full_shortfall() -> None:
    gap = resource_gap({"tractors": Decimal("3")}, {})
    assert gap == {"tractors": Decimal("3")}
