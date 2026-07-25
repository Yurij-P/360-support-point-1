from uuid import UUID

import pytest

from tps360.core.exceptions import DomainRuleViolation
from tps360.simulation.domain import (
    EventId,
    EventOccurrenceId,
    ImpactAttribute,
    ImpactSourceReference,
    ImpactSourceType,
    ImpactTargetType,
    TypedImpactTarget,
)

SESSION = UUID(int=1)
SCENARIO = UUID(int=2)


def test_typed_event_source_requires_event_and_occurrence() -> None:
    source = ImpactSourceReference(
        ImpactSourceType.EVENT, SESSION, SCENARIO, EventId(UUID(int=3)), EventOccurrenceId(UUID(int=4))
    )
    assert source.event_id == UUID(int=3)
    with pytest.raises(DomainRuleViolation):
        ImpactSourceReference(ImpactSourceType.EVENT, SESSION, SCENARIO, EventId(UUID(int=3)))


def test_combined_and_reversal_sources_are_strict() -> None:
    with pytest.raises(DomainRuleViolation):
        ImpactSourceReference(ImpactSourceType.COMBINED, SESSION, SCENARIO)
    with pytest.raises(DomainRuleViolation):
        ImpactSourceReference(ImpactSourceType.REVERSAL, SESSION, SCENARIO)


def test_typed_target_has_closed_attribute_contract() -> None:
    target = TypedImpactTarget(ImpactTargetType.RESOURCE, UUID(int=5), ImpactAttribute.QUANTITY, SESSION, SCENARIO)
    assert target.state_key.attribute == "quantity"
    with pytest.raises(DomainRuleViolation):
        TypedImpactTarget(ImpactTargetType.RESOURCE, UUID(int=5), ImpactAttribute.CAPACITY, SESSION, SCENARIO)


def test_dependency_and_conflict_events_are_immutable_typed_contracts() -> None:
    from dataclasses import FrozenInstanceError

    from tps360.simulation.domain import (
        ImpactConflictDetected,
        ImpactDefinitionId,
        ImpactDependency,
        ImpactInstanceId,
        StateKey,
    )
    dependency = ImpactDependency(ImpactDefinitionId(UUID(int=7)), required=False)
    event = ImpactConflictDetected(SESSION, SCENARIO, ImpactInstanceId(UUID(int=8)), 1, __import__("datetime").datetime(2026, 1, 1), "conflict", UUID(int=9), None, conflicting_impact_ids=(ImpactInstanceId(UUID(int=10)),), state_keys=(StateKey(ImpactTargetType.RESOURCE, UUID(int=5), "quantity"),))
    assert dependency.required is False and event.conflicting_impact_ids == (UUID(int=10),)
    with pytest.raises(FrozenInstanceError): event.policy = event.policy  # type: ignore[misc]


def test_activated_reversed_and_expired_events_are_immutable_typed_contracts() -> None:
    from dataclasses import FrozenInstanceError
    from datetime import datetime

    from tps360.simulation.domain import (
        ImpactActivated,
        ImpactExpired,
        ImpactInstanceId,
        ImpactReversed,
    )
    arguments = (SESSION, SCENARIO, ImpactInstanceId(UUID(int=12)), 1, datetime(2026, 1, 1), "lifecycle", UUID(int=13), None)
    for event_type in (ImpactActivated, ImpactReversed, ImpactExpired):
        event = event_type(*arguments)
        assert event.impact_id == UUID(int=12)
        with pytest.raises(FrozenInstanceError): event.reason = "changed"  # type: ignore[misc]
