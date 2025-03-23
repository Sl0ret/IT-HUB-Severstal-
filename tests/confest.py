import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.testclient import TestClient

from internal.models.models import Base

from app.main import app

from internal.storage.database import get_storage

@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)

    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    from internal.storage.database_storage import DatabaseStorage

    def override_get_storage():
        return DatabaseStorage(db_session)

    app.dependency_overrides[get_storage] = override_get_storage

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
    db_session.close()