import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


def get_database_url():
    url = os.getenv("DATABASE_URL", "sqlite:///./main.db")
    # plain postgres URLs default to psycopg2, the installed driver is psycopg 3
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


SQLALCHEMY_DB_URL = get_database_url()

if SQLALCHEMY_DB_URL.startswith("sqlite"):
    engine = create_engine(SQLALCHEMY_DB_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(SQLALCHEMY_DB_URL, pool_pre_ping=True)

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
