import yaml
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from jwt.exceptions import InvalidTokenError
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from fastapi import Depends, FastAPI, HTTPException, status


from .schemas.user import User
from .schemas.security import TokenData
from .utils import get_table_data


ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
with open('config_secret.yaml', 'r', encoding='utf-8') as file:
    config_secret = yaml.safe_load(file)


def verify_password(plain_password, hashed_password):
    """
    Verifies that a plaintext password matches a hashed password.
    
    Args:
        plain_password (str): The plaintext password input by the user.
        hashed_password (str): The hashed password stored in the database.
    
    Returns:
        bool: True if the password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """
    Hashes a plaintext password using bcrypt.
    
    Args:
        password (str): The plaintext password to hash.
    
    Returns:
        str: The resulting bcrypt hash of the password.
    """
    return pwd_context.hash(password)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, config_secret['HASH_SECRET_KEY'], algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return username
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_user(username: str):
    """
    Retrieves a user record from the 'user_info' table given a username.
    
    Args:
        username (str): The username to look up.
    
    Returns:
        User or None: A User object if the user exists, otherwise None.
    """
    db = get_table_data("users", "user_info")
    if username in db.username.values:
        user_dict = db[db['username'] == username].iloc[0].to_dict()
        return User(**user_dict)


def authenticate_user(username: str, password: str):
    """
    Authenticates a user by verifying their username and password.
    
    Args:
        username (str): The username provided by the client.
        password (str): The password provided by the client.
    
    Returns:
        User or bool: Returns the User object if authentication is successful; otherwise False.
    """
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """
    Creates a signed JWT access token with an optional expiration time.
    
    Args:
        data (dict): The payload to encode in the token (e.g., username).
        expires_delta (timedelta, optional): Token expiration interval. Defaults to 15 minutes if not provided.
    
    Returns:
        str: The encoded JWT access token as a string.
    """
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
