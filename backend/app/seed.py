from app.core.database import SessionLocal, engine
from app.db.models import Base, HealthCheck, Service


def seed():
    Base.metadata.create_all(bind=engine)
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
