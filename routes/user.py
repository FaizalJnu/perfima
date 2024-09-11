from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from controllers.user_controller import get_current_user
from schemas import UserInDB
from database import get_db

router = APIRouter(prefix="/users")

@router.get("/me", response_model=UserInDB)
def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    return current_user