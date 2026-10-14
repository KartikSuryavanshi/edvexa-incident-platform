def test_repeated_failure_is_deduplicated(client, service):
    first = client.post(f"/api/services/{service.id}/telemetry/simulate", json={"scenario": "unhealthy", "count": 1})
    second = client.post(f"/api/services/{service.id}/telemetry/simulate", json={"scenario": "unhealthy", "count": 1})
    assert first.status_code == 201
    assert second.status_code == 201

    incidents = client.get(f"/api/incidents?service_id={service.id}").json()
    assert incidents["total"] == 1
    events = client.get(f"/api/incidents/{incidents['items'][0]['id']}/events")
    assert events.status_code == 200
    assert [event["event_type"] for event in events.json()] == ["incident_created", "signal_observed"]


def test_recovery_closes_incident_and_next_failure_reopens_new_incident(client, service):
    client.post(f"/api/services/{service.id}/telemetry/simulate", json={"scenario": "unhealthy"})
    client.post(f"/api/services/{service.id}/telemetry/simulate", json={"scenario": "healthy"})
    client.post(f"/api/services/{service.id}/telemetry/simulate", json={"scenario": "unhealthy"})

    incidents = client.get(f"/api/incidents?service_id={service.id}&limit=10").json()
    assert incidents["total"] == 2
    assert {item["status"] for item in incidents["items"]} == {"open", "resolved"}
