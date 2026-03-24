from pydantic import BaseModel, EmailStr
from enum import Enum


class UserRole(str, Enum):
    sme_owner = "sme_owner"
    investor = "investor"
    advisor = "advisor"
    admin = "admin"


# What we expect when someone registers
class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    phone_number: str | None = None
    role: UserRole


# What we expect when someone logs in
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# What we send back to the user (never send password!)
class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    role: UserRole
    is_verified: bool

    class Config:
        from_attributes = True


# Token response after login
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
