from __future__ import annotations

from dataclasses import dataclass

from tps360.community.domain.passport_read_model import CommunityPassportReadModel
from tps360.core.exceptions import DomainRuleViolation
from tps360.simulation.domain.time_dilation import SimulationRoundClock


@dataclass(frozen=True)
class SimulationContextSnapshotReadModel:
    """Immutable pre-start snapshot combining community passport, scenario metadata, time dilation, and role scoping."""

    session_id: str
    community_passport: CommunityPassportReadModel
    scenario_id: str
    scenario_title: str
    threat_categories: tuple[str, ...]
    time_dilation_clock: SimulationRoundClock
    is_osm_bounded: bool = True
    bounding_box: dict[str, float] | None = None
    facilitator_role_id: str = "facilitator_moderator"
    max_participants: int = 10

    def __post_init__(self) -> None:
        if not self.session_id or not self.scenario_id or not self.scenario_title:
            raise DomainRuleViolation("Simulation Context Snapshot requires session_id, scenario_id, and scenario_title.")
        if self.max_participants < 1:
            raise DomainRuleViolation("max_participants must be at least 1.")
