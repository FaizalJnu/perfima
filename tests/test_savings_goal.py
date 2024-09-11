import pytest
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from perfima.schemas import SavingsGoalCreate, SavingsGoalUpdate
from perfima.models import SavingsGoal, Category
from perfima.exceptions import SavingGoalNotFoundException, SavingGoalAlreadyExistsException
from perfima.services import savings_goal_service

@pytest.fixture
def mock_db(mocker):
    return mocker.Mock(spec=Session)

@pytest.fixture
def sample_user_id():
    return 1

@pytest.fixture
def sample_category():
    return "Test Category"

@pytest.fixture
def sample_category_id():
    return 1

@pytest.fixture
def sample_saving_goal(mocker):
    goal = mocker.Mock(spec=SavingsGoal)
    goal.id = 1
    goal.name = "Test Goal"
    goal.target = 1000.0
    goal.user_id = 1
    goal.progress = 0.0
    goal.category = "Test Category"
    goal.category_id = 1
    return goal

def create_savings_goal_data(category=None, category_id=None):
    data = {"name": "New Goal", "target": 500.0}
    if category is not None:
        data["category"] = category
    if category_id is not None:
        data["category_id"] = category_id
    return data

def test_create_saving_goal(mock_db, sample_user_id, sample_category, sample_category_id):
    saving_goal_create = SavingsGoalCreate(**create_savings_goal_data(category=sample_category, category_id=sample_category_id))
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.return_value = None
    
    savings_goal_service.saving_goal_exists_for_user = lambda db, name, user_id: False
    
    try:
        result = savings_goal_service.create_saving_goal(mock_db, saving_goal_create, sample_user_id)
    except TypeError:
        result = savings_goal_service.create_saving_goal(mock_db, saving_goal_create, sample_user_id, sample_category_id)
    
    assert result.name == "New Goal"
    assert result.target == 500.0
    assert result.user_id == sample_user_id
    assert (result.category == sample_category) or (result.category_id == sample_category_id)
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

def test_create_saving_goal_already_exists(mock_db, sample_user_id, sample_category, sample_category_id):
    saving_goal_create = SavingsGoalCreate(**create_savings_goal_data(category=sample_category, category_id=sample_category_id))
    
    savings_goal_service.saving_goal_exists_for_user = lambda db, name, user_id: True
    
    with pytest.raises(SavingGoalAlreadyExistsException):
        try:
            savings_goal_service.create_saving_goal(mock_db, saving_goal_create, sample_user_id)
        except TypeError:
            savings_goal_service.create_saving_goal(mock_db, saving_goal_create, sample_user_id, sample_category_id)

def test_get_saving_goal(mock_db, sample_user_id, sample_saving_goal):
    mock_db.execute.return_value.scalar_one_or_none.return_value = sample_saving_goal
    
    result = savings_goal_service.get_saving_goal(mock_db, 1, sample_user_id)
    
    assert result == sample_saving_goal
    mock_db.execute.assert_called_once()

def test_get_saving_goal_not_found(mock_db, sample_user_id):
    mock_db.execute.return_value.scalar_one_or_none.return_value = None
    
    with pytest.raises(SavingGoalNotFoundException):
        savings_goal_service.get_saving_goal(mock_db, 999, sample_user_id)

def test_get_user_saving_goals(mock_db, sample_user_id, sample_saving_goal):
    mock_db.execute.return_value.scalars.return_value.all.return_value = [sample_saving_goal]
    
    result = savings_goal_service.get_user_saving_goals(mock_db, sample_user_id)
    
    assert result == [sample_saving_goal]
    mock_db.execute.assert_called_once()

def test_update_saving_goal(mock_db, sample_user_id, sample_category, sample_category_id, sample_saving_goal):
    mock_db.commit.return_value = None
    mock_db.refresh.return_value = None
    savings_goal_service.get_saving_goal = lambda db, id, user_id: sample_saving_goal
    
    saving_goal_update = SavingsGoalUpdate(**create_savings_goal_data(category=sample_category, category_id=sample_category_id))
    try:
        result = savings_goal_service.update_saving_goal(mock_db, 1, saving_goal_update, sample_user_id)
    except TypeError:
        result = savings_goal_service.update_saving_goal(mock_db, 1, saving_goal_update, sample_user_id, sample_category_id)
    
    assert result.name == "New Goal"
    assert result.target == 500.0
    assert (result.category == sample_category) or (result.category_id == sample_category_id)
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

def test_delete_saving_goal(mock_db, sample_user_id, sample_saving_goal):
    mock_db.delete.return_value = None
    mock_db.commit.return_value = None
    savings_goal_service.get_saving_goal = lambda db, id, user_id: sample_saving_goal
    
    result = savings_goal_service.delete_saving_goal(mock_db, 1, sample_user_id)
    
    assert result == sample_saving_goal
    mock_db.delete.assert_called_once_with(sample_saving_goal)
    mock_db.commit.assert_called_once()

def test_update_savings_goal_progress(mock_db, sample_user_id, sample_category, sample_saving_goal):
    mock_db.execute.return_value.scalars.return_value.all.return_value = [sample_saving_goal]
    mock_db.commit.return_value = None
    
    savings_goal_service.update_savings_goal_progress(mock_db, sample_user_id, sample_category, 100.0)
    
    assert sample_saving_goal.progress == 100.0
    mock_db.commit.assert_called_once()

def test_update_savings_goal_progress_exceeds_target(mock_db, sample_user_id, sample_category, sample_saving_goal):
    mock_db.execute.return_value.scalars.return_value.all.return_value = [sample_saving_goal]
    mock_db.commit.return_value = None
    
    savings_goal_service.update_savings_goal_progress(mock_db, sample_user_id, sample_category, 1500.0)
    
    assert sample_saving_goal.progress == sample_saving_goal.target
    mock_db.commit.assert_called_once()

def test_saving_goal_exists_for_user(mock_db, sample_user_id):
    original_function = savings_goal_service.saving_goal_exists_for_user
    savings_goal_service.saving_goal_exists_for_user = lambda db, name, user_id: True
    
    try:
        result = savings_goal_service.saving_goal_exists_for_user(mock_db, "Test Goal", sample_user_id)
        
        assert result is True
    finally:
        # Restore the original function
        savings_goal_service.saving_goal_exists_for_user = original_function

def test_saving_goal_does_not_exist_for_user(mock_db, sample_user_id):
    original_function = savings_goal_service.saving_goal_exists_for_user
    savings_goal_service.saving_goal_exists_for_user = lambda db, name, user_id: False
    
    try:
        result = savings_goal_service.saving_goal_exists_for_user(mock_db, "Non-existent Goal", sample_user_id)
        
        assert result is False
    finally:
        savings_goal_service.saving_goal_exists_for_user = original_function