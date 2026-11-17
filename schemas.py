from pydantic import BaseModel, ConfigDict, EmailStr, Field
from enum import Enum
from datetime import date as date_type
from decimal import Decimal
from typing import Annotated, List, Optional


# Amounts are exact decimals with at most 2 decimal places, serialized as strings in JSON (e.g. "12.50")
Money = Annotated[Decimal, Field(max_digits=12, decimal_places=2)]
PositiveMoney = Annotated[Decimal, Field(max_digits=12, decimal_places=2, gt=0)]
Budget = Annotated[Decimal, Field(max_digits=12, decimal_places=2, ge=0)]


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

    model_config = ConfigDict(from_attributes=True)

class TransactionType(str, Enum):
    credit = "credit"
    debit = "debit"

class TransactionBase(BaseModel):
    amount: PositiveMoney
    date: date_type
    description: str
    transaction_type: TransactionType
    category: str

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(BaseModel):
    amount: Optional[PositiveMoney] = None
    date: Optional[date_type] = None
    description: Optional[str] = None
    transaction_type: Optional[TransactionType] = None
    category: Optional[str] = None

class TransactionResponse(BaseModel):
    id: int
    user_id: int
    amount: Decimal
    date: date_type
    description: str
    transaction_type: TransactionType
    category: str

    model_config = ConfigDict(from_attributes=True)


class Transaction(TransactionBase):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)


class CategoryBase(BaseModel):
    name: str
    monthly_budget: Optional[Budget] = None


class CategoryCreate(CategoryBase):
    pass


# Every field is optional so a budget can be changed without resending the name
class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    monthly_budget: Optional[Budget] = None


class Category(CategoryBase):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)


class SavingsGoalBase(BaseModel):
    name: str
    target: PositiveMoney
    category: str


class SavingsGoalCreate(SavingsGoalBase):
    pass


class SavingsGoalUpdate(SavingsGoalBase):
    pass


class SavingsGoal(SavingsGoalBase):
    id: int
    user_id: int
    progress: Decimal

    model_config = ConfigDict(from_attributes=True)


class CategorySpending(BaseModel):
    name: str
    spent: Decimal
    budget: Optional[Decimal] = None


class MonthlyTrend(BaseModel):
    month: str
    income: Decimal
    expenses: Decimal
    categories: List[CategorySpending]
