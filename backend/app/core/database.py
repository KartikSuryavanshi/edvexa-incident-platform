from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings

database_url = settings.sqlalchemy_database_url
is_sqlite = database_url.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}
pool_options = {"poolclass": StaticPool} if database_url in {"sqlite://", "sqlite:///:memory:"} else {}
engine = create_engine(database_url, connect_args=connect_args, pool_pre_ping=True, **pool_options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
