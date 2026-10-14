import os

os.environ["DATABASE_URL"] = "sqlite:///./test_edvexa.db"

import pytest
from fastapi.testclient import TestClient

from app.core.database import engine
from app.db.models import Base, Service
from app.main import app


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def service():
    from app.core.database import SessionLocal

    with SessionLocal() as db:
        item = Service(name="test-api", environment="test", status="healthy")
        db.add(item)
        db.commit()
        db.refresh(item)
        return item
