import pytest

from tps360.core.exceptions import DomainRuleViolation
from tps360.simulation.domain.time_dilation import (
    CrisisVelocity,
    SimulationRoundClock,
    resolve_crisis_velocity,
)


def test_time_dilation_clock_initialization() -> None:
    clock = SimulationRoundClock(real_round_minutes=10, velocity=CrisisVelocity.FAST)
    assert clock.real_round_minutes == 10
    assert clock.velocity is CrisisVelocity.FAST
    assert clock.simulated_minutes_per_real_minute == 30
    assert clock.total_simulated_minutes_per_round == 300
    assert clock.total_simulated_hours_per_round == 5.0


def test_time_dilation_clock_invalid_round_length_raises_error() -> None:
    with pytest.raises(DomainRuleViolation, match="between 5 and 30 minutes"):
        SimulationRoundClock(real_round_minutes=4)

    with pytest.raises(DomainRuleViolation, match="between 5 and 30 minutes"):
        SimulationRoundClock(real_round_minutes=35)


@pytest.mark.parametrize(
    "crisis_type,expected_velocity,expected_sim_minutes_per_min",
    [
        ("FIRE", CrisisVelocity.FAST, 30),
        ("MILITARY_ATTACK", CrisisVelocity.FAST, 30),
        ("CHOLERA", CrisisVelocity.MODERATE, 60),
        ("WATER_CONTAMINATION", CrisisVelocity.MODERATE, 60),
        ("LIVESTOCK_MORTALITY", CrisisVelocity.SLOW_MAX, 90),
        ("QUARANTINE_ISOLATION", CrisisVelocity.SLOW_MAX, 90),
        ("BLACKOUT", CrisisVelocity.SLOW_MAX, 90),
    ],
)
def test_crisis_velocity_resolution(
    crisis_type: str, expected_velocity: CrisisVelocity, expected_sim_minutes_per_min: int
) -> None:
    velocity = resolve_crisis_velocity(crisis_type)
    assert velocity is expected_velocity
    clock = SimulationRoundClock(real_round_minutes=10, velocity=velocity)
    assert clock.simulated_minutes_per_real_minute == expected_sim_minutes_per_min


def test_simulated_seconds_passed_calculation() -> None:
    clock = SimulationRoundClock(real_round_minutes=20, velocity=CrisisVelocity.SLOW_MAX)
    # Ratio 1:90 -> 60 real seconds = 5400 simulated seconds (90 simulated minutes)
    assert clock.simulated_seconds_passed(60.0) == 5400.0
