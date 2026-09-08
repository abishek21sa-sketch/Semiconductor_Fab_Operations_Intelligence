def calculate_health_index(utilization=0, alarms=0, pm_due_hours=999, failures=0):
    score = max(0, min(100, 100 - float(utilization)*.2 - alarms*4 - max(0, 24-pm_due_hours)*.8 - failures*10))
    return {"health_score": round(score, 2), "utilization_stress": round(min(100, float(utilization)), 2), "alarm_exposure": alarms, "pm_exposure_hours": pm_due_hours}
