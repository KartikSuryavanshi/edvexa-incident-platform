def test_analysis_is_deterministic_and_recovery_is_idempotent(client, service):
    client.post(f"/api/services/{service.id}/telemetry/simulate", json={"scenario": "unhealthy"})
    incident = client.get(f"/api/incidents?service_id={service.id}").json()["items"][0]

    analysis = client.post(f"/api/incidents/{incident['id']}/analysis")
    assert analysis.status_code == 200
    assert analysis.json()["provider"] == "deterministic-mock"
    assert analysis.json()["observed_facts"]
    assert analysis.json()["limitations"]

    request = {"action_type": "restart_simulated", "idempotency_key": "recovery-test-1", "approved": False}
    pending = client.post(f"/api/incidents/{incident['id']}/recovery", json=request)
    assert pending.status_code == 200
    assert pending.json()["status"] == "pending_approval"

    approved = client.post(f"/api/incidents/{incident['id']}/recovery", json={**request, "approved": True})
    repeated = client.post(f"/api/incidents/{incident['id']}/recovery", json={**request, "approved": True})
    assert approved.status_code == 200
    assert approved.json()["status"] == "succeeded"
    assert repeated.json()["id"] == approved.json()["id"]
    assert repeated.json()["attempts"] == 1


def test_recovery_retries_transient_simulated_failure(client, service):
    client.post(f"/api/services/{service.id}/telemetry/simulate", json={"scenario": "unhealthy"})
    incident = client.get(f"/api/incidents?service_id={service.id}").json()["items"][0]
    response = client.post(
        f"/api/incidents/{incident['id']}/recovery",
        json={"action_type": "retry_job_simulated", "idempotency_key": "retry-test-1", "approved": True},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "succeeded"
    assert response.json()["attempts"] == 2


def test_deterministic_analysis_is_offline_and_structured(client, service):
    client.post(f"/api/services/{service.id}/telemetry/simulate", json={"scenario": "degraded"})
    incident = client.get(f"/api/incidents?service_id={service.id}").json()["items"][0]

    response = client.post(f"/api/incidents/{incident['id']}/analysis")

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "deterministic-mock"
    assert payload["observed_facts"]
    assert payload["hypotheses"]
    assert payload["diagnostic_steps"]
    assert payload["recommendations"]
    assert 0 <= payload["confidence"] <= 1
    assert payload["limitations"] == ["No external logs, traces, or infrastructure signals are available in local demo mode."]
