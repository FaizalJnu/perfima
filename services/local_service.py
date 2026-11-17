import secrets
import threading
import time
import logging
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from perfima.models import Category, User
from perfima.services import user_service
from perfima.services.auth_service import get_password_hash

logger = logging.getLogger(__name__)

LOCAL_USERNAME = "local"
DEFAULT_CATEGORIES = ["Food", "Groceries", "Rent", "Transport", "Utilities", "Entertainment", "Shopping", "Health", "Salary"]


# Shared with the desktop launcher, which watches it to decide when to exit
class LocalState:
    def __init__(self):
        self.last_heartbeat = time.monotonic()
        self.shutdown = threading.Event()

    def heartbeat(self):
        self.last_heartbeat = time.monotonic()

    def idle_seconds(self):
        return time.monotonic() - self.last_heartbeat


state = LocalState()


def get_or_create_local_user(db: Session):
    user = user_service.get_user_by_username(db, LOCAL_USERNAME)
    if user:
        return user

    # Nobody logs in with a password in local mode, so the hash is of a random throwaway value
    user = User(
        username=LOCAL_USERNAME,
        email="local@example.com",
        name="Local",
        hashed_password=get_password_hash(secrets.token_urlsafe(32))
    )
    db.add(user)
    try:
        db.flush()
        db.add_all([Category(name=name, user_id=user.id) for name in DEFAULT_CATEGORIES])
        db.commit()
    except IntegrityError:
        # another request created the user first
        db.rollback()
        return user_service.get_user_by_username(db, LOCAL_USERNAME)

    db.refresh(user)
    logger.info(f"Created local user with {len(DEFAULT_CATEGORIES)} default categories")
    return user
