from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
from controllers import user_controller, report_controller, user_controller
from schemas import UserInDB
from typing import List

router = APIRouter(prefix="/reports")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

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

@router.get("/monthly/{year}/{month}", response_model=dict)
def get_monthly_report(
        year: int,
        month: int,
        current_user: UserInDB = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    return report_controller.get_monthly_report(year, month, current_user, db)


@router.get("/yearly/{year}", response_model=dict)
def get_yearly_report(
        year: int,
        current_user: UserInDB = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    return report_controller.get_yearly_report(year, current_user, db)


@router.get("/category/monthly/{year}/{month}", response_model=dict)
def get_monthly_category_report(
        year: int,
        month: int,
        current_user: UserInDB = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    return report_controller.get_monthly_category_report(year, month, current_user, db)


@router.get("/category/yearly/{year}", response_model=dict)
def get_yearly_category_report(
        year: int,
        current_user: UserInDB = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    return report_controller.get_yearly_category_report(year, current_user, db)
