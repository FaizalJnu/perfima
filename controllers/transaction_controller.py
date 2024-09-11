from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from perfima.schemas import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    UserInDB,
    TransactionType
)
from perfima.services import category_service, savings_goal_service
from perfima.services.transaction_service import TransactionService
from perfima.database import get_db
from perfima.routes.transaction import get_current_user

class TransactionController:
    @staticmethod
    def create_transaction(
        transaction: TransactionCreate,
        current_user: UserInDB = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> TransactionResponse:
        category = category_service.get_category(db, transaction.category, current_user.id)
        if not category:
            raise HTTPException(status_code=400, detail="Category not found")

        new_transaction = TransactionService.create_transaction(db, transaction, current_user.id)

        if transaction.transaction_type == TransactionType.credit:
            savings_goal_service.update_savings_goal_progress(db, current_user.id, category.id, transaction.amount)

        return TransactionResponse.from_orm(new_transaction)

    @staticmethod
    def get_transaction(
        transaction_id: int,
        current_user: UserInDB = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> TransactionResponse:
        transaction = TransactionService.get_transaction(db, transaction_id)
        if not transaction or transaction.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return TransactionResponse.from_orm(transaction)

    @staticmethod
    def get_user_transactions(
        current_user: UserInDB = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> List[TransactionResponse]:
        transactions = TransactionService.get_user_transactions(db, current_user.id)
        return [TransactionResponse.from_orm(t) for t in transactions]

    @staticmethod
    def update_transaction(
        transaction_id: int,
        transaction_update: TransactionUpdate,
        current_user: UserInDB = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> TransactionResponse:
        transaction = TransactionService.get_transaction(db, transaction_id)
        if not transaction or transaction.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        if transaction_update.category:
            category = category_service.get_category(db, transaction_update.category, current_user.id)
            if not category:
                raise HTTPException(status_code=400, detail="Category not found")

        updated_transaction = TransactionService.update_transaction(db, transaction_id, transaction_update)
        return TransactionResponse.from_orm(updated_transaction)

    @staticmethod
    def delete_transaction(
        transaction_id: int,
        current_user: UserInDB = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> None:
        transaction = TransactionService.get_transaction(db, transaction_id)
        if not transaction or transaction.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Transaction not found")
        TransactionService.delete_transaction(db, transaction_id)