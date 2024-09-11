from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from perfima.database import get_db
from perfima.controllers import auth_controller
from typing import List
from perfima.schemas import Token, UserCreate

router = APIRouter()

@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
    ):
    return auth_controller.login(form_data, db)

@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(
    user: UserCreate, 
    db: Session = Depends(get_db)
    ):
    return auth_controller.signup(user, db)
