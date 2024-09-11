from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
import sqlite3

SQLALCHEMY_DB_URL = "sqlite:///./main.db"
engine = create_engine(SQLALCHEMY_DB_URL, connect_args={"check_same_thread": False})
localSession = sessionmaker(autocommit=False, autoflush=False, bind= engine)
Base = declarative_base()

def get_db():
    db = localSession()
    try:
        yield db
    
    # except:
    #     print("db inaccessible")

    finally:
        db.close()