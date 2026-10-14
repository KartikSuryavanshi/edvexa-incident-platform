from app.db.models import TelemetrySample
from app.services.monitoring import evaluate_health


def sample(latency_ms, error_rate, availability):
    return TelemetrySample(
        service_id=1,
        latency_ms=latency_ms,
        error_rate=error_rate,
        availability=availability,
    )


def test_health_evaluation_covers_realistic_states():
    assert evaluate_health(sample(80, 0.01, 0.999)).state == "healthy"
    assert evaluate_health(sample(450, 0.08, 0.985)).state == "degraded"
    assert evaluate_health(sample(1500, 0.30, 0.90)).state == "unhealthy"
