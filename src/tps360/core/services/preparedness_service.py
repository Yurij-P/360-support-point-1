from tps360.core.domain.enums import MaturityLevel


class PreparednessService:
    def calculate_dimension_score(self, values: list[float]) -> float:
        if not values:
            return 0.0
        return round(sum(values) / len(values), 2)

    def calculate_total_score(self, dimensions: dict[str, float]) -> float:
        return self.calculate_dimension_score(list(dimensions.values()))

    def determine_maturity_level(self, score: float) -> MaturityLevel:
        if score < 20:
            return MaturityLevel.REACTIVE
        if score < 40:
            return MaturityLevel.BASIC
        if score < 60:
            return MaturityLevel.MANAGED
        if score < 80:
            return MaturityLevel.INTEGRATED
        return MaturityLevel.RESILIENT

    def detect_evidence_gaps(self, dimensions: dict[str, float], evidence: list[str]) -> list[str]:
        return list(dimensions) if not evidence else []
