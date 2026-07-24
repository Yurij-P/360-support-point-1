from tps360.core.domain.models import Evaluation


class EvaluationService:
    def evaluate_criterion(self, achieved: float) -> float:
        return max(0.0, min(100.0, achieved))

    def evaluate_capability(self, values: list[float]) -> float:
        return round(sum(values) / len(values), 2) if values else 0.0

    def calculate_simulation_score(self, evaluation: Evaluation) -> float:
        values = list(evaluation.criteria_results.values()) + list(
            evaluation.capability_scores.values()
        )
        return self.evaluate_capability(values)

    def generate_findings(self, evaluation: Evaluation) -> list[str]:
        return [f"Gap: {gap}" for gap in evaluation.gaps] + [
            f"Strength: {item}" for item in evaluation.strengths
        ]
