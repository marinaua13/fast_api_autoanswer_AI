from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.auth import create_access_token, verify_password
from core.dependencies import get_db
from modules.user.schemas import UserCreate, UserResponse, UserLogin
from modules.user.crud import create_user, get_user_by_email


router = APIRouter()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = create_user(db, user)
    return db_user


@router.post("/login")
def login(user_login: UserLogin, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, email=user_login.email)
    if not db_user or not verify_password(user_login.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token_expires = timedelta(minutes=60)
    access_token = create_access_token(
        data={"sub": db_user.email}, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
