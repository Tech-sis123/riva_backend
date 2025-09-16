from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets

from auth_app import models, schemas
from auth_app.database import engine, SessionLocal

# Create DB tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()


# -------------------------------
# Dependency: DB Session
# -------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------------------
# Helpers
# -------------------------------
def get_current_user(token: str = Header(None), db: Session = Depends(get_db)):
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    db_session = db.query(models.Session).filter(models.Session.token == token).first()
    if not db_session or db_session.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return db_session.user


# -------------------------------
# Routes
# -------------------------------

@app.post("/signup")
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    # Create new user
    db_user = models.User(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        password=user.password,  # ⚠️ plain text
        role=user.role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Create session token
    token = secrets.token_hex(32)
    expires = datetime.utcnow() + timedelta(days=30)
    db_session = models.Session(user_id=db_user.id, token=token, expires_at=expires)
    db.add(db_session)
    db.commit()

    return {
        "success": True,
        "token": token,
        "user": {
            "id": db_user.id,
            "first_name": db_user.first_name,
            "last_name": db_user.last_name,
            "email": db_user.email,
            "role": db_user.role,
        },
    }


@app.post("/login")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or db_user.password != user.password:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Create new session token
    token = secrets.token_hex(32)
    expires = datetime.utcnow() + timedelta(days=30)
    db_session = models.Session(user_id=db_user.id, token=token, expires_at=expires)
    db.add(db_session)
    db.commit()

    return {
        "success": True,
        "token": token,
        "user": {
            "id": db_user.id,
            "first_name": db_user.first_name,
            "last_name": db_user.last_name,
            "email": db_user.email,
            "role": db_user.role,
        },
    }


@app.get("/me")
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return {
        "success": True,
        "user": {
            "id": current_user.id,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "email": current_user.email,
            "role": current_user.role,
        },
    }
