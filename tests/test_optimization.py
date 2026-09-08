from fabops.optimization.scheduler import optimize_parallel_tool_assignment

def test_assignment_respects_qualification():
    jobs=[{"job_id":"A","process_time":5,"qualified_tools":["T1"]},{"job_id":"B","process_time":7,"qualified_tools":["T2"]}]
    r=optimize_parallel_tool_assignment(jobs,["T1","T2"])
    assert r.success
    assert {x["job_id"]:x["tool_id"] for x in r.assignments}=={"A":"T1","B":"T2"}
