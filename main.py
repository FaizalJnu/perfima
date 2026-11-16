from fastapi import FastAPI
import perfima.models
from perfima.routes import auth, user, transaction, category, savings_goal, report
from perfima.database import engine
from perfima.telemetry import setup_tracing

app = FastAPI()
perfima.models.Base.metadata.create_all(bind=engine)
setup_tracing(app, engine)

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
