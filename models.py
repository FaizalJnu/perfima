from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum, Date
from database import Base
from sqlalchemy.orm import relationship
import enum
from datetime import date


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="categories")
    transactions = relationship("Transaction", back_populates="category")
    savings_goals = relationship("SavingsGoal", back_populates="category")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    hashed_password = Column(String)

    transactions = relationship("Transaction", back_populates="user")
    categories = relationship("Category", back_populates="user")
    savings_goals = relationship("SavingsGoal", back_populates="user")


class TransactionType(str, enum.Enum):
    debit = "debit"
    credit = "credit"


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    category_id = Column(Integer, ForeignKey("categories.id"))
    amount = Column(Float)
    description = Column(String)
    transaction_type = Column(Enum(TransactionType))
    date = Column(Date, default=date.today)

    user = relationship("User", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")


class SavingsGoal(Base):
    __tablename__ = "savings_goals"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    target = Column(Float)
    progress = Column(Float, default=0.0)
    category_id = Column(Integer, ForeignKey("categories.id"))

    user = relationship("User", back_populates="savings_goals")
    category = relationship("Category", back_populates="savings_goals")