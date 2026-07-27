from dataclasses import dataclass
from enum import StrEnum

from tps360.core.exceptions import DomainRuleViolation


class CrisisCategory(StrEnum):
    MILITARY_POLITICAL = "military_political"
    TECHNOLOGICAL = "technological"
    NATURAL = "natural"
    MEDICAL_BIOLOGICAL = "medical_biological"
    SOCIAL_HUMANITARIAN = "social_humanitarian"
    CYBER_INFORMATION = "cyber_information"
    COMBINED = "combined"


class HazardType(StrEnum):
    ARMED_CONFLICT = "armed_conflict"
    OCCUPATION = "occupation"
    ARTILLERY_SHELLING = "artillery_shelling"
    MORTAR_SHELLING = "mortar_shelling"
    MISSILE_STRIKE = "missile_strike"
    DRONE_STRIKE = "drone_strike"
    SABOTAGE = "sabotage"
    TERRORIST_ATTACK = "terrorist_attack"
    BLOCKADE = "blockade"
    EXPLOSIVE_HAZARD = "explosive_hazard"
    MINE_HAZARD = "mine_hazard"
    CRITICAL_INFRASTRUCTURE_DAMAGE = "critical_infrastructure_damage"
    POWER_GRID_DAMAGE = "power_grid_damage"
    BLACKOUT = "blackout"
    WATER_SYSTEM_FAILURE = "water_system_failure"
    GAS_SYSTEM_FAILURE = "gas_system_failure"
    HEATING_SYSTEM_FAILURE = "heating_system_failure"
    TRANSPORT_ACCIDENT = "transport_accident"
    HAZARDOUS_MATERIAL_TRANSPORT_ACCIDENT = "hazardous_material_transport_accident"
    CHEMICAL_RELEASE = "chemical_release"
    FUEL_STORAGE_EXPLOSION = "fuel_storage_explosion"
    AMMUNITION_STORAGE_EXPLOSION = "ammunition_storage_explosion"
    DAM_FAILURE = "dam_failure"
    FLOODING = "flooding"
    RADIATION_INCIDENT = "radiation_incident"
    NUCLEAR_FACILITY_DAMAGE = "nuclear_facility_damage"
    SEVERE_WIND = "severe_wind"
    TORNADO = "tornado"
    HEAVY_SNOW = "heavy_snow"
    ICE_STORM = "ice_storm"
    HEAVY_RAIN = "heavy_rain"
    DROUGHT = "drought"
    LANDSLIDE = "landslide"
    MUDFLOW = "mudflow"
    EARTHQUAKE = "earthquake"
    WILDFIRE = "wildfire"
    PEAT_FIRE = "peat_fire"
    STRUCTURAL_FIRE = "structural_fire"
    EPIDEMIC = "epidemic"
    PANDEMIC = "pandemic"
    WATERBORNE_DISEASE = "waterborne_disease"
    MASS_POISONING = "mass_poisoning"
    EPIZOOTIC = "epizootic"
    EPIPHYTOTIC = "epiphytotic"
    MASS_DISPLACEMENT = "mass_displacement"
    HUMANITARIAN_SUPPLY_FAILURE = "humanitarian_supply_failure"
    HEALTHCARE_OVERLOAD = "healthcare_overload"
    SOCIAL_UNREST = "social_unrest"
    HOSTAGE_SITUATION = "hostage_situation"
    CROWD_CRUSH = "crowd_crush"
    CYBERATTACK = "cyberattack"
    DATA_LOSS = "data_loss"
    WARNING_SYSTEM_COMPROMISE = "warning_system_compromise"
    DISINFORMATION = "disinformation"
    COMBINED_CRISIS = "combined_crisis"


class ImpactType(StrEnum):
    CASUALTIES = "casualties"
    BUILDING_DAMAGE = "building_damage"
    INFRASTRUCTURE_FAILURE = "infrastructure_failure"
    ELECTRICITY_LOSS = "electricity_loss"
    WATER_LOSS = "water_loss"
    HEATING_LOSS = "heating_loss"
    COMMUNICATIONS_LOSS = "communications_loss"
    TRANSPORT_DISRUPTION = "transport_disruption"
    EVACUATION_REQUIRED = "evacuation_required"
    SHELTER_OVERLOAD = "shelter_overload"
    HEALTHCARE_OVERLOAD = "healthcare_overload"
    HAZARDOUS_CONTAMINATION = "hazardous_contamination"
    RADIATION_EXPOSURE = "radiation_exposure"
    SUPPLY_SHORTAGE = "supply_shortage"
    DISPLACEMENT = "displacement"
    GOVERNANCE_DISRUPTION = "governance_disruption"
    PUBLIC_PANIC = "public_panic"
    ENVIRONMENTAL_DAMAGE = "environmental_damage"


@dataclass(frozen=True)
class CrisisClassification:
    """A classification of a community crisis and its expected impacts."""

    category: CrisisCategory
    primary_hazard: HazardType
    secondary_hazards: tuple[HazardType, ...] = ()
    potential_impacts: tuple[ImpactType, ...] = ()
    is_combined: bool = False

    def __post_init__(self) -> None:
        if self.primary_hazard in self.secondary_hazards:
            raise DomainRuleViolation("Primary hazard must not appear among secondary hazards.")
        if len(set(self.secondary_hazards)) != len(self.secondary_hazards):
            raise DomainRuleViolation("Secondary hazards must not contain duplicates.")
        if len(set(self.potential_impacts)) != len(self.potential_impacts):
            raise DomainRuleViolation("Potential impacts must not contain duplicates.")
        if self.category is CrisisCategory.COMBINED and not self.is_combined:
            raise DomainRuleViolation("Combined crises must be marked as combined.")

    def all_hazards(self) -> tuple[HazardType, ...]:
        return (self.primary_hazard, *self.secondary_hazards)