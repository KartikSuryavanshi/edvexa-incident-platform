def test_telemetry_validation_and_missing_resources(client, service):
    invalid = client.post(
        f"/api/services/{service.id}/telemetry",
        json={"latency_ms": -1, "error_rate": 0.1, "availability": 0.99},
    )
    assert invalid.status_code == 422
    assert client.get("/api/services/9999/health").status_code == 404
    assert client.get(f"/api/services/{service.id}/telemetry?limit=0").status_code == 422
