from datetime import datetime
from uuid import UUID, uuid4

import pytest

from tps360.core.exceptions import DomainRuleViolation
from tps360.simulation.domain import (
    ImpactAttribute,
    ImpactCategory,
    ImpactChange,
    ImpactDefinition,
    ImpactDefinitionId,
    ImpactInstanceId,
    ImpactOperation,
    ImpactSourceReference,
    ImpactSourceType,
    ImpactStatus,
    ImpactTargetType,
    SimulationState,
    StateValue,
    TypedImpactTarget,
)

SESSION, SCENARIO, RESOURCE = UUID(int=1), UUID(int=2), UUID(int=3)
NOW = datetime(2026, 1, 1)


def target(attribute: ImpactAttribute = ImpactAttribute.QUANTITY) -> TypedImpactTarget:
    return TypedImpactTarget(ImpactTargetType.RESOURCE, RESOURCE, attribute, SESSION, SCENARIO)


def source() -> ImpactSourceReference:
    return ImpactSourceReference(ImpactSourceType.SYSTEM, SESSION, SCENARIO)


def definition(*changes: ImpactChange, **values: object) -> ImpactDefinition:
    data: dict[str, object] = {"id": ImpactDefinitionId(uuid4()), "scenario_id": SCENARIO, "source": source(), "name": "Resource", "description": "Typed impact", "category": ImpactCategory.RESOURCE, "changes": changes}
    data.update(values)
    return ImpactDefinition(**data)  # type: ignore[arg-type]


def test_definition_requires_typed_source_and_target() -> None:
    change = ImpactChange(target(), ImpactOperation.INCREASE, 2.0, "units")
    assert definition(change).source.source_type is ImpactSourceType.SYSTEM
    with pytest.raises(DomainRuleViolation):
        ImpactChange(target(), ImpactOperation.ACTIVATE, True, "state")


def test_operation_attribute_matrix_rejects_invalid_combination() -> None:
    with pytest.raises(DomainRuleViolation):
        ImpactChange(target(ImpactAttribute.STATUS), ImpactOperation.MULTIPLY, 2.0, "x")


def test_state_key_is_derived_from_typed_target() -> None:
    assert target().state_key.attribute == ImpactAttribute.QUANTITY.value


def test_required_failure_is_atomic_without_state_calculation() -> None:
    required = ImpactChange(target(), ImpactOperation.DECREASE, 2.0, "units")
    from tps360.simulation.domain import ImpactEngine
    engine = ImpactEngine(SESSION, SCENARIO)
    state = SimulationState(SESSION, 4, (StateValue(target().state_key, 1.0),))
    with pytest.raises(DomainRuleViolation): engine._calculate(state, (required,))
    assert state.version == 4 and state.get(target().state_key) == 1.0


def test_optional_failure_is_structured_skip() -> None:
    optional = ImpactChange(target(), ImpactOperation.DECREASE, 2.0, "units", required=False)
    from tps360.simulation.domain import ImpactEngine
    _, skipped, values = ImpactEngine(SESSION, SCENARIO)._calculate(SimulationState(SESSION, 0, (StateValue(target().state_key, 1.0),)), (optional,))
    assert len(skipped) == 1 and skipped[0].change is optional and values[0].value == 1.0


def test_lifecycle_transition_matrix_and_final_protection() -> None:
    from tps360.simulation.domain import ImpactInstance
    instance = ImpactInstance(ImpactInstanceId(uuid4()), definition(ImpactChange(target(), ImpactOperation.INCREASE, 1.0, "units")), SESSION, NOW, uuid4(), None)
    instance.transition(ImpactStatus.READY); instance.transition(ImpactStatus.APPLIED)
    with pytest.raises(DomainRuleViolation): instance.transition(ImpactStatus.CANCELLED)

@pytest.mark.parametrize(
    ("operation", "value", "attribute"),
    [
        (ImpactOperation.SET, 1.0, ImpactAttribute.QUANTITY),
        (ImpactOperation.INCREASE, 1.0, ImpactAttribute.QUANTITY),
        (ImpactOperation.DECREASE, 1.0, ImpactAttribute.QUANTITY),
        (ImpactOperation.MULTIPLY, 2.0, ImpactAttribute.QUANTITY),
        (ImpactOperation.DAMAGE, 1.0, ImpactAttribute.QUANTITY),
        (ImpactOperation.RESTORE, 1.0, ImpactAttribute.QUANTITY),
        (ImpactOperation.CONSUME, 1.0, ImpactAttribute.QUANTITY),
        (ImpactOperation.REPLENISH, 1.0, ImpactAttribute.QUANTITY),
        (ImpactOperation.ACTIVATE, True, ImpactAttribute.STATUS),
        (ImpactOperation.DEACTIVATE, False, ImpactAttribute.STATUS),
        (ImpactOperation.LOCK, True, ImpactAttribute.STATUS),
        (ImpactOperation.UNLOCK, True, ImpactAttribute.STATUS),
    ],
)
def test_supported_operations_have_typed_attribute_contract(operation: ImpactOperation, value: float | bool, attribute: ImpactAttribute) -> None:
    assert ImpactChange(target(attribute), operation, value, "unit").operation is operation


def test_system_source_has_no_untyped_identifier() -> None:
    assert source().event_id is None and source().decision_outcome_id is None


