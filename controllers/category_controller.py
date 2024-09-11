from fastapi import HTTPException
from sqlalchemy.orm import Session
from perfima.services import category_service, transaction_service
from perfima.schemas import CategoryCreate, UserInDB, CategoryUpdate
import logging
logger = logging.getLogger(__name__)

# function to fetch a category and check ownership
def get_category_or_raise(db: Session, category_id: int, current_user: UserInDB):
    category = category_service.get_category(db, category_id)
    if not category:
        logger.error(f"Category not found: {category_id}")
        raise HTTPException(status_code=404, detail="Category not found")
    if category.user_id != current_user.id:
        logger.warning(f"Unauthorized access attempt by user {current_user.id} for category {category_id}")
        raise HTTPException(status_code=403, detail="Not authorized to access this category")
    return category


def create_category(category: CategoryCreate, current_user: UserInDB, db: Session):
    if category_service.category_name_exists_for_user(db, category.name, current_user.id):
        logger.warning(f"Category creation failed: {category.name} already exists for user {current_user.id}")
        raise HTTPException(status_code=400, detail="Category with this name already exists")
    new_category = category_service.create_category(db, category, current_user.id)
    logger.info(f"Category created: {new_category.name} for user {current_user.id}")
    return new_category


def get_category_name_from_id(category_id: int, current_user: UserInDB, db: Session):
    category = get_category_or_raise(db, category_id, current_user)
    return category.name


def get_category(category_id: int, current_user: UserInDB, db: Session):
    return get_category_or_raise(db, category_id, current_user)


def get_user_categories(current_user: UserInDB, db: Session):
    categories = category_service.get_user_categories(db, current_user.id)
    logger.info(f"Fetched {len(categories)} categories for user {current_user.id}")
    return categories


def update_category(category_id: int, category: CategoryUpdate, current_user: UserInDB, db: Session):
    db_category = get_category_or_raise(db, category_id, current_user)
    updated_category = category_service.update_category(db, category_id, category)
    logger.info(f"Category updated: {updated_category.name} (ID: {category_id}) for user {current_user.id}")
    return updated_category


def delete_category(category_id: int, current_user: UserInDB, db: Session):
    if transaction_service.get_transactions_by_category(db, current_user.id, category_id):
        logger.error(f"Category deletion failed: {category_id} has associated transactions for user {current_user.id}")
        raise HTTPException(status_code=400, detail="Cannot delete category with transactions")
    
    db_category = get_category_or_raise(db, category_id, current_user)
    deleted_category = category_service.delete_category(db, category_id)
    logger.info(f"Category deleted: {db_category.name} (ID: {category_id}) for user {current_user.id}")
    return deleted_category
