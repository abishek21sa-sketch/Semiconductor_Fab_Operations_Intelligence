
def synthesize(lot_passport):
    risk=lot_passport["risk"]
    action="MOVE_LOT_AND_REVIEW_TOOL" if risk["level"]=="HIGH" else "MONITOR"
    return {"agent":"decision_synthesizer","lot":lot_passport["lot_id"],
            "recommendation":action,"evidence":risk["drivers"],"human_gate":True}
