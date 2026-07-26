from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CriticalInfrastructureCategory(StrEnum):
    """Exhaustive domain classification of community critical infrastructure, agricultural, mining & hazard assets."""

    # Agro-Industrial & Biosecurity
    POULTRY_FARM = "POULTRY_FARM"
    LIVESTOCK_COMPLEX = "LIVESTOCK_COMPLEX"
    ELEVATOR_GRAIN_TERMINAL = "ELEVATOR_GRAIN_TERMINAL"
    FERTILIZER_PESTICIDE_STORE = "FERTILIZER_PESTICIDE_STORE"

    # Mining, Subsoil & Tailings
    QUARRY_MINING = "QUARRY_MINING"
    TAILINGS_DUMP = "TAILINGS_DUMP"
    GAS_OIL_WELL = "GAS_OIL_WELL"

    # Energy & Heating Grid
    POWER_LINE = "POWER_LINE"
    TRANSFORMER_SUBSTATION = "TRANSFORMER_SUBSTATION"
    POWER_PLANT = "POWER_PLANT"
    BOILER_PLANT = "BOILER_PLANT"
    NUCLEAR_PROXIMITY_ZONE = "NUCLEAR_PROXIMITY_ZONE"

    # Transport Infrastructure & Logistics
    ROAD_NETWORK = "ROAD_NETWORK"
    RAILWAY_HUB = "RAILWAY_HUB"
    BRIDGE_VIADUCT = "BRIDGE_VIADUCT"
    FUEL_STATION = "FUEL_STATION"
    FUEL_DEPOT = "FUEL_DEPOT"

    # Pipelines & Hazardous Materials
    GAS_PIPELINE = "GAS_PIPELINE"
    OIL_PIPELINE = "OIL_PIPELINE"
    AMMONIA_PIPELINE = "AMMONIA_PIPELINE"
    CHEMICAL_PLANT = "CHEMICAL_PLANT"
    METALLURGICAL_PLANT = "METALLURGICAL_PLANT"

    # Hydrography & Water Engineering
    RIVER_WATERWAY = "RIVER_WATERWAY"
    DAM_HYDRO_STRUCTURE = "DAM_HYDRO_STRUCTURE"
    WATER_SUPPLY_FACILITY = "WATER_SUPPLY_FACILITY"
    SEWAGE_TREATMENT_PLANT = "SEWAGE_TREATMENT_PLANT"

    # Environmental & Epizootic Hazards
    FOREST_MASS = "FOREST_MASS"
    SEISMIC_ZONE = "SEISMIC_ZONE"
    FLOOD_PRONE_ZONE = "FLOOD_PRONE_ZONE"
    EPIZOOTIC_BURIAL_SITE = "EPIZOOTIC_BURIAL_SITE"
    WASTE_LANDFILL = "WASTE_LANDFILL"

    # Civil Protection & Healthcare
    HOSPITAL_MEDICAL = "HOSPITAL_MEDICAL"
    RESCUE_FIRE_STATION = "RESCUE_FIRE_STATION"
    SHELTER_UNBREAKABLE = "SHELTER_UNBREAKABLE"
    POLICE_SECURITY = "POLICE_SECURITY"


@dataclass(frozen=True)
class OSMTagMapping:
    category: CriticalInfrastructureCategory
    osm_key: str
    osm_value: str
    attribution_notice: str = "© OpenStreetMap contributors (ODbL)"


