from uuid import UUID

import pytest

from tps360.core.exceptions import DomainRuleViolation
from tps360.threats.domain import (
    Threat,
    ThreatImpact,
    ThreatSeverity,
    ThreatTargetType,
    ThreatType,
)


def build_threat(**overrides: object) -> Threat:
    values: dict[str, object] = {
        "id": UUID("12345678-1234-5678-1234-567812345678"),
        "name": "Power grid attack",
        "threat_type": ThreatType.MILITARY,
        "severity": ThreatSeverity.HIGH,
        "target_type": ThreatTargetType.CRITICAL_INFRASTRUCTURE,
        "description": "A threat to electrical distribution infrastructure.",
        "impacts": (ThreatImpact.ESSENTIAL_SERVICES,),
        "is_active": True,
        "evidence": ("assessment",),
    }
    values.update(overrides)
    return Threat(**values)  # type: ignore[arg-type]


def test_valid_threat() -> None:
    assert build_threat().name == "Power grid attack"


def test_military_threat_type_value() -> None:
    assert ThreatType.MILITARY.value == "military"


def test_technological_threat_type_value() -> None:
    assert ThreatType.TECHNOLOGICAL.value == "technological"


def test_natural_threat_type_value() -> None:
    assert ThreatType.NATURAL.value == "natural"


def test_medical_biological_threat_type_value() -> None:
    assert ThreatType.MEDICAL_BIOLOGICAL.value == "medical_biological"


def test_social_humanitarian_threat_type_value() -> None:
    assert ThreatType.SOCIAL_HUMANITARIAN.value == "social_humanitarian"


def test_cyber_information_threat_type_value() -> None:
    assert ThreatType.CYBER_INFORMATION.value == "cyber_information"


def test_combined_threat_type_value() -> None:
    assert ThreatType.COMBINED.value == "combined"


def test_empty_name_raises_error() -> None:
    with pytest.raises(DomainRuleViolation):
        build_threat(name=" ")


def test_empty_description_raises_error() -> None:
    with pytest.raises(DomainRuleViolation):
        build_threat(description=" ")


def test_duplicate_impacts_raise_error() -> None:
    with pytest.raises(DomainRuleViolation):
        build_threat(impacts=(ThreatImpact.HEALTH, ThreatImpact.HEALTH))


def test_empty_evidence_raises_error() -> None:
    with pytest.raises(DomainRuleViolation):
        build_threat(evidence=(" ",))


def test_has_impact_returns_true() -> None:
    assert build_threat().has_impact(ThreatImpact.ESSENTIAL_SERVICES)


def test_has_impact_returns_false() -> None:
    assert not build_threat().has_impact(ThreatImpact.ENVIRONMENT)


def test_critical_threat_is_critical() -> None:
    assert build_threat(severity=ThreatSeverity.CRITICAL).is_critical()


def test_non_critical_threat_is_not_critical() -> None:
    assert not build_threat(severity=ThreatSeverity.HIGH).is_critical()


def test_active_threat_is_active() -> None:
    assert build_threat().is_active


def test_deactivate_threat() -> None:
    threat = build_threat()

    threat.deactivate()

    assert not threat.is_active


def test_activate_threat() -> None:
    threat = build_threat(is_active=False)

    threat.activate()

    assert threat.is_active


def test_target_type_is_preserved() -> None:
    assert build_threat(target_type=ThreatTargetType.INFORMATION_SYSTEM).target_type is (
        ThreatTargetType.INFORMATION_SYSTEM
    )