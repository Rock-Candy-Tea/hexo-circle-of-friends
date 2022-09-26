import os
from typing import Union
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_or_create_token(password: str):
    password_hash = create_password_hash(password)
    return password_hash
    # try:
    #     payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    #     return payload
    #     username: str = payload.get("sub")
    #     if username is None:
    #         raise credentials_exception
    # except JWTError:
    #     return "123"


def encode_access_token(data: dict, secert_key: str,
                        expires_delta: timedelta = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secert_key, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str, secert_key: str):
    payload = jwt.decode(token, secert_key, algorithms=[ALGORITHM])
    return payload
