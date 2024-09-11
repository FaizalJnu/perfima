from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Annotated
import models
from routes import auth, user, transaction, category, savings_goal, report
from database import engine, localSession
from sqlalchemy.orm import session

app = FastAPI()
models.Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return "First check complete"

@app.get("/healthCheck")
def healtcheck():
    return {"status": "ok"}

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(transaction.router)
app.include_router(category.router)
app.include_router(savings_goal.router)
app.include_router(report.router)

