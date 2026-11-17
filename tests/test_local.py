import os
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from perfima.database import get_db
from perfima.models import Base, Category, User
from perfima.routes import local, category
from perfima.services import local_service

# The main app only mounts the local router when PERFIMA_LOCAL_MODE=1 at import time, so these tests build their own app
SQLALCHEMY_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///./test_local.db")
connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()
app.include_router(local.router)
app.include_router(category.router)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def client():
    return TestClient(app, base_url="http://127.0.0.1")


def session_headers(client):
    response = client.post("/local/session")
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_session_creates_local_user_once(client):
    first = session_headers(client)
    second = session_headers(client)

    db = TestingSessionLocal()
    try:
        assert db.query(User).filter(User.username == local_service.LOCAL_USERNAME).count() == 1
        assert db.query(Category).count() == len(local_service.DEFAULT_CATEGORIES)
    finally:
        db.close()

    for headers in (first, second):
        names = [c["name"] for c in client.get("/categories/", headers=headers).json()]
        assert sorted(names) == sorted(local_service.DEFAULT_CATEGORIES)


def test_heartbeat_and_shutdown_need_a_token(client):
    assert client.post("/local/heartbeat").status_code == 401
    assert client.post("/local/shutdown").status_code == 401

    headers = session_headers(client)
    assert client.post("/local/heartbeat", headers=headers).status_code == 200
    assert local_service.state.idle_seconds() < 5

    assert client.post("/local/shutdown", headers=headers).status_code == 200
    assert local_service.state.shutdown.is_set()
    local_service.state.shutdown.clear()


def test_non_local_host_is_rejected():
    remote = TestClient(app, base_url="http://perfima.example.com")
    assert remote.post("/local/session").status_code == 403
