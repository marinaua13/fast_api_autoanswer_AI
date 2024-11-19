from fastapi import Depends, HTTPException
from core.dependencies import get_current_user
from models import User


def get_user_by_token(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
