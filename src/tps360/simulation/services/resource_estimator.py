"""Endowment estimator: approximate role resources from the community passport.

TPS360-RES-001 §5.1. No real inventory of communal assets exists, so the
endowment is an *estimate* derived deterministically from passport proxies
(population, area, infrastructure). Coefficients below are provisional
placeholders (marked estimated), to be refined against real norms
(ДСНС/МОЗ/ДБН) or registry/procurement data (Phase 2).
"""
from __future__ import annotations

from decimal import Decimal

from tps360.community.domain.passport_read_model import CommunityPassportReadModel


def _per(population: int, divisor: int, minimum: int) -> Decimal:
    """One unit per `divisor` residents, never below `minimum`."""
    return Decimal(max(minimum, round(population / divisor)))


def _agri_object_count(passport: CommunityPassportReadModel) -> int:
    return sum(
        1
        for item in passport.infrastructure_items
        if "FARM" in item.category.value or "AGRO" in item.category.value
    )


def estimate_role_resources(
    role_id: str, passport: CommunityPassportReadModel
) -> dict[str, Decimal]:
    """Estimate a role's initial resources from the passport. Deterministic."""
    pop = passport.total_population
    area = passport.area_sq_km

    if role_id == "emerg-dsns":
        vehicles = _per(pop, 7000, 2) + _per(pop, 20000, 1)
        return {
            "fire_trucks": _per(pop, 7000, 2),
            "water_tankers": _per(pop, 20000, 1),
            "rescue_personnel": _per(pop, 700, 12),
            "rescue_equipment_units": _per(pop, 5000, 3),
            "fuel_liters": vehicles * Decimal("500"),
        }
    if role_id == "emerg-ems":
        ambulances = _per(pop, 10000, 2)
        return {
            "ambulances": ambulances,
            "medical_teams": ambulances,
            "medical_personnel": _per(pop, 1500, 10),
            "medical_kits": _per(pop, 40, 100),
            "fuel_liters": ambulances * Decimal("300"),
        }
    if role_id == "emerg-police":
        patrol_cars = _per(pop, 4000, 3)
        return {
            "patrol_cars": patrol_cars,
            "police_officers": _per(pop, 500, 15),
            "barricades": _per(pop, 1000, 10),
            "fuel_liters": patrol_cars * Decimal("250"),
        }
    if role_id == "communal-utility":
        tractors = Decimal(max(2, round(area / 40) + _agri_object_count(passport)))
        utility_vehicles = _per(pop, 6000, 3)
        sewage_trucks = _per(pop, 9000, 1)
        fleet = tractors + utility_vehicles + sewage_trucks
        return {
            "tractors": tractors,
            "utility_vehicles": utility_vehicles,
            "sewage_trucks": sewage_trucks,
            "backup_generators": _per(pop, 5000, 2),
            "utility_workers": _per(pop, 800, 10),
            "fuel_liters": fleet * Decimal("400"),
        }
    if role_id == "chief_sanitary_inspector":
        return {
            "decontamination_units": _per(pop, 20000, 1),
            "sanitary_inspectors": _per(pop, 2000, 5),
            "disinfectant_liters": _per(pop, 20, 200),
            "water_testing_kits": _per(pop, 300, 20),
        }

    # Generic fallback for any other role.
    return {
        "vehicles": _per(pop, 6000, 2),
        "personnel": _per(pop, 900, 10),
        "backup_generators": _per(pop, 8000, 1),
        "fuel_liters": _per(pop, 6000, 2) * Decimal("300"),
    }
