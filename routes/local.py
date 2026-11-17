from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from perfima.database import get_db
from perfima.routes.category import get_current_user
from perfima.schemas import Token, UserInDB
from perfima.services import auth_service, local_service

LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}


# Only answer requests addressed to the loopback host, so a web page using DNS rebinding can't fetch a token
def require_local_host(request: Request):
    if request.url.hostname not in LOCAL_HOSTS:
        raise HTTPException(status_code=403, detail="Local mode only accepts requests to localhost")


router = APIRouter(prefix="/local", dependencies=[Depends(require_local_host)])


@router.post("/session", response_model=Token)
def create_session(db: Session = Depends(get_db)):
    user = local_service.get_or_create_local_user(db)
    local_service.state.heartbeat()
    access_token = auth_service.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/heartbeat")
def heartbeat(current_user: UserInDB = Depends(get_current_user)):
    local_service.state.heartbeat()
    return {"status": "ok"}


@router.post("/shutdown")
def shutdown(current_user: UserInDB = Depends(get_current_user)):
    local_service.state.shutdown.set()
    return {"status": "shutting down"}