def test_definition_rejects_target_from_another_session() -> None:
    foreign = TypedImpactTarget(ImpactTargetType.RESOURCE, RESOURCE, ImpactAttribute.QUANTITY, UUID(int=99), SCENARIO)
    with pytest.raises(DomainRuleViolation):
        definition(ImpactChange(foreign, ImpactOperation.INCREASE, 1.0, "units"))

class _Simulation:
    def __init__(self, state: SimulationState) -> None:
        self.id = SESSION
        self.current_time = NOW
        self.simulation_state = state

    @property
    def state(self) -> SimulationState:
        return self.simulation_state

    def replace_simulation_state(self, state: SimulationState) -> None:
        self.simulation_state = state


def test_apply_required_failure_preserves_state_version_and_state_events() -> None:
    from tps360.simulation.domain import ImpactEngine
    failing = definition(ImpactChange(target(), ImpactOperation.DECREASE, 2.0, "units"))
    simulation = _Simulation(SimulationState(SESSION, 7, (StateValue(target().state_key, 1.0),)))
    engine = ImpactEngine(SESSION, SCENARIO)
    instance = engine.create(simulation, ImpactInstanceId(uuid4()), failing, uuid4())
    with pytest.raises(DomainRuleViolation):
        engine.apply(simulation, instance.id)
    assert simulation.state.version == 7
    assert all(type(event).__name__ != "SimulationStateChanged" for event in engine.audit_trail)


def test_apply_is_atomic_and_records_typed_applied_and_state_events() -> None:
    from tps360.simulation.domain import ImpactEngine
    valid = definition(ImpactChange(target(), ImpactOperation.INCREASE, 2.0, "units"))
    simulation = _Simulation(SimulationState(SESSION, 0, (StateValue(target().state_key, 1.0),)))
    engine = ImpactEngine(SESSION, SCENARIO)
    instance = engine.create(simulation, ImpactInstanceId(uuid4()), valid, uuid4())
    result = engine.apply(simulation, instance.id)
    assert result.state_version_before == 0 and result.state_version_after == 1
    assert {type(event).__name__ for event in engine.audit_trail} >= {"ImpactApplied", "SimulationStateChanged"}


def test_delayed_lifecycle_and_cancellation_matrix() -> None:
    from tps360.simulation.domain import ImpactInstance
    instance = ImpactInstance(ImpactInstanceId(uuid4()), definition(ImpactChange(target(), ImpactOperation.INCREASE, 1.0, "units"), delay_minutes=1), SESSION, NOW, uuid4(), None)
    instance.transition(ImpactStatus.SCHEDULED)
    instance.transition(ImpactStatus.READY)
    instance.transition(ImpactStatus.CANCELLED)
    with pytest.raises(DomainRuleViolation):
        instance.transition(ImpactStatus.READY)

@pytest.mark.parametrize(
    ("operation", "start", "value", "expected"),
    [
        (ImpactOperation.SET, 4.0, 3.0, 3.0),
        (ImpactOperation.ADD, 4.0, 3.0, 7.0),
        (ImpactOperation.SUBTRACT, 4.0, 3.0, 1.0),
        (ImpactOperation.MULTIPLY, 4.0, 3.0, 12.0),
        (ImpactOperation.DIVIDE, 4.0, 2.0, 2.0),
        (ImpactOperation.MIN, 4.0, 3.0, 3.0),
        (ImpactOperation.MAX, 4.0, 3.0, 4.0),
        (ImpactOperation.DAMAGE, 4.0, 3.0, 1.0),
        (ImpactOperation.RESTORE, 4.0, 3.0, 7.0),
    ],
)
def test_numeric_operation_execution(operation: ImpactOperation, start: float, value: float, expected: float) -> None:
    from tps360.simulation.domain import ImpactEngine
    assert ImpactEngine._operate(start, ImpactChange(target(), operation, value, "units")) == expected


def test_divide_by_zero_and_non_finite_values_are_rejected() -> None:
    from tps360.simulation.domain import ImpactEngine
    with pytest.raises(DomainRuleViolation): ImpactEngine._operate(1.0, ImpactChange(target(), ImpactOperation.DIVIDE, 0.0, "units"))
    with pytest.raises(DomainRuleViolation): ImpactChange(target(), ImpactOperation.ADD, float("nan"), "units")
    with pytest.raises(DomainRuleViolation): ImpactChange(target(), ImpactOperation.ADD, float("inf"), "units")


def test_boolean_is_rejected_for_numeric_operation_and_negative_result_is_rejected() -> None:
    from tps360.simulation.domain import ImpactEngine
    with pytest.raises(DomainRuleViolation): ImpactChange(target(), ImpactOperation.ADD, True, "units")
    with pytest.raises(DomainRuleViolation): ImpactEngine(SESSION, SCENARIO)._calculate(SimulationState(SESSION, 0, (StateValue(target().state_key, 1.0),)), (ImpactChange(target(), ImpactOperation.SUBTRACT, 2.0, "units"),))


def test_full_final_status_transition_protection() -> None:
    from tps360.simulation.domain import ImpactInstance
    for final in (ImpactStatus.APPLIED, ImpactStatus.REVERSED, ImpactStatus.EXPIRED, ImpactStatus.CANCELLED, ImpactStatus.FAILED):
        instance = ImpactInstance(ImpactInstanceId(uuid4()), definition(ImpactChange(target(), ImpactOperation.ADD, 1.0, "units")), SESSION, NOW, uuid4(), None, status=final)
        with pytest.raises(DomainRuleViolation): instance.transition(ImpactStatus.READY)
