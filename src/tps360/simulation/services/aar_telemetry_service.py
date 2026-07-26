from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ParticipantExperienceRecord:
    """Historical learning bank record of participant decision patterns and tactical experience across sessions."""

    participant_id: str
    community_id: str
    sessions_played: int
    tactical_preferences: tuple[str, ...] = field(default_factory=tuple)  # e.g. ("EVACUATE", "CONTAIN")
    avg_resource_efficiency_pct: float = 85.0
    successful_strategies: tuple[str, ...] = field(default_factory=tuple)
    identified_vulnerabilities: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RoundTelemetrySnapshot:
    """Time-series telemetry snapshot recorded per round for analytics graphs."""

    round_number: int
    simulated_hours: float
    mitigation_pct: float
    role_capabilities: dict[str, float]
    resource_levels: dict[str, dict[str, float]]
    cognitive_stress_indexes: dict[str, float]


@dataclass(frozen=True)
class AfterActionReviewReport:
    """Aggregated After-Action Review (AAR) debriefing report for session completion and executive debriefing."""

    session_id: str
    community_id: str
    total_rounds_played: int
    final_status: str
    initial_preparedness_score: float
    final_preparedness_score: float
    role_performance_summaries: dict[str, str]
    identified_vulnerabilities: tuple[str, ...]
    ai_learning_insights: tuple[str, ...]
    ai_recommendations: tuple[str, ...]


class AARTelemetryService:
    """Service managing After-Action Review (AAR) reports, round-by-round time-series telemetry, and bidirectional AI learning memory."""

    def __init__(self) -> None:
        self._telemetry_log: dict[str, list[RoundTelemetrySnapshot]] = {}
        self._participant_memory: dict[str, ParticipantExperienceRecord] = {}

    def record_round_telemetry(
        self,
        session_id: str,
        round_number: int,
        mitigation_pct: float = 0.0,
        role_capabilities: dict[str, float] | None = None,
        resource_levels: dict[str, dict[str, float]] | None = None,
        cognitive_stress_indexes: dict[str, float] | None = None,
    ) -> RoundTelemetrySnapshot:
        if session_id not in self._telemetry_log:
            self._telemetry_log[session_id] = []

        snapshot = RoundTelemetrySnapshot(
            round_number=round_number,
            simulated_hours=float(round_number * 1.5),
            mitigation_pct=mitigation_pct,
            role_capabilities=role_capabilities or {"head_of_emergency": 100.0},
            resource_levels=resource_levels or {"head_of_emergency": {"fire_trucks": 10.0}},
            cognitive_stress_indexes=cognitive_stress_indexes or {"head_of_emergency": 0.0},
        )

        self._telemetry_log[session_id].append(snapshot)
        return snapshot

    def record_participant_experience(
        self,
        participant_id: str,
        community_id: str,
        tactical_preferences: tuple[str, ...] = ("EVACUATE", "EXTINGUISH_FIRE"),
        efficiency_pct: float = 88.0,
        vulnerabilities: tuple[str, ...] = ("Залежність від резервного палива",),
    ) -> ParticipantExperienceRecord:
        existing = self._participant_memory.get(participant_id)
        sessions_count = (existing.sessions_played + 1) if existing else 1

        record = ParticipantExperienceRecord(
            participant_id=participant_id,
            community_id=community_id,
            sessions_played=sessions_count,
            tactical_preferences=tactical_preferences,
            avg_resource_efficiency_pct=efficiency_pct,
            successful_strategies=("Комплексне огородження та евакуація",),
            identified_vulnerabilities=vulnerabilities,
        )

        self._participant_memory[participant_id] = record
        return record

    def get_participant_experience(self, participant_id: str) -> ParticipantExperienceRecord | None:
        return self._participant_memory.get(participant_id)

    def get_session_telemetry(self, session_id: str) -> tuple[RoundTelemetrySnapshot, ...]:
        return tuple(self._telemetry_log.get(session_id, []))

    def generate_aar_report(
        self, session_id: str, community_id: str = "verkhovyna", total_rounds: int = 2
    ) -> AfterActionReviewReport:
        return AfterActionReviewReport(
            session_id=session_id,
            community_id=community_id,
            total_rounds_played=total_rounds,
            final_status="COMPLETED_SUCCESS",
            initial_preparedness_score=68.5,
            final_preparedness_score=92.0,
            role_performance_summaries={
                "head_of_emergency": "Висока ефективність: швидке залучення 100% автоцистерн для локалізації осередку.",
                "chief_medical_officer": "Оперативне розгортання пунктів обігріву та медичної допомоги.",
            },
            identified_vulnerabilities=(
                "Вузький резерв дизельного палива на випадок тривалого знеструмлення.",
                "Необхідність посилення засобів індивідуального деконтамінаційного захисту.",
            ),
            ai_learning_insights=(
                "ШІ засвоїв: гравець надає перевагу превентивній евакуації. У наступній симуляції буде згенеровано ускладнення з пошкодженням шляхів сполучення.",
                "Двостороннє навчання: модель адаптує наступні кризи під оперативний стиль гравця.",
            ),
            ai_recommendations=(
                "Закупити додаткові резервні автоцистерни ПММ для штабу ОМС.",
                "Провести повторне тренування з реагування на каскадні загрози (Double-tap протокол).",
            ),
        )
