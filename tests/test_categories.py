import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from perfima.models import Base, Category
from perfima.schemas import CategoryCreate, CategoryUpdate
from perfima.services import category_service

# Create an in-memory SQLite database for testing
engine = create_engine('sqlite:///:memory:')
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def sample_category():
    return Category(id=1, name="Test Category", user_id=1)

def test_get_category_by_id(db_session, sample_category):
    db_session.add(sample_category)
    db_session.commit()

    result = category_service.get_category_by_id(db_session, 1, 1)
    assert result.id == 1
    assert result.name == "Test Category"
    assert result.user_id == 1

def test_create_category(db_session):
    category_data = CategoryCreate(name="New Category")
    result = category_service.create_category(db_session, category_data, user_id=1)

    assert result.name == "New Category"
    assert result.user_id == 1

def test_get_category_id(db_session, sample_category):
    db_session.add(sample_category)
    db_session.commit()

    result = category_service.get_category_id(db_session, "Test Category", 1)
    assert result.id == 1

def test_get_category_name_from_id(db_session, sample_category):
    db_session.add(sample_category)
    db_session.commit()

    result = category_service.get_category_name_from_id(db_session, 1, 1)
    assert result.name == "Test Category"

def test_get_user_categories(db_session, sample_category):
    db_session.add(sample_category)
    db_session.add(Category(name="Another Category", user_id=1))
    db_session.commit()

    result = category_service.get_user_categories(db_session, 1)
    assert len(result) == 2
    assert result[0].name == "Test Category"
    assert result[1].name == "Another Category"

def test_update_category(db_session, sample_category):
    db_session.add(sample_category)
    db_session.commit()

    update_data = CategoryUpdate(name="Updated Category")
    result = category_service.update_category(db_session, 1, update_data, 1)

    assert result.name == "Updated Category"

def test_delete_category(db_session, sample_category):
    db_session.add(sample_category)
    db_session.commit()

    result = category_service.delete_category(db_session, 1, 1)
    assert result.id == 1

    # Verify the category is deleted
    assert category_service.get_category_by_id(db_session, 1, 1) is None

def test_category_exists(db_session, sample_category):
    db_session.add(sample_category)
    db_session.commit()

    assert category_service.category_exists(db_session, 1, 1) is True
    assert category_service.category_exists(db_session, 2, 1) is False

def test_category_name_exists_for_user(db_session, sample_category):
    db_session.add(sample_category)
    db_session.commit()

    assert category_service.category_name_exists_for_user(db_session, "Test Category", 1) is True
    assert category_service.category_name_exists_for_user(db_session, "Non-existent Category", 1) is False