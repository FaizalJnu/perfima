import pytest
from fastapi.testclient import TestClient
from perfima.main import app
from perfima.database import get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from perfima.models import Base
from perfima.services.auth_service import get_password_hash

# Configure test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./main.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency override
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)

# Setup test database
@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

# Test user registration
def test_user_registration():
    response = client.post(
        "/signup",
        json={
            "username": "testuser",
            "email": "testuser@example.com",
            "name": "Test User",
            "password": "password123"
        }
    )
    assert response.status_code == 201
    assert response.json() == {"message": "User created successfully"}

# Test user login
def test_user_login():
    response = client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

# Test login with invalid credentials
def test_invalid_login():
    response = client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}