import pytest
from unittest.mock import Mock, patch
from perfima.models import User
from perfima.schemas import UserCreate
from perfima.services import user_service

@pytest.fixture
def mock_db():
    return Mock()

@pytest.fixture
def mock_user():
    return User(id=1, username="testuser", email="test@example.com", name="Test User", hashed_password="hashed_password")

@patch("perfima.services.user_service.get_password_hash")
def test_create_user(mock_get_password_hash, mock_db):
    mock_get_password_hash.return_value = "hashed_password"
    user_create = UserCreate(username="testuser", email="test@example.com", name="Test User", password="password123")
    
    result = user_service.create_user(mock_db, user_create)
    
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()
    
    assert result.username == user_create.username
    assert result.email == user_create.email
    assert result.name == user_create.name
    assert result.hashed_password == "hashed_password"

def test_get_user_by_username_or_email(mock_db, mock_user):
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user
    
    result = user_service.get_user_by_username_or_email(mock_db, "testuser", "test@example.com")
    
    assert result == mock_user
    mock_db.query.assert_called_once_with(User)

def test_get_user_by_username(mock_db, mock_user):
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user
    
    result = user_service.get_user_by_username(mock_db, "testuser")
    
    assert result == mock_user
    mock_db.query.assert_called_once_with(User)

def test_get_user_by_email(mock_db, mock_user):
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user
    
    result = user_service.get_user_by_email(mock_db, "test@example.com")
    
    assert result == mock_user
    mock_db.query.assert_called_once_with(User)