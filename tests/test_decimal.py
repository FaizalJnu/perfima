import os
import pytest
from datetime import date
from decimal import Decimal
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from perfima.models import Base, User, Category, Transaction, TransactionType
from perfima.schemas import TransactionCreate, SavingsGoalCreate
from perfima.services import report_service

SQLALCHEMY_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///./test_decimal.db")
connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def add_transactions(db, amounts, transaction_type=TransactionType.debit):
    user = User(username="decimal", email="decimal@example.com", name="Decimal", hashed_password="x")
    db.add(user)
    db.commit()
    category = Category(name="Food", user_id=user.id)
    db.add(category)
    db.commit()
    for amount in amounts:
        db.add(Transaction(user_id=user.id, category_id=category.id, amount=Decimal(amount),
                           description="t", transaction_type=transaction_type, date=date(2024, 5, 10)))
    db.commit()
    return user


def test_amounts_round_trip_as_decimal(db_session):
    add_transactions(db_session, ["19.99"])
    stored = db_session.query(Transaction).one()
    assert isinstance(stored.amount, Decimal)
    assert stored.amount == Decimal("19.99")


def test_report_sums_are_exact(db_session):
    # 0.1 + 0.2 is 0.30000000000000004 as floats
    user = add_transactions(db_session, ["0.10", "0.20"])
    report = report_service.get_monthly_report(db_session, user.id, 2024, 5)
    assert report["expenses"] == Decimal("0.30")
    assert isinstance(report["expenses"], Decimal)


def test_many_small_amounts_sum_exactly(db_session):
    user = add_transactions(db_session, ["0.01"] * 1000)
    report = report_service.get_monthly_report(db_session, user.id, 2024, 5)
    assert report["expenses"] == Decimal("10.00")


def make_transaction(amount):
    return TransactionCreate(amount=amount, date=date(2024, 5, 10), description="t",
                             transaction_type="debit", category="Food")


def test_schema_accepts_two_decimal_places():
    assert make_transaction("12.50").amount == Decimal("12.50")
    assert make_transaction(12.5).amount == Decimal("12.5")


@pytest.mark.parametrize("amount", ["12.505", "0", "-5", "10000000000.00"])
def test_schema_rejects_invalid_amounts(amount):
    with pytest.raises(ValidationError):
        make_transaction(amount)


def test_savings_target_must_be_positive():
    with pytest.raises(ValidationError):
        SavingsGoalCreate(name="Trip", target="0", category="Food")
