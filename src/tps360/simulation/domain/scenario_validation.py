from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .enums import ScenarioValidationLevel
from .scenario_definition import ScenarioDefinition

if TYPE_CHECKING:
    from .simulation import Simulation


@dataclass(frozen=True)
class ScenarioValidationMessage:
    level: ScenarioValidationLevel
    code: str
    message: str


@dataclass(frozen=True)
class ScenarioValidationResult:
    messages: tuple[ScenarioValidationMessage, ...]

    @property
    def errors(self) -> tuple[ScenarioValidationMessage, ...]:
        return tuple(message for message in self.messages if message.level is ScenarioValidationLevel.ERROR)

    @property
    def warnings(self) -> tuple[ScenarioValidationMessage, ...]:
        return tuple(message for message in self.messages if message.level is ScenarioValidationLevel.WARNING)

    @property
    def information(self) -> tuple[ScenarioValidationMessage, ...]:
        return tuple(
            message for message in self.messages if message.level is ScenarioValidationLevel.INFORMATION
        )

    @property
    def can_activate(self) -> bool:
        return not self.errors


class ScenarioCompatibilityPolicy:
    """Validates a scenario definition against immutable simulation inputs."""

    @staticmethod
    def validate(
        definition: ScenarioDefinition,
        simulation: Simulation,
        available_team_roles: tuple[str, ...],
    ) -> ScenarioValidationResult:
        messages: list[ScenarioValidationMessage] = []
        community_territories = set(simulation.community.settlements)
        missing_territories = set(definition.required_territories) - community_territories
        if missing_territories:
            messages.append(
                ScenarioValidationMessage(
                    ScenarioValidationLevel.ERROR,
                    "missing_territories",
                    "Required scenario territories are absent from the community snapshot.",
                )
            )
        community_infrastructure = set(simulation.community.critical_infrastructure)
        missing_infrastructure = set(definition.required_infrastructure) - community_infrastructure
        if missing_infrastructure:
            messages.append(
                ScenarioValidationMessage(
                    ScenarioValidationLevel.ERROR,
                    "missing_infrastructure",
                    "Required infrastructure is absent from the community snapshot.",
                )
            )
        missing_resources = set(definition.required_resource_ids) - set(
            simulation.context.available_resource_ids
        )
        if missing_resources:
            messages.append(
                ScenarioValidationMessage(
                    ScenarioValidationLevel.ERROR,
                    "missing_resources",
                    "Required resources are absent from the simulation context snapshot.",
                )
            )
        if (
            definition.supported_threat_types
            and simulation.threat.threat_type not in definition.supported_threat_types
        ):
            messages.append(
                ScenarioValidationMessage(
                    ScenarioValidationLevel.ERROR,
                    "unsupported_threat_type",
                    "The simulation threat type is not supported by the scenario.",
                )
            )
        missing_roles = set(definition.allowed_team_roles) - set(available_team_roles)
        if missing_roles:
            messages.append(
                ScenarioValidationMessage(
                    ScenarioValidationLevel.ERROR,
                    "missing_team_roles",
                    "Required team roles are unavailable for the simulation.",
                )
            )
        if any(event.timestamp < simulation.current_time for event in definition.planned_events):
            messages.append(
                ScenarioValidationMessage(
                    ScenarioValidationLevel.ERROR,
                    "invalid_event_timing",
                    "Planned events cannot precede the current simulation time.",
                )
            )
        if not definition.planned_events:
            messages.append(
                ScenarioValidationMessage(
                    ScenarioValidationLevel.WARNING,
                    "no_planned_events",
                    "The scenario contains no planned events.",
                )
            )
        if not definition.completion_criteria:
            messages.append(
                ScenarioValidationMessage(
                    ScenarioValidationLevel.WARNING,
                    "no_completion_criteria",
                    "The scenario has no explicit completion criteria.",
                )
            )
        messages.append(
            ScenarioValidationMessage(
                ScenarioValidationLevel.INFORMATION,
                "definition_checked",
                "Scenario definition was checked against immutable simulation inputs.",
            )
        )
        return ScenarioValidationResult(tuple(messages))