OSM_TAG_MAPPINGS: dict[CriticalInfrastructureCategory, OSMTagMapping] = {
    CriticalInfrastructureCategory.POULTRY_FARM: OSMTagMapping(
        CriticalInfrastructureCategory.POULTRY_FARM, "farmyard", "poultry"
    ),
    CriticalInfrastructureCategory.LIVESTOCK_COMPLEX: OSMTagMapping(
        CriticalInfrastructureCategory.LIVESTOCK_COMPLEX, "landuse", "farmyard"
    ),
    CriticalInfrastructureCategory.ELEVATOR_GRAIN_TERMINAL: OSMTagMapping(
        CriticalInfrastructureCategory.ELEVATOR_GRAIN_TERMINAL, "building", "silo"
    ),
    CriticalInfrastructureCategory.FERTILIZER_PESTICIDE_STORE: OSMTagMapping(
        CriticalInfrastructureCategory.FERTILIZER_PESTICIDE_STORE, "industrial", "fertilizer"
    ),
    CriticalInfrastructureCategory.QUARRY_MINING: OSMTagMapping(
        CriticalInfrastructureCategory.QUARRY_MINING, "landuse", "quarry"
    ),
    CriticalInfrastructureCategory.TAILINGS_DUMP: OSMTagMapping(
        CriticalInfrastructureCategory.TAILINGS_DUMP, "man_made", "spoil_heap"
    ),
    CriticalInfrastructureCategory.GAS_OIL_WELL: OSMTagMapping(
        CriticalInfrastructureCategory.GAS_OIL_WELL, "man_made", "petroleum_well"
    ),
    CriticalInfrastructureCategory.POWER_LINE: OSMTagMapping(
        CriticalInfrastructureCategory.POWER_LINE, "power", "line"
    ),
    CriticalInfrastructureCategory.TRANSFORMER_SUBSTATION: OSMTagMapping(
        CriticalInfrastructureCategory.TRANSFORMER_SUBSTATION, "power", "substation"
    ),
    CriticalInfrastructureCategory.POWER_PLANT: OSMTagMapping(
        CriticalInfrastructureCategory.POWER_PLANT, "power", "plant"
    ),
    CriticalInfrastructureCategory.BOILER_PLANT: OSMTagMapping(
        CriticalInfrastructureCategory.BOILER_PLANT, "industrial", "heating_plant"
    ),
    CriticalInfrastructureCategory.NUCLEAR_PROXIMITY_ZONE: OSMTagMapping(
        CriticalInfrastructureCategory.NUCLEAR_PROXIMITY_ZONE, "zone", "nuclear_buffer"
    ),
    CriticalInfrastructureCategory.ROAD_NETWORK: OSMTagMapping(
        CriticalInfrastructureCategory.ROAD_NETWORK, "highway", "primary"
    ),
    CriticalInfrastructureCategory.RAILWAY_HUB: OSMTagMapping(
        CriticalInfrastructureCategory.RAILWAY_HUB, "railway", "rail"
    ),
    CriticalInfrastructureCategory.BRIDGE_VIADUCT: OSMTagMapping(
        CriticalInfrastructureCategory.BRIDGE_VIADUCT, "bridge", "yes"
    ),
    CriticalInfrastructureCategory.FUEL_STATION: OSMTagMapping(
        CriticalInfrastructureCategory.FUEL_STATION, "amenity", "fuel"
    ),
    CriticalInfrastructureCategory.FUEL_DEPOT: OSMTagMapping(
        CriticalInfrastructureCategory.FUEL_DEPOT, "industrial", "oil_depot"
    ),
    CriticalInfrastructureCategory.GAS_PIPELINE: OSMTagMapping(
        CriticalInfrastructureCategory.GAS_PIPELINE, "substance", "gas"
    ),
    CriticalInfrastructureCategory.OIL_PIPELINE: OSMTagMapping(
        CriticalInfrastructureCategory.OIL_PIPELINE, "substance", "oil"
    ),
    CriticalInfrastructureCategory.AMMONIA_PIPELINE: OSMTagMapping(
        CriticalInfrastructureCategory.AMMONIA_PIPELINE, "substance", "ammonia"
    ),
    CriticalInfrastructureCategory.CHEMICAL_PLANT: OSMTagMapping(
        CriticalInfrastructureCategory.CHEMICAL_PLANT, "industrial", "chemical"
    ),
    CriticalInfrastructureCategory.METALLURGICAL_PLANT: OSMTagMapping(
        CriticalInfrastructureCategory.METALLURGICAL_PLANT, "industrial", "factory"
    ),
    CriticalInfrastructureCategory.RIVER_WATERWAY: OSMTagMapping(
        CriticalInfrastructureCategory.RIVER_WATERWAY, "waterway", "river"
    ),
    CriticalInfrastructureCategory.DAM_HYDRO_STRUCTURE: OSMTagMapping(
        CriticalInfrastructureCategory.DAM_HYDRO_STRUCTURE, "waterway", "dam"
    ),
    CriticalInfrastructureCategory.WATER_SUPPLY_FACILITY: OSMTagMapping(
        CriticalInfrastructureCategory.WATER_SUPPLY_FACILITY, "man_made", "water_works"
    ),
    CriticalInfrastructureCategory.SEWAGE_TREATMENT_PLANT: OSMTagMapping(
        CriticalInfrastructureCategory.SEWAGE_TREATMENT_PLANT, "amenity", "wastewater_plant"
    ),
    CriticalInfrastructureCategory.FOREST_MASS: OSMTagMapping(
        CriticalInfrastructureCategory.FOREST_MASS, "landuse", "forest"
    ),
    CriticalInfrastructureCategory.SEISMIC_ZONE: OSMTagMapping(
        CriticalInfrastructureCategory.SEISMIC_ZONE, "geology", "seismic_risk"
    ),
    CriticalInfrastructureCategory.FLOOD_PRONE_ZONE: OSMTagMapping(
        CriticalInfrastructureCategory.FLOOD_PRONE_ZONE, "hazard", "flood"
    ),
    CriticalInfrastructureCategory.EPIZOOTIC_BURIAL_SITE: OSMTagMapping(
        CriticalInfrastructureCategory.EPIZOOTIC_BURIAL_SITE, "sanitary", "epizootic_burial"
    ),
    CriticalInfrastructureCategory.WASTE_LANDFILL: OSMTagMapping(
        CriticalInfrastructureCategory.WASTE_LANDFILL, "landuse", "landfill"
    ),
    CriticalInfrastructureCategory.HOSPITAL_MEDICAL: OSMTagMapping(
        CriticalInfrastructureCategory.HOSPITAL_MEDICAL, "amenity", "hospital"
    ),
    CriticalInfrastructureCategory.RESCUE_FIRE_STATION: OSMTagMapping(
        CriticalInfrastructureCategory.RESCUE_FIRE_STATION, "amenity", "fire_station"
    ),
    CriticalInfrastructureCategory.SHELTER_UNBREAKABLE: OSMTagMapping(
        CriticalInfrastructureCategory.SHELTER_UNBREAKABLE, "amenity", "shelter"
    ),
    CriticalInfrastructureCategory.POLICE_SECURITY: OSMTagMapping(
        CriticalInfrastructureCategory.POLICE_SECURITY, "amenity", "police"
    ),
}


def get_osm_tag_mapping(category: CriticalInfrastructureCategory) -> OSMTagMapping:
    return OSM_TAG_MAPPINGS.get(
        category,
        OSMTagMapping(category=category, osm_key="infrastructure", osm_value="general"),
    )
