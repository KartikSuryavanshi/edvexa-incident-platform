from fastapi.testclient import TestClient

from app.main import app


def test_state_changes_require_operator_role(client, service):
    viewer = TestClient(app, headers={"Authorization": "Bearer viewer-test"})
    response = viewer.post(f"/api/services/{service.id}/telemetry/simulate", json={"scenario": "degraded"})
    assert response.status_code == 403


def test_protected_reads_require_a_valid_token(service):
    anonymous = TestClient(app)
    response = anonymous.get("/api/services")
    assert response.status_code == 401
