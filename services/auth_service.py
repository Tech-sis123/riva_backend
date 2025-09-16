from sqlalchemy.orm import Session
from scopes import user_scopes
from utils import security
from config import settings

def signup(db: Session, email: str, password: str):
    existing = user_scopes.get_user_by_email(db, email)
    if existing:
        raise ValueError("Email already registered")
    
    hashed = security.hash_password(password)
    user = user_scopes.create_user(db, email, hashed)
    token = security.create_access_token(subject=str(user.id))
    return {"user_id": user.id, "access_token": token}


