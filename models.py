# models.py

from cgitb import text
import uuid
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, Boolean, func, Enum
from sqlalchemy.orm import relationship
from db.session import Base
import datetime
from sqlalchemy import text, inspect
from sqlalchemy.orm import declarative_base, Session
import cv2

Base = declarative_base()

class RoleEnum(Enum): 
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
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)

    b_wallet_address = Column(String(255), unique=True, index=True, nullable=True)
    private_key = Column(String(255), unique=True, index=True, nullable=True)

    role = Column(String(20), default=RoleEnum.USER)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    wallet = relationship("Wallet", back_populates="user", uselist=False)
    # The name is now "UserSession" to match the renamed class below.
    sessions = relationship("UserSession", back_populates="user")


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
    type = Column(String(20))
    amount = Column(Numeric(12,2))
    status = Column(String(20), default="pending")
    reference = Column(String(255), unique=True, index=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    wallet = relationship("Wallet", back_populates="transactions")

# The class name has been changed to `UserSession` to avoid conflict.
class UserSession(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    token = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    # The back-reference now points back to the correct model name.
    user = relationship("User", back_populates="sessions")


class Movie(Base):
    __tablename__ = "movies"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    genre = Column(String, nullable=False)
    year = Column(Integer)

    tags = Column(String)  #store as comma-separated string or JSON
    description = Column(String)
    cover = Column(String)  #url to the cover imagd
    url = Column(String) 
    hash = Column(String, unique=True, index=True)  #hash of the video file
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserPreference(Base):
    __tablename__ = "user_preferences"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    genres = Column(String)
    types = Column(String)

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


class MovieFTS(Base):
    __tablename__ = 'movies_fts'
    __table_args__ = {'sqlite_autoincrement': True}
    
    rowid = Column(Integer, primary_key=True)
    title = Column(String)
    genre = Column(String)
    tags = Column(String)

def create_and_populate_fts_table(db: Session):
    inspector = inspect(db.bind)

    if 'movies_fts' not in inspector.get_table_names():
        print("Creating FTS table 'movies_fts'...")
        db.execute(text("""
            CREATE VIRTUAL TABLE movies_fts USING fts5(
                title, 
                genre, 
                tags,
                content='movies',
                content_rowid='id'
            );
        """))
        db.execute(text("""
            INSERT INTO movies_fts(rowid, title, genre, tags)
            SELECT id, title, genre, tags FROM movies;
        """))
        db.commit()
        print("FTS table 'movies_fts' created and populated.")
    else:
        print("FTS table 'movies_fts' already exists.")