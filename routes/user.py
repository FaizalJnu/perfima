from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from perfima.controllers.user_controller import get_current_user
from perfima.schemas import UserInDB
from perfima.database import get_db

router = APIRouter(prefix="/users")

@router.get("/me", response_model=UserInDB)
def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    return current_user