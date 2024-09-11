from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from perfima.database import get_db
from perfima.services import auth_service, user_service
from perfima.schemas import UserCreate
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)
logger.debug("we enter the auth controller")
def login(form_data: OAuth2PasswordRequestForm, db: Session):
    user = auth_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.warning(f"Failed login attempt for username: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=auth_service.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    logger.info(f"Successful login for user: {user.username}")
    return {"access_token": access_token, "token_type": "bearer"}


def signup(user: UserCreate, db: Session):
    # username and email existence check
    db_user = user_service.get_user_by_username(db, user.username)
    if db_user:
        if db_user.username == user.username:
            logger.warning(f"Signup attempt with existing username: {user.username}")
            raise HTTPException(status_code=400, detail="Username already registered")
        # if db_user.email == user.email:
        #     logger.warning(f"Signup attempt with existing email: {user.email}")
        #     raise HTTPException(status_code=400, detail="Email already registered")

    user_service.create_user(db, user)
    logger.info(f"User created successfully: {user.username}")
    return {"message": "User created successfully"}