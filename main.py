import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import perfima.models
from perfima.routes import auth, user, transaction, category, savings_goal, report, local
from perfima.database import engine
from perfima.telemetry import setup_tracing

STATIC_DIR = Path(__file__).parent / "static"

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

# Single user desktop mode, enabled by the launcher
if os.getenv("PERFIMA_LOCAL_MODE") == "1":
    app.include_router(local.router)

# The browser UI is served from the same origin as the API
app.mount("/app", StaticFiles(directory=STATIC_DIR, html=True, check_dir=False), name="app")
