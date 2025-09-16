from sqlalchemy.orm import Session
import models

def create_transaction(db: Session, wallet_id: int, t_type: str, amount, status: str = "pending", reference: str | None = None):
    tx = models.Transaction(wallet_id=wallet_id, type=t_type, amount=amount, status=status, reference=reference)
    db.add(tx)
    db.flush()
    return tx

def get_by_reference(db: Session, reference: str):
    return db.query(models.Transaction).filter(models.Transaction.reference == reference).first()