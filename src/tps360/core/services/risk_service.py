from tps360.core.domain.models import Risk


class RiskService:
    """Provisional, documented calculation; not an approved TPS360 methodology."""

    def calculate_risk(self, risk: Risk) -> float:
        # Weighted exposure-impact-probability score, reduced by available capability.
        raw = (
            (risk.probability_score * 0.35)
            + (risk.impact_score * 0.40)
            + (risk.exposure_score * 0.25)
        )
        return round(max(0.0, min(100.0, raw * (1 - risk.capability_modifier / 200))), 2)

    def validate_evidence(self, risk: Risk) -> bool:
        return bool(risk.evidence) and all(item.strip() for item in risk.evidence)

    def classify_risk_level(self, score: float) -> str:
        if score < 25:
            return "low"
        if score < 50:
            return "moderate"
        if score < 75:
            return "high"
        return "critical"
