def predict_failure(health_score=100, alarms=0, pm_due_hours=999):
    probability = max(0, min(.99, .02 + (100-health_score)*.006 + alarms*.015 + max(0, 24-pm_due_hours)*.01))
    return {"failure_probability": round(probability, 3), "recommended_action": "SCHEDULE_PM_WITHIN_24_HOURS" if probability >= .15 else "CONTINUE_MONITORING"}
