from dataclasses import FrozenInstanceError
from datetime import datetime
from uuid import UUID

import pytest

from tps360.core.domain.models import Community
from tps360.core.exceptions import DomainRuleViolation
from tps360.simulation.domain import (
    Scenario,
    Simulation,
    SimulationClock,
    SimulationContext,
    SimulationStatus,
    Timeline,
)
from tps360.simulation.services import generate_context_checksum
from tps360.threats.domain import Threat, ThreatSeverity, ThreatTargetType, ThreatType

NOW = datetime(2026, 7, 24, 9, 0)
PRIMARY_THREAT_ID = UUID("11111111-1111-1111-1111-111111111111")
SECONDARY_THREAT_ID = UUID("22222222-2222-2222-2222-222222222222")
RESOURCE_ID = UUID("33333333-3333-3333-3333-333333333333")
CAPABILITY_ID = UUID("44444444-4444-4444-4444-444444444444")
ORGANIZATION_ID = UUID("55555555-5555-5555-5555-555555555555")
SETTLEMENT_ID = UUID("66666666-6666-6666-6666-666666666666")


def build_context(**overrides: object) -> SimulationContext:
    values: dict[str, object] = {
        "id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        "community_id": UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
        "community_profile_id": UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
        "community_profile_version": "1.0.0",
        "community_map_id": UUID("dddddddd-dddd-dddd-dddd-dddddddddddd"),
        "community_map_version": 1,
        "scenario_id": UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"),
        "scenario_version": 1,
        "primary_threat_id": PRIMARY_THREAT_ID,
        "secondary_threat_ids": (SECONDARY_THREAT_ID,),
        "available_resource_ids": (RESOURCE_ID,),
        "operational_capability_ids": (CAPABILITY_ID,),
        "participating_organization_ids": (ORGANIZATION_ID,),
        "participating_emergency_service_ids": (),
        "affected_settlement_ids": (SETTLEMENT_ID,),
        "initial_assumptions": ("Backup power is operational.",),
        "data_quality_score": 80.0,
        "created_at": NOW,
        "checksum": "valid-checksum",
    }
    values.update(overrides)
    return SimulationContext(**values)  # type: ignore[arg-type]


def test_valid_simulation_context_creation() -> None:
    assert build_context().community_profile_version == "1.0.0"


def test_empty_profile_version_raises_error() -> None:
    with pytest.raises(DomainRuleViolation):
        build_context(community_profile_version=" ")


def test_invalid_map_version_raises_error() -> None:
    with pytest.raises(DomainRuleViolation):
        build_context(community_map_version=0)


def test_invalid_scenario_version_raises_error() -> None:
    with pytest.raises(DomainRuleViolation):
        build_context(scenario_version=0)


def test_data_quality_below_zero_raises_error() -> None:
    with pytest.raises(DomainRuleViolation):
        build_context(data_quality_score=-0.1)


def test_data_quality_above_one_hundred_raises_error() -> None:
    with pytest.raises(DomainRuleViolation):
        build_context(data_quality_score=100.1)


def test_primary_threat_in_secondary_threats_raises_error() -> None:
    with pytest.raises(DomainRuleViolation):
        build_context(secondary_threat_ids=(PRIMARY_THREAT_ID,))


def test_duplicate_resource_ids_raise_error() -> None:
    with pytest.raises(DomainRuleViolation):
        build_context(available_resource_ids=(RESOURCE_ID, RESOURCE_ID))


def test_empty_assumption_raises_error() -> None:
    with pytest.raises(DomainRuleViolation):
        build_context(initial_assumptions=(" ",))


def test_context_is_immutable() -> None:
    context = build_context()

    with pytest.raises(FrozenInstanceError):
        context.checksum = "new-checksum"  # type: ignore[misc]


def test_all_threat_ids() -> None:
    assert build_context().all_threat_ids() == (PRIMARY_THREAT_ID, SECONDARY_THREAT_ID)


def test_includes_and_affects_methods() -> None:
    context = build_context()

    assert context.includes_resource(RESOURCE_ID)
    assert context.includes_capability(CAPABILITY_ID)
    assert context.includes_organization(ORGANIZATION_ID)
    assert context.affects_settlement(SETTLEMENT_ID)


def test_checksum_is_deterministic() -> None:
    first = generate_context_checksum({"id": RESOURCE_ID, "created_at": NOW, "version": 1})
    second = generate_context_checksum({"version": 1, "created_at": NOW, "id": RESOURCE_ID})

    assert first == second


def test_simulation_does_not_start_with_low_data_quality() -> None:
    context = build_context(data_quality_score=59.9)
    simulation = Simulation(
        id=UUID("ffffffff-ffff-ffff-ffff-ffffffffffff"),
        scenario=Scenario(
            id=UUID("12121212-1212-1212-1212-121212121212"),
            name="Exercise",
            description="A reproducibility exercise.",
        ),
        community=Community(name="Example", code="EX", oblast="Kyiv", population=1, area_km2=1.0),
        threat=Threat(
            id=PRIMARY_THREAT_ID,
            name="Threat",
            threat_type=ThreatType.TECHNOLOGICAL,
            severity=ThreatSeverity.HIGH,
            target_type=ThreatTargetType.CRITICAL_INFRASTRUCTURE,
            description="A test threat.",
        ),
        timeline=Timeline(),
        current_time=NOW,
        status=SimulationStatus.DRAFT,
        clock=SimulationClock(start_time=NOW, current_time=NOW),
        context=context,
    )

    simulation.prepare()

    with pytest.raises(DomainRuleViolation):
        simulation.start()