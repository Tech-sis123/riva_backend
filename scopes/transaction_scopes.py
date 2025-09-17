from sqlalchemy.orm import Session
import models
from datetime import datetime, timedelta, timezone
# from utils.security import get_current_date

def create_transaction(db: Session, wallet_id: int, t_type: str, amount, status: str = "pending", reference: str | None = None):
    tx = models.Transaction(wallet_id=wallet_id, type=t_type, amount=amount, status=status, reference=reference)
    db.add(tx)
    db.flush()
    return tx

def get_by_reference(db: Session, reference: str):
    return db.query(models.Transaction).filter(models.Transaction.reference == reference).first()

def user_has_paid_today(db: Session, wallet_id: int) -> bool:
    tx = db.query(models.Transaction).filter(
            models.Transaction.wallet_id == wallet_id,
            models.Transaction.type == "pay",
            models.Transaction.status == "success",
        ).order_by(models.Transaction.created_at.desc()).first()

    current_time = datetime.now(timezone.utc)

    #check if a transaction was found
    if tx:
        last_transaction_time = tx.created_at

        time_difference = current_time - last_transaction_time

        threshold_24_hours = timedelta(hours=24)

        if time_difference >= threshold_24_hours:
            print("More than 24 hours have elapsed since the last successful pay transaction.")
            return False
        else:
            print("Less than 24 hours have elapsed since the last successful pay transaction.")
            return True
    else:
        print("No successful pay transactions found.")
        return False 


