from fastapi import APIRouter, Depends, status, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from perfima.database import get_db
from perfima.controllers import user_controller, category_controller, user_controller, savings_goal_controller
from perfima.schemas import UserInDB, SavingsGoalCreate, SavingsGoal, SavingsGoalUpdate
from typing import List

router = APIRouter(prefix="/savings_goal")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl = "token")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> UserInDB:
    user = user_controller.get_current_user(token, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return user


# A helper function to build the SavingsGoal response
def build_savings_goal_response(savings_goal, current_user: UserInDB, db: Session) -> SavingsGoal:
    category = category_controller.get_category_name_from_id(savings_goal.category_id, current_user, db)
    return SavingsGoal(
        name=savings_goal.name,
        target=savings_goal.target,
        progress=savings_goal.progress,
        category=category,
        id=savings_goal.id,
        user_id=savings_goal.user_id
    )


@router.post("/", response_model=SavingsGoal)
def create_savings_goal(
    savings_goal: SavingsGoalCreate,
    current_user: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    created_savings_goal = savings_goal_controller.create_savings_goal(savings_goal, current_user, db)
    return build_savings_goal_response(created_savings_goal, current_user, db)


@router.get("/", response_model=List[SavingsGoal])
def read_savings_goals(
    current_user: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    savings_goal_arr_in_db = savings_goal_controller.get_user_savings_goals(current_user, db)
    return [build_savings_goal_response(savings_goal, current_user, db) for savings_goal in savings_goal_arr_in_db]


@router.get("/{savings_goal_id}", response_model=SavingsGoal)
def read_savings_goal(
    savings_goal_id: int,
    current_user: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    savings_goal_in_db = savings_goal_controller.get_savings_goal(savings_goal_id, current_user, db)
    return build_savings_goal_response(savings_goal_in_db, current_user, db)


@router.put("/{savings_goal_id}", response_model=SavingsGoal)
def update_savings_goal(
    savings_goal_id: int,
    savings_goal: SavingsGoalUpdate,
    current_user: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    updated_savings_goal = savings_goal_controller.update_savings_goal(savings_goal_id, savings_goal, current_user, db)
    return build_savings_goal_response(updated_savings_goal, current_user, db)


@router.delete("/{savings_goal_id}", response_model=SavingsGoal)
def delete_savings_goal(
    savings_goal_id: int,
    current_user: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    deleted_savings_goal = savings_goal_controller.delete_savings_goal(savings_goal_id, current_user, db)
    return build_savings_goal_response(deleted_savings_goal, current_user, db)