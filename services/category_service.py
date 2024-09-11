from sqlalchemy.orm import Session
from schemas import CategoryCreate, CategoryUpdate
from models import Category

def get_category_by_id(db: Session, category_id: int, user_id: int):
    return db.query(Category).filter(Category.id == category_id, Category.user_id == user_id).first()


def create_category(db: Session, category: CategoryCreate, user_id: int):
    db_category = Category(**category.dict(), user_id=user_id)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def get_category_id(db: Session, category: str, user_id: int):
    return db.query(Category).filter(Category.name == category, Category.user_id == user_id).first()


def get_category_name_from_id(db: Session, category_id: int, user_id: int):
    return db.query(Category).filter(Category.id == category_id, Category.user_id == user_id).first()


def get_category(db: Session, category_id: int):
    return db.query(Category).filter(Category.id == category_id).first()


def get_user_categories(db: Session, user_id: int):
    return db.query(Category).filter(Category.user_id == user_id).all()


def update_category(db: Session, category_id: int, category: CategoryUpdate, user_id: int):
    db_category = get_category_by_id(db, category_id, user_id)
    if db_category:
        update_data = category.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_category, key, value)
        db.commit()
        db.refresh(db_category)
    return db_category


def delete_category(db: Session, category_id: int, user_id: int):
    db_category = get_category_by_id(db, category_id, user_id)
    if db_category:
        db.delete(db_category)
        db.commit()
    return db_category

def category_exists(db: Session, category_id: int, user_id: int):
    return get_category_by_id(db, category_id, user_id) is not None


def category_name_exists_for_user(db: Session, category: str, user_id: int):
    return db.query(Category).filter(Category.name == category, Category.user_id == user_id).first() is not None
