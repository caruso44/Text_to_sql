from pydantic import BaseModel


class SessionData(BaseModel):
    session_name: str


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None
    hashed_password: str

class UserCredentials(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    password: str | None = None


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None