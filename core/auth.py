from datetime import datetime, timedelta
from typing import Union

from dotenv import load_dotenv
from jose import jwt, JWSError
import os
from passlib.context import CryptContext

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


# hashing password
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# function to create JWT token
def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    # check SECRET_KEY
    if not SECRET_KEY or not isinstance(SECRET_KEY, (str, bytes)):
        raise ValueError("SECRET_KEY is missing or is not a string/bytes")

    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})

    try:
        # create token
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except JWSError as e:
        raise ValueError(f"Failed to encode JWT: {str(e)}")


# to hash the password
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# to check the password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
