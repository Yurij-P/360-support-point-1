import pytest

from tps360.community.domain.infrastructure_taxonomy import (
    CriticalInfrastructureCategory,
    OSMTagMapping,
    get_osm_tag_mapping,
)


@pytest.mark.parametrize(
    "category,expected_key,expected_value",
    [
        (CriticalInfrastructureCategory.POULTRY_FARM, "farmyard", "poultry"),
        (CriticalInfrastructureCategory.QUARRY_MINING, "landuse", "quarry"),
        (CriticalInfrastructureCategory.ELEVATOR_GRAIN_TERMINAL, "building", "silo"),
        (CriticalInfrastructureCategory.TAILINGS_DUMP, "man_made", "spoil_heap"),
        (CriticalInfrastructureCategory.AMMONIA_PIPELINE, "substance", "ammonia"),
        (CriticalInfrastructureCategory.TRANSFORMER_SUBSTATION, "power", "substation"),
        (CriticalInfrastructureCategory.FUEL_STATION, "amenity", "fuel"),
        (CriticalInfrastructureCategory.SEWAGE_TREATMENT_PLANT, "amenity", "wastewater_plant"),
        (CriticalInfrastructureCategory.EPIZOOTIC_BURIAL_SITE, "sanitary", "epizootic_burial"),
        (CriticalInfrastructureCategory.MILITARY_BASE, "military", "base"),
        (CriticalInfrastructureCategory.TERRITORIAL_DEFENSE_HQ, "military", "office"),
        (CriticalInfrastructureCategory.MILITARY_CHECKPOINT, "military", "checkpoint"),
        (CriticalInfrastructureCategory.FORTIFICATION_LINE, "military", "trench"),
        (CriticalInfrastructureCategory.CIVIL_MILITARY_COOPERATION_CENTER, "military", "office"),

    ],
)
def test_infrastructure_osm_tag_mapping(
    category: CriticalInfrastructureCategory, expected_key: str, expected_value: str
) -> None:
    mapping = get_osm_tag_mapping(category)
    assert isinstance(mapping, OSMTagMapping)
    assert mapping.category is category
    assert mapping.osm_key == expected_key
    assert mapping.osm_value == expected_value
    assert "OpenStreetMap" in mapping.attribution_notice
