from fastapi.testclient import TestClient

from fabops.api.app import app


def test_public_data_route_exposes_research_boundary():
    response = TestClient(app).get("/research/public-data")
    assert response.status_code == 200
    body = response.json()
    assert body["dataset"]
    assert body["claim_boundary"]
    assert body["autonomous_execution"] is False
    assert body["case_study"]["status"] in {"ACTIVE", "ACQUISITION_REQUIRED", "TARGET_UNAVAILABLE"}
