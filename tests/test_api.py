import os
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from perfima.main import app
from perfima.database import get_db
from perfima.models import Base

# End to end tests through the HTTP layer, so routes, controllers and services are exercised together
SQLALCHEMY_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///./test_api.db")
connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    previous = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if previous:
        app.dependency_overrides[get_db] = previous
    else:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def auth_headers(client, username):
    client.post("/signup", json={
        "username": username,
        "email": f"{username}@example.com",
        "name": username.title(),
        "password": "password123",
    })
    response = client.post("/login", data={"username": username, "password": "password123"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture(scope="module")
def headers(client):
    return auth_headers(client, "apiuser")


def new_transaction(client, headers, **overrides):
    payload = {
        "amount": 12.5,
        "date": date.today().isoformat(),
        "description": "Lunch",
        "transaction_type": "debit",
        "category": "Food",
    }
    payload.update(overrides)
    return client.post("/transactions/", json=payload, headers=headers)


def test_category_crud(client, headers):
    for name in ["Food", "Salary", "Temp"]:
        response = client.post("/categories/", json={"name": name}, headers=headers)
        assert response.status_code == 200
    temp_id = response.json()["id"]

    response = client.put(f"/categories/{temp_id}", json={"name": "Temporary"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Temporary"

    response = client.delete(f"/categories/{temp_id}", headers=headers)
    assert response.status_code == 200

    names = [c["name"] for c in client.get("/categories/", headers=headers).json()]
    assert names == ["Food", "Salary"]


def test_transaction_crud(client, headers):
    response = new_transaction(client, headers)
    assert response.status_code == 200
    body = response.json()
    assert body["category"] == "Food"
    assert float(body["amount"]) == 12.5
    transaction_id = body["id"]

    response = new_transaction(client, headers, category="Missing")
    assert response.status_code == 400

    response = client.get(f"/transactions/{transaction_id}", headers=headers)
    assert response.status_code == 200

    response = client.put(f"/transactions/{transaction_id}", json={"amount": 15, "category": "Salary"}, headers=headers)
    assert response.status_code == 200
    assert float(response.json()["amount"]) == 15
    assert response.json()["category"] == "Salary"

    response = client.delete(f"/transactions/{transaction_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == transaction_id

    response = client.get(f"/transactions/{transaction_id}", headers=headers)
    assert response.status_code == 404


def test_transactions_listed_newest_first(client, headers):
    new_transaction(client, headers, date="2024-01-05", description="older")
    new_transaction(client, headers, date="2024-03-05", description="newer")
    descriptions = [t["description"] for t in client.get("/transactions/", headers=headers).json()]
    assert descriptions.index("newer") < descriptions.index("older")


def test_category_with_transactions_cannot_be_deleted(client, headers):
    categories = client.get("/categories/", headers=headers).json()
    food_id = next(c["id"] for c in categories if c["name"] == "Food")
    response = client.delete(f"/categories/{food_id}", headers=headers)
    assert response.status_code == 400


def test_savings_goal_crud_and_progress(client, headers):
    response = client.post("/savings_goal/", json={"name": "Trip", "target": 500, "category": "Salary"}, headers=headers)
    assert response.status_code == 200
    goal_id = response.json()["id"]

    new_transaction(client, headers, amount=200, category="Salary", transaction_type="credit")

    response = client.get(f"/savings_goal/{goal_id}", headers=headers)
    assert response.status_code == 200
    assert float(response.json()["progress"]) == 200

    response = client.put(f"/savings_goal/{goal_id}", json={"name": "Trip", "target": 800, "category": "Salary"}, headers=headers)
    assert response.status_code == 200
    assert float(response.json()["target"]) == 800

    assert len(client.get("/savings_goal/", headers=headers).json()) == 1

    response = client.delete(f"/savings_goal/{goal_id}", headers=headers)
    assert response.status_code == 200

    response = client.post("/savings_goal/", json={"name": "Bad", "target": 10, "category": "Missing"}, headers=headers)
    assert response.status_code == 400


def test_reports(client, headers):
    today = date.today()
    response = client.get(f"/reports/monthly/{today.year}/{today.month}", headers=headers)
    assert response.status_code == 200
    assert float(response.json()["income"]) == 200

    response = client.get(f"/reports/yearly/{today.year}", headers=headers)
    assert response.status_code == 200
    assert response.json()["start_date"] == f"{today.year}-01-01"

    response = client.get(f"/reports/category/monthly/{today.year}/{today.month}", headers=headers)
    assert response.status_code == 200
    assert "Salary" in response.json()["category_report"]


def test_other_users_cannot_see_transactions(client, headers):
    transaction_id = client.get("/transactions/", headers=headers).json()[0]["id"]
    other = auth_headers(client, "otheruser")
    assert client.get(f"/transactions/{transaction_id}", headers=other).status_code == 404
    assert client.get("/transactions/", headers=other).json() == []
