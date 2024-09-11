from fastapi import HTTPException
from sqlalchemy.orm import Session
from perfima.schemas import UserInDB
from perfima.services import report_service


def get_monthly_report(year: int, month: int, current_user: UserInDB, db: Session):
    if year < 1947 or year > 2037 or month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Invalid year or month")
    return report_service.get_monthly_report(db, current_user.id, year, month)


def get_yearly_report(year: int, current_user: UserInDB, db: Session):
    if year < 1947 or year > 2038:
        raise HTTPException(status_code=400, detail="Invalid year")
    return report_service.get_yearly_report(db, current_user.id, year)


def get_monthly_category_report(year: int, month: int, current_user: UserInDB, db: Session):
    if year < 1947 or year > 2038 or month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Invalid year or month")
    return report_service.get_monthly_category_report(db, current_user.id, year, month)


def get_yearly_category_report(year: int, current_user: UserInDB, db: Session):
    if year < 1947 or year > 2038:
        raise HTTPException(status_code=400, detail="Invalid year")
    return report_service.get_yearly_category_report(db, current_user.id, year)