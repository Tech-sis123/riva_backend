from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from decimal import Decimal
from db.session import SessionLocal
from services import wallet_service
from utils import security
from scopes import user_scopes, wallet_scopes, transaction_scopes

router = APIRouter(prefix="/wallet", tags=["wallet"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(db: Session = Depends(get_db), authorization: str | None = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing auth")
    token = authorization.split(" ")[1]
    payload = security.decode_access_token(token)
    user_id = int(payload["sub"])
    user = user_scopes.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@router.get("/me", response_model=dict)
def get_my_wallet(user = Depends(get_current_user), db: Session = Depends(get_db)):
    wallet = wallet_service.get_wallet(db, user.id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return {"balance": str(wallet.balance), "currency": wallet.currency}

@router.post("/transfer")
def transfer(destination_email: str, amount: Decimal, user = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        wallet_service.transfer(db, from_user_id=user.id, to_email=destination_email, amount=amount)
        return {"ok": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
