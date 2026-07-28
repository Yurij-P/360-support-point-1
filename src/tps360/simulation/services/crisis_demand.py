"""Crisis resource DEMAND model and endowment gap (TPS360-RES-001 §5.1 part B/C).

Estimates how much resource is needed to liquidate a crisis, from hazard type,
affected population, hazard radius and severity. Deterministic. Coefficients are
provisional placeholders (estimated), to be refined against real norms. Pairs
with `resource_estimator` (endowment, side A) to produce the gap (side C).
"""
from __future__ import annotations

from decimal import ROUND_CEILING, Decimal

# Hazard families keyed by substrings of HazardType values (crisis_taxonomy).
_FIRE = ("fire", "fuel_storage_explosion")
_FLOOD = ("flood", "dam_failure")
_CHEMICAL = ("chemical", "hazardous_material", "mass_poisoning")
_RADIATION = ("radiation", "nuclear")
_UTILITY = ("blackout", "power_grid", "water_system", "gas_system", "heating_system")
_STRIKE = ("missile", "artillery", "drone", "armed_conflict", "shelling", "explosive", "mine")
_EPIDEMIC = ("epidemic", "pandemic", "waterborne", "epizootic")


def _family(hazard_type: str) -> str:
    h = hazard_type.strip().lower()
    for name, keys in (
        ("fire", _FIRE),
        ("flood", _FLOOD),
        ("chemical", _CHEMICAL),
        ("radiation", _RADIATION),
        ("utility", _UTILITY),
        ("strike", _STRIKE),
        ("epidemic", _EPIDEMIC),
    ):
        if any(k in h for k in keys):
            return name
    return "generic"


def _c(value: Decimal) -> Decimal:
    return value.quantize(Decimal("1"), rounding=ROUND_CEILING)


def estimate_demand(
    hazard_type: str,
    affected_population: int,
    hazard_radius_km: float = 1.0,
    severity: float = 1.0,
) -> dict[str, Decimal]:
    """Estimate resources required to liquidate the crisis. Deterministic."""
    radius = Decimal(str(max(1.0, hazard_radius_km)))
    sev = Decimal(str(max(0.1, severity)))
    mult = radius * sev
    pop_k = Decimal(max(0, affected_population)) / Decimal("1000")
    family = _family(hazard_type)

    if family == "fire":
        return {
            "fire_trucks": _c(Decimal("3") * mult),
            "water_tankers": _c(Decimal("2") * mult),
            "rescue_personnel": _c(Decimal("8") * mult + Decimal("4") * pop_k),
            "fuel_liters": _c(Decimal("800") * mult),
        }
    if family == "flood":
        return {
            "sewage_trucks": _c(Decimal("2") * mult),
            "backup_generators": _c(Decimal("2") * mult),
            "rescue_personnel": _c(Decimal("6") * mult + Decimal("6") * pop_k),
            "fuel_liters": _c(Decimal("700") * mult),
        }
    if family == "chemical":
        return {
            "decontamination_units": _c(Decimal("2") * mult),
            "disinfectant_liters": _c(Decimal("400") * mult),
            "sanitary_inspectors": _c(Decimal("6") * mult),
            "medical_personnel": _c(Decimal("10") * pop_k),
        }
    if family == "radiation":
        return {
            "decontamination_units": _c(Decimal("3") * mult),
            "sanitary_inspectors": _c(Decimal("8") * mult),
            "medical_personnel": _c(Decimal("12") * pop_k),
            "ambulances": _c(Decimal("2") * mult),
        }
    if family == "utility":
        return {
            "backup_generators": _c(Decimal("4") * mult),
            "utility_workers": _c(Decimal("8") * mult),
            "utility_vehicles": _c(Decimal("3") * mult),
            "fuel_liters": _c(Decimal("900") * mult),
        }
    if family == "strike":
        return {
            "fire_trucks": _c(Decimal("2") * mult),
            "ambulances": _c(Decimal("3") * mult),
            "rescue_personnel": _c(Decimal("10") * mult + Decimal("5") * pop_k),
            "medical_personnel": _c(Decimal("8") * pop_k),
            "fuel_liters": _c(Decimal("600") * mult),
        }
    if family == "epidemic":
        return {
            "medical_personnel": _c(Decimal("15") * pop_k),
            "medical_kits": _c(Decimal("50") * pop_k),
            "sanitary_inspectors": _c(Decimal("6") * mult),
            "disinfectant_liters": _c(Decimal("300") * mult),
        }
    return {
        "personnel": _c(Decimal("10") * mult + Decimal("5") * pop_k),
        "vehicles": _c(Decimal("3") * mult),
        "fuel_liters": _c(Decimal("500") * mult),
    }


def resource_gap(
    demand: dict[str, Decimal], available: dict[str, Decimal]
) -> dict[str, Decimal]:
    """Shortfall per resource: positive amount of demand not covered by `available`."""
    gap: dict[str, Decimal] = {}
    for resource, needed in demand.items():
        have = available.get(resource, Decimal("0"))
        shortfall = needed - have
        if shortfall > 0:
            gap[resource] = shortfall
    return gap
