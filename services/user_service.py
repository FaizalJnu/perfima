from perfima.models import User
from perfima.schemas import UserCreate
from perfima.services.auth_service import get_password_hash
from sqlalchemy.orm import Session

def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        name=user.name,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_username_or_email(db: Session, username: str, email: str):
    return db.query(User).filter((User.username == username) | (User.email == email)).first()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()
