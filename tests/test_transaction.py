import pytest
from datetime import date
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from perfima.schemas import TransactionCreate, TransactionUpdate, TransactionResponse, TransactionType
from perfima.models import Transaction, Category
from perfima.services.transaction_service import TransactionService

@pytest.fixture
def mock_db():
    return Mock(spec=Session)

@pytest.fixture
def mock_category():
    return Mock(spec=Category, id=1, name="Test Category")

@pytest.fixture
def mock_transaction():
    return Mock(spec=Transaction, id=1, category_id=1, user_id=1, amount=100.0, 
                date=date(2023, 1, 1), description="Test Transaction", 
                transaction_type="expense", category=Mock(spec=Category, name="Test Category"))


def test_create_transaction(mock_db, mock_category):
    with patch('perfima.services.category_service.get_category', return_value=mock_category):
        transaction_create = TransactionCreate(
            category="Test Category",
            amount=100.0,
            date=date(2023, 1, 1),
            description="Test Transaction",
            transaction_type=TransactionType.debit  # or TransactionType.credit
        )
        result = TransactionService.create_transaction(mock_db, transaction_create, user_id=1)
        
        assert result is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

def test_get_transaction(mock_db, mock_transaction):
    mock_db.execute.return_value.scalars.return_value.first.return_value = mock_transaction
    
    result = TransactionService.get_transaction(mock_db, transaction_id=1)
    
    assert result == mock_transaction
    mock_db.execute.assert_called_once()

def test_get_user_transactions(mock_db, mock_transaction):
    mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_transaction]
    
    result = TransactionService.get_user_transactions(mock_db, user_id=1)
    
    assert result == [mock_transaction]
    mock_db.execute.assert_called_once()

def test_update_transaction(mock_db, mock_transaction, mock_category):
    mock_db.execute.return_value.scalars.return_value.first.return_value = mock_transaction
    
    with patch('perfima.services.category_service.get_category', return_value=mock_category):
        transaction_update = TransactionUpdate(
            category="Updated Category",
            amount=200.0,
            date=date(2023, 2, 1),
            description="Updated Transaction",
            transaction_type=TransactionType.credit
        )
        result = TransactionService.update_transaction(mock_db, transaction_id=1, transaction=transaction_update, user_id=1)
        
        assert result == mock_transaction
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

def test_delete_transaction(mock_db, mock_transaction):
    mock_db.execute.return_value.scalars.return_value.first.return_value = mock_transaction
    
    result = TransactionService.delete_transaction(mock_db, transaction_id=1)
    
    assert result == mock_transaction
    mock_db.delete.assert_called_once_with(mock_transaction)
    mock_db.commit.assert_called_once()

def test_get_transactions_by_category(mock_db, mock_transaction):
    mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_transaction]
    
    result = TransactionService.get_transactions_by_category(mock_db, user_id=1, category_id=1)
    
    assert result == [mock_transaction]
    mock_db.execute.assert_called_once()

def test_to_response(mock_transaction):
    mock_transaction.id = 1
    mock_transaction.user_id = 1
    mock_transaction.category.name = "Test Category"
    mock_transaction.amount = 100.0
    mock_transaction.date = date(2023, 1, 1)
    mock_transaction.description = "Test Transaction"
    mock_transaction.transaction_type = "credit"  # or "debit"

    result = TransactionService.to_response(mock_transaction)
    
    assert isinstance(result, TransactionResponse)
    assert result.id == mock_transaction.id
    assert result.user_id == mock_transaction.user_id
    assert result.category == mock_transaction.category.name
    assert result.amount == mock_transaction.amount
    assert result.date == mock_transaction.date
    assert result.description == mock_transaction.description
    assert result.transaction_type == TransactionType(mock_transaction.transaction_type)