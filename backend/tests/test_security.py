from fastapi.testclient import TestClient
from fastapi.security import HTTPAuthorizationCredentials

from app.core.security import current_user
from app.main import app


def test_state_changes_require_operator_role(client, service):
    viewer = TestClient(app, headers={"Authorization": "Bearer viewer-test"})
    response = viewer.post(f"/api/services/{service.id}/telemetry/simulate", json={"scenario": "degraded"})
    assert response.status_code == 403


def test_protected_reads_require_a_valid_token(service):
    anonymous = TestClient(app)
    response = anonymous.get("/api/services")
    assert response.status_code == 401


def test_sse_requires_authentication_and_accepts_viewer_query_token():
    anonymous = TestClient(app)
    assert anonymous.get("/api/events/stream").status_code == 401
    viewer = current_user(credentials=None, access_token="viewer-test")
    assert viewer.role == "viewer"
    bearer = current_user(credentials=HTTPAuthorizationCredentials(scheme="Bearer", credentials="viewer-test"), access_token=None)
    assert bearer.role == "viewer"
