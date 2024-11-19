from datetime import timedelta
from sqlalchemy.orm import Session
from core.auth import create_access_token
from modules.user.schemas import UserLogin
import modules
from modules.user import crud
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def login_user(db: Session, user_login: UserLogin):
    user = modules.user.crud.authenticate_user(db, user_login.email, user_login.password)
    if not user:
        return None

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
