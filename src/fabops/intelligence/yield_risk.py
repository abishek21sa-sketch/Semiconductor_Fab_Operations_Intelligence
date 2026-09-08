from datetime import datetime, timezone

def assess_yield_risk(metrology: dict | None = None, spc: dict | None = None, history: dict | None = None) -> dict:
    metrology, spc, history = metrology or {}, spc or {}, history or {}
    signals = {"shewhart": float(spc.get("shewhart", 0)), "ewma": float(spc.get("ewma", 0)), "cusum": float(spc.get("cusum", 0)), "metrology_excursion": float(metrology.get("excursion", 0))}
    severity = round(min(100, sum(min(100, max(0, v)) for v in signals.values()) / len(signals)), 2)
    return {"predicted_yield_impact_pct": round(-severity * .35, 2), "risk_score": severity, "confidence": round(min(.99, .55 + .1 * min(4, len(history.get("samples", []))) / 4), 2), "signals": signals, "affected_lots": history.get("affected_lots", []), "evidence": [k for k, v in signals.items() if v > 0], "timestamp": datetime.now(timezone.utc).isoformat()}
