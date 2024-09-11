from sqlalchemy.orm import Session
from sqlalchemy.future import select
from perfima.schemas import SavingsGoalCreate, SavingsGoalUpdate
from perfima.models import SavingsGoal
from perfima.services import category_service
from perfima.exceptions import SavingGoalNotFoundException, SavingGoalAlreadyExistsException, CategoryNotFoundException

def create_saving_goal(db: Session, saving_goal: SavingsGoalCreate, user_id: int, category_id: int):
    if saving_goal_exists_for_user(db, saving_goal.name, user_id):
        raise SavingGoalAlreadyExistsException("Saving goal with this name already exists")
    
    db_saving_goal = SavingsGoal(
        name=saving_goal.name, 
        target=saving_goal.target, 
        user_id=user_id, 
        progress=0.0,
        category_id=category_id
    )
    db.add(db_saving_goal)
    db.commit()
    db.refresh(db_saving_goal)
    return db_saving_goal

def get_saving_goal(db: Session, saving_goal_id: int, user_id: int):
    result = db.execute(select(SavingsGoal).filter(SavingsGoal.id == saving_goal_id, SavingsGoal.user_id == user_id))
    saving_goal = result.scalar_one_or_none()
    if not saving_goal:
        raise SavingGoalNotFoundException("Saving goal not found")
    return saving_goal

def get_user_saving_goals(db: Session, user_id: int):
    result = db.execute(select(SavingsGoal).filter(SavingsGoal.user_id == user_id))
    return result.scalars().all()

def update_saving_goal(db: Session, saving_goal_id: int, saving_goal: SavingsGoalUpdate, user_id: int, category_id: int):
    db_saving_goal = get_saving_goal(db, saving_goal_id, user_id)
    
    update_data = saving_goal.dict(exclude_unset=True)
    for key, value in update_data.items():
        if key == 'category':
            setattr(db_saving_goal, 'category_id', category_id)
        else:
            setattr(db_saving_goal, key, value)
    
    db.commit()
    db.refresh(db_saving_goal)
    return db_saving_goal

def delete_saving_goal(db: Session, saving_goal_id: int, user_id: int):
    db_saving_goal = get_saving_goal(db, saving_goal_id, user_id)
    db.delete(db_saving_goal)
    db.commit()
    return db_saving_goal

def update_savings_goal_progress(db: Session, user_id: int, category_id: int, amount: float):
    result = db.execute(select(SavingsGoal).filter(
        SavingsGoal.user_id == user_id,
        SavingsGoal.category_id == category_id
    ))
    saving_goals = result.scalars().all()

    for goal in saving_goals:
        goal.progress += amount
        if goal.progress > goal.target:
            goal.progress = goal.target

    db.commit()

def saving_goal_exists_for_user(db: Session, saving_goal_name: str, user_id: int):
    result = db.execute(select(SavingsGoal).filter(
        SavingsGoal.name == saving_goal_name,
        SavingsGoal.user_id == user_id
    ))
    return result.scalar_one_or_none() is not None