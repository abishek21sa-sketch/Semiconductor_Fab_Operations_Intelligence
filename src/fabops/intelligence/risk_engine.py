from dataclasses import dataclass

DEFAULT_WEIGHTS = {"queue_pressure": .20, "equipment_degradation": .20, "yield_excursion": .25, "maintenance_exposure": .15, "delivery_risk": .20}

@dataclass(frozen=True)
class RiskAnalysis:
    score: float
    level: str
    contributions: list[dict]

def analyze_risk(factors: dict, weights: dict | None = None) -> dict:
    weights = {**DEFAULT_WEIGHTS, **(weights or {})}
    contributions = [{"factor": k, "value": round(max(0, min(100, float(factors.get(k, 0)))), 2), "weight": weights[k], "contribution": round(max(0, min(100, float(factors.get(k, 0)))) * weights[k], 2)} for k in weights]
    score = round(sum(x["contribution"] for x in contributions), 2)
    level = "HIGH" if score >= 70 else "MEDIUM" if score >= 40 else "LOW"
    return {"score": score, "level": level, "contributions": sorted(contributions, key=lambda x: x["contribution"], reverse=True), "weights": weights}
