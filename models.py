import uuid
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, Boolean, func, Enum
from sqlalchemy.orm import relationship
from db.session import Base
import datetime

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
    # password = Column(String(200), nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)

    role = Column(String(20), default=RoleEnum.USER)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    wallet = relationship("Wallet", back_populates="user", uselist=False)
    sessions = relationship("Session", back_populates="user")


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


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    token = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="sessions")


class Movie(Base):
    __tablename__ = "movies"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    genre = Column(String, nullable=False)
    year = Column(Integer)
    tags = Column(String)  # store as comma-separated string or JSON
    description = Column(String)
    cover = Column(String)  # URL


class UserPreference(Base):
    __tablename__ = "user_preferences"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    genres = Column(String)  # e.g. "Action,Comedy,Drama"
    types = Column(String)   # e.g. "Series,Full Movie"

class ShareCode(Base):
    __tablename__ = "share_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"))
    shared_by = Column(Integer, ForeignKey("users.id"))
    shared_with = Column(Integer, ForeignKey("users.id"), nullable=True)
    redeemed = Column(Boolean, default=False)
    expires_at = Column(DateTime, default=lambda: datetime.datetime.utcnow() + datetime.timedelta(days=1))

    movie = relationship("Movie")