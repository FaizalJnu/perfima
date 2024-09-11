from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from perfima.models import User
import logging
import os
logger = logging.getLogger(__name__)


SECRET_KEY = "faiz"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 300

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(db, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        logger.warning(f"Authentication failed: Username not found - {username}")
        return None
    if not verify_password(password, user.hashed_password):
        logger.warning(f"Authentication failed: Incorrect password for username - {username}")
        return None
    logger.info(f"Authentication successful for username - {username}")
    return user

def create_access_token(data: dict, expires_delta: timedelta = None):
    logger.info("We enter the access token stage")
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(f"Access token created for {data.get('sub')}")
    return encoded_jwt
