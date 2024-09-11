from perfima.routes.category import get_current_user
from perfima.controllers.transaction_controller import TransactionController
from perfima.schemas import TransactionResponse, UserInDB, TransactionCreate, TransactionUpdate
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from perfima.database import get_db
from typing import List


router = APIRouter(prefix="/transactions")

@router.post("/", response_model=TransactionResponse)
def create_transaction(
    transaction: TransactionCreate,
    current_user: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return TransactionController.create_transaction(transaction, current_user, db)

@router.get("/", response_model=List[TransactionResponse])
def read_transactions(
    current_user: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return TransactionController.get_user_transactions(current_user, db)

@router.get("/{transaction_id}", response_model=TransactionResponse)
def read_transaction(
    transaction_id: int,
    current_user: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return TransactionController.get_transaction(transaction_id, current_user, db)

@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: int,
    transaction: TransactionUpdate,
    current_user: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return TransactionController.update_transaction(transaction_id, transaction, current_user, db)

@router.delete("/{transaction_id}", response_model=TransactionResponse)
def delete_transaction(
    transaction_id: int,
    current_user: UserInDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return TransactionController.delete_transaction(transaction_id, current_user, db)