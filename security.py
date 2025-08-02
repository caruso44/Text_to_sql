import yaml
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from jwt.exceptions import InvalidTokenError
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from fastapi import Depends, FastAPI, HTTPException, status

from schemas import User, TokenData
from utils import get_table_data



ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(username: str):
    db = get_table_data("users", "user_info")
    if username in db.username.values:
        user_dict = db[db['username'] == username].loc[0].to_dict()
        return User(**user_dict)

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user
    

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    with open("config_secret.yaml", "r") as f:
        config = yaml.safe_load(f)
    HASH_SECRET_KEY = config.get("HASH_SECRET_KEY") 
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, HASH_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
