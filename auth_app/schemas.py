from pydantic import BaseModel, EmailStr
from enum import Enum

class UserRole(str, Enum):
    user = "user"
    creator = "creator"

# Shared properties
class UserBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    role: UserRole = UserRole.user   # default role

# For creating users
class UserCreate(UserBase):
    password: str

# For login
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# For returning user info in responses
class UserResponse(UserBase):
    id: int

    class Config:
        orm_mode = True
