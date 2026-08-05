"""Authentication endpoints: register, login, current user."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.logging import log_event
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    if db.query(User).filter(User.email == body.email.lower()).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "email already registered")
    first_user = db.query(User).count() == 0
    user = User(
        email=body.email.lower(),
        name=body.name,
        hashed_password=hash_password(body.password),
        is_admin=first_user and get_settings().FIRST_USER_IS_ADMIN,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log_event(db, "INFO", f"user registered: {user.email}", context={"user_id": user.id})
    return TokenResponse(access_token=create_access_token(str(user.id)))


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.email == body.email.lower()).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid email or password")
    return TokenResponse(access_token=create_access_token(str(user.id)))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)
