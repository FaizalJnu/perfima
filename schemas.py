from pydantic import BaseModel, EmailStr
from enum import Enum
from datetime import date as date_type
from typing import Optional


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    name: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class UserInDB(BaseModel):
    id: int
    username: str
    email: EmailStr
    name: str

    class Config:
        orm_mode = True
        from_attributes = True

class TransactionType(str, Enum):
    credit = "credit"
    debit = "debit"

class TransactionBase(BaseModel):
    amount: float
    date: date_type
    description: str
    transaction_type: TransactionType
    category: str

class TransactionCreate(TransactionBase):
    pass

class TransactionsUpdate(BaseModel):
    amount: Optional[float] = None
    date: Optional[date_type] = None
    description: Optional[str] = None
    transaction_type: Optional[TransactionType] = None
    category: Optional[str] = None

class TransactionResponse(TransactionBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True


class TransactionCreate(TransactionBase):
    # Derive all from transaction base, userid will be taken separately
    pass


class TransactionUpdate(TransactionBase):
    # Derive all from transaction base, userid will be taken separately
    pass


class Transaction(TransactionBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True


class CategoryBase(BaseModel):
    name: str


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(CategoryBase):
    pass


class Category(CategoryBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True


class SavingsGoalBase(BaseModel):
    name: str
    target: float
    category: str


class SavingsGoalCreate(SavingsGoalBase):
    pass


class SavingsGoalUpdate(SavingsGoalBase):
    pass


class SavingsGoal(SavingsGoalBase):
    id: int
    user_id: int
    progress: float

    class Config:
        orm_mode = True
