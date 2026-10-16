from app.core.database import SessionLocal
from app.db.models import HealthCheck, Service


def seed():
    with SessionLocal() as db:
        if db.query(Service).count() == 0:
            services = [
                Service(name="checkout-api", environment="demo", status="healthy"),
                Service(name="payments-worker", environment="demo", status="healthy"),
                Service(name="catalog-api", environment="demo", status="healthy"),
            ]
            db.add_all(services)
            db.flush()
            for service in services:
                db.add(HealthCheck(name=f"{service.name} synthetic", service_id=service.id, endpoint=f"/demo/{service.name}/health"))
            db.commit()


if __name__ == "__main__":
    seed()
