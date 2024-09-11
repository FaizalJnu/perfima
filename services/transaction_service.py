from sqlalchemy.orm import Session
from sqlalchemy.future import select
from typing import List, Optional

from schemas import TransactionCreate, TransactionUpdate, TransactionResponse
from models import Transaction
from services import category_service

class TransactionService:
    @staticmethod
    def create_transaction(db: Session, transaction: TransactionCreate, user_id: int) -> Transaction:
        category = category_service.get_category(db, transaction.category, user_id)
        db_transaction = Transaction(
            category_id=category.id,
            user_id=user_id,
            amount=transaction.amount,
            date=transaction.date,
            description=transaction.description,
            transaction_type=transaction.transaction_type
        )
        db.add(db_transaction)
        db.commit()
        db.refresh(db_transaction)
        return db_transaction

    @staticmethod
    def get_transaction(db: Session, transaction_id: int) -> Optional[Transaction]:
        query = select(Transaction).where(Transaction.id == transaction_id)
        result = db.execute(query)
        return result.scalars().first()

    @staticmethod
    def get_user_transactions(db: Session, user_id: int) -> List[Transaction]:
        query = select(Transaction).where(Transaction.user_id == user_id)
        result = db.execute(query)
        return result.scalars().all()

    @staticmethod
    def update_transaction(db: Session, transaction_id: int, transaction: TransactionUpdate, user_id: int) -> Optional[Transaction]:
        db_transaction = TransactionService.get_transaction(db, transaction_id)
        if db_transaction and db_transaction.user_id == user_id:
            update_data = transaction.dict(exclude_unset=True)
            if 'category' in update_data:
                category = category_service.get_category(db, update_data['category'], user_id)
                update_data['category_id'] = category.id
                del update_data['category']
            for key, value in update_data.items():
                setattr(db_transaction, key, value)
            db.commit()
            db.refresh(db_transaction)
        return db_transaction

    @staticmethod
    def delete_transaction(db: Session, transaction_id: int) -> Optional[Transaction]:
        db_transaction = TransactionService.get_transaction(db, transaction_id)
        if db_transaction:
            db.delete(db_transaction)
            db.commit()
        return db_transaction

    @staticmethod
    def get_transactions_by_category(db: Session, user_id: int, category_id: int) -> List[Transaction]:
        query = select(Transaction).where(Transaction.user_id == user_id, Transaction.category_id == category_id)
        result = db.execute(query)
        return result.scalars().all()

    @staticmethod
    def to_response(transaction: Transaction) -> TransactionResponse:
        return TransactionResponse(
            id=transaction.id,
            category=transaction.category.name,
            amount=transaction.amount,
            date=transaction.date,
            description=transaction.description,
            transaction_type=transaction.transaction_type
        )