def test_lifecycle_transition_and_invalid_transition_are_audited(client, service):
    client.post(f"/api/services/{service.id}/telemetry/simulate", json={"scenario": "unhealthy"})
    incident = client.get(f"/api/incidents?service_id={service.id}").json()["items"][0]

    acknowledged = client.post(
        f"/api/incidents/{incident['id']}/transition",
        json={"status": "acknowledged", "message": "Operator triage started"},
        headers={"X-Actor": "test-operator"},
    )
    assert acknowledged.status_code == 200
    invalid = client.post(f"/api/incidents/{incident['id']}/transition", json={"status": "reopened"})
    assert invalid.status_code == 409

    events = client.get(f"/api/incidents/{incident['id']}/events")
    assert events.status_code == 200
    assert events.json()[-1]["event_type"] == "lifecycle_transition"
    assert events.json()[-1]["event_metadata"]["to_status"] == "acknowledged"
