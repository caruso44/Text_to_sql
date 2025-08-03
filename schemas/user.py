from pydantic import BaseModel


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