from sqlalchemy.orm import Session
import models

def get_wallet_by_user_id(db: Session, user_id: int):
    return db.query(models.Wallet).filter(models.Wallet.user_id == user_id).first()

def get_wallet_by_id_for_update(db: Session, wallet_id: int):
    #lock for safe concurrent updates
    return db.query(models.Wallet).filter(models.Wallet.id == wallet_id).with_for_update().first()

def update_balance(db: Session, wallet: models.Wallet, new_balance):
    wallet.balance = new_balance
    db.add(wallet)
    db.flush()
    return wallet