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
