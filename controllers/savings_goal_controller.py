from fastapi import HTTPException
from sqlalchemy.orm import Session
from perfima.schemas import SavingsGoalCreate, UserInDB, SavingsGoalUpdate
from perfima.services import category_service, savings_goal_service
from perfima.exceptions import CategoryNotFoundException, SavingGoalAlreadyExistsException, SavingGoalNotFoundException, UnauthorizedAccessException


def get_category_by_name_or_raise(db: Session, name: str, user_id: int):
    category = category_service.get_category_id(db, name, user_id)
    if not category:
        raise CategoryNotFoundException(f"Category {name} not found")
    return category

def create_savings_goal(saving_goal: SavingsGoalCreate, current_user: UserInDB, db: Session):
    try:
        category = get_category_by_name_or_raise(db, saving_goal.category, current_user.id)
        return savings_goal_service.create_saving_goal(db, saving_goal, current_user.id, category.id)
    except CategoryNotFoundException:
        raise HTTPException(status_code=400, detail="Invalid category for this user")
    except SavingGoalAlreadyExistsException:
        raise HTTPException(status_code=400, detail="Saving goal with this name already exists")

def get_savings_goal(saving_goal_id: int, current_user: UserInDB, db: Session):
    try:
        return savings_goal_service.get_saving_goal(db, saving_goal_id, current_user.id)
    except SavingGoalNotFoundException:
        raise HTTPException(status_code=404, detail="Saving goal not found")
    except UnauthorizedAccessException:
        raise HTTPException(status_code=403, detail="Not authorized to access this saving goal")

def get_user_savings_goals(current_user: UserInDB, db: Session):
    return savings_goal_service.get_user_saving_goals(db, current_user.id)

def update_savings_goal(saving_goal_id: int, saving_goal: SavingsGoalUpdate, current_user: UserInDB, db: Session):
    try:
        category = get_category_by_name_or_raise(db, saving_goal.category, current_user.id)
        return savings_goal_service.update_saving_goal(db, saving_goal_id, saving_goal, current_user.id, category.id)
    except CategoryNotFoundException:
        raise HTTPException(status_code=400, detail="Invalid category for this user")
    except SavingGoalNotFoundException:
        raise HTTPException(status_code=404, detail="Saving goal not found")
    except UnauthorizedAccessException:
        raise HTTPException(status_code=403, detail="Not authorized to modify this saving goal")

def delete_savings_goal(saving_goal_id: int, current_user: UserInDB, db: Session):
    try:
        return savings_goal_service.delete_saving_goal(db, saving_goal_id, current_user.id)
    except SavingGoalNotFoundException:
        raise HTTPException(status_code=404, detail="Saving goal not found")
    except UnauthorizedAccessException:
        raise HTTPException(status_code=403, detail="Not authorized to delete this saving goal")
