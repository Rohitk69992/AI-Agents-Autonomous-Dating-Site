import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.base import Base
from app.db.session import engine
from app.db.seed_demo import seed_database

@pytest.fixture(scope="session")
def client():
    Base.metadata.create_all(bind=engine)
    seed_database(run_simulation=True)
    with TestClient(app) as c:
        yield c
