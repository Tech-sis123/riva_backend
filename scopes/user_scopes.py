from sqlalchemy.orm import Session
import models

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def create_user(db: Session, email: str, password_hash: str, role: str = "user"):
    user = models.User(email=email, password_hash=password_hash, role=role)
    db.add(user)

    wallet = models.Wallet(user_id=user.id, balance=0.00)
    db.add(wallet)

    db.flush()
    db.commit()
    db.refresh(user)
    return user
