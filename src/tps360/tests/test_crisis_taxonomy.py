import pytest

from tps360.core.domain.crisis_taxonomy import (
    CrisisCategory,
    CrisisClassification,
    HazardType,
    ImpactType,
)
from tps360.core.exceptions import DomainRuleViolation


def test_valid_single_crisis() -> None:
    crisis = CrisisClassification(
        category=CrisisCategory.NATURAL,
        primary_hazard=HazardType.FLOODING,
        potential_impacts=(ImpactType.BUILDING_DAMAGE,),
    )

    assert not crisis.is_combined


def test_valid_combined_crisis() -> None:
    crisis = CrisisClassification(
        category=CrisisCategory.COMBINED,
        primary_hazard=HazardType.DRONE_STRIKE,
        secondary_hazards=(HazardType.POWER_GRID_DAMAGE,),
        is_combined=True,
    )

    assert crisis.is_combined


def test_duplicate_primary_hazard_raises_error() -> None:
    with pytest.raises(DomainRuleViolation):
        CrisisClassification(
            category=CrisisCategory.MILITARY_POLITICAL,
            primary_hazard=HazardType.MISSILE_STRIKE,
            secondary_hazards=(HazardType.MISSILE_STRIKE,),
        )


def test_duplicate_secondary_hazards_raise_error() -> None:
    with pytest.raises(DomainRuleViolation):
        CrisisClassification(
            category=CrisisCategory.TECHNOLOGICAL,
            primary_hazard=HazardType.BLACKOUT,
            secondary_hazards=(HazardType.POWER_GRID_DAMAGE, HazardType.POWER_GRID_DAMAGE),
        )


def test_duplicate_impacts_raise_error() -> None:
    with pytest.raises(DomainRuleViolation):
        CrisisClassification(
            category=CrisisCategory.NATURAL,
            primary_hazard=HazardType.WILDFIRE,
            potential_impacts=(ImpactType.ENVIRONMENTAL_DAMAGE, ImpactType.ENVIRONMENTAL_DAMAGE),
        )


def test_combined_category_requires_is_combined() -> None:
    with pytest.raises(DomainRuleViolation):
        CrisisClassification(
            category=CrisisCategory.COMBINED,
            primary_hazard=HazardType.COMBINED_CRISIS,
        )


def test_all_hazards() -> None:
    crisis = CrisisClassification(
        category=CrisisCategory.NATURAL,
        primary_hazard=HazardType.FLOODING,
        secondary_hazards=(HazardType.HEAVY_RAIN,),
    )

    assert crisis.all_hazards() == (HazardType.FLOODING, HazardType.HEAVY_RAIN)


def test_drone_strike_power_grid_damage_and_blackout() -> None:
    crisis = CrisisClassification(
        category=CrisisCategory.COMBINED,
        primary_hazard=HazardType.DRONE_STRIKE,
        secondary_hazards=(HazardType.POWER_GRID_DAMAGE, HazardType.BLACKOUT),
        potential_impacts=(ImpactType.ELECTRICITY_LOSS,),
        is_combined=True,
    )

    assert crisis.all_hazards() == (
        HazardType.DRONE_STRIKE,
        HazardType.POWER_GRID_DAMAGE,
        HazardType.BLACKOUT,
    )