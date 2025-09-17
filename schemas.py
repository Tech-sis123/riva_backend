from pydantic import BaseModel, EmailStr, condecimal, Field
from decimal import Decimal
from typing import Optional, Annotated
from enum import Enum

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class WalletRead(BaseModel):
    balance: Decimal
    currency: str
    class Config:
        from_attributes = True

class TransactionCreate(BaseModel):
    amount: Annotated[Decimal, Field(gt=0, decimal_places=2)]
    type: str

class TransactionRead(BaseModel):
    id: int
    amount: Decimal
    type: str
    status: str
    reference: Optional[str]
    created_at: str
    class Config:
        from_attributes = True

class UserRole(str, Enum):
    user = "user"
    creator = "creator"

class UserBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    role: UserRole = UserRole.user   # default role

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    class Config:
        from_attributes = True
