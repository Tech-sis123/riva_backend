from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, func, Enum
from sqlalchemy.orm import relationship
from db.session import Base

class RoleEnum(Enum): #fvgvgtbg
    USER = "user" 
    CREATOR = "creator"

class TransactionTypeEnum(Enum):
    FUND = "fund"
    PAY = "pay"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default=RoleEnum.USER.value)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    wallet = relationship("Wallet", back_populates="user", uselist=False)

class Wallet(Base):
    __tablename__ = "wallets"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    balance = Column(Numeric(12, 2), default=0.00)
    currency = Column(String(3), default="NGN")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="wallet")
    transactions = relationship("Transaction", back_populates="wallet", cascade="all, delete-orphan")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False)
    type = Column(String(20))  #fund, pay
    amount = Column(Numeric(12,2))
    status = Column(String(20), default="pending")
    reference = Column(String(255), unique=True, index=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    wallet = relationship("Wallet", back_populates="transactions")