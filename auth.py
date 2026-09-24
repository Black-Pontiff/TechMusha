from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..db import get_db
from ..models import User
from ..schemas import SignupIn, LoginIn, TokenOut, UserOut
from ..security import hash_password, verify_password, make_access, make_refresh, decode
from ..deps import current_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=TokenOut)
def signup(body: SignupIn, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == body.email)):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already in use")
    user = User(name=body.name, email=body.email, phone=body.phone,
                password_hash=hash_password(body.password))
    db.add(user); db.commit(); db.refresh(user)
    return TokenOut(access_token=make_access(user.id), refresh_token=make_refresh(user.id))

@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    return TokenOut(access_token=make_access(user.id), refresh_token=make_refresh(user.id))

@router.post("/refresh", response_model=TokenOut)
def refresh(refresh_token: str = Body(..., embed=True)):
    uid = decode(refresh_token, "refresh")
    if not uid:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")
    return TokenOut(access_token=make_access(uid), refresh_token=make_refresh(uid))

@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user