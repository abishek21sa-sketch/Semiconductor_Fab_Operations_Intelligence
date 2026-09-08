
from .risk_scoring import score_lot
def build_lot_passport(lot_id, operations=14, queue=65, yield_risk=72, equipment=55, delivery=61):
    risk=score_lot(queue,yield_risk,equipment,delivery)
    return {"lot_id":lot_id,"completed_steps":operations,"risk":{"score":risk.score,"level":risk.level,"drivers":risk.drivers},
            "recommendation":"ENGINEERING_REVIEW" if risk.level=="HIGH" else "CONTINUE_MONITORING"}
