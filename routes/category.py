from fastapi import APIRouter, Depends, status, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from perfima.database import get_db
from perfima.controllers import user_controller, category_controller, user_controller
from perfima.schemas import UserInDB, Category, CategoryCreate, CategoryUpdate
from typing import List

router = APIRouter(prefix='/categories')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# A dependency created to get the current user
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


@router.post("/", response_model=Category)
def create_category(
    category: CategoryCreate, 
    current_user: UserInDB = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    return category_controller.create_category(category, current_user, db)


@router.get("/", response_model=List[Category])
def read_categories(
    current_user: UserInDB = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    return category_controller.get_user_categories(current_user, db)


@router.get("/{category_id}", response_model=Category)
def read_category(
    category_id: int, 
    current_user: UserInDB = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    return category_controller.get_category(category_id, current_user, db)


@router.put("/{category_id}", response_model=Category)
def update_category(
    category_id: int, 
    category: CategoryUpdate, 
    current_user: UserInDB = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    return category_controller.update_category(category_id, category, current_user, db)


@router.delete("/{category_id}", response_model=Category)
def delete_category(
    category_id: int, 
    current_user: UserInDB = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    return category_controller.delete_category(category_id, current_user, db)
