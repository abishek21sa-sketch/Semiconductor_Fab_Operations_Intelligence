
def create_decision_packet(lot, risk, options):
    return {"decision_id":"DEC-"+lot,"situation":f"Risk detected for {lot}",
            "risk":risk,"options":options,"confidence":0.86,"approval":"SUPERVISOR_REQUIRED"}